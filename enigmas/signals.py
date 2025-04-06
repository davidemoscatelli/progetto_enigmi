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

    # Ottieni l'elenco dei nomi dei badge già ottenuti dall'utente per efficienza
    earned_badges = set(UserBadge.objects.filter(utente=utente).values_list('badge__nome', flat=True))

    # --- Logica per i Badge Semplici ---

    # 1. Badge "Benvenuto Sfidante" (Primo enigma risolto)
    # Controlliamo se questo è l'UNICO RispostaUtente corretta per questo utente
    if RispostaUtente.objects.filter(utente=utente, is_corretta=True).count() == 1:
        award_badge(utente, "Benvenuto Sfidante", earned_badges)

    # 2. Badge "Mente Pura" (Risolto senza hint)
    if instance.suggerimenti_usati == 0:
        award_badge(utente, "Mente Pura", earned_badges)

    # 3. Badge "Fino in Fondo" (Risolto con 3 hint)
    # Nota: MAX_HINTS_ALLOWED dovrebbe essere consistente con la logica altrove
    MAX_HINTS_ALLOWED = 3
    if instance.suggerimenti_usati == MAX_HINTS_ALLOWED:
        award_badge(utente, "Fino in Fondo", earned_badges)

    # 4. Badge "Collezionista" (Contatore enigmi risolti)
    total_correct_answers = RispostaUtente.objects.filter(utente=utente, is_corretta=True).count()

    if total_correct_answers >= 5:
        award_badge(utente, "Collezionista di Enigmi (Bronzo)", earned_badges)
    if total_correct_answers >= 15:
        award_badge(utente, "Collezionista di Enigmi (Argento)", earned_badges)
    if total_correct_answers >= 30:
        award_badge(utente, "Collezionista di Enigmi (Oro)", earned_badges)

    # --- Aggiungi qui la logica per altri badge semplici ---
