from django.contrib import admin
from django.urls import path, include # Assicurati che include sia importato

urlpatterns = [
    path('admin/', admin.site.urls),
    # Includi gli URL dell'app 'enigmas' per il percorso radice e altri percorsi
    path('', include('enigmas.urls')),
    
    # Potresti voler separare l'autenticazione, ma per semplicità la lasciamo in enigmas.urls
    # path('accounts/', include('django.contrib.auth.urls')), # Include altri URL di auth se servono
]