# enigmas/forms.py
from django import forms
from .models import OpzioneRisposta

class RispostaCheckboxForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # Riceve le "domande" (campi_risposta) dalla vista
        campi_risposta = kwargs.pop('campi_risposta')
        super().__init__(*args, **kwargs)

        # Per ogni domanda, crea un campo a scelta multipla (checkbox)
        for campo in campi_risposta:
            self.fields[f'campo_{campo.id}'] = forms.ModelMultipleChoiceField(
                # Le opzioni tra cui scegliere sono quelle collegate a questa specifica domanda
                queryset=OpzioneRisposta.objects.filter(campo_risposta=campo),
                
                # Usa le checkbox per la visualizzazione
                widget=forms.CheckboxSelectMultiple,
                
                # L'etichetta del gruppo di checkbox è la domanda stessa
                label=campo.etichetta,
                
                # Rendi il campo non obbligatorio, così l'utente può inviare il form
                # anche se non risponde a tutte le domande.
                required=False
            )
