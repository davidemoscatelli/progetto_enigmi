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
        # Controlla se la risposta è corretta
        self.is_corretta = self.risposta_inserita.strip().lower() == self.enigma.risposta_corretta.strip().lower()

        # Calcola e applica il punteggio se la risposta è corretta
        if self.is_corretta:
            punteggio_base = self.calcola_punteggio_base()
            # Ora self.suggerimenti_usati esiste!
            penalita_percentuale = self.suggerimenti_usati * 0.10
            punteggio_finale = punteggio_base * (1.0 - penalita_percentuale)
            self.punteggio = max(0.0, round(punteggio_finale, 2))
        else:
            self.punteggio = 0.0

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