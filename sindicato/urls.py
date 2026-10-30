from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

app_name = "sindicato"

urlpatterns = [
    path("ingresar/", auth_views.LoginView.as_view(template_name="sindicato/login.html"), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.inicio, name="inicio"),
    path("centro/<int:pk>/", views.centro_detalle, name="centro_detalle"),
    path("documentos/", views.documentos_lista, name="documentos"),
]
