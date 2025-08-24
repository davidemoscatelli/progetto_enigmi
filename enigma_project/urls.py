# enigma_project/urls.py

from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.views.static import serve # Importa la vista per servire i file

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('enigmas.urls')),
]

# --- MODIFICA CHIAVE PER SERVIRE I FILE MEDIA SU RENDER ---
# Aggiunge un URL pattern che funziona anche quando DEBUG = False
# Questo dice a Django: "Quando ricevi una richiesta per un file in /media/,
# cercalo nella cartella specificata in MEDIA_ROOT (il nostro disco)".
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
