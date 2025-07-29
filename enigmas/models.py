from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver

# Modello Enigma (invariato)
class Enigma(models.Model):
    titolo = models.CharField(max_length=200, blank=True, null=True)
    testo = models.TextField(help_text="La descrizione principale o l'introduzione all'enigma/caso.")
    start_time = models.DateTimeField(help_text="Data e ora di inizio visibilità")
    end_time = models.DateTimeField(editable=False)
    is_active = models.BooleanField(default=False, help_text="Seleziona per rendere questo l'enigma/caso corrente")
    notifica_inviata = models.BooleanField(default=False, help_text="Indica se la notifica è già stata inviata")
    def save(self, *args, **kwargs):
        self.end_time = self.start_time + datetime.timedelta(days=7)
        if self.is_active:
            Enigma.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.titolo if self.titolo else f"Enigma: {self.testo[:50]}..."
    class Meta:
        verbose_name = "Enigma o Caso"
        verbose_name_plural = "Enigmi o Casi"
        ordering = ['-start_time']

# Modello Allegato (invariato)
class Allegato(models.Model):
    TIPO_FILE_CHOICES = [('IMG', 'Immagine'), ('VID', 'Video'), ('AUD', 'Audio'), ('DOC', 'Documento')]
    enigma = models.ForeignKey(Enigma, on_delete=models.CASCADE, related_name='allegati')
    nome = models.CharField(max_length=100, help_text="Un nome descrittivo per l'allegato.")
    file = models.FileField(upload_to='allegati_enigmi/')
    tipo_file = models.CharField(max_length=3, choices=TIPO_FILE_CHOICES)
    def __str__(self):
        return f"{self.nome} per '{self.enigma.titolo}'"

# Modello CampoRisposta (invariato)
class CampoRisposta(models.Model):
    enigma = models.ForeignKey(Enigma, on_delete=models.CASCADE, related_name='campi_risposta')
    etichetta = models.CharField(max_length=255, help_text="La domanda (es. 'Nome del colpevole')")
    risposta_corretta = models.CharField(max_length=255)
    ordine = models.PositiveIntegerField(default=0, help_text="Ordine di visualizzazione del campo nel form")
    is_domanda_principale = models.BooleanField(default=False, help_text="Spunta questa casella se questa è la domanda principale che assegna il punteggio base.")
    class Meta:
        ordering = ['ordine']
    def __str__(self):
        return f"Campo '{self.etichetta}' per '{self.enigma.titolo}'"

# Modello RispostaUtente (invariato)
class RispostaUtente(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='risposte')
    enigma = models.ForeignKey(Enigma, on_delete=models.CASCADE)
    data_invio = models.DateTimeField(default=timezone.now)
    is_completa_corretta = models.BooleanField(default=False)
    punteggio = models.FloatField(default=0.0)
    class Meta:
        unique_together = ('utente', 'enigma')
        ordering = ['-data_invio']

# Modello RispostaUtenteMultipla (invariato)
class RispostaUtenteMultipla(models.Model):
    risposta_generale = models.ForeignKey(RispostaUtente, on_delete=models.CASCADE, related_name='risposte_multiple')
    campo = models.ForeignKey(CampoRisposta, on_delete=models.CASCADE)
    valore_inserito = models.CharField(max_length=255)
    def is_corretta(self):
        return self.valore_inserito.strip().lower() == self.campo.risposta_corretta.strip().lower()

# Modello Profile (invariato)
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    punteggio_bonus = models.FloatField(default=0.0)

# --- MODIFICA FONDAMENTALE QUI ---
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, **kwargs):
    """
    Usa get_or_create per creare un profilo se non esiste.
    Questo metodo è più sicuro e gestisce anche gli utenti creati manualmente.
    """
    Profile.objects.get_or_create(user=instance)
# --- FINE MODIFICA ---

# Altri modelli (Badge, UserBadge, Notifica, etc. rimangono invariati)
class Badge(models.Model):
    nome = models.CharField(max_length=100)
    descrizione = models.TextField()
    icona = models.CharField(max_length=50, help_text="Es. 'bi bi-star'", default='bi bi-patch-question')
    def __str__(self):
        return self.nome

class UserBadge(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    data_ottenimento = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('utente', 'badge')

class Notifica(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifiche')
    messaggio = models.CharField(max_length=255)
    data_creazione = models.DateTimeField(auto_now_add=True)
    letta = models.BooleanField(default=False)
    url = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self):
        return f"Notifica per {self.utente.username}: {self.messaggio[:30]}"
    class Meta:
        ordering = ['-data_creazione']

class MessaggioEnigmista(models.Model):
    testo = models.TextField()
    is_active = models.BooleanField(default=False)
    data_creazione = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Messaggio del {self.data_creazione.strftime('%d/%m/%Y')}"
