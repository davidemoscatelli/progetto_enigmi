# enigmas/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# Importa TUTTI i modelli che vuoi gestire nell'admin
from .models import Enigma, RispostaUtente, Suggerimento, Profile, Badge, UserBadge, Notifica, MessaggioEnigmista# <-- Importato anche Notifica

# --- INLINES (Definizioni per mostrarli dentro altri modelli) ---

class SuggerimentoInline(admin.TabularInline):
    model = Suggerimento
    extra = 1
    fields = ('ordine', 'testo')
    ordering = ('ordine',)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profilo Dettagliato'
    fk_name = 'user'
    fields = ('bio',) # Aggiungi altri campi del profilo qui se li crei

class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    extra = 0 # Non mostrare form vuoti
    fields = ('badge', 'data_ottenimento')
    readonly_fields = ('badge', 'data_ottenimento')
    can_delete = False
    verbose_name_plural = "Badges Ottenuti"
    autocomplete_fields = ['badge'] # Rende più facile cercare/selezionare il badge

# --- ADMIN PER MODELLI PRINCIPALI ---

@admin.register(Enigma)
class EnigmaAdmin(admin.ModelAdmin):
    # Aggiunto notifica_inviata per vederlo/filtrarlo facilmente
    list_display = ('titolo', 'testo_troncato', 'start_time', 'end_time', 'is_active', 'notifica_inviata')
    list_filter = ('is_active', 'notifica_inviata', 'start_time')
    search_fields = ('titolo', 'testo')
    readonly_fields = ('end_time',)
    inlines = [SuggerimentoInline] # Permette di aggiungere hint direttamente qui

    def testo_troncato(self, obj):
        if obj.testo:
            return obj.testo[:75] + '...' if len(obj.testo) > 75 else obj.testo
        return ""
    testo_troncato.short_description = 'Testo Enigma (Troncato)'

@admin.register(RispostaUtente)
class RispostaUtenteAdmin(admin.ModelAdmin):
    list_display = ('utente', 'enigma', 'data_inserimento', 'is_corretta', 'punteggio', 'suggerimenti_usati')
    list_filter = ('is_corretta', 'enigma__is_active', 'enigma', 'utente')
    search_fields = ('utente__username', 'enigma__titolo', 'risposta_inserita')
    readonly_fields = ('is_corretta', 'suggerimenti_usati')
    autocomplete_fields = ['utente', 'enigma'] # Rende più facile selezionare

# Rimuoviamo la vecchia registrazione di User/UserAdmin se presente
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Registra User con l'admin personalizzato che include Profile E Badge
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, UserBadgeInline, ) # Mostra Profile e Badges nella pagina User
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'rarita', 'descrizione')
    list_filter = ('rarita',)
    search_fields = ('nome', 'descrizione')

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('utente', 'badge', 'data_ottenimento')
    list_filter = ('badge', 'utente')
    readonly_fields = ('data_ottenimento',)
    autocomplete_fields = ['utente', 'badge']


# --- NUOVA REGISTRAZIONE PER IL MODELLO NOTIFICA ---
@admin.register(Notifica)
class NotificaAdmin(admin.ModelAdmin):
    list_display = ('utente', 'messaggio_troncato', 'tipo_notifica', 'letta', 'data_creazione', 'link_display')
    list_filter = ('letta', 'tipo_notifica', 'data_creazione', 'utente')
    search_fields = ('utente__username', 'messaggio')
    list_editable = ('letta',) # Permette di segnare come letta/non letta direttamente dalla lista
    readonly_fields = ('data_creazione',)
    autocomplete_fields = ['utente'] # Rende più facile selezionare l'utente se devi crearne manualmente

    @admin.display(description='Messaggio (Troncato)')
    def messaggio_troncato(self, obj):
        limit = 75
        if obj.messaggio:
            return obj.messaggio[:limit] + '...' if len(obj.messaggio) > limit else obj.messaggio
        return ""

    @admin.display(description='Link')
    def link_display(self, obj):
        # Rende il link cliccabile nell'admin se presente
        from django.utils.html import format_html
        if obj.link:
            return format_html('<a href="{}" target="_blank">Apri Link</a>', obj.link)
        return "-" # Mostra un trattino se non c'è link
# --- FINE REGISTRAZIONE NOTIFICA ---

# NUOVA REGISTRAZIONE MESSAGGIO ENIGMISTA
@admin.register(MessaggioEnigmista)
class MessaggioEnigmistaAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'data_pubblicazione', 'pubblicato', 'testo_troncato')
    list_filter = ('pubblicato', 'data_pubblicazione')
    search_fields = ('titolo', 'testo')
    list_editable = ('pubblicato',) # Permette di cambiare lo stato dalla lista

    @admin.display(description='Testo (Troncato)')
    def testo_troncato(self, obj):
        limit = 100
        if obj.testo:
            return obj.testo[:limit] + '...' if len(obj.testo) > limit else obj.testo
        return ""
