from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('download_results', views.download_results, name='download_results'),
    path('download_graph', views.download_graph, name='download_graph'),
]
