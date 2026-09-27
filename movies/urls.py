"""URLs of the movies catalogue."""

from django.urls import path

from . import views

app_name = 'movies'

urlpatterns = [
    path('', views.recommendation_list, name='recommendation_list'),
    path('movies/<int:pk>/', views.movie_detail, name='movie_detail'),
]
