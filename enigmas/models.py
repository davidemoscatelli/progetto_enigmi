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
    # end_time verrà calcolato automaticamente quando si salva
    end_time = models.DateTimeField(editable=False)
    # Usiamo is_active per mostrare SOLO un enigma alla volta
    is_active = models.BooleanField(default=False, help_text="Seleziona per rendere questo l'enigma corrente (assicurati che solo uno sia attivo!)")

    def save(self, *args, **kwargs):
        # Calcola end_time = start_time + 7 giorni
        self.end_time = self.start_time + datetime.timedelta(days=7)
        # Assicura che solo un enigma sia attivo (opzionale ma utile)
        if self.is_active:
            Enigma.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs) # Chiama il metodo save originale

    def __str__(self):
        return self.titolo if self.titolo else f"Enigma: {self.testo[:50]}..."

    class Meta:
        verbose_name = "Enigma"
        verbose_name_plural = "Enigmi"
        ordering = ['-start_time'] # Ordina dal più recente

class RispostaUtente(models.Model):
    utente = models.ForeignKey(User, on_delete=models.CASCADE)
    enigma = models.ForeignKey(Enigma, on_delete=models.CASCADE)
    risposta_inserita = models.CharField(max_length=255)
    # auto_now_add=True funziona ancora, ma impostiamo il valore anche prima
    # se necessario per il calcolo del punteggio.
    data_inserimento = models.DateTimeField(auto_now_add=True, editable=False)
    is_corretta = models.BooleanField(default=False)
    punteggio = models.FloatField(default=0.0, help_text="Punteggio da 0 a 10")

    def calcola_punteggio(self):
        # Questo metodo ora dovrebbe ricevere un data_inserimento valido
        if not self.is_corretta or self.data_inserimento is None: # Aggiunto controllo per sicurezza
            return 0.0

        # Tempo totale disponibile (in secondi)
        tempo_totale = (self.enigma.end_time - self.enigma.start_time).total_seconds()
        if tempo_totale <= 0: # Evita divisione per zero
             return 0.0

        # Tempo impiegato dall'utente (in secondi)
        tempo_impiegato = (self.data_inserimento - self.enigma.start_time).total_seconds()
        if tempo_impiegato < 0: # Se inserito prima dell'inizio (improbabile ma sicuro)
            tempo_impiegato = 0
        # Nota: il controllo se si è fuori tempo massimo è implicito nel calcolo sotto

        # Tempo rimanente alla scadenza quando l'utente ha risposto
        tempo_rimanente = (self.enigma.end_time - self.data_inserimento).total_seconds()
        if tempo_rimanente < 0:
            tempo_rimanente = 0 # Nessun punto se inviato dopo la scadenza

        # Calcola il punteggio: proporzionale al tempo rimanente rispetto al tempo totale
        punteggio_calcolato = max(0.0, 10.0 * (tempo_rimanente / tempo_totale))

        # Arrotonda a due cifre decimali (opzionale)
        return round(punteggio_calcolato, 2)


    def save(self, *args, **kwargs):
        # --- MODIFICA CHIAVE ---
        # Imposta data_inserimento se l'oggetto è nuovo (non ha ancora un pk)
        # e data_inserimento non è già stato impostato (è None).
        # Questo assicura che calcola_punteggio() abbia un valore su cui lavorare.
        if self.pk is None and self.data_inserimento is None:
            self.data_inserimento = timezone.now()
        # --- FINE MODIFICA CHIAVE ---

        # Controlla se la risposta è corretta
        self.is_corretta = self.risposta_inserita.strip().lower() == self.enigma.risposta_corretta.strip().lower()

        # Calcola il punteggio solo se la risposta è corretta e
        # se l'oggetto è nuovo (pk is None) per evitare ricalcoli successivi.
        if self.is_corretta and self.pk is None:
             self.punteggio = self.calcola_punteggio()
        # Assicura che il punteggio sia 0 se la risposta non è corretta
        elif not self.is_corretta:
            self.punteggio = 0.0
        # Se l'oggetto esiste già (self.pk non è None) e la risposta è corretta,
        # non ricalcoliamo il punteggio per non sovrascrivere quello originale.

        # Chiamiamo il save originale DOPO aver fatto i nostri calcoli.
        # auto_now_add in data_inserimento non avrà effetto se abbiamo già impostato
        # il valore, il che va bene.
        super().save(*args, **kwargs)

    def __str__(self):
        stato = "Corretta" if self.is_corretta else "Errata"
        # Usiamo safe navigation per il titolo enigma nel caso non ci sia
        titolo_enigma = getattr(getattr(self, 'enigma', None), 'titolo', 'Enigma Sconosciuto')
        # Usiamo safe navigation per username nel caso utente sia None (improbabile)
        username = getattr(getattr(self, 'utente', None), 'username', 'Utente Sconosciuto')
        return f"Risposta di {username} per '{titolo_enigma}' - {stato} ({self.punteggio:.2f} punti)"


    class Meta:
        verbose_name = "Risposta Utente"
        verbose_name_plural = "Risposte Utenti"
        unique_together = ('utente', 'enigma')
        ordering = ['-data_inserimento']
