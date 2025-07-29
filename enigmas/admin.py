# enigmas/admin.py
from django.contrib import admin
from .models import (
    Enigma, Allegato, CampoRisposta, RispostaUtente, RispostaUtenteMultipla,
    Profile, Badge, UserBadge, Notifica, MessaggioEnigmista
)

# Inline per gestire modelli correlati dentro la pagina di un altro
class AllegatoInline(admin.TabularInline):
    model = Allegato
    extra = 1

class CampoRispostaInline(admin.TabularInline):
    model = CampoRisposta
    extra = 1
    fields = ('ordine', 'etichetta', 'risposta_corretta', 'is_domanda_principale')

@admin.register(Enigma)
class EnigmaAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'start_time', 'end_time', 'is_active')
    search_fields = ['titolo', 'testo']
    list_filter = ['is_active']
    inlines = [AllegatoInline, CampoRispostaInline]

class RispostaUtenteMultiplaInline(admin.TabularInline):
    model = RispostaUtenteMultipla
    extra = 0
    readonly_fields = ('campo', 'valore_inserito')

@admin.register(RispostaUtente)
class RispostaUtenteAdmin(admin.ModelAdmin):
    # CORREZIONE: Rimosso 'suggerimenti_usati' da entrambe le liste
    list_display = ('utente', 'enigma', 'data_invio', 'is_completa_corretta', 'punteggio')
    readonly_fields = ('utente', 'enigma', 'data_invio', 'is_completa_corretta', 'punteggio')
    list_filter = ('enigma', 'is_completa_corretta')
    search_fields = ('utente__username', 'enigma__titolo')
    inlines = [RispostaUtenteMultiplaInline]

# Il resto del file rimane per gestire gli altri modelli
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
admin.site.register(CampoRisposta)
