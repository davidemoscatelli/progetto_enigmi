# enigmas/admin.py
from django.contrib import admin
# Importa TUTTI i modelli necessari
from .models import Enigma, RispostaUtente, Suggerimento

# Definisci l'inline per i suggerimenti da mostrare nell'admin dell'Enigma
class SuggerimentoInline(admin.TabularInline): # O admin.StackedInline per un layout diverso
    model = Suggerimento
    extra = 1 # Mostra N form vuoti per aggiungere nuovi suggerimenti (imposta a 0 se preferisci cliccare "Aggiungi")
    fields = ('ordine', 'testo') # Campi da mostrare/modificare per ogni suggerimento
    ordering = ('ordine',) # Ordina i suggerimenti per numero d'ordine

@admin.register(Enigma)
class EnigmaAdmin(admin.ModelAdmin):
    list_display = ('titolo', 'testo_troncato', 'start_time', 'end_time', 'is_active')
    list_filter = ('is_active', 'start_time')
    search_fields = ('titolo', 'testo')
    readonly_fields = ('end_time',) # end_time è calcolato

    # Aggiungi l'inline per gestire i suggerimenti DENTRO l'enigma
    inlines = [SuggerimentoInline]

    # La tua funzione per troncare il testo va bene
    def testo_troncato(self, obj):
        # Aggiunto controllo per evitare errori se testo è None (anche se non dovrebbe esserlo)
        if obj.testo:
            return obj.testo[:75] + '...' if len(obj.testo) > 75 else obj.testo
        return ""
    testo_troncato.short_description = 'Testo Enigma (Troncato)'

@admin.register(RispostaUtente)
class RispostaUtenteAdmin(admin.ModelAdmin):
    # Aggiungi 'suggerimenti_usati' al display
    list_display = ('utente', 'enigma', 'data_inserimento', 'is_corretta', 'punteggio', 'suggerimenti_usati')
    list_filter = ('is_corretta', 'enigma__is_active', 'enigma', 'utente') # Aggiunto filtro per enigma attivo
    search_fields = ('utente__username', 'enigma__titolo', 'risposta_inserita')
    # Aggiungi 'suggerimenti_usati' e 'data_inserimento' ai readonly
    readonly_fields = ('punteggio', 'is_corretta', 'data_inserimento', 'suggerimenti_usati')

# Non è strettamente necessario registrare SuggerimentoAdmin separatamente
# se usi l'inline, ma puoi farlo se vuoi una vista dedicata solo ai suggerimenti.
# @admin.register(Suggerimento)
# class SuggerimentoAdmin(admin.ModelAdmin):
#     list_display = ('enigma', 'ordine', 'testo')
#     list_filter = ('enigma',)