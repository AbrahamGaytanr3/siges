from django.contrib import admin
from .models import InformacionSindicato, CentroTrabajo, Agremiado, Documento


@admin.register(InformacionSindicato)
class InformacionSindicatoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "siglas", "correo_contacto", "actualizado")

    def has_add_permission(self, request):
        # Solo permite crear el registro si aún no existe (singleton)
        return not InformacionSindicato.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class AgremiadoInline(admin.TabularInline):
    model = Agremiado
    extra = 0
    fields = ("matricula", "nombre_completo", "puesto", "activo")
    show_change_link = True


@admin.register(CentroTrabajo)
class CentroTrabajoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "empresa", "ciudad", "total_agremiados", "activo")
    list_filter = ("activo", "empresa", "ciudad")
    search_fields = ("nombre", "empresa", "ciudad")
    inlines = [AgremiadoInline]


@admin.register(Agremiado)
class AgremiadoAdmin(admin.ModelAdmin):
    list_display = ("matricula", "nombre_completo", "centro_trabajo", "puesto", "activo")
    list_filter = ("activo", "centro_trabajo__empresa", "centro_trabajo")
    search_fields = ("matricula", "nombre_completo")
    autocomplete_fields = ("centro_trabajo",)


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "tipo", "centro_trabajo", "es_publico", "fecha_publicacion")
    list_filter = ("tipo", "es_publico")
    search_fields = ("titulo", "descripcion")
