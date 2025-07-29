from .models import Notifica

def unread_notifications_context(request):
    """
    Provides the count of unread notifications to all templates.
    """
    if request.user.is_authenticated:
        count = Notifica.objects.filter(utente=request.user, letta=False).count()
        return {'unread_notifications_count': count}
    return {}