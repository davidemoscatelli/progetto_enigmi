# enigma_project/urls.py

from django.contrib import admin
from django.urls import path, include

# Queste due importazioni sono FONDAMENTALI
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('enigmas.urls')),
]

# QUESTA È LA PARTE MANCANTE O NON CORRETTA NEL TUO FILE.
# Aggiunge gli URL per i file media (immagini, video, etc.)
# ma solo quando il progetto è in modalità DEBUG.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
