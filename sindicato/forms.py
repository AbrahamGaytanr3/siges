from django import forms

from .models import Documento

CAMPO_TEXTO = forms.TextInput(attrs={"class": "campo-formulario"})
CAMPO_SELECT = forms.Select(attrs={"class": "campo-formulario"})
CAMPO_TEXTAREA = forms.Textarea(attrs={"class": "campo-formulario", "rows": 4})
CAMPO_ARCHIVO = forms.ClearableFileInput(attrs={"class": "campo-formulario"})
CAMPO_CHECKBOX = forms.CheckboxInput(attrs={"class": "campo-checkbox"})


class DocumentoForm(forms.ModelForm):
    class Meta:
        model = Documento
        fields = ["titulo", "tipo", "archivo", "descripcion", "centro_trabajo", "es_publico"]
        widgets = {
            "titulo": CAMPO_TEXTO,
            "tipo": CAMPO_SELECT,
            "archivo": CAMPO_ARCHIVO,
            "descripcion": CAMPO_TEXTAREA,
            "centro_trabajo": CAMPO_SELECT,
            "es_publico": CAMPO_CHECKBOX,
        }
