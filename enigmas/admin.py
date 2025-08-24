# enigmas/admin.py
from django.contrib import admin
from .models import (
    Enigma, Allegato, CampoRisposta, OpzioneRisposta, RispostaUtente, RispostaUtenteMultipla,
    Profile, Badge, UserBadge, Notifica, MessaggioEnigmista
)

# Rimuoviamo il vecchio CampoRispostaInline
# class CampoRispostaInline(admin.TabularInline): ...

class AllegatoInline(admin.TabularInline):
    model = Allegato
    extra = 1

@admin.register(Enigma)
class EnigmaAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'start_time', 'end_time', 'is_active')
    search_fields = ['titolo', 'testo']
    list_filter = ['is_active']
    # Ora qui aggiungiamo solo gli allegati. Le domande verranno gestite a parte.
    inlines = [AllegatoInline]

# --- NUOVA SEZIONE PER GESTIRE DOMANDE E OPZIONI ---
class OpzioneRispostaInline(admin.TabularInline):
    model = OpzioneRisposta
    extra = 1 # Mostra un campo vuoto per aggiungere una nuova opzione

@admin.register(CampoRisposta)
class CampoRispostaAdmin(admin.ModelAdmin):
    list_display = ('etichetta', 'enigma', 'is_domanda_principale')
    list_filter = ('enigma',)
    search_fields = ('etichetta',)
    # Dentro ogni domanda, potrai aggiungere le opzioni di risposta
    inlines = [OpzioneRispostaInline]

# Il resto del file admin rimane quasi invariato
class RispostaUtenteMultiplaInline(admin.TabularInline):
    model = RispostaUtenteMultipla
    extra = 0
    readonly_fields = ('campo', 'valore_inserito')

@admin.register(RispostaUtente)
class RispostaUtenteAdmin(admin.ModelAdmin):
    list_display = ('utente', 'enigma', 'data_invio', 'is_completa_corretta', 'punteggio')
    readonly_fields = ('utente', 'enigma', 'data_invio', 'is_completa_corretta', 'punteggio')
    list_filter = ('enigma', 'is_completa_corretta')
    search_fields = ('utente__username', 'enigma__titolo')
    inlines = [RispostaUtenteMultiplaInline]

# ... (Le altre classi Admin: BadgeAdmin, ProfileAdmin, etc. rimangono uguali) ...
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'descrizione', 'icona')
    search_fields = ('nome',)

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('utente', 'badge', 'data_ottenimento')
    list_filter = ('badge', 'utente')

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'punteggio_bonus')
    search_fields = ('user__username',)

@admin.register(Notifica)
class NotificaAdmin(admin.ModelAdmin):
    list_display = ('utente', 'messaggio', 'letta', 'data_creazione')
    list_filter = ('letta', 'utente')
    search_fields = ('utente__username', 'messaggio')

@admin.register(MessaggioEnigmista)
class MessaggioEnigmistaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'data_creazione')
    list_filter = ('is_active',)
    list_editable = ('is_active',)

admin.site.register(Allegato)
# Non registriamo più CampoRisposta qui perché ha la sua classe Admin
# admin.site.register(CampoRisposta)