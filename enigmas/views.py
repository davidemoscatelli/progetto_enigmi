# enigmas/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView as BaseLoginView
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Sum
from django.contrib import messages # Per mostrare messaggi all'utente
from .models import Enigma, RispostaUtente, Suggerimento, UserBadge, Notifica, MessaggioEnigmista
from .forms import RispostaForm # Creeremo questo form tra poco
from django.contrib.auth.models import User
from django.http import JsonResponse, Http404, HttpResponseForbidden
from django.views.decorators.http import require_POST


@login_required
def enigma_view(request):
    enigma_corrente = None
    risposta_precedente = None
    messaggio_attesa = None
    tempo_rimanente_ms = 0
    suggerimenti_visti = []
    suggerimenti_usati_count = 0
    max_suggerimenti = 3

    # Trova l'enigma attivo e valido
    try:
        enigma_attivo = Enigma.objects.get(is_active=True, start_time__lte=timezone.now())
        if timezone.now() <= enigma_attivo.end_time:
            enigma_corrente = enigma_attivo
        else:
            messaggio_attesa = "L'enigma corrente è scaduto. Attendi il prossimo!"
    except Enigma.DoesNotExist:
        messaggio_attesa = "Nessun enigma attivo al momento. Attendi il prossimo!"
    except Enigma.MultipleObjectsReturned:
        # Logga questo errore! E prendi il più recente come fallback
        enigma_corrente = Enigma.objects.filter(is_active=True, start_time__lte=timezone.now()).order_by('-start_time').first()
        if enigma_corrente and timezone.now() > enigma_corrente.end_time:
             enigma_corrente = None # Era attivo ma è scaduto nel frattempo
        messaggio_attesa = "Errore: più enigmi attivi trovati. Contatta l'amministratore." if enigma_corrente else "Errore: più enigmi attivi trovati (e scaduti)."


    # Se abbiamo trovato un enigma valido, procedi
    if enigma_corrente:
        # Recupera la risposta precedente dell'utente (se esiste)
        try:
            risposta_precedente = RispostaUtente.objects.get(utente=request.user, enigma=enigma_corrente)
            suggerimenti_usati_count = risposta_precedente.suggerimenti_usati
            if suggerimenti_usati_count > 0:
                 suggerimenti_visti = list(Suggerimento.objects.filter(
                     enigma=enigma_corrente,
                     ordine__lte=suggerimenti_usati_count
                 ).order_by('ordine').values_list('testo', flat=True))
        except RispostaUtente.DoesNotExist:
            risposta_precedente = None # Assicurati sia None se non trovata
            suggerimenti_usati_count = 0
            suggerimenti_visti = []

        # --- CALCOLO FLAG BOOLEANI PER IL TEMPLATE ---
        utente_ha_risposto = risposta_precedente is not None
        risposta_utente_corretta = utente_ha_risposto and risposta_precedente.is_corretta

        # Mostra form/timer se non ha risposto correttamente E l'enigma non è scaduto
        mostra_interfaccia_risposta = not risposta_utente_corretta # and enigma_corrente.end_time > timezone.now() # Già implicito perché enigma_corrente è None se scaduto

        mostra_timer = False
        if mostra_interfaccia_risposta:
            tempo_rimasto_delta = enigma_corrente.end_time - timezone.now()
            tempo_rimanente_ms = max(0, int(tempo_rimasto_delta.total_seconds() * 1000))
            if tempo_rimanente_ms > 0:
                mostra_timer = True # Mostra timer solo se c'è tempo > 0

        # Determina se l'utente può chiedere un hint
        puo_chiedere_hint = mostra_interfaccia_risposta and suggerimenti_usati_count < max_suggerimenti
        # -----------------------------------------------

        # Gestione POST (invio risposta) - rimane quasi uguale
        if request.method == 'POST' and mostra_interfaccia_risposta: # Aggiunto check mostra_interfaccia_risposta
            form = RispostaForm(request.POST)
            if form.is_valid():
                if timezone.now() > enigma_corrente.end_time:
                    messages.error(request, "Tempo scaduto! Non puoi più inviare la risposta.")
                    return redirect('enigma_view')

                risposta_utente_obj, created = RispostaUtente.objects.get_or_create(
                    utente=request.user,
                    enigma=enigma_corrente,
                    defaults={'risposta_inserita': form.cleaned_data['risposta_inserita']}
                )

                if not created and not risposta_utente_obj.is_corretta:
                    risposta_utente_obj.risposta_inserita = form.cleaned_data['risposta_inserita']
                    # Se permettessimo tentativi multipli, aggiorneremmo anche qui

                # Il save() del modello calcola is_corretta e punteggio (con penalità hint)
                risposta_utente_obj.save()

                if risposta_utente_obj.is_corretta:
                    messages.success(request, f"Risposta corretta! Hai ottenuto {risposta_utente_obj.punteggio:.2f} punti.")
                else:
                    messages.warning(request, "Risposta errata.")

                return redirect('enigma_view') # Ricarica per vedere stato aggiornato
        else:
            # Se è GET o se non deve mostrare interfaccia risposta, inizializza form vuoto (o None)
            form = RispostaForm() if mostra_interfaccia_risposta else None

    else: # Se non c'è un enigma corrente valido
        form = None

    ultimo_messaggio = MessaggioEnigmista.objects.filter(
        pubblicato=True,
        data_pubblicazione__lte=timezone.now() # Mostra solo quelli la cui data è passata
    ).order_by('-data_pubblicazione').first() # Prendi solo il più recente

    # Contesto per il template
    context = {
        'enigma': enigma_corrente,
        'form': form, # Sarà None se l'utente ha già risposto correttamente
        'risposta_precedente': risposta_precedente, # Utile per mostrare la risposta data
        'messaggio_attesa': messaggio_attesa,
        'tempo_rimanente_ms': tempo_rimanente_ms, # Per il timer JS

        # Nuovi Flag Booleani Semplici
        'mostra_timer': mostra_timer,
        'mostra_form_risposta': mostra_interfaccia_risposta, # Usato per mostrare il form
        'utente_ha_risposto': utente_ha_risposto,
        'risposta_utente_corretta': risposta_utente_corretta,
        'puo_chiedere_hint': puo_chiedere_hint,

        # Dati per i Suggerimenti
        'suggerimenti_visti': suggerimenti_visti,
        'suggerimenti_usati_count': suggerimenti_usati_count,
        'max_suggerimenti': max_suggerimenti,
        'ultimo_messaggio_enigmista': ultimo_messaggio,
    }
    return render(request, 'enigmas/enigma_detail.html', context)

# La view richiedi_suggerimento rimane INVARIATA rispetto a prima
@login_required
@require_POST
def richiedi_suggerimento(request, enigma_id):
    # ... (stesso codice di prima) ...
    enigma = get_object_or_404(Enigma, pk=enigma_id)
    utente = request.user
    MAX_HINTS_ALLOWED = 3

    if enigma.end_time < timezone.now():
         return JsonResponse({'success': False, 'error': 'Tempo scaduto per questo enigma.'}, status=403)

    risposta_utente, created = RispostaUtente.objects.get_or_create(
        utente=utente,
        enigma=enigma
    )

    if risposta_utente.is_corretta:
         return JsonResponse({'success': False, 'error': 'Hai già risposto correttamente!'}, status=400)

    hints_usati = risposta_utente.suggerimenti_usati
    ordine_prossimo_hint = hints_usati + 1

    if ordine_prossimo_hint > MAX_HINTS_ALLOWED:
        return JsonResponse({'success': False, 'error': f'Hai già usato tutti i {MAX_HINTS_ALLOWED} suggerimenti disponibili!'}, status=400)

    try:
        prossimo_suggerimento = Suggerimento.objects.get(enigma=enigma, ordine=ordine_prossimo_hint)
    except Suggerimento.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Non ci sono altri suggerimenti disponibili per questo enigma.'}, status=404)

    risposta_utente.suggerimenti_usati += 1
    risposta_utente.save(update_fields=['suggerimenti_usati'])

    return JsonResponse({
        'success': True,
        'testo_suggerimento': prossimo_suggerimento.testo,
        'suggerimenti_usati_ora': risposta_utente.suggerimenti_usati
    })

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

@login_required
@require_POST # Accetta solo richieste POST per cambiare stato (incrementare hint)
def richiedi_suggerimento(request, enigma_id):
    """Gestisce la richiesta AJAX per un suggerimento."""
    enigma = get_object_or_404(Enigma, pk=enigma_id)
    utente = request.user
    MAX_HINTS_ALLOWED = 3 # Massimo suggerimenti consentiti

    # Controlla se l'enigma è ancora valido per richiedere hint
    if enigma.end_time < timezone.now():
        return JsonResponse({'success': False, 'error': 'Tempo scaduto per questo enigma.'}, status=403) # 403 Forbidden

    # Trova o crea la RispostaUtente per tracciare gli hint
    # Usiamo get_or_create così funziona anche se l'utente non ha ancora inviato risposte
    risposta_utente, created = RispostaUtente.objects.get_or_create(
        utente=utente,
        enigma=enigma
        # I valori di default del modello (punteggio=0, suggerimenti_usati=0) vanno bene
    )

    # Non dare hint se ha già risposto correttamente
    if risposta_utente.is_corretta:
        return JsonResponse({'success': False, 'error': 'Hai già risposto correttamente!'}, status=400) # 400 Bad Request

    # Controlla quanti suggerimenti ha già usato
    hints_usati = risposta_utente.suggerimenti_usati
    ordine_prossimo_hint = hints_usati + 1

    # Controlla se ha superato il limite massimo
    if ordine_prossimo_hint > MAX_HINTS_ALLOWED:
        return JsonResponse({'success': False, 'error': f'Hai già usato tutti i {MAX_HINTS_ALLOWED} suggerimenti disponibili!'}, status=400) # 400 Bad Request

    # Cerca il prossimo suggerimento nel database
    try:
        prossimo_suggerimento = Suggerimento.objects.get(enigma=enigma, ordine=ordine_prossimo_hint)
    except Suggerimento.DoesNotExist:
        # Se non esiste un suggerimento con quell'ordine per questo enigma
        return JsonResponse({'success': False, 'error': 'Non ci sono altri suggerimenti disponibili per questo enigma.'}, status=404) # 404 Not Found

    # Se tutto ok, incrementa il contatore e salva SOLO quel campo
    risposta_utente.suggerimenti_usati += 1
    risposta_utente.save(update_fields=['suggerimenti_usati'])

    # Restituisci successo, il testo del suggerimento e il nuovo conteggio
    return JsonResponse({
        'success': True,
        'testo_suggerimento': prossimo_suggerimento.testo,
        'suggerimenti_usati_ora': risposta_utente.suggerimenti_usati
    })

def profile_view(request, username):
    """Mostra il profilo di un utente specifico."""
    profile_user = get_object_or_404(User, username=username)

    # Recupera punteggio totale (come prima)
    punteggio_totale_obj = RispostaUtente.objects.filter(
        utente=profile_user,
        is_corretta=True
    ).aggregate(punteggio_totale=Sum('punteggio'))
    punteggio_totale = punteggio_totale_obj['punteggio_totale'] or 0

    # --- NUOVA QUERY: Recupera i badge ottenuti dall'utente ---
    # Usiamo select_related('badge') per caricare anche i dati del Badge
    # correlato in un'unica query più efficiente.
    badges_utente = UserBadge.objects.filter(utente=profile_user).select_related('badge')
    # ----------------------------------------------------------

    context = {
        'profile_user': profile_user,
        'punteggio_totale': punteggio_totale,
        'badges': badges_utente, # <-- Passiamo i badge al template
    }
    return render(request, 'enigmas/profile_detail.html', context)

@login_required
def my_profile_view(request):
    """Reindirizza alla pagina del profilo dell'utente loggato."""
    # Questo evita di dover passare l'username nell'URL per il proprio profilo
    return redirect('profile_view', username=request.user.username)

@login_required
def lista_notifiche(request):
    """
    Mostra l'elenco delle notifiche per l'utente loggato
    e le segna tutte come lette.
    """
    # Recupera tutte le notifiche, le più recenti prima
    notifiche = Notifica.objects.filter(utente=request.user).order_by('-data_creazione')

    # Segna come lette quelle non ancora lette PRIMA di passarle al template
    # Così nel template possiamo ancora distinguerle se vogliamo, ma il contatore si azzererà
    unread_notifications = notifiche.filter(letta=False)
    unread_notifications_count_now = unread_notifications.count() # Conteggio prima di aggiornare
    if unread_notifications_count_now > 0:
        unread_notifications.update(letta=True)
        print(f"INFO: Segnate {unread_notifications_count_now} notifiche come lette per {request.user.username}")

    context = {
        'notifiche': notifiche
    }
    return render(request, 'enigmas/lista_notifiche.html', context)

