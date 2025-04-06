# enigmas/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# Importa TUTTI i modelli, inclusi i nuovi Badge e UserBadge
from .models import Enigma, RispostaUtente, Suggerimento, Profile, Badge, UserBadge

# --- INLINES ESISTENTI E NUOVI ---

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

# NUOVO: Inline per mostrare i badge ottenuti nella pagina User
class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    extra = 0 # Non mostrare form vuoti, i badge vengono assegnati automaticamente
    fields = ('badge', 'data_ottenimento')
    readonly_fields = ('badge', 'data_ottenimento') # Non modificabili da qui
    can_delete = False # Generalmente non si cancellano i badge ottenuti
    verbose_name_plural = "Badges Ottenuti"

# --- ADMIN PER MODELLI PRINCIPALI ---

@admin.register(Enigma)
class EnigmaAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'testo_troncato', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'start_time')
    search_fields = ('titolo', 'testo')
    readonly_fields = ('end_time',)
    inlines = [SuggerimentoInline] # Mantiene l'inline dei suggerimenti

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
    readonly_fields = ('punteggio', 'is_corretta', 'data_inserimento', 'suggerimenti_usati')

# Rimuoviamo la vecchia registrazione di User/UserAdmin se presente
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

# Registra User con l'admin personalizzato che include Profile E Badge
@admin.register(User) # Usiamo il decoratore anche qui per coerenza
class UserAdmin(BaseUserAdmin):
    # Aggiungi ProfileInline e il nuovo UserBadgeInline
    inlines = (ProfileInline, UserBadgeInline, )
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined') # Modificato list_display esempio
    # list_select_related = ('profile',) # Togliamo per ora

# --- NUOVI ADMIN PER BADGE ---

@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'rarita', 'descrizione')
    list_filter = ('rarita',)
    search_fields = ('nome', 'descrizione')

@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ('utente', 'badge', 'data_ottenimento')
    list_filter = ('badge', 'utente')
    readonly_fields = ('data_ottenimento',) # La data è automatica
    # Rendi utente e badge non modificabili dopo la creazione?
    # readonly_fields = ('utente', 'badge', 'data_ottenimento')
    autocomplete_fields = ['utente', 'badge'] # Rende più facile selezionare
