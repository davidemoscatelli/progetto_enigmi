# enigmas/forms.py
from django import forms
from .models import RispostaUtente

class RispostaMultiplaForm(forms.Form):
    def __init__(self, *args, **kwargs):
        # Riceve i campi risposta dalla vista
        campi_risposta = kwargs.pop('campi_risposta')
        super().__init__(*args, **kwargs)

        # Crea un campo di input per ogni 'CampoRisposta'
        for campo in campi_risposta:
            self.fields[f'campo_{campo.id}'] = forms.CharField(
                label=campo.etichetta,
                required=True,
                widget=forms.TextInput(attrs={'class': 'form-control mb-2'})
            )