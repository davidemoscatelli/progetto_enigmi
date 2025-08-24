# enigmas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F, Q, Value, FloatField
from django.contrib import messages
from .models import Enigma, Allegato, CampoRisposta, RispostaUtente, RispostaUtenteMultipla, UserBadge, Notifica, OpzioneRisposta, Profile, Suggerimento
from .forms import RispostaCheckboxForm
from django.contrib.auth.models import User
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from allauth.account.views import SignupView
from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
def enigma_view(request):
    now = timezone.now()
    enigma_corrente = Enigma.objects.filter(is_active=True, start_time__lte=now).first()

    if not enigma_corrente:
        return render(request, 'enigmas/enigma_detail.html', {'messaggio_attesa': 'Nessun enigma attivo.'})
    if enigma_corrente.end_time < now:
        return render(request, 'enigmas/enigma_detail.html', {'messaggio_scaduto': 'Tempo scaduto!'})

    delta = enigma_corrente.end_time - now
    time_remaining = {'days': delta.days, 'hours': delta.seconds // 3600, 'minutes': (delta.seconds % 3600) // 60, 'seconds': delta.seconds % 60}
    
    allegati = Allegato.objects.filter(enigma=enigma_corrente)
    campi_risposta = CampoRisposta.objects.filter(enigma=enigma_corrente).order_by('ordine')
    
    risposta_generale = RispostaUtente.objects.filter(utente=request.user, enigma=enigma_corrente).first()
    
    if risposta_generale and risposta_generale.risposte_multiple.exists():
        risposte_date = risposta_generale.risposte_multiple.all()
        return render(request, 'enigmas/enigma_detail.html', {
            'enigma': enigma_corrente, 'allegati': allegati, 'risposte_date': risposte_date,
            'risposta_generale': risposta_generale, 'time_remaining': time_remaining
        })

    if request.method == 'POST':
        form = RispostaCheckboxForm(request.POST, campi_risposta=campi_risposta)
        if form.is_valid():
            risposta_generale, created = RispostaUtente.objects.get_or_create(utente=request.user, enigma=enigma_corrente)
            
            punteggio_finale = 0
            domanda_principale_corretta = False
            tutte_le_risposte_corrette = True

            for campo in campi_risposta:
                opzioni_selezionate = form.cleaned_data[f'campo_{campo.id}']
                testo_risposta_utente = ", ".join(sorted([opzione.testo for opzione in opzioni_selezionate]))
                risposta_multipla = RispostaUtenteMultipla.objects.create(risposta_generale=risposta_generale, campo=campo, valore_inserito=testo_risposta_utente)
                is_this_field_correct = risposta_multipla.is_corretta()
                if campo.is_domanda_principale and is_this_field_correct:
                    domanda_principale_corretta = True
                if not is_this_field_correct:
                    tutte_le_risposte_corrette = False
            
            if domanda_principale_corretta:
                punteggio_finale += 50
                punteggio_aggiuntivo_per_domanda = 25
                for risposta_obj in risposta_generale.risposte_multiple.all():
                    if not risposta_obj.campo.is_domanda_principale and risposta_obj.is_corretta():
                        punteggio_finale += punteggio_aggiuntivo_per_domanda
                
                secondi_totali = (enigma_corrente.end_time - enigma_corrente.start_time).total_seconds()
                secondi_rimanenti = (enigma_corrente.end_time - timezone.now()).total_seconds()
                bonus_tempo = 50 * (max(0, secondi_rimanenti) / secondi_totali)
                punteggio_finale += bonus_tempo
                
                penalita_aiuti = risposta_generale.suggerimenti_usati * 15
                punteggio_finale -= penalita_aiuti
            
            risposta_generale.punteggio = round(max(0, punteggio_finale), 2)
            risposta_generale.is_completa_corretta = tutte_le_risposte_corrette
            risposta_generale.save()

            messages.success(request, "La tua soluzione è stata inviata!")
            return redirect('enigma_view')
    else:
        form = RispostaCheckboxForm(campi_risposta=campi_risposta)

    risposta_temp, _ = RispostaUtente.objects.get_or_create(utente=request.user, enigma=enigma_corrente)
    suggerimenti_visti = Suggerimento.objects.filter(enigma=enigma_corrente, ordine__lte=risposta_temp.suggerimenti_usati).order_by('ordine')

    context = {
        'enigma': enigma_corrente, 'allegati': allegati, 'form': form, 'time_remaining': time_remaining,
        'suggerimenti_visti': suggerimenti_visti,
        'aiuti_usati': risposta_temp.suggerimenti_usati,
        'max_aiuti': 3
    }
    return render(request, 'enigmas/enigma_detail.html', context)

@login_required
@require_POST
def richiedi_aiuto_view(request, enigma_id):
    enigma = get_object_or_404(Enigma, pk=enigma_id)
    if enigma.end_time < timezone.now():
        return JsonResponse({'success': False, 'error': 'Tempo scaduto!'}, status=403)

    risposta_generale, created = RispostaUtente.objects.get_or_create(utente=request.user, enigma=enigma)

    if risposta_generale.is_completa_corretta:
        return JsonResponse({'success': False, 'error': 'Hai già risolto questo enigma!'}, status=400)

    prossimo_aiuto_ordine = risposta_generale.suggerimenti_usati + 1
    max_aiuti = 3

    if prossimo_aiuto_ordine > max_aiuti:
        return JsonResponse({'success': False, 'error': f'Hai già usato tutti gli {max_aiuti} aiuti disponibili.'}, status=400)

    try:
        aiuto = Suggerimento.objects.get(enigma=enigma, ordine=prossimo_aiuto_ordine)
        risposta_generale.suggerimenti_usati = prossimo_aiuto_ordine
        risposta_generale.save(update_fields=['suggerimenti_usati'])
        return JsonResponse({'success': True, 'testo_aiuto': aiuto.testo, 'aiuti_usati': risposta_generale.suggerimenti_usati, 'max_aiuti': max_aiuti})
    except Suggerimento.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Non ci sono altri aiuti disponibili.'}, status=404)

@login_required
def classifica_view(request):
    utenti = User.objects.filter(
        is_active=True, 
        is_staff=False, 
        is_superuser=False
    ).annotate(
        # CORREZIONE: Rimuoviamo il filtro. La logica del punteggio è già nel campo 'punteggio'.
        # Se la domanda principale è sbagliata, il punteggio è già 0.
        punti_da_risposte=Coalesce(
            Sum('risposte__punteggio'), 
            Value(0.0), 
            output_field=FloatField()
        ),
        punti_bonus=Coalesce(
            F('profile__punteggio_bonus'), 
            Value(0.0), 
            output_field=FloatField()
        )
    ).annotate(
        punteggio_totale_reale=F('punti_da_risposte') + F('punti_bonus')
    ).order_by('-punteggio_totale_reale', 'username')
    
    context = {'classifica': utenti}
    return render(request, 'enigmas/classifica.html', context)

@login_required
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    risposte = RispostaUtente.objects.filter(utente=profile_user).select_related('enigma').order_by('-enigma__start_time')
    badges_utente = UserBadge.objects.filter(utente=profile_user).select_related('badge')
    context = {'profile_user': profile_user, 'risposte': risposte, 'badges': badges_utente}
    return render(request, 'enigmas/profile_detail.html', context)

@login_required
def my_profile_view(request):
    return redirect('profile_view', username=request.user.username)

@login_required
def lista_notifiche(request):
    notifiche = Notifica.objects.filter(utente=request.user)
    notifiche.filter(letta=False).update(letta=True)
    return render(request, 'enigmas/lista_notifiche.html', {'notifiche': notifiche})

@login_required
def regole_punteggio_view(request):
    return render(request, 'enigmas/regole_punteggio.html')

class CustomSignupView(SignupView):
    success_url = reverse_lazy("account_inactive")

def account_inactive_view(request):
    return render(request, 'account/account_inactive.html')
