from django.urls import path
from . import views

app_name = "sindicato"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("centro/<int:pk>/", views.centro_detalle, name="centro_detalle"),
    path("documentos/", views.documentos_lista, name="documentos"),
]
