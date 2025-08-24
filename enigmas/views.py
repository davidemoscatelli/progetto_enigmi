# enigmas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as BaseLoginView
from django.utils import timezone
from django.db.models import Sum, F, Q, Value, FloatField
from django.contrib import messages
from .models import Enigma, Allegato, CampoRisposta, RispostaUtente, RispostaUtenteMultipla, UserBadge, Notifica, OpzioneRisposta, Profile
from .forms import RispostaCheckboxForm
from django.contrib.auth.models import User
from django.db.models.functions import Coalesce
from django.urls import reverse_lazy
from allauth.account.views import SignupView

@login_required
def enigma_view(request):
    now = timezone.now()
    enigma_corrente = Enigma.objects.filter(is_active=True, start_time__lte=now).first()

    if not enigma_corrente:
        return render(request, 'enigmas/enigma_detail.html', {'messaggio_attesa': 'Nessun enigma attivo.'})
    if enigma_corrente.end_time < now:
        return render(request, 'enigmas/enigma_detail.html', {'messaggio_scaduto': 'Tempo scaduto!'})

    delta = enigma_corrente.end_time - now
    time_remaining = {
        'days': delta.days, 'hours': delta.seconds // 3600,
        'minutes': (delta.seconds % 3600) // 60, 'seconds': delta.seconds % 60
    }
    
    allegati = Allegato.objects.filter(enigma=enigma_corrente)
    campi_risposta = CampoRisposta.objects.filter(enigma=enigma_corrente).order_by('ordine')

    try:
        risposta_generale = RispostaUtente.objects.get(utente=request.user, enigma=enigma_corrente)
        risposte_date = RispostaUtenteMultipla.objects.filter(risposta_generale=risposta_generale)
        return render(request, 'enigmas/enigma_detail.html', {
            'enigma': enigma_corrente, 'allegati': allegati, 'risposte_date': risposte_date,
            'risposta_generale': risposta_generale, 'time_remaining': time_remaining
        })
    except RispostaUtente.DoesNotExist:
        pass

    if request.method == 'POST':
        form = RispostaCheckboxForm(request.POST, campi_risposta=campi_risposta)
        if form.is_valid():
            risposta_generale = RispostaUtente.objects.create(utente=request.user, enigma=enigma_corrente)
            
            punteggio_finale = 0
            domanda_principale_corretta = False
            tutte_le_risposte_corrette = True

            for campo in campi_risposta:
                opzioni_selezionate = form.cleaned_data[f'campo_{campo.id}']
                testo_risposta_utente = ", ".join(sorted([opzione.testo for opzione in opzioni_selezionate]))
                
                risposta_multipla = RispostaUtenteMultipla.objects.create(
                    risposta_generale=risposta_generale,
                    campo=campo,
                    valore_inserito=testo_risposta_utente
                )
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
            
            risposta_generale.punteggio = round(punteggio_finale, 2)
            risposta_generale.is_completa_corretta = tutte_le_risposte_corrette
            risposta_generale.save()

            messages.success(request, "La tua soluzione è stata inviata!")
            return redirect('enigma_view')
    else:
        form = RispostaCheckboxForm(campi_risposta=campi_risposta)

    context = {
        'enigma': enigma_corrente, 'allegati': allegati,
        'form': form, 'time_remaining': time_remaining
    }
    return render(request, 'enigmas/enigma_detail.html', context)

# --- VISTA CLASSIFICA MODIFICATA ---
@login_required
def classifica_view(request):
    utenti = User.objects.filter(
        is_active=True,
        is_staff=False,      # Esclude lo staff dalla classifica
        is_superuser=False   # Esclude i superuser dalla classifica
    ).annotate(
        punti_da_risposte=Coalesce(
            Sum('risposte__punteggio', filter=Q(risposte__is_completa_corretta=True)),
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
    ).order_by('-punteggio_totale_reale', 'username') # Rimosso il filtro che escludeva gli zeri
    
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