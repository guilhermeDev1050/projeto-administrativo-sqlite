from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('financeiro.urls')),  # ◄ Essa linha aponta para o seu arquivo de rotas do app
]