# enigmas/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
# Importa TUTTI i modelli necessari
from .models import Enigma, RispostaUtente, Suggerimento, Profile

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


class ProfileInline(admin.StackedInline): # Stacked occupa più spazio di Tabular
    model = Profile
    can_delete = False # Non vogliamo cancellare il profilo quando cancelliamo l'utente? O sì?
    verbose_name_plural = 'Profilo'
    fk_name = 'user'

# Ridefinisci l'Admin per il modello User standard
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,) # Aggiungi l'inline del profilo
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_profile_info') # Aggiunto metodo custom
    list_select_related = ('profile',) # Ottimizza il recupero del profilo

    @admin.display(description='Bio (Profilo)') # Nome colonna custom
    def get_profile_info(self, instance):
         # Potremmo mostrare la bio o altro dal profilo qui nella lista
        return instance.profile.bio[:50] + '...' if instance.profile.bio else '-'
    # get_profile_info.short_description = 'Bio (Profilo)' # Alternativa per nome colonna

# De-registra l'admin User di default e registra il nostro custom
admin.site.unregister(User)
admin.site.register(User, UserAdmin)