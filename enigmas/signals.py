# enigmas/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from .models import Profile, RispostaUtente, Badge, UserBadge, Notifica, Enigma

@receiver(post_save, sender=User)
def crea_o_aggiorna_profilo_utente(sender, instance, created, **kwargs):
    """
    Crea un profilo utente quando un nuovo utente viene creato,
    usando un metodo sicuro per evitare errori di duplicazione.
    """
    if created:
        # CORREZIONE: Usa get_or_create per prevenire l'errore 'UNIQUE constraint failed'.
        Profile.objects.get_or_create(user=instance)
        print(f"Creato o trovato profilo per l'utente: {instance.username}")

# La funzione award_badge è corretta, ma dipende dal modello Notifica.
# Assumiamo che il modello Notifica abbia il campo 'tipo_notifica'.
def award_badge(user, badge_name, user_earned_badges_set):
    if badge_name not in user_earned_badges_set:
        try:
            badge = Badge.objects.get(nome=badge_name)
            UserBadge.objects.create(utente=user, badge=badge)
            print(f"INFO: Badge '{badge_name}' assegnato a {user.username}")
            user_earned_badges_set.add(badge_name)

            # Creazione notifica
            messaggio_notifica = f"Congratulazioni! Hai ottenuto il badge: '{badge.nome}'!"
            link_profilo = reverse('profile_view', kwargs={'username': user.username})
            Notifica.objects.create(
                utente=user,
                messaggio=messaggio_notifica,
                # tipo_notifica=Notifica.TIPO_BADGE_OTTENUTO, # Assumendo che questo esista nel modello Notifica
                link=link_profilo
            )
            print(f"INFO: Notifica per badge '{badge_name}' creata per {user.username}")
        except Badge.DoesNotExist:
            print(f"ATTENZIONE: Badge '{badge_name}' non trovato nel database!")
        except Exception as e:
            print(f"ERRORE durante assegnazione badge '{badge_name}' a {user.username}: {e}")

@receiver(post_save, sender=RispostaUtente)
def check_and_award_badges(sender, instance, created, **kwargs):
    """
    Controlla se assegnare badge quando una RispostaUtente viene salvata.
    """
    # CORREZIONE: Usiamo 'is_completa_corretta' invece di 'is_corretta'.
    if not instance.is_completa_corretta:
        return

    utente = instance.utente
    enigma = instance.enigma
    earned_badges = set(UserBadge.objects.filter(utente=utente).values_list('badge__nome', flat=True))

    # Logica per Badge
    # CORREZIONE: Usiamo 'is_completa_corretta' in tutte le query.
    if RispostaUtente.objects.filter(utente=utente, is_completa_corretta=True).count() == 1:
        award_badge(utente, "Benvenuto Sfidante", earned_badges)
    
    total_correct_answers = RispostaUtente.objects.filter(utente=utente, is_completa_corretta=True).count()
    if total_correct_answers >= 5:
        award_badge(utente, "Collezionista di Enigmi (Bronzo)", earned_badges)
    if total_correct_answers >= 15:
        award_badge(utente, "Collezionista di Enigmi (Argento)", earned_badges)
    if total_correct_answers >= 30:
        award_badge(utente, "Collezionista di Enigmi (Oro)", earned_badges)

    # CORREZIONE: Usiamo 'data_invio' invece di 'data_inserimento'.
    if enigma and enigma.start_time and enigma.end_time and instance.data_invio:
        start_time = enigma.start_time
        end_time = enigma.end_time
        submission_time = instance.data_invio
        ONE_HOUR_IN_SECONDS = 3600

        if submission_time >= start_time:
            time_since_release_seconds = (submission_time - start_time).total_seconds()
            if time_since_release_seconds <= ONE_HOUR_IN_SECONDS:
                award_badge(utente, "Lampo di Genio", earned_badges)

        if submission_time <= end_time:
            time_before_deadline_seconds = (end_time - submission_time).total_seconds()
            if 0 < time_before_deadline_seconds <= ONE_HOUR_IN_SECONDS:
                award_badge(utente, "Sul Filo di Lana", earned_badges)
    
    if instance.punteggio >= 9.5 and instance.suggerimenti_usati == 0:
        award_badge(utente, "Punteggio Quasi Perfetto", earned_badges)


# Questo signal sembra corretto, lo lascio invariato.
# Assumiamo che il modello Notifica abbia il campo 'tipo_notifica'.
@receiver(post_save, sender=Enigma)
def crea_notifica_nuovo_enigma(sender, instance, created, **kwargs):
    if instance.is_active and instance.start_time <= timezone.now() and not instance.notifica_inviata:
        print(f"INFO: Rilevato enigma attivo: {instance.titolo}. Creazione notifiche...")
        utenti_da_notificare = User.objects.filter(is_active=True, is_superuser=False)

        if not utenti_da_notificare.exists():
            Enigma.objects.filter(pk=instance.pk).update(notifica_inviata=True)
            return

        messaggio = f"È uscito un nuovo enigma: '{instance.titolo or 'Senza Titolo'}'! Mettiti alla prova."
        try:
            link_notifica = reverse('enigma_view')
        except Exception:
            link_notifica = "/"

        notifiche_da_creare = [
            Notifica(
                utente=utente,
                messaggio=messaggio,
                # tipo_notifica=Notifica.TIPO_NUOVO_ENIGMA,
                link=link_notifica
            )
            for utente in utenti_da_notificare
        ]
        try:
            Notifica.objects.bulk_create(notifiche_da_creare)
            Enigma.objects.filter(pk=instance.pk).update(notifica_inviata=True)
        except Exception as e:
            print(f"ERRORE durante bulk_create notifiche: {e}")