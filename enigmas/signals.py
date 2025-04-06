# enigmas/signals.py
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def crea_o_aggiorna_profilo_utente(sender, instance, created, **kwargs):
    """
    Crea un profilo utente quando un nuovo utente viene creato.
    """
    if created: # Solo se l'utente è stato appena creato
        Profile.objects.create(user=instance)
        print(f"Creato profilo per l'utente: {instance.username}") # Log per debug

# Puoi anche aggiungere un segnale per salvare il profilo quando l'utente viene salvato,
# ma spesso non è necessario se le modifiche avvengono tramite form specifici.
# @receiver(post_save, sender=User)
# def salva_profilo_utente(sender, instance, **kwargs):
#     try:
#         instance.profile.save()
#         print(f"Salvato profilo per l'utente: {instance.username}") # Log per debug
#     except Profile.DoesNotExist:
#         # Questo non dovrebbe accadere se il segnale 'crea' funziona
#         Profile.objects.create(user=instance)
#         print(f"Profilo non esisteva, creato profilo per: {instance.username}")