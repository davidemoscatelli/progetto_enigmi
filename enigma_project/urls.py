from django.contrib import admin
from django.urls import path, include # Assicurati che include sia importato
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Includi gli URL dell'app 'enigmas' per il percorso radice e altri percorsi
    path('', include('enigmas.urls')),
   # 1. Definisci l'URL per il LOGIN PRIMA dell'include generale,
    #    specificando il template che vuoi usare tu.
    path('accounts/login/',
         auth_views.LoginView.as_view(template_name='enigmas/login.html'),
         name='login'),

    # 2. Includi gli ALTRI URL di autenticazione standard (logout, password reset, ecc.)
    #    Django sarà abbastanza intelligente da non includere di nuovo 'login'.
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts/', include('allauth.urls')),
]