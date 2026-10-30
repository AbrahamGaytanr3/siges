import atexit
import shutil
import tempfile

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ProtectedError
from django.test import TestCase, override_settings
from django.urls import reverse

# Los FileField no se revierten con el rollback de transacciones de TestCase,
# así que las pruebas que suben archivos usan un MEDIA_ROOT temporal en vez
# de escribir en la carpeta media/ real del proyecto.
MEDIA_ROOT_PRUEBAS = tempfile.mkdtemp(prefix="siges_test_media_")
atexit.register(shutil.rmtree, MEDIA_ROOT_PRUEBAS, ignore_errors=True)

from .admin import InformacionSindicatoAdmin
from .models import Agremiado, CentroTrabajo, Documento, InformacionSindicato


def crear_centro(**kwargs):
    datos = {"nombre": "Planta Norte", "empresa": "Acme SA de CV"}
    datos.update(kwargs)
    return CentroTrabajo.objects.create(**datos)


def crear_agremiado(centro, **kwargs):
    datos = {
        "matricula": "A-001",
        "nombre_completo": "Juana Pérez",
        "centro_trabajo": centro,
    }
    datos.update(kwargs)
    return Agremiado.objects.create(**datos)


def crear_usuario(**kwargs):
    datos = {"username": "delegado1", "password": "clave-segura-123"}
    datos.update(kwargs)
    return get_user_model().objects.create_user(**datos)


def crear_directivo(**kwargs):
    from django.contrib.auth.models import Group

    datos = {"username": "directivo1"}
    datos.update(kwargs)
    usuario = crear_usuario(**datos)
    usuario.groups.add(Group.objects.get(name="Directiva"))
    return usuario


class InformacionSindicatoModelTests(TestCase):
    def test_save_fuerza_singleton(self):
        primero = InformacionSindicato.objects.create(nombre="Sindicato A")
        segundo = InformacionSindicato.objects.create(nombre="Sindicato B")

        self.assertEqual(primero.pk, 1)
        self.assertEqual(segundo.pk, 1)
        self.assertEqual(InformacionSindicato.objects.count(), 1)
        self.assertEqual(InformacionSindicato.objects.get().nombre, "Sindicato B")

    def test_delete_no_borra_el_registro(self):
        info = InformacionSindicato.objects.create(nombre="Sindicato A")
        info.delete()
        self.assertEqual(InformacionSindicato.objects.count(), 1)


class CentroTrabajoModelTests(TestCase):
    def test_total_agremiados_solo_cuenta_activos(self):
        centro = crear_centro()
        crear_agremiado(centro, matricula="A-001", activo=True)
        crear_agremiado(centro, matricula="A-002", activo=True)
        crear_agremiado(centro, matricula="A-003", activo=False)

        self.assertEqual(centro.total_agremiados, 2)

    def test_no_se_puede_borrar_centro_con_agremiados(self):
        centro = crear_centro()
        crear_agremiado(centro)

        with self.assertRaises(ProtectedError):
            centro.delete()

    def test_se_puede_borrar_centro_sin_agremiados(self):
        centro = crear_centro()
        centro.delete()
        self.assertEqual(CentroTrabajo.objects.count(), 0)


class AgremiadoModelTests(TestCase):
    def test_matricula_debe_ser_unica(self):
        centro = crear_centro()
        crear_agremiado(centro, matricula="A-001")

        with self.assertRaises(Exception):
            Agremiado.objects.create(
                matricula="A-001", nombre_completo="Otro", centro_trabajo=centro
            )

    def test_matricula_rechaza_caracteres_invalidos(self):
        centro = crear_centro()
        agremiado = Agremiado(
            matricula="A-001 con espacios",
            nombre_completo="Juana Pérez",
            centro_trabajo=centro,
        )
        with self.assertRaises(ValidationError):
            agremiado.full_clean()


@override_settings(MEDIA_ROOT=MEDIA_ROOT_PRUEBAS)
class DocumentoModelTests(TestCase):
    def _archivo(self):
        return SimpleUploadedFile("estatuto.txt", b"contenido", content_type="text/plain")

    def test_centro_se_pone_en_null_al_borrar_el_centro(self):
        centro = crear_centro()
        documento = Documento.objects.create(
            titulo="Estatuto general", archivo=self._archivo(), centro_trabajo=centro
        )

        centro.delete()
        documento.refresh_from_db()
        self.assertIsNone(documento.centro_trabajo)


class InformacionSindicatoAdminTests(TestCase):
    def setUp(self):
        self.admin = InformacionSindicatoAdmin(InformacionSindicato, AdminSite())

    def test_no_permite_agregar_si_ya_existe_un_registro(self):
        self.assertTrue(self.admin.has_add_permission(request=None))
        InformacionSindicato.objects.create(nombre="Sindicato A")
        self.assertFalse(self.admin.has_add_permission(request=None))

    def test_nunca_permite_borrar(self):
        InformacionSindicato.objects.create(nombre="Sindicato A")
        self.assertFalse(self.admin.has_delete_permission(request=None))


@override_settings(MEDIA_ROOT=MEDIA_ROOT_PRUEBAS)
class VistasPublicasTests(TestCase):
    def setUp(self):
        # Todo el sitio requiere sesión iniciada; estas vistas ya no son
        # públicas, solo accesibles para delegados/integrantes autenticados.
        self.client.force_login(crear_usuario())

    def _archivo(self):
        return SimpleUploadedFile("doc.txt", b"contenido", content_type="text/plain")

    def test_inicio_solo_muestra_centros_activos_y_totales_correctos(self):
        activo = crear_centro(nombre="Planta Norte", activo=True)
        crear_centro(nombre="Planta Cerrada", empresa="Acme SA de CV", activo=False)
        crear_agremiado(activo, matricula="A-001", activo=True)
        crear_agremiado(activo, matricula="A-002", activo=False)

        response = self.client.get(reverse("sindicato:inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["centros"]), [activo])
        self.assertEqual(response.context["total_centros"], 1)
        self.assertEqual(response.context["total_agremiados"], 1)

    def test_inicio_solo_lista_documentos_publicos(self):
        Documento.objects.create(titulo="Público", archivo=self._archivo(), es_publico=True)
        Documento.objects.create(titulo="Privado", archivo=self._archivo(), es_publico=False)

        response = self.client.get(reverse("sindicato:inicio"))

        titulos = [doc.titulo for doc in response.context["documentos"]]
        self.assertEqual(titulos, ["Público"])

    def test_centro_detalle_404_si_esta_inactivo(self):
        centro = crear_centro(activo=False)
        response = self.client.get(reverse("sindicato:centro_detalle", args=[centro.pk]))
        self.assertEqual(response.status_code, 404)

    def test_centro_detalle_muestra_solo_sus_documentos_publicos(self):
        centro = crear_centro(activo=True)
        otro_centro = crear_centro(nombre="Planta Sur", empresa="Acme SA de CV", activo=True)
        Documento.objects.create(
            titulo="De este centro", archivo=self._archivo(),
            es_publico=True, centro_trabajo=centro,
        )
        Documento.objects.create(
            titulo="De otro centro", archivo=self._archivo(),
            es_publico=True, centro_trabajo=otro_centro,
        )

        response = self.client.get(reverse("sindicato:centro_detalle", args=[centro.pk]))

        titulos = [doc.titulo for doc in response.context["documentos"]]
        self.assertEqual(titulos, ["De este centro"])

    def test_documentos_lista_excluye_privados(self):
        Documento.objects.create(titulo="Público", archivo=self._archivo(), es_publico=True)
        Documento.objects.create(titulo="Privado", archivo=self._archivo(), es_publico=False)

        response = self.client.get(reverse("sindicato:documentos"))

        titulos = [doc.titulo for doc in response.context["documentos"]]
        self.assertEqual(titulos, ["Público"])


class AdminLoginTests(TestCase):
    def test_admin_requiere_login(self):
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)

    def test_staff_puede_entrar_al_admin(self):
        # force_login en vez de login(): el test client no pasa `request` a
        # authenticate(), y el backend de axes lo requiere.
        usuario = get_user_model().objects.create_user(
            username="staff", password="clave-segura-123", is_staff=True
        )
        self.client.force_login(usuario)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)


class AccesoProtegidoTests(TestCase):
    """Todo el sitio requiere sesión iniciada (software interno, no público)."""

    def test_inicio_redirige_a_login_sin_sesion(self):
        response = self.client.get(reverse("sindicato:inicio"))
        self.assertRedirects(
            response, f"{reverse('sindicato:login')}?next={reverse('sindicato:inicio')}"
        )

    def test_documentos_redirige_a_login_sin_sesion(self):
        response = self.client.get(reverse("sindicato:documentos"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("sindicato:login"), response.url)

    def test_centro_detalle_redirige_a_login_sin_sesion(self):
        centro = crear_centro()
        response = self.client.get(reverse("sindicato:centro_detalle", args=[centro.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("sindicato:login"), response.url)

    def test_inicio_accesible_con_sesion(self):
        self.client.force_login(crear_usuario())
        response = self.client.get(reverse("sindicato:inicio"))
        self.assertEqual(response.status_code, 200)


class LoginLogoutViewTests(TestCase):
    def test_login_con_credenciales_validas_redirige_a_inicio(self):
        crear_usuario(username="delegado1", password="clave-segura-123")
        response = self.client.post(reverse("sindicato:login"), {
            "username": "delegado1", "password": "clave-segura-123",
        })
        self.assertRedirects(response, reverse("sindicato:inicio"))

    def test_login_con_credenciales_invalidas_no_autentica(self):
        crear_usuario(username="delegado1", password="clave-segura-123")
        response = self.client.post(reverse("sindicato:login"), {
            "username": "delegado1", "password": "incorrecta",
        })
        self.assertEqual(response.status_code, 200)  # reformula el mismo form
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_cierra_sesion_y_redirige_a_login(self):
        self.client.force_login(crear_usuario())
        response = self.client.post(reverse("sindicato:logout"))
        self.assertRedirects(response, reverse("sindicato:login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_nav_no_muestra_links_internos_sin_sesion(self):
        response = self.client.get(reverse("sindicato:login"))
        self.assertNotContains(response, 'href="/documentos/"')

    def test_nav_muestra_cerrar_sesion_con_sesion(self):
        self.client.force_login(crear_usuario())
        response = self.client.get(reverse("sindicato:inicio"))
        self.assertContains(response, "Cerrar sesión")


class GruposMigracionTests(TestCase):
    """La migración de datos 0004 crea los grupos Directiva/Delegados."""

    def test_grupo_directiva_tiene_permisos_completos_en_los_4_modelos(self):
        from django.contrib.auth.models import Group

        directiva = Group.objects.get(name="Directiva")
        codenames = set(directiva.permissions.values_list("codename", flat=True))
        esperados = {
            f"{accion}_{modelo}"
            for accion in ("add", "change", "delete", "view")
            for modelo in ("informacionsindicato", "centrotrabajo", "agremiado", "documento")
        }
        self.assertEqual(codenames, esperados)

    def test_grupo_delegados_existe_sin_permisos_especiales(self):
        from django.contrib.auth.models import Group

        delegados = Group.objects.get(name="Delegados")
        self.assertEqual(delegados.permissions.count(), 0)


@override_settings(MEDIA_ROOT=MEDIA_ROOT_PRUEBAS)
class GestionDocumentosTests(TestCase):
    """Subir/editar/eliminar documentos: solo Directiva puede, vía permisos."""

    def _archivo(self, nombre="doc.txt"):
        return SimpleUploadedFile(nombre, b"contenido", content_type="text/plain")

    def _datos_formulario(self, **overrides):
        datos = {
            "titulo": "Estatuto 2026",
            "tipo": "estatuto",
            "descripcion": "",
            "centro_trabajo": "",
            "es_publico": "on",
        }
        datos.update(overrides)
        return datos

    # --- Directiva puede subir/editar/eliminar ---

    def test_directiva_puede_subir_documento(self):
        self.client.force_login(crear_directivo())
        response = self.client.post(
            reverse("sindicato:documento_subir"),
            {**self._datos_formulario(), "archivo": self._archivo()},
        )
        self.assertRedirects(response, reverse("sindicato:documentos"))
        self.assertTrue(Documento.objects.filter(titulo="Estatuto 2026").exists())

    def test_directiva_puede_editar_documento(self):
        self.client.force_login(crear_directivo())
        documento = Documento.objects.create(titulo="Viejo título", archivo=self._archivo())

        response = self.client.post(
            reverse("sindicato:documento_editar", args=[documento.pk]),
            {**self._datos_formulario(titulo="Título actualizado"), "archivo": self._archivo("otro.txt")},
        )

        self.assertRedirects(response, reverse("sindicato:documentos"))
        documento.refresh_from_db()
        self.assertEqual(documento.titulo, "Título actualizado")

    def test_directiva_puede_eliminar_documento(self):
        self.client.force_login(crear_directivo())
        documento = Documento.objects.create(titulo="A borrar", archivo=self._archivo())

        response = self.client.post(reverse("sindicato:documento_eliminar", args=[documento.pk]))

        self.assertRedirects(response, reverse("sindicato:documentos"))
        self.assertFalse(Documento.objects.filter(pk=documento.pk).exists())

    # --- Delegado autenticado sin permisos: 403 ---

    def test_delegado_no_puede_subir_documento(self):
        self.client.force_login(crear_usuario())
        response = self.client.get(reverse("sindicato:documento_subir"))
        self.assertEqual(response.status_code, 403)

    def test_delegado_no_puede_editar_documento(self):
        self.client.force_login(crear_usuario())
        documento = Documento.objects.create(titulo="Doc", archivo=self._archivo())
        response = self.client.get(reverse("sindicato:documento_editar", args=[documento.pk]))
        self.assertEqual(response.status_code, 403)

    def test_delegado_no_puede_eliminar_documento(self):
        self.client.force_login(crear_usuario())
        documento = Documento.objects.create(titulo="Doc", archivo=self._archivo())
        response = self.client.get(reverse("sindicato:documento_eliminar", args=[documento.pk]))
        self.assertEqual(response.status_code, 403)

    # --- Anónimo: redirige a login ---

    def test_anonimo_redirige_a_login_al_subir(self):
        response = self.client.get(reverse("sindicato:documento_subir"))
        self.assertIn(reverse("sindicato:login"), response.url)

    # --- Visibilidad de botones en el HTML ---

    def test_delegado_no_ve_botones_de_gestion(self):
        Documento.objects.create(titulo="Doc público", archivo=self._archivo(), es_publico=True)
        self.client.force_login(crear_usuario())

        response = self.client.get(reverse("sindicato:documentos"))

        self.assertNotContains(response, "Subir documento")
        self.assertNotContains(response, ">Editar<")
        self.assertNotContains(response, ">Eliminar<")

    def test_directiva_ve_botones_de_gestion(self):
        Documento.objects.create(titulo="Doc público", archivo=self._archivo(), es_publico=True)
        self.client.force_login(crear_directivo())

        response = self.client.get(reverse("sindicato:documentos"))

        self.assertContains(response, "Subir documento")
        self.assertContains(response, ">Editar<")
        self.assertContains(response, ">Eliminar<")
