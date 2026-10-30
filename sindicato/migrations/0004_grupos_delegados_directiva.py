from django.apps import apps as global_apps
from django.contrib.auth.management import create_permissions
from django.db import migrations

MODELOS_SINDICATO = ["informacionsindicato", "centrotrabajo", "agremiado", "documento"]


def crear_grupos(apps, schema_editor):
    # En una base de datos nueva (p.ej. la de pruebas), los Permission de
    # cada modelo recién se crean en el post_migrate al FINAL de todo el
    # comando migrate, no durante. Como esta migración los necesita ya, se
    # generan explícitamente aquí (create_permissions es idempotente).
    create_permissions(global_apps.get_app_config("sindicato"), verbosity=0)

    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    directiva, _ = Group.objects.get_or_create(name="Directiva")
    delegados, _ = Group.objects.get_or_create(name="Delegados")

    content_types = ContentType.objects.filter(
        app_label="sindicato", model__in=MODELOS_SINDICATO
    )
    permisos = Permission.objects.filter(content_type__in=content_types)
    directiva.permissions.set(permisos)
    # Delegados: sin permisos de Django; solo necesita sesión iniciada
    # para ver el sitio interno (no entra a /admin/).


def eliminar_grupos(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=["Directiva", "Delegados"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("sindicato", "0003_alter_documento_es_publico"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(crear_grupos, eliminar_grupos),
    ]
