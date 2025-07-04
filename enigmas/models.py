# enigmas/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

class Enigma(models.Model):
    titolo = models.CharField(max_length=200, blank=True, null=True) # Titolo opzionale
    testo = models.TextField(unique=True) # Il testo dell'enigma, deve essere unico
    risposta_corretta = models.CharField(max_length=255)
    start_time = models.DateTimeField(help_text="Data e ora di inizio visibilità dell'enigma")
    end_time = models.DateTimeField(editable=False)
    is_active = models.BooleanField(default=False, help_text="Seleziona per rendere questo l'enigma corrente (assicurati che solo uno sia attivo!)")
    notifica_inviata = models.BooleanField(default=False, help_text="Indica se la notifica per questo enigma è già stata inviata")
    def save(self, *args, **kwargs):
        self.end_time = self.start_time + datetime.timedelta(days=7)
        if self.is_active:
            Enigma.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.titolo if self.titolo else f"Enigma: {self.testo[:50]}..."

    class Meta:
        verbose_name = "Enigma"
        verbose_name_plural = "Enigmi"
        ordering = ['-start_time']

class RispostaUtente(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    enigma = models.ForeignKey(Enigma, on_delete=models.CASCADE)
    risposta_inserita = models.CharField(max_length=255)
    # Corretto: Usiamo default invece di auto_now_add
    data_inserimento = models.DateTimeField(default=timezone.now)
    is_corretta = models.BooleanField(default=False)
    # Aggiornato help_text per chiarezza
    punteggio = models.FloatField(default=0.0, help_text="Punteggio da 0 a 10 (con penalità hint)")
    # --- ECCO IL CAMPO CHE MANCAVA ---
    suggerimenti_usati = models.PositiveIntegerField(default=0, help_text="Numero di suggerimenti usati per questo enigma")
    # ---------------------------------

    def calcola_punteggio_base(self):
        """Calcola il punteggio BASATO SUL TEMPO (0-10) senza considerare gli hint."""
        # Aggiunto controllo più robusto per data_inserimento
        if not self.is_corretta or not self.data_inserimento or not self.enigma or not self.enigma.start_time or not self.enigma.end_time:
            return 0.0

        end_time = self.enigma.end_time
        start_time = self.enigma.start_time # Aggiunto per chiarezza

        if start_time >= end_time: # Controllo coerenza date
            return 0.0
        tempo_totale = (end_time - start_time).total_seconds()

        if self.data_inserimento < start_time or self.data_inserimento > end_time:
             return 0.0

        tempo_rimanente = (end_time - self.data_inserimento).total_seconds()
        punteggio_base = 10.0 * (tempo_rimanente / tempo_totale)
        return punteggio_base

    def save(self, *args, **kwargs):
        # Determina lo stato di correttezza *prima* di salvare, basandosi sull'input attuale
        risposta_attuale_corretta = self.risposta_inserita.strip().lower() == self.enigma.risposta_corretta.strip().lower()

        # Controlla se l'oggetto esiste già e qual era il suo stato precedente
        is_newly_correct = False
        old_is_corretta = False
        if self.pk is not None: # Se è un update
            try:
                # Recupera lo stato salvato nel database
                old_instance = RispostaUtente.objects.get(pk=self.pk)
                old_is_corretta = old_instance.is_corretta
            except RispostaUtente.DoesNotExist:
                 old_is_corretta = False # Se non esiste, considerala non corretta prima
        # Altrimenti (se self.pk is None), old_is_corretta rimane False (default)

        # Determina se la risposta è diventata corretta *proprio ora*
        if not old_is_corretta and risposta_attuale_corretta:
            is_newly_correct = True

        # Aggiorna lo stato di correttezza dell'oggetto Python
        self.is_corretta = risposta_attuale_corretta

        # Aggiorna timestamp e calcola punteggio SOLO QUANDO diventa corretta
        if is_newly_correct:
            # Imposta il timestamp al momento della risposta corretta!
            self.data_inserimento = timezone.now()
            # Calcola il punteggio usando il nuovo timestamp
            punteggio_base = self.calcola_punteggio_base() # Ora usa la data_inserimento aggiornata
            penalita_percentuale = self.suggerimenti_usati * 0.10
            punteggio_finale = punteggio_base * (1.0 - penalita_percentuale)
            self.punteggio = max(0.0, round(punteggio_finale, 2))
        elif not self.is_corretta:
            # Se è (o torna ad essere) errata, azzera il punteggio
            self.punteggio = 0.0
        # Se era già corretta in precedenza (old_is_corretta=True), non facciamo nulla
        # per non cambiare il punteggio/timestamp originali.

        # Salva l'oggetto nel database
        super().save(*args, **kwargs)

    def __str__(self):
        stato = "Corretta" if self.is_corretta else "Errata"
        titolo_enigma = getattr(getattr(self, 'enigma', None), 'titolo', 'Enigma Sconosciuto')
        username = getattr(getattr(self, 'utente', None), 'username', 'Utente Sconosciuto')
        # Ora self.suggerimenti_usati esiste!
        return f"Risposta di {username} per '{titolo_enigma}' - {stato} ({self.punteggio:.2f} punti, {self.suggerimenti_usati} hint)"

    class Meta:
        verbose_name = "Risposta Utente"
        verbose_name_plural = "Risposte Utenti"
        unique_together = ('utente', 'enigma')
        ordering = ['-data_inserimento']


# Modello Suggerimento (correttamente definito fuori da RispostaUtente)
class Suggerimento(models.Model):
    enigma = models.ForeignKey(Enigma, on_delete=models.CASCADE, related_name='suggerimenti')
    testo = models.TextField(help_text="Il testo del suggerimento")
    ordine = models.PositiveIntegerField(default=1, help_text="Ordine in cui mostrare i suggerimenti (1, 2, 3)")

    def __str__(self):
        titolo_enigma = getattr(getattr(self, 'enigma', None), 'titolo', 'Enigma Sconosciuto')
        return f"Suggerimento {self.ordine} per '{titolo_enigma}'"

    class Meta:
        ordering = ['enigma', 'ordine']
        unique_together = ('enigma', 'ordine')
        verbose_name = "Suggerimento"
        verbose_name_plural = "Suggerimenti"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, help_text="Una breve biografia (opzionale)")
    riceve_notifiche = models.BooleanField(default=True, help_text="L'utente desidera ricevere notifiche in-app?")
    # --- NUOVO CAMPO PER BONUS/MALUS ---
    punteggio_bonus = models.FloatField(
        default=0.0,
        help_text="Punti da aggiungere (positivi) o sottrarre (negativi) manualmente al punteggio totale dell'utente."
    )
    # ------------------------------------

    def __str__(self):
        return f"Profilo di {self.user.username}"

    class Meta:
        verbose_name = "Profilo Utente"
        verbose_name_plural = "Profili Utenti"



# NUOVO: Modello per descrivere un Badge/Achievement
class Badge(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    descrizione = models.TextField(help_text="Cosa bisogna fare per ottenere questo badge?")
    # Potresti aggiungere un campo per l'icona (es. CharField per nome icona Bootstrap/FontAwesome o ImageField)
    # icona_classe = models.CharField(max_length=50, blank=True, help_text="Es. 'bi bi-award-fill text-warning'")
    # Oppure:
    # icona_img = models.ImageField(upload_to='badge_icons/', null=True, blank=True)
    rarita = models.CharField(max_length=20, choices=[('Comune', 'Comune'), ('Bronzo', 'Bronzo'), ('Argento', 'Argento'), ('Oro', 'Oro')], default='Bronzo') # Esempio di rarità

    def __str__(self):
        return self.nome

    class Meta:
        ordering = ['nome']
        verbose_name = "Badge"
        verbose_name_plural = "Badges"


# NUOVO: Modello Many-to-Many per tracciare quali utenti hanno ottenuto quali badge
class UserBadge(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    data_ottenimento = models.DateTimeField(auto_now_add=True) # Data in cui è stato ottenuto

    def __str__(self):
        return f"{self.utente.username} ha ottenuto '{self.badge.nome}'"

    class Meta:
        # Assicura che un utente possa ottenere ogni badge solo una volta
        unique_together = ('utente', 'badge')
        ordering = ['-data_ottenimento']
        verbose_name = "Badge Utente"
        verbose_name_plural = "Badges Utenti"
    
class Notifica(models.Model):
    # Tipi di notifica per poterle filtrare o mostrare icone diverse
    TIPO_NUOVO_ENIGMA = 'ENIGMA'
    TIPO_BADGE_OTTENUTO = 'BADGE'
    TIPO_GENERALE = 'INFO'
    TIPI_NOTIFICA_CHOICES = [
        (TIPO_NUOVO_ENIGMA, 'Nuovo Enigma'),
        (TIPO_BADGE_OTTENUTO, 'Badge Ottenuto'),
        (TIPO_GENERALE, 'Generale'),
    ]

    # Utente a cui è destinata la notifica
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifiche')
    # Messaggio della notifica
    messaggio = models.TextField()
    # Data e ora di creazione
    data_creazione = models.DateTimeField(auto_now_add=True)
    # Flag per indicare se l'utente l'ha letta
    letta = models.BooleanField(default=False, db_index=True) # db_index aiuta a filtrare velocemente le non lette
    # Tipo di notifica (opzionale ma utile)
    tipo_notifica = models.CharField(
        max_length=10,
        choices=TIPI_NOTIFICA_CHOICES,
        default=TIPO_GENERALE
    )
    # Link opzionale a cui porta la notifica (es. pagina enigma, profilo)
    link = models.URLField(max_length=200, blank=True, null=True)

    def __str__(self):
        stato = "[Letta]" if self.letta else "[Non Letta]"
        return f"{stato} Notifica per {self.utente.username}: {self.messaggio[:50]}..."

    class Meta:
        ordering = ['-data_creazione'] # Mostra le più recenti prima
        verbose_name = "Notifica"
        verbose_name_plural = "Notifiche"

class MessaggioEnigmista(models.Model):
    titolo = models.CharField(max_length=150, blank=True, null=True, help_text="Titolo opzionale del messaggio")
    testo = models.TextField(help_text="Il contenuto del messaggio (può contenere HTML di base se necessario)")
    data_pubblicazione = models.DateTimeField(default=timezone.now, help_text="Data e ora in cui il messaggio diventa visibile")
    pubblicato = models.BooleanField(default=True, db_index=True, help_text="Deseleziona per nascondere il messaggio senza cancellarlo")

    def __str__(self):
        return self.titolo if self.titolo else f"Messaggio del {self.data_pubblicazione.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['-data_pubblicazione'] # Mostra i più recenti prima nell'admin
        verbose_name = "Messaggio dell'Enigmista"
        verbose_name_plural = "Messaggi dell'Enigmista"