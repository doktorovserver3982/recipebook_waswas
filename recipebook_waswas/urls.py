"""
URL configuration for recipebook_waswas project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('save/<uuid:recipe_id>/', views.save_recipe, name='save_recipe'),
    path('search/', views.search_results, name='search_results'),
    path('recipe/<uuid:recipe_id>/', views.recipe_page, name='recipe_page'),

    path('accounts/', include('django.contrib.auth.urls')),
    path('register/', views.register, name='register'),
    path('fridge/', views.fridge, name='fridge'),
    path('fridge/add/', views.add_to_fridge, name='add_to_fridge'),
    path('fridge/remove/<uuid:item_id>/', views.remove_from_fridge, name='remove_from_fridge'),
    path('recipe/<uuid:recipe_id>/save/', views.toggle_save_recipe, name='toggle_save_recipe'),
    path('favorites/', views.favorites, name='favorites'),
]
