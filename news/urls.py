"""
URL routes for the news application.

Every route has its own name so templates can reference them with the
{% url %} tag instead of hardcoding addresses.
"""
from django.urls import path

from . import views

app_name = 'news'

urlpatterns = [
    path('', views.home, name='home'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('category/<slug:slug>/', views.category_list, name='category_list'),
]
