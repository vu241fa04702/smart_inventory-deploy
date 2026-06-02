"""
URL configuration for Smart Inventory Management System
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    path(
        '',
        lambda request: redirect('dashboard')
        if request.user.is_authenticated
        else redirect('login'),
        name='home'
    ),

    path('', include('inventory.urls')),

    path('api/', include('inventory.api_urls')),
]