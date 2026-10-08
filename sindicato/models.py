from django.db import models
from django.core.validators import RegexValidator


class InformacionSindicato(models.Model):
    """
    Información general, pública y administrativa del sindicato.
    Se maneja como registro único (singleton): solo debe existir un renglón.
    """
    nombre = models.CharField("Nombre del sindicato", max_length=255)
    siglas = models.CharField("Siglas", max_length=50, blank=True)
    mision = models.TextField("Misión", blank=True)
    vision = models.TextField("Visión", blank=True)
    historia = models.TextField("Historia / reseña", blank=True)
    domicilio_oficinas_centrales = models.CharField(
        "Domicilio de oficinas centrales", max_length=255, blank=True
    )
    telefono_contacto = models.CharField("Teléfono de contacto", max_length=30, blank=True)
    correo_contacto = models.EmailField("Correo de contacto", blank=True)
    sitio_web = models.URLField("Sitio web", blank=True)
    actualizado = models.DateTimeField("Última actualización", auto_now=True)

    class Meta:
        verbose_name = "Información del sindicato"
        verbose_name_plural = "Información del sindicato"

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        # Garantiza que solo exista un registro (singleton)
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # evita que se borre accidentalmente el único registro


class CentroTrabajo(models.Model):
    nombre = models.CharField("Nombre del centro de trabajo", max_length=255)
    empresa = models.CharField("Empresa", max_length=255)
    direccion = models.CharField("Dirección", max_length=255, blank=True)
    ciudad = models.CharField("Ciudad", max_length=120, blank=True)
    contacto_nombre = models.CharField("Nombre del contacto sindical", max_length=150, blank=True)
    contacto_telefono = models.CharField("Teléfono del contacto", max_length=30, blank=True)
    activo = models.BooleanField("Activo", default=True)
    fecha_alta = models.DateField("Fecha de alta en el sistema", auto_now_add=True)

    class Meta:
        verbose_name = "Centro de trabajo"
        verbose_name_plural = "Centros de trabajo"
        ordering = ["empresa", "nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.empresa})"

    @property
    def total_agremiados(self):
        return self.agremiados.filter(activo=True).count()


class Agremiado(models.Model):
    matricula = models.CharField(
        "Matrícula / número de afiliado", max_length=30, unique=True,
        validators=[RegexValidator(r"^[A-Za-z0-9\-]+$", "Solo letras, números y guiones.")],
    )
    nombre_completo = models.CharField("Nombre completo", max_length=255)
    centro_trabajo = models.ForeignKey(
        CentroTrabajo, on_delete=models.PROTECT, related_name="agremiados",
        verbose_name="Centro de trabajo",
    )
    puesto = models.CharField("Puesto", max_length=150, blank=True)
    fecha_ingreso_sindicato = models.DateField("Fecha de ingreso al sindicato", null=True, blank=True)
    activo = models.BooleanField("Activo", default=True)
    notas = models.TextField("Notas internas", blank=True)

    class Meta:
        verbose_name = "Agremiado"
        verbose_name_plural = "Agremiados"
        ordering = ["nombre_completo"]

    def __str__(self):
        return f"{self.nombre_completo} ({self.matricula})"


class Documento(models.Model):
    TIPO_CHOICES = [
        ("estatuto", "Estatuto"),
        ("reglamento", "Reglamento"),
        ("comunicado", "Comunicado"),
        ("acta", "Acta / minuta"),
        ("otro", "Otro"),
    ]
    titulo = models.CharField("Título", max_length=255)
    tipo = models.CharField("Tipo de documento", max_length=20, choices=TIPO_CHOICES, default="otro")
    archivo = models.FileField("Archivo", upload_to="documentos/%Y/%m/")
    descripcion = models.TextField("Descripción breve", blank=True)
    centro_trabajo = models.ForeignKey(
        CentroTrabajo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="documentos", verbose_name="Centro de trabajo (opcional)",
        help_text="Déjalo vacío si el documento aplica a todo el sindicato.",
    )
    es_publico = models.BooleanField(
        "Visible en la sección pública", default=True,
        help_text="Si está marcado, aparecerá en la página pública del sindicato.",
    )
    fecha_publicacion = models.DateField("Fecha de publicación", auto_now_add=True)

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ["-fecha_publicacion"]

    def __str__(self):
        return self.titulo
