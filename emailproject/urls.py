# emailproject/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # route root ('/') to mailapp so /, /inbox/, /send/ etc are handled
    path('', include('mailapp.urls')),
]

