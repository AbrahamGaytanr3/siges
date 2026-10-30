from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

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


class VistasPublicasTests(TestCase):
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
