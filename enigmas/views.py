# enigmas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as BaseLoginView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages # Per mostrare messaggi all'utente
from .models import Enigma, RispostaUtente
from .forms import RispostaForm # Creeremo questo form tra poco
from django.contrib.auth.models import User

@login_required # Richiede che l'utente sia loggato per accedere
def enigma_view(request):
    try:
        # Trova l'unico enigma attivo
        enigma_corrente = Enigma.objects.get(is_active=True, start_time__lte=timezone.now())
        now = timezone.now()

        # Controlla se l'enigma è scaduto
        if now > enigma_corrente.end_time:
             enigma_corrente = None # Non mostrare enigmi scaduti come attivi
             messaggio_attesa = "L'enigma corrente è scaduto. Attendi il prossimo!"
        else:
             messaggio_attesa = None

    except Enigma.DoesNotExist:
        enigma_corrente = None
        messaggio_attesa = "Nessun enigma attivo al momento. Attendi il prossimo!"
    except Enigma.MultipleObjectsReturned:
        # Questo non dovrebbe accadere se l'admin gestisce bene is_active
        # Potresti loggare un errore qui
        enigma_corrente = Enigma.objects.filter(is_active=True, start_time__lte=timezone.now()).order_by('-start_time').first()
        if enigma_corrente and timezone.now() > enigma_corrente.end_time:
             enigma_corrente = None
        messaggio_attesa = "Errore: più enigmi attivi trovati. Contatta l'amministratore."


    risposta_precedente = None
    form = None
    tempo_rimanente_ms = 0 # Tempo rimanente in millisecondi per il timer JS

    if enigma_corrente:
        # Controlla se l'utente ha già risposto a questo enigma
        try:
            risposta_precedente = RispostaUtente.objects.get(utente=request.user, enigma=enigma_corrente)
        except RispostaUtente.DoesNotExist:
            risposta_precedente = None

        if not risposta_precedente:
            # Calcola il tempo rimanente solo se l'utente non ha risposto
            tempo_rimasto_delta = enigma_corrente.end_time - timezone.now()
            tempo_rimanente_ms = max(0, int(tempo_rimasto_delta.total_seconds() * 1000))

            if request.method == 'POST':
                form = RispostaForm(request.POST)
                if form.is_valid():
                    # Controlla di nuovo se il tempo è scaduto prima di salvare
                    if timezone.now() > enigma_corrente.end_time:
                         messages.error(request, "Tempo scaduto! Non puoi più inviare la risposta.")
                         return redirect('enigma_view') # Ricarica la pagina

                    # Crea l'oggetto RispostaUtente ma non salvarlo ancora nel DB
                    nuova_risposta = form.save(commit=False)
                    nuova_risposta.utente = request.user
                    nuova_risposta.enigma = enigma_corrente
                    # Il check della correttezza e il calcolo del punteggio avvengono nel save() del modello
                    nuova_risposta.save()

                    if nuova_risposta.is_corretta:
                        messages.success(request, f"Risposta corretta! Hai ottenuto {nuova_risposta.punteggio:.2f} punti.")
                    else:
                        messages.warning(request, "Risposta errata.")

                    return redirect('enigma_view') # Ricarica la pagina per mostrare il messaggio/stato
            else:
                form = RispostaForm() # Mostra un form vuoto
        else:
             # L'utente ha già risposto, non mostrare il form
             form = None

    context = {
        'enigma': enigma_corrente,
        'form': form,
        'risposta_precedente': risposta_precedente,
        'messaggio_attesa': messaggio_attesa,
        'tempo_rimanente_ms': tempo_rimanente_ms, # Passa al template per JS
    }
    return render(request, 'enigmas/enigma_detail.html', context)

@login_required
def classifica_view(request):
    # Raggruppa le risposte corrette per utente e somma i punteggi
    classifica_data = RispostaUtente.objects.filter(is_corretta=True)\
        .values('utente__username')\
        .annotate(punteggio_totale=Sum('punteggio'))\
        .order_by('-punteggio_totale') # Ordina per punteggio decrescente

    context = {
        'classifica': classifica_data,
    }
    return render(request, 'enigmas/classifica.html', context)

# Vista per il login (usa quella built-in di Django ma personalizza il template)
class CustomLoginView(BaseLoginView):
    template_name = 'enigmas/login.html' # Specifichiamo il nostro template
    # Puoi aggiungere extra_context se necessario
    # success_url = reverse_lazy('enigma_view') # Dove reindirizzare dopo il login (opzionale, default è ACCOUNTS_PROFILE_REDIRECT o /accounts/profile/)

# Nota: La registrazione utente non è inclusa qui per semplicità,
# ma potresti aggiungerla usando `django.contrib.auth.forms.UserCreationForm`
# e una vista dedicata.

# Vista per il logout (usa quella built-in)
# Non serve una vista custom se non hai logiche particolari,
# basta definire l'URL come vedremo dopo.

@login_required # Manteniamo la coerenza: solo gli utenti loggati vedono le regole
def regole_punteggio_view(request):
    """
    Mostra la pagina statica che spiega come viene calcolato il punteggio.
    """
    # Non servono dati dal database, basta renderizzare il template
    return render(request, 'enigmas/regole_punteggio.html')
