# enigmas/context_processors.py
from .models import Notifica

def unread_notifications_count(request):
    """
    Aggiunge il conteggio delle notifiche non lette al contesto del template
    per l'utente autenticato.
    """
    count = 0
    if request.user.is_authenticated:
        count = Notifica.objects.filter(utente=request.user, letta=False).count()
    return {'unread_notifications_count': count}