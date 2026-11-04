import csv

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import (
    CadastroForm,
    FiltroPeriodoForm,
    ItemFormSet,
    PontoForm,
    SolicitacaoForm,
    TipoForm,
)
from .models import ItemDescartado, PontoColeta, SolicitacaoDescarte, TipoResiduo
from .permissions import administrador_required


# ----------------------------------------------------------------- páginas públicas
def home(request):
    contexto = {
        "total_itens": ItemDescartado.objects.aggregate(t=Sum("quantidade"))["t"] or 0,
        "total_solicitacoes": SolicitacaoDescarte.objects.count(),
        "total_pontos": PontoColeta.objects.filter(ativo=True).count(),
    }
    return render(request, "descarte/home.html", contexto)


def orientacoes(request):
    """RF08: orientações educativas sobre descarte correto e proteção de dados."""
    return render(request, "descarte/orientacoes.html", {"tipos": TipoResiduo.objects.all()})


def _pontos_filtrados(tipo_id):
    pontos = PontoColeta.objects.filter(ativo=True).prefetch_related("tipos")
    if tipo_id and str(tipo_id).isdigit():
        pontos = pontos.filter(tipos__id=int(tipo_id))
    return pontos.distinct()


def pontos(request):
    """RF03: consulta pública aos pontos de coleta, com filtro por tipo de resíduo."""
    tipo_id = request.GET.get("tipo", "")
    contexto = {
        "pontos": _pontos_filtrados(tipo_id),
        "tipos": TipoResiduo.objects.all(),
        "tipo_selecionado": tipo_id,
    }
    return render(request, "descarte/pontos.html", contexto)


@require_GET
def api_pontos(request):
    """Mesmo filtro da página, em JSON, para atualizar a lista sem recarregar a página."""
    dados = [
        {
            "id": p.id,
            "nome": p.nome,
            "endereco": p.endereco,
            "horario": p.horario,
            "tipos": [t.nome for t in p.tipos.all()],
        }
        for p in _pontos_filtrados(request.GET.get("tipo", ""))
    ]
    return JsonResponse({"pontos": dados})


# ----------------------------------------------------------------- conta
def cadastro(request):
    """RF01: cadastro de colaborador."""
    if request.user.is_authenticated:
        return redirect("minhas_solicitacoes")
    form = CadastroForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, "Conta criada com sucesso. Você já pode registrar um descarte.")
        return redirect("registrar")
    return render(request, "registration/cadastro.html", {"form": form})


# ----------------------------------------------------------------- colaborador
@login_required
def registrar(request):
    """RF02: registro de solicitação de descarte, com um ou mais itens."""
    solicitacao = SolicitacaoDescarte(usuario=request.user)
    form = SolicitacaoForm(request.POST or None, instance=solicitacao, initial={"unidade": request.user.unidade})
    formset = ItemFormSet(request.POST or None, instance=solicitacao, prefix="itens")
    if request.method == "POST" and form.is_valid() and formset.is_valid():
        ponto = form.cleaned_data["ponto"]
        aceitos = set(ponto.tipos.values_list("id", flat=True))
        erro = False
        if aceitos:
            for f in formset.forms:
                tipo = f.cleaned_data.get("tipo")
                if tipo and tipo.id not in aceitos:
                    f.add_error("tipo", f"Este ponto de coleta não recebe {tipo.nome.lower()}.")
                    erro = True
        if not erro:
            with transaction.atomic():
                solicitacao = form.save()
                formset.instance = solicitacao
                formset.save()
            messages.success(request, "Descarte registrado. Acompanhe o status em “Meus registros”.")
            return redirect("minhas_solicitacoes")
    return render(request, "descarte/registrar.html", {"form": form, "formset": formset})


@login_required
def minhas_solicitacoes(request):
    """RF04 e RF06: acompanhamento de status e histórico, com filtro por período e tipo."""
    filtro = FiltroPeriodoForm(request.GET or None)
    qs = SolicitacaoDescarte.objects.filter(usuario=request.user).select_related("unidade", "ponto").prefetch_related(
        "itens__tipo"
    )
    if filtro.is_valid():
        d = filtro.cleaned_data
        if d.get("de"):
            qs = qs.filter(data__gte=d["de"])
        if d.get("ate"):
            qs = qs.filter(data__lte=d["ate"])
        if d.get("tipo"):
            qs = qs.filter(itens__tipo=d["tipo"]).distinct()
    return render(request, "descarte/minhas.html", {"solicitacoes": qs, "filtro": filtro})


# ----------------------------------------------------------------- administrador
@administrador_required
def gestao_solicitacoes(request):
    """RF04: o administrador acompanha todas as solicitações e atualiza o status."""
    status = request.GET.get("status", "")
    qs = SolicitacaoDescarte.objects.select_related("usuario", "unidade", "ponto").prefetch_related("itens__tipo")
    if status in SolicitacaoDescarte.Status.values:
        qs = qs.filter(status=status)
    return render(
        request,
        "descarte/gestao.html",
        {"solicitacoes": qs, "status_escolhas": SolicitacaoDescarte.Status.choices, "status_atual": status},
    )


@administrador_required
@require_POST
def avancar_status(request, pk):
    solicitacao = get_object_or_404(SolicitacaoDescarte, pk=pk)
    avancou = solicitacao.avancar_status(por=request.user)
    quer_json = "application/json" in request.headers.get("Accept", "")
    if quer_json:
        proximo = solicitacao.proximo_status
        return JsonResponse(
            {
                "ok": avancou,
                "status": solicitacao.status,
                "status_label": solicitacao.get_status_display(),
                "proximo_label": SolicitacaoDescarte.Status(proximo).label if proximo else "",
            },
            status=200 if avancou else 409,
        )
    if avancou:
        messages.success(request, f"Solicitação #{solicitacao.pk} atualizada para “{solicitacao.get_status_display()}”.")
    else:
        messages.error(request, "Esta solicitação já está no último status.")
    return redirect("gestao_solicitacoes")


@administrador_required
def pontos_admin(request):
    return render(request, "descarte/pontos_admin.html", {"pontos": PontoColeta.objects.prefetch_related("tipos")})


@administrador_required
def ponto_form(request, pk=None):
    """RF05: cadastrar e editar pontos de coleta."""
    ponto = get_object_or_404(PontoColeta, pk=pk) if pk else None
    form = PontoForm(request.POST or None, instance=ponto)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Ponto de coleta salvo.")
        return redirect("pontos_admin")
    return render(request, "descarte/form_generico.html", {"form": form, "titulo": "Editar ponto de coleta" if ponto else "Novo ponto de coleta", "voltar": "pontos_admin"})


@administrador_required
def tipos_admin(request):
    return render(request, "descarte/tipos_admin.html", {"tipos": TipoResiduo.objects.annotate(qtd=Count("itens"))})


@administrador_required
def tipo_form(request, pk=None):
    """RF05: cadastrar e editar tipos de resíduo."""
    tipo = get_object_or_404(TipoResiduo, pk=pk) if pk else None
    form = TipoForm(request.POST or None, instance=tipo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Tipo de resíduo salvo.")
        return redirect("tipos_admin")
    return render(request, "descarte/form_generico.html", {"form": form, "titulo": "Editar tipo de resíduo" if tipo else "Novo tipo de resíduo", "voltar": "tipos_admin"})


@administrador_required
def relatorio(request):
    """RF07 (e RF09, em CSV): total de itens por tipo, unidade e período."""
    filtro = FiltroPeriodoForm(request.GET or None)
    itens = ItemDescartado.objects.all()
    if filtro.is_valid():
        d = filtro.cleaned_data
        if d.get("de"):
            itens = itens.filter(solicitacao__data__gte=d["de"])
        if d.get("ate"):
            itens = itens.filter(solicitacao__data__lte=d["ate"])
        if d.get("tipo"):
            itens = itens.filter(tipo=d["tipo"])
        if d.get("unidade"):
            itens = itens.filter(solicitacao__unidade=d["unidade"])

    por_tipo = list(itens.values("tipo__nome").annotate(total=Sum("quantidade")).order_by("-total"))
    por_unidade = list(itens.values("solicitacao__unidade__nome").annotate(total=Sum("quantidade")).order_by("-total"))
    por_mes = list(
        itens.annotate(mes=TruncMonth("solicitacao__data")).values("mes").annotate(total=Sum("quantidade")).order_by("mes")
    )
    total = sum(x["total"] for x in por_tipo)

    if request.GET.get("formato") == "csv":
        resposta = HttpResponse(content_type="text/csv; charset=utf-8")
        resposta["Content-Disposition"] = 'attachment; filename="relatorio-descarte.csv"'
        resposta.write("﻿")  # BOM para o Excel reconhecer UTF-8
        w = csv.writer(resposta, delimiter=";")
        w.writerow(["Tipo de resíduo", "Quantidade"])
        for linha in por_tipo:
            w.writerow([linha["tipo__nome"], linha["total"]])
        w.writerow([])
        w.writerow(["Unidade", "Quantidade"])
        for linha in por_unidade:
            w.writerow([linha["solicitacao__unidade__nome"], linha["total"]])
        w.writerow(["Total", total])
        return resposta

    def com_percentual(linhas):
        maior = max((x["total"] for x in linhas), default=0)
        for x in linhas:
            x["pct"] = round(100 * x["total"] / maior) if maior else 0
        return linhas

    contexto = {
        "filtro": filtro,
        "total": total,
        "por_tipo": com_percentual(por_tipo),
        "por_unidade": com_percentual(por_unidade),
        "por_mes": com_percentual(por_mes),
        "total_solicitacoes": SolicitacaoDescarte.objects.filter(itens__in=itens).distinct().count(),
    }
    return render(request, "descarte/relatorio.html", contexto)
