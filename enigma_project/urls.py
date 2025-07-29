# enigma_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importiamo la nostra vista di registrazione personalizzata
from enigmas.views import CustomSignupView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Sovrascriviamo l'URL di registrazione di allauth con la nostra vista
    path('accounts/signup/', CustomSignupView.as_view(), name='account_signup'),
    
    # 2. Includiamo tutti gli altri URL di allauth (login, logout, etc.)
    path('accounts/', include('allauth.urls')),
    
    # Includiamo gli URL della nostra app 'enigmas'
    path('', include('enigmas.urls')),
]

# Aggiunge gli URL per i file media solo in modalità DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
