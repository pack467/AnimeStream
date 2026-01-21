# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    
    # Authentication routes (from accounts app)
    path("", include("accounts.urls")),
    
    # Main app routes (home, recommendations, widgets)
    path("", include("main.urls")),
]