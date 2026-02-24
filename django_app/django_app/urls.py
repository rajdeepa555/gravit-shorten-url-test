"""
URL configuration for Django URL shortener.
"""
from django.urls import path
from shortener import views

urlpatterns = [
    path('', views.home),
    path('api/urls', views.get_all_urls),
    path('api/shorten', views.shorten_url),
    path('<str:code>', views.redirect_to_original),
]
