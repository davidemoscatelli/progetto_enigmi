# enigmas/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # Importa le viste di autenticazione
from . import views # Importa le viste della tua app

urlpatterns = [
    path('', views.enigma_view, name='enigma_view'), # Pagina principale con l'enigma
    path('classifica/', views.classifica_view, name='classifica'),
    path('regole-punteggio/', views.regole_punteggio_view, name='regole_punteggio'),

    # URLs di Autenticazione
    # Usiamo la nostra vista custom per il template di login
    path('login/', views.CustomLoginView.as_view(), name='login'),
    # Usiamo la vista built-in per il logout
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'), # Reindirizza al login dopo logout

    # Aggiungere qui altri URL se necessari (es. registrazione, password reset)
    # path('register/', views.register_view, name='register'),
    # path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    # ... ecc ...
]