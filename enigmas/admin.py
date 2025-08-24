# enigmas/admin.py
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    Enigma, Allegato, CampoRisposta, OpzioneRisposta, RispostaUtente, RispostaUtenteMultipla,
    Profile, Badge, UserBadge, Notifica, MessaggioEnigmista, Suggerimento
)

class AllegatoInline(admin.TabularInline):
    model = Allegato
    extra = 1

class CampoRispostaInline(admin.TabularInline):
    model = CampoRisposta
    extra = 1
    fields = ('ordine', 'etichetta', 'is_domanda_principale', 'link_alle_opzioni')
    readonly_fields = ('link_alle_opzioni',)
    def link_alle_opzioni(self, obj):
        if obj.pk:
            url = reverse('admin:enigmas_camporisposta_change', args=[obj.pk])
            return format_html('<a href="{}" target="_blank">Aggiungi/Modifica Opzioni &rarr;</a>', url)
        return "Salva prima di aggiungere le opzioni di risposta."
    link_alle_opzioni.short_description = 'Opzioni di Risposta'

# --- NUOVO INLINE PER GLI AIUTI ---
class SuggerimentoInline(admin.TabularInline):
    model = Suggerimento
    extra = 1

@admin.register(Enigma)
class EnigmaAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'start_time', 'end_time', 'is_active')
    search_fields = ['titolo', 'testo']
    list_filter = ['is_active']
    # Aggiungiamo il pannello degli aiuti qui
    inlines = [AllegatoInline, CampoRispostaInline, SuggerimentoInline]

class OpzioneRispostaInline(admin.TabularInline):
    model = OpzioneRisposta
    extra = 1

@admin.register(CampoRisposta)
class CampoRispostaAdmin(admin.ModelAdmin):
    list_display = ('etichetta', 'enigma', 'is_domanda_principale')
    list_filter = ('enigma',)
    search_fields = ('etichetta',)
    inlines = [OpzioneRispostaInline]

class RispostaUtenteMultiplaInline(admin.TabularInline):
    model = RispostaUtenteMultipla
    extra = 0
    readonly_fields = ('campo', 'valore_inserito')

@admin.register(RispostaUtente)
class RispostaUtenteAdmin(admin.ModelAdmin):
    list_display = ('utente', 'enigma', 'data_invio', 'is_completa_corretta', 'punteggio', 'suggerimenti_usati')
    readonly_fields = ('utente', 'enigma', 'data_invio', 'is_completa_corretta', 'punteggio', 'suggerimenti_usati')
    list_filter = ('enigma', 'is_completa_corretta')
    search_fields = ('utente__username', 'enigma__titolo')
    inlines = [RispostaUtenteMultiplaInline]

# ... (Il resto del file rimane invariato)
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
