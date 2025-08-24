# enigmas/models.py
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

# --- MODIFICA 1: CampoRisposta ora è solo la DOMANDA ---
class CampoRisposta(models.Model):
    enigma = models.ForeignKey(Enigma, on_delete=models.CASCADE, related_name='campi_risposta')
    etichetta = models.CharField(max_length=255, help_text="La domanda (es. 'Chi è il colpevole?')")
    ordine = models.PositiveIntegerField(default=0, help_text="Ordine di visualizzazione del campo nel form")
    is_domanda_principale = models.BooleanField(default=False, help_text="Spunta se questa è la domanda principale.")
    class Meta:
        ordering = ['ordine']
    def __str__(self):
        return f"Domanda '{self.etichetta}' per '{self.enigma.titolo}'"

# --- NUOVO MODELLO: Le OPZIONI di risposta per ogni domanda ---
class OpzioneRisposta(models.Model):
    campo_risposta = models.ForeignKey(CampoRisposta, on_delete=models.CASCADE, related_name='opzioni')
    testo = models.CharField(max_length=255, help_text="Il testo di una possibile risposta (es. 'Mario Rossi').")
    is_corretta = models.BooleanField(default=False, help_text="Spunta se questa è una delle risposte corrette.")
    def __str__(self):
        return self.testo

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

# --- MODIFICA 2: La logica di controllo ora usa il nuovo modello OpzioneRisposta ---
class RispostaUtenteMultipla(models.Model):
    risposta_generale = models.ForeignKey(RispostaUtente, on_delete=models.CASCADE, related_name='risposte_multiple')
    campo = models.ForeignKey(CampoRisposta, on_delete=models.CASCADE)
    valore_inserito = models.CharField(max_length=255)

    def is_corretta(self):
        # 1. Trova tutte le opzioni di risposta corrette per questa domanda
        opzioni_corrette = OpzioneRisposta.objects.filter(campo_risposta=self.campo, is_corretta=True)
        
        # 2. Estrai il testo di ogni opzione corretta e normalizzalo (minuscolo, senza spazi)
        risposte_corrette_set = {opzione.testo.strip().lower() for opzione in opzioni_corrette}

        # 3. Prendi la risposta dell'utente, dividila per la virgola e normalizzala
        risposte_inserite_set = {ans.strip().lower() for ans in self.valore_inserito.split(',') if ans.strip()}

        # 4. La risposta è corretta se l'insieme delle risposte dell'utente è identico all'insieme delle risposte corrette
        return risposte_corrette_set == risposte_inserite_set

# ... (Il resto dei tuoi modelli: Profile, Badge, etc. rimane invariato) ...
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    punteggio_bonus = models.FloatField(default=0.0)

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, **kwargs):
    Profile.objects.get_or_create(user=instance)

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
    link = models.CharField(max_length=255, blank=True, null=True)
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
    

class RispostaUtenteMultipla(models.Model):
    risposta_generale = models.ForeignKey(RispostaUtente, on_delete=models.CASCADE, related_name='risposte_multiple')
    campo = models.ForeignKey(CampoRisposta, on_delete=models.CASCADE)
    valore_inserito = models.CharField(max_length=255, blank=True)

    def is_corretta(self):
        """
        Controlla se le opzioni scelte dall'utente corrispondono a quelle corrette nel database.
        """
        # 1. Trova il testo di tutte le opzioni corrette definite nell'admin
        opzioni_corrette_db = OpzioneRisposta.objects.filter(campo_risposta=self.campo, is_corretta=True)
        risposte_corrette_set = set(opzione.testo.strip().lower() for opzione in opzioni_corrette_db)

        # 2. Prendi il testo salvato delle opzioni scelte dall'utente
        risposte_inserite_set = set(ans.strip().lower() for ans in self.valore_inserito.split(',') if ans.strip())

        # 3. La risposta è corretta se i due insiemi sono identici
        return risposte_corrette_set == risposte_inserite_set
    