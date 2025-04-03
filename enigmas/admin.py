# enigmas/admin.py
from django.contrib import admin
from .models import Enigma, RispostaUtente

class EnigmaAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'testo_troncato', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'start_time')
    search_fields = ('titolo', 'testo')
    readonly_fields = ('end_time',) # Non modificabile direttamente, calcolato da save

    def testo_troncato(self, obj):
        return obj.testo[:75] + '...' if len(obj.testo) > 75 else obj.testo
    testo_troncato.short_description = 'Testo Enigma (Troncato)'

class RispostaUtenteAdmin(admin.ModelAdmin):
    list_display = ('utente', 'enigma', 'data_inserimento', 'is_corretta', 'punteggio')
    list_filter = ('is_corretta', 'enigma', 'utente')
    search_fields = ('utente__username', 'enigma__titolo', 'risposta_inserita')
    readonly_fields = ('punteggio', 'is_corretta') # Calcolati automaticamente

admin.site.register(Enigma, EnigmaAdmin)
admin.site.register(RispostaUtente, RispostaUtenteAdmin)