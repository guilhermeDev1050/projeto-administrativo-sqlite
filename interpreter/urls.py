from django.urls import path
from . import views

urlpatterns = [
    path('', views.interpretar_pdf, name='interpretar_pdf'),
]
