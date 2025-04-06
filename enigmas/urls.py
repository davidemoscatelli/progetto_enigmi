# enigmas/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # Importa le viste di autenticazione
from . import views # Importa le viste della tua app

urlpatterns = [
    path('', views.enigma_view, name='enigma_view'), # Pagina principale con l'enigma
    path('classifica/', views.classifica_view, name='classifica'),
    path('regole-punteggio/', views.regole_punteggio_view, name='regole_punteggio'),
    path('enigma/<int:enigma_id>/suggerimento/', views.richiedi_suggerimento, name='richiedi_suggerimento'),
    # URLs di Autenticazione
    # Usiamo la nostra vista custom per il template di login
    path('login/', views.CustomLoginView.as_view(), name='login'),
    # Usiamo la vista built-in per il logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'), # Reindirizza al login dopo logout

    path('profilo/<str:username>/', views.profile_view, name='profile_view'),
    path('profilo/', views.my_profile_view, name='my_profile'), # URL per il proprio profilo
    # Aggiungere qui altri URL se necessari (es. registrazione, password reset)
    # path('register/', views.register_view, name='register'),
    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # ... ecc ...
    path('notifiche/', views.lista_notifiche, name='lista_notifiche'),
]