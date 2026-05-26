from django.urls import path
from .views import ConsultaRAGView # Importe a nova View

urlpatterns = [
    path('api/consulta-rag/', ConsultaRAGView.as_view(), name='consulta_rag'), # ◄ Certifique-se de que tem a / aqui
]