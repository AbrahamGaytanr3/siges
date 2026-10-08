from django.shortcuts import render, get_object_or_404
from .models import InformacionSindicato, CentroTrabajo, Documento


def inicio(request):
    info = InformacionSindicato.objects.first()
    centros = CentroTrabajo.objects.filter(activo=True)
    documentos = Documento.objects.filter(es_publico=True)[:8]
    total_agremiados = sum(c.total_agremiados for c in centros)
    context = {
        "info": info,
        "centros": centros,
        "documentos": documentos,
        "total_centros": centros.count(),
        "total_agremiados": total_agremiados,
    }
    return render(request, "sindicato/inicio.html", context)


def centro_detalle(request, pk):
    centro = get_object_or_404(CentroTrabajo, pk=pk, activo=True)
    documentos = Documento.objects.filter(es_publico=True, centro_trabajo=centro)
    return render(request, "sindicato/centro_detalle.html", {"centro": centro, "documentos": documentos})


def documentos_lista(request):
    documentos = Documento.objects.filter(es_publico=True)
    return render(request, "sindicato/documentos.html", {"documentos": documentos})
