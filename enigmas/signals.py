# enigmas/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Profile, RispostaUtente, Badge, UserBadge, Notifica, Enigma

@receiver(post_save, sender=User)
def crea_o_aggiorna_profilo_utente(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)

def award_badge(user, badge_name, user_earned_badges_set):
    if badge_name not in user_earned_badges_set:
        try:
            badge = Badge.objects.get(nome=badge_name)
            UserBadge.objects.create(utente=user, badge=badge)
            print(f"INFO: Badge '{badge_name}' assegnato a {user.username}")
            user_earned_badges_set.add(badge_name)
            
            messaggio_notifica = f"Congratulazioni! Hai ottenuto il badge: '{badge.nome}'!"
            link_profilo = reverse('profile_view', kwargs={'username': user.username})
            Notifica.objects.create(utente=user, messaggio=messaggio_notifica, link=link_profilo)
        except Badge.DoesNotExist:
            print(f"ATTENZIONE: Badge '{badge_name}' non trovato! Crealo nel pannello di amministrazione.")
        except Exception as e:
            print(f"ERRORE durante assegnazione badge '{badge_name}': {e}")

@receiver(post_save, sender=RispostaUtente)
def check_and_award_badges(sender, instance, **kwargs):
    if not instance.is_completa_corretta:
        return

    utente = instance.utente
    enigma = instance.enigma
    earned_badges = set(UserBadge.objects.filter(utente=utente).values_list('badge__nome', flat=True))
    
    # Recupera tutte le risposte corrette dell'utente in ordine di tempo
    risposte_corrette_utente = RispostaUtente.objects.filter(
        utente=utente, is_completa_corretta=True
    ).order_by('data_invio')
    
    total_correct_answers = risposte_corrette_utente.count()

    # --- Logica per i Badge ---

    # 1. Sulla Scena del Crimine
    if total_correct_answers == 1:
        award_badge(utente, "Sulla Scena del Crimine", earned_badges)
    
    # 2. Intuito del Detective
    if instance.suggerimenti_usati == 0:
        award_badge(utente, "Intuito del Detective", earned_badges)
        
    # 3. Tutte le Piste
    if instance.suggerimenti_usati == 3:
        award_badge(utente, "Tutte le Piste", earned_badges)

    # 4. L'Ora d'Oro
    if enigma and enigma.start_time and instance.data_invio:
        if (instance.data_invio - enigma.start_time).total_seconds() <= 3600:
            award_badge(utente, "L'Ora d'Oro", earned_badges)
    
    # 5. Sul Filo di Lana
    if enigma and enigma.end_time and instance.data_invio:
        if (enigma.end_time - instance.data_invio).total_seconds() <= 86400: # 24 ore
            award_badge(utente, "Sul Filo di Lana", earned_badges)

    # 6. Analisi Perfetta
    if instance.punteggio > 140:
        award_badge(utente, "Analisi Perfetta", earned_badges)
        
    # 7. Metodico
    if 100.00 <= instance.punteggio <= 110.00:
        award_badge(utente, "Metodico", earned_badges)
        
    # 8. Colpo da Maestro
    if risposte_corrette_utente.filter(punteggio__gt=125).count() >= 3:
        award_badge(utente, "Colpo da Maestro", earned_badges)

    # 9-13. Progressione
    if total_correct_answers >= 5: award_badge(utente, "Investigatore Junior", earned_badges)
    if total_correct_answers >= 10: award_badge(utente, "Investigatore Senior", earned_badges)
    if total_correct_answers >= 15: award_badge(utente, "Detective Capo", earned_badges)
    if total_correct_answers >= 20: award_badge(utente, "Commissario", earned_badges)
    if total_correct_answers >= 30: award_badge(utente, "Leggenda Investigativa", earned_badges)
    
    # Logica per le serie (streaks)
    if total_correct_answers >= 2:
        # 18. Stacanovista & 19. Doppietta
        ultima_risposta = risposte_corrette_utente.last()
        penultima_risposta = risposte_corrette_utente[total_correct_answers - 2]
        if ultima_risposta.data_invio.date() == penultima_risposta.data_invio.date():
            award_badge(utente, "Stacanovista", earned_badges)
        if (ultima_risposta.data_invio - penultima_risposta.data_invio) <= timedelta(hours=24):
            award_badge(utente, "Doppietta", earned_badges)

    if total_correct_answers >= 3:
        # 20. Maratoneta
        terzultima_risposta = risposte_corrette_utente[total_correct_answers - 3]
        if (risposte_corrette_utente.last().data_invio - terzultima_risposta.data_invio) <= timedelta(days=7):
            award_badge(utente, "Maratoneta", earned_badges)
            
        # 14. Implacabile (3 di fila)
        award_badge(utente, "Implacabile", earned_badges)
        
        # 16 & 17. Mente Brillante & Genio Investigativo (serie senza aiuti)
        ultime_tre_risposte = risposte_corrette_utente.order_by('-data_invio')[:3]
        if all(r.suggerimenti_usati == 0 for r in ultime_tre_risposte):
            award_badge(utente, "Genio Investigativo", earned_badges)
            if ultime_tre_risposte.count() >= 2 and all(r.suggerimenti_usati == 0 for r in ultime_tre_risposte[:2]):
                 award_badge(utente, "Mente Brillante", earned_badges)

    if total_correct_answers >= 5:
        # 15. Infallibile (5 di fila)
        award_badge(utente, "Infallibile", earned_badges)

@receiver(post_save, sender=Enigma)
def crea_notifica_nuovo_enigma(sender, instance, created, **kwargs):
    if instance.is_active and instance.start_time <= timezone.now() and not instance.notifica_inviata:
        utenti_da_notificare = User.objects.filter(is_active=True, is_superuser=False)
        if not utenti_da_notificare.exists():
            Enigma.objects.filter(pk=instance.pk).update(notifica_inviata=True)
            return
        messaggio = f"È uscito un nuovo enigma: '{instance.titolo or 'Senza Titolo'}'!"
        link_notifica = reverse('enigma_view')
        notifiche_da_creare = [Notifica(utente=utente, messaggio=messaggio, link=link_notifica) for utente in utenti_da_notificare]
        try:
            Notifica.objects.bulk_create(notifiche_da_creare)
            Enigma.objects.filter(pk=instance.pk).update(notifica_inviata=True)
        except Exception as e:
            print(f"ERRORE durante bulk_create notifiche: {e}")
