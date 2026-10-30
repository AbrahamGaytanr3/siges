from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .forms import DocumentoForm
from .models import InformacionSindicato, CentroTrabajo, Documento

CENTROS_POR_PAGINA = 10
DOCUMENTOS_POR_PAGINA = 12


@login_required
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


@login_required
def centro_detalle(request, pk):
    centro = get_object_or_404(CentroTrabajo, pk=pk, activo=True)
    documentos = Documento.objects.filter(es_publico=True, centro_trabajo=centro)
    return render(request, "sindicato/centro_detalle.html", {"centro": centro, "documentos": documentos})


@login_required
def documentos_lista(request):
    documentos_qs = Documento.objects.filter(es_publico=True)
    paginador = Paginator(documentos_qs, DOCUMENTOS_POR_PAGINA)
    documentos = paginador.get_page(request.GET.get("pagina"))
    return render(request, "sindicato/documentos.html", {"documentos": documentos})


@login_required
@permission_required("sindicato.add_documento", raise_exception=True)
def documento_subir(request):
    if request.method == "POST":
        form = DocumentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento subido correctamente.")
            return redirect("sindicato:documentos")
    else:
        form = DocumentoForm()
    return render(request, "sindicato/documento_form.html", {"form": form, "accion": "Subir"})


@login_required
@permission_required("sindicato.change_documento", raise_exception=True)
def documento_editar(request, pk):
    documento = get_object_or_404(Documento, pk=pk)
    if request.method == "POST":
        form = DocumentoForm(request.POST, request.FILES, instance=documento)
        if form.is_valid():
            form.save()
            messages.success(request, "Documento actualizado.")
            return redirect("sindicato:documentos")
    else:
        form = DocumentoForm(instance=documento)
    return render(request, "sindicato/documento_form.html", {
        "form": form, "accion": "Editar", "documento": documento,
    })


@login_required
@permission_required("sindicato.delete_documento", raise_exception=True)
def documento_eliminar(request, pk):
    documento = get_object_or_404(Documento, pk=pk)
    if request.method == "POST":
        documento.delete()
        messages.success(request, "Documento eliminado.")
        return redirect("sindicato:documentos")
    return render(request, "sindicato/documento_confirmar_eliminar.html", {"documento": documento})
