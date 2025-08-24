# enigmas/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.enigma_view, name='enigma_view'),
    path('classifica/', views.classifica_view, name='classifica'),
    path('regole-punteggio/', views.regole_punteggio_view, name='regole_punteggio'),
    path('profilo/<str:username>/', views.profile_view, name='profile_view'),
    path('profilo/', views.my_profile_view, name='my_profile'),
    path('notifiche/', views.lista_notifiche, name='lista_notifiche'),
    path('account/inactive/', views.account_inactive_view, name='account_inactive'),

    # --- NUOVO URL PER LA RICHIESTA DI AIUTI ---
    path('enigma/<int:enigma_id>/richiedi_aiuto/', views.richiedi_aiuto_view, name='richiedi_aiuto'),
]
