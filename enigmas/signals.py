# enigmas/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.urls import reverse
from .models import Profile, RispostaUtente, Badge, UserBadge, Notifica, Enigma

@receiver(post_save, sender=User)
def crea_o_aggiorna_profilo_utente(sender, instance, **kwargs):
    """
    Crea un profilo utente se non esiste.
    """
    Profile.objects.get_or_create(user=instance)

def award_badge(user, badge_name, user_earned_badges_set):
    """
    Assegna un badge a un utente se non lo possiede già e crea una notifica.
    """
    if badge_name not in user_earned_badges_set:
        try:
            badge = Badge.objects.get(nome=badge_name)
            UserBadge.objects.create(utente=user, badge=badge)
            print(f"INFO: Badge '{badge_name}' assegnato a {user.username}")
            user_earned_badges_set.add(badge_name)
            
            messaggio_notifica = f"Congratulazioni! Hai ottenuto il badge: '{badge.nome}'!"
            link_profilo = reverse('profile_view', kwargs={'username': user.username})
            Notifica.objects.create(
                utente=user,
                messaggio=messaggio_notifica,
                link=link_profilo
            )
        except Badge.DoesNotExist:
            print(f"ATTENZIONE: Badge '{badge_name}' non trovato nel database!")
        except Exception as e:
            print(f"ERRORE durante assegnazione badge '{badge_name}': {e}")

@receiver(post_save, sender=RispostaUtente)
def check_and_award_badges(sender, instance, **kwargs):
    """
    Controlla se assegnare badge quando una RispostaUtente viene salvata.
    """
    if not instance.is_completa_corretta:
        return

    utente = instance.utente
    enigma = instance.enigma
    earned_badges = set(UserBadge.objects.filter(utente=utente).values_list('badge__nome', flat=True))

    # --- Logica per i Badge rimanenti ---
    
    # 1. Badge "Benvenuto Sfidante"
    if RispostaUtente.objects.filter(utente=utente, is_completa_corretta=True).count() == 1:
        award_badge(utente, "Benvenuto Sfidante", earned_badges)
    
    # 2. Badge "Lampo di Genio" (Risolto entro 1 ora)
    if enigma and enigma.start_time and instance.data_invio:
        time_since_release = instance.data_invio - enigma.start_time
        if time_since_release.total_seconds() <= 3600:
            award_badge(utente, "Lampo di Genio", earned_badges)

@receiver(post_save, sender=Enigma)
def crea_notifica_nuovo_enigma(sender, instance, created, **kwargs):
    """
    Crea notifiche per gli utenti quando un enigma diventa attivo.
    """
    if instance.is_active and instance.start_time <= timezone.now() and not instance.notifica_inviata:
        utenti_da_notificare = User.objects.filter(is_active=True, is_superuser=False)
        if not utenti_da_notificare.exists():
            Enigma.objects.filter(pk=instance.pk).update(notifica_inviata=True)
            return

        messaggio = f"È uscito un nuovo enigma: '{instance.titolo or 'Senza Titolo'}'!"
        link_notifica = reverse('enigma_view')
        
        notifiche_da_creare = [
            Notifica(utente=utente, messaggio=messaggio, link=link_notifica)
            for utente in utenti_da_notificare
        ]
        try:
            Notifica.objects.bulk_create(notifiche_da_creare)
            Enigma.objects.filter(pk=instance.pk).update(notifica_inviata=True)
        except Exception as e:
            print(f"ERRORE durante bulk_create notifiche: {e}")