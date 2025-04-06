# enigmas/apps.py
from django.apps import AppConfig

class EnigmasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'enigmas'

    # Aggiungi questo metodo per caricare i segnali
    def ready(self):
        import enigmas.signals # Importa il modulo signals quando l'app è pronta