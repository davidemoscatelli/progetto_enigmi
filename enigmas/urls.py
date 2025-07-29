# enigmas/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URL Principali dell'app
    path('', views.enigma_view, name='enigma_view'),
    path('classifica/', views.classifica_view, name='classifica'),
    path('regole-punteggio/', views.regole_punteggio_view, name='regole_punteggio'),

    # URL per i profili utente
    path('profilo/<str:username>/', views.profile_view, name='profile_view'),
    path('profilo/', views.my_profile_view, name='my_profile'),

    # URL per le notifiche
    path('notifiche/', views.lista_notifiche, name='lista_notifiche'),
]
