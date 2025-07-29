# enigmas/adapters.py

from allauth.account.adapter import DefaultAccountAdapter

class AccountAdapter(DefaultAccountAdapter):

    def save_user(self, request, user, form, commit=True):
        """
        Questo metodo viene chiamato quando un utente si registra.
        Noi lo modifichiamo per impostare l'utente come non attivo.
        """
        # Prima, eseguiamo la logica di salvataggio standard
        user = super().save_user(request, user, form, commit=False)
        
        # Poi, impostiamo il campo 'is_active' a False
        user.is_active = False
        
        # Infine, salviamo l'utente nel database
        if commit:
            user.save()
            
        return user
