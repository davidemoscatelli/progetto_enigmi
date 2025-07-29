# enigmas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as BaseLoginView
from django.utils import timezone
from django.db.models import Sum, Q, Value, FloatField, F
from django.contrib import messages
from .models import Enigma, Allegato, CampoRisposta, RispostaUtente, RispostaUtenteMultipla, UserBadge, Notifica
from .forms import RispostaMultiplaForm
from django.contrib.auth.models import User
from django.db.models.functions import Coalesce

@login_required
def enigma_view(request):
    now = timezone.now()
    enigma_corrente = Enigma.objects.filter(is_active=True, start_time__lte=now).first()

    if not enigma_corrente:
        return render(request, 'enigmas/enigma_detail.html', {'messaggio_attesa': 'Nessun enigma attivo.'})
    if enigma_corrente.end_time < now:
        return render(request, 'enigmas/enigma_detail.html', {'messaggio_scaduto': 'Tempo scaduto!'})

    # --- CALCOLO DEL TEMPO CORRETTO ---
    delta = enigma_corrente.end_time - now
    time_remaining = {
        'days': delta.days,
        'hours': delta.seconds // 3600,
        'minutes': (delta.seconds % 3600) // 60,
        'seconds': delta.seconds % 60
    }
    # --- FINE CALCOLO ---
    
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
        form = RispostaMultiplaForm(request.POST, campi_risposta=campi_risposta)
        if form.is_valid():
            risposta_generale = RispostaUtente.objects.create(utente=request.user, enigma=enigma_corrente)
            
            punteggio_finale = 0
            domanda_principale_corretta = False
            tutte_le_risposte_corrette = True
            risposte_salvate = []
            
            for campo in campi_risposta:
                valore_inserito = form.cleaned_data[f'campo_{campo.id}']
                risposta_obj = RispostaUtenteMultipla(
                    risposta_generale=risposta_generale, campo=campo, valore_inserito=valore_inserito)
                risposta_obj.save()
                risposte_salvate.append(risposta_obj)
                risposta_corretta = risposta_obj.is_corretta()
                if campo.is_domanda_principale and risposta_corretta:
                    domanda_principale_corretta = True
                if not risposta_corretta:
                    tutte_le_risposte_corrette = False
            
            if domanda_principale_corretta:
                punteggio_finale += 50
                punteggio_aggiuntivo_per_domanda = 25
                for risposta_obj in risposte_salvate:
                    if not risposta_obj.campo.is_domanda_principale and risposta_obj.is_corretta():
                        punteggio_finale += punteggio_aggiuntivo_per_domanda
                
                secondi_totali = (enigma_corrente.end_time - enigma_corrente.start_time).total_seconds()
                secondi_rimanenti = (enigma_corrente.end_time - timezone.now()).total_seconds()
                if secondi_rimanenti < 0:
                    secondi_rimanenti = 0
                bonus_tempo = 50 * (secondi_rimanenti / secondi_totali)
                punteggio_finale += bonus_tempo
            
            risposta_generale.punteggio = round(punteggio_finale, 2)
            risposta_generale.is_completa_corretta = tutte_le_risposte_corrette
            risposta_generale.save()

            messages.success(request, "La tua soluzione è stata inviata!")
            return redirect('enigma_view')
    else:
        form = RispostaMultiplaForm(campi_risposta=campi_risposta)

    context = {
        'enigma': enigma_corrente, 'allegati': allegati,
        'form': form, 'time_remaining': time_remaining
    }
    return render(request, 'enigmas/enigma_detail.html', context)


@login_required
def classifica_view(request):
    utenti = User.objects.filter(is_active=True).annotate(
        punti_da_risposte=Coalesce(Sum('risposte__punteggio'), Value(0.0)),
        punti_bonus=Coalesce(F('profile__punteggio_bonus'), Value(0.0))
    ).annotate(
        punteggio_totale_reale=F('punti_da_risposte') + F('punti_bonus')
    ).filter(punteggio_totale_reale__gt=0).order_by('-punteggio_totale_reale', 'username')
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

class CustomLoginView(BaseLoginView):
    template_name = 'enigmas/login.html'

 
class CustomSignupView(SignupView):
    # Dopo una registrazione andata a buon fine, reindirizza sempre
    # alla pagina che mostra il messaggio di "account inattivo".
    success_url = reverse_lazy("account_inactive")
