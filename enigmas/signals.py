# enigmas/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile, RispostaUtente, Badge, UserBadge

@receiver(post_save, sender=User)
def crea_o_aggiorna_profilo_utente(sender, instance, created, **kwargs):
    """
    Crea un profilo utente quando un nuovo utente viene creato.
    """
    if created: # Solo se l'utente è stato appena creato
        Profile.objects.create(user=instance)
        print(f"Creato profilo per l'utente: {instance.username}") # Log per debug

# Funzione helper per assegnare un badge solo se l'utente non ce l'ha già
def award_badge(user, badge_name, user_earned_badges_set):
    """
    Assegna un badge a un utente se non lo possiede già.
    'user_earned_badges_set' è un set con i nomi dei badge già ottenuti.
    """
    if badge_name not in user_earned_badges_set:
        try:
            badge = Badge.objects.get(nome=badge_name)
            UserBadge.objects.create(utente=user, badge=badge)
            print(f"INFO: Badge '{badge_name}' assegnato a {user.username}") # Log per debug
            user_earned_badges_set.add(badge_name) # Aggiorna il set locale
        except Badge.DoesNotExist:
            print(f"ATTENZIONE: Badge '{badge_name}' non trovato nel database!")
        except Exception as e:
            # Logga altri errori imprevisti durante la creazione di UserBadge
            print(f"ERRORE durante assegnazione badge '{badge_name}' a {user.username}: {e}")

@receiver(post_save, sender=RispostaUtente)
def check_and_award_badges(sender, instance, created, **kwargs):
    """
    Controlla se assegnare badge quando una RispostaUtente viene salvata.
    'instance' è l'oggetto RispostaUtente appena salvato.
    'created' è True se è la prima volta che viene salvato.
    """
    # Consideriamo solo le risposte corrette
    if not instance.is_corretta:
        return

    utente = instance.utente
    enigma = instance.enigma # Ottieni l'enigma correlato
    earned_badges = set(UserBadge.objects.filter(utente=utente).values_list('badge__nome', flat=True))

    # --- Logica per Badge Semplici (Già implementata) ---
    # 1. Benvenuto Sfidante
    if RispostaUtente.objects.filter(utente=utente, is_corretta=True).count() == 1:
        award_badge(utente, "Benvenuto Sfidante", earned_badges)
    # 2. Mente Pura
    if instance.suggerimenti_usati == 0:
        award_badge(utente, "Mente Pura", earned_badges)
    # 3. Fino in Fondo
    MAX_HINTS_ALLOWED = 3
    if instance.suggerimenti_usati == MAX_HINTS_ALLOWED:
        award_badge(utente, "Fino in Fondo", earned_badges)
    # 4. Collezionista
    total_correct_answers = RispostaUtente.objects.filter(utente=utente, is_corretta=True).count()
    if total_correct_answers >= 5:
        award_badge(utente, "Collezionista di Enigmi (Bronzo)", earned_badges)
    if total_correct_answers >= 15:
        award_badge(utente, "Collezionista di Enigmi (Argento)", earned_badges)
    if total_correct_answers >= 30:
        award_badge(utente, "Collezionista di Enigmi (Oro)", earned_badges)

    # Recupera i tempi necessari se l'enigma esiste
    if enigma and enigma.start_time and enigma.end_time and instance.data_inserimento:
        start_time = enigma.start_time
        end_time = enigma.end_time
        submission_time = instance.data_inserimento
        ONE_HOUR_IN_SECONDS = 3600

        # 5. Badge "Lampo di Genio" (Risolto entro 1 ora dal rilascio)
        # Assicurati che l'invio sia dopo l'inizio!
        if submission_time >= start_time:
            time_since_release_seconds = (submission_time - start_time).total_seconds()
            if time_since_release_seconds <= ONE_HOUR_IN_SECONDS:
                award_badge(utente, "Lampo di Genio", earned_badges)

        # 6. Badge "Sul Filo di Lana" (Risolto nell'ultima ora)
        # Assicurati che l'invio sia prima della fine!
        if submission_time <= end_time:
            time_before_deadline_seconds = (end_time - submission_time).total_seconds()
            # Deve essere nell'ultima ora (<= 3600s) ma non esattamente 0 (o negativo)
            if 0 < time_before_deadline_seconds <= ONE_HOUR_IN_SECONDS:
                 award_badge(utente, "Sul Filo di Lana", earned_badges)

    # 7. Badge "Punteggio Quasi Perfetto" (Punteggio >= 9.5 senza hint)
    # Usiamo instance.punteggio che è già calcolato e salvato
    if instance.punteggio >= 9.5 and instance.suggerimenti_usati == 0:
        award_badge(utente, "Punteggio Quasi Perfetto", earned_badges)

