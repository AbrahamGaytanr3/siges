from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import InformacionSindicato, CentroTrabajo, Documento

CENTROS_POR_PAGINA = 10
DOCUMENTOS_POR_PAGINA = 12


def inicio(request):
    info = InformacionSindicato.objects.first()
    centros_qs = CentroTrabajo.objects.filter(activo=True)
    documentos = Documento.objects.filter(es_publico=True)[:8]
    total_agremiados = sum(c.total_agremiados for c in centros_qs)

    paginador_centros = Paginator(centros_qs, CENTROS_POR_PAGINA)
    centros = paginador_centros.get_page(request.GET.get("pagina"))

    context = {
        "info": info,
        "centros": centros,
        "documentos": documentos,
        "total_centros": paginador_centros.count,
        "total_agremiados": total_agremiados,
    }
    return render(request, "sindicato/inicio.html", context)


def centro_detalle(request, pk):
    centro = get_object_or_404(CentroTrabajo, pk=pk, activo=True)
    documentos = Documento.objects.filter(es_publico=True, centro_trabajo=centro)
    return render(request, "sindicato/centro_detalle.html", {"centro": centro, "documentos": documentos})


def documentos_lista(request):
    documentos_qs = Documento.objects.filter(es_publico=True)
    paginador = Paginator(documentos_qs, DOCUMENTOS_POR_PAGINA)
    documentos = paginador.get_page(request.GET.get("pagina"))
    return render(request, "sindicato/documentos.html", {"documentos": documentos})
