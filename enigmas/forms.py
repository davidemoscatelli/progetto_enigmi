# enigmas/forms.py
from django import forms
from .models import RispostaUtente

class RispostaForm(forms.ModelForm):
    risposta_inserita = forms.CharField(
        label="La tua Risposta",
        widget=forms.TextInput(attrs={'placeholder': 'Inserisci qui la soluzione...'}),
        max_length=255,
        required=True
    )

    class Meta:
        model = RispostaUtente
        fields = ['risposta_inserita'] # Solo questo campo deve essere mostrato nel form