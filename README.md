# SIGES — Sistema Integral de Gestión Sindical

Proyecto base (Django) para el sistema que centraliza el control de los
centros de trabajo, agremiados y documentos/estatutos del sindicato.
Corresponde a las fases 3-7 del proyecto (diseño de base de datos,
arquitectura, mockups y desarrollo de backend/frontend).

## Qué incluye este avance

- **Modelos de datos**: `InformacionSindicato`, `CentroTrabajo`, `Agremiado`, `Documento`.
- **Panel administrativo** (Django admin) ya funcional: alta, baja y edición
  de centros de trabajo, agremiados y documentos, con búsqueda y filtros.
- **Sitio público**: página de inicio con indicadores generales, listado de
  centros de trabajo, y sección de documentos/estatutos descargables.
- Todo en español, con SQLite para desarrollo (no requiere instalar un
  servidor de base de datos aparte).

## Requisitos

- Python 3.11 o superior instalado en tu equipo.

## Cómo ejecutarlo en tu computadora

1. Descomprime la carpeta del proyecto y abre una terminal dentro de ella.
2. Crea el entorno virtual e instala las dependencias:

   ```
   python -m venv venv
   venv\Scripts\activate        (en Windows)
   source venv/bin/activate     (en Mac/Linux)
   pip install -r requirements.txt
   ```

3. Crea la base de datos local:

   ```
   python manage.py migrate
   ```

4. Crea tu usuario administrador (te pedirá usuario, correo y contraseña):

   ```
   python manage.py createsuperuser
   ```

5. Levanta el servidor local:

   ```
   python manage.py runserver
   ```

6. Abre en el navegador:
   - Sitio público: http://127.0.0.1:8000/
   - Panel administrativo: http://127.0.0.1:8000/admin/

## Primeros pasos al entrar al panel administrativo

1. Entra a **Información del sindicato** y crea el único registro con el
   nombre, siglas, historia y datos de contacto (esto es lo que se ve en
   la página pública de inicio).
2. Da de alta los **Centros de trabajo**.
3. Da de alta los **Agremiados**, asignando su centro de trabajo.
4. Sube los **Documentos** (estatutos, reglamentos, etc.) y marca cuáles
   deben verse en la sección pública.

## Siguientes pasos sugeridos (fases 8-10 del proyecto)

- Migrar la información real recopilada por Zayra (fase 8).
- Probar el sistema con personal del sindicato y ajustar según su
  retroalimentación (fase 9).
- Preparar el manual de uso y la capacitación de entrega (fase 10).

## Estructura del proyecto

```
siges_dev/
├── manage.py
├── requirements.txt
├── siges/              # configuración del proyecto (settings, urls)
└── sindicato/           # app principal
    ├── models.py         # Centros de trabajo, Agremiados, Documentos, Información
    ├── admin.py          # panel administrativo
    ├── views.py          # vistas públicas
    ├── urls.py
    ├── templates/        # plantillas HTML del sitio público
    └── static/           # hoja de estilos
```
