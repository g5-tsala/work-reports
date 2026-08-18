"""Aba: Captação por Grupo.

Visão canônica do drill-down: YTD por grupo econômico no nível zero e, ao
clicar, a movimentação mês a mês daquele grupo.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    faixa_kpis,
    fonte,
    grafico,
    kpi,
    linha_detalhe,
    linha_expansivel,
    nota,
    num,
    secao,
    tabela,
)

MAIORES_NO_GRAFICO = 12


@pagina(
    identificador="captacao-grupos",
    titulo="Captação › Grupos",
    grupo="Captação",
    ordem=20,
    subtitulo="Quem captou e quem sacou no ano. Clique em um grupo para ver a movimentação "
    "mês a mês.",
)
def render(ctx: Contexto) -> str:
    ytd = ctx.bloco("captacao", "grupos", "ytd")
    mensal = ctx.bloco("captacao", "grupos", "mensal")

    return "".join(
        [
            _kpis(ytd),
            secao("Maiores movimentações do ano", _barras(ctx, ytd)),
            secao(
                "Por grupo econômico (YTD)",
                _tabela(ctx, ytd, mensal),
                fonte("io_grupos", ctx.rotulo_mes, "Onshore + offshore, em R$, sem o grupo G5."),
                nota(
                    "O valor YTD é a soma das movimentações do ano. Um grupo pode aparecer com "
                    "NET positivo e ainda assim ter sacado em algum mês — o detalhe abre na linha."
                ),
            ),
        ]
    )


def _kpis(ytd: list[dict[str, Any]]) -> str:
    entradas = sum(registro["valor"] for registro in ytd if (registro["valor"] or 0) > 0)
    saidas = sum(registro["valor"] for registro in ytd if (registro["valor"] or 0) < 0)
    positivos = sum(1 for registro in ytd if (registro["valor"] or 0) > 0)
    return faixa_kpis(
        kpi("Grupos com movimentação", formato.inteiro(len(ytd)), detalhe=f"{positivos} com NET positivo"),
        kpi("Entradas no ano", formato.milhoes(entradas)),
        kpi("Saídas no ano", formato.milhoes(saidas)),
        kpi(
            "NET no ano",
            formato.milhoes(entradas + saidas),
            classe_delta=formato.classe_sinal(entradas + saidas),
        ),
    )


def _barras(ctx: Contexto, ytd: list[dict[str, Any]]) -> str:
    ordenados = sorted(ytd, key=lambda registro: abs(registro["valor"] or 0), reverse=True)
    itens = [(registro["grupo"], registro["valor"]) for registro in ordenados[:MAIORES_NO_GRAFICO]]
    return grafico(
        graficos.barras_horizontais(
            itens,
            formatador=lambda v: formato.em_milhoes(v, 1),
            titulo="Maiores movimentações do ano",
            largura_rotulo=260,
        ),
        itens_legenda=[("NET no ano (R$ mi)", graficos.SERIES[0])],
        rodape=fonte("io_grupos", ctx.rotulo_mes, "Acumulado do ano até o mês-base."),
    )


def _tabela(ctx: Contexto, ytd: list[dict[str, Any]], mensal: list[dict[str, Any]]) -> str:
    por_grupo: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for movimento in mensal:
        por_grupo[movimento["grupo"]].append(movimento)

    colunas = [
        Coluna("Grupo econômico"),
        Coluna("Officer"),
        Coluna("Segmento"),
        Coluna("Lead G5"),
        Coluna("NET no ano (R$)", numerica=True),
    ]

    linhas = []
    for indice, registro in enumerate(sorted(ytd, key=lambda r: r["valor"] or 0, reverse=True)):
        alvo = f"grupo-{indice}"
        movimentos = sorted(por_grupo.get(registro["grupo"], []), key=lambda m: m["mes"] or "")
        celulas = [
            registro["grupo"],
            registro["officer"] or formato.NAO_APLICAVEL,
            registro["segmento"] or formato.NAO_APLICAVEL,
            registro["lead_g5"] or formato.NAO_APLICAVEL,
            num(
                formato.numero(registro["valor"], 0),
                formato.classe_sinal(registro["valor"]),
                ordem=registro["valor"],
            ),
        ]
        if movimentos:
            linhas.append(Linha(celulas, atributos=linha_expansivel(alvo)))
            for movimento in movimentos:
                linhas.append(
                    Linha(
                        [
                            formato.mes_extenso(movimento["mes"]),
                            movimento["officer"] or formato.NAO_APLICAVEL,
                            movimento["segmento"] or formato.NAO_APLICAVEL,
                            movimento["lead_externo"] or formato.NAO_APLICAVEL,
                            num(
                                formato.numero(movimento["valor"], 0),
                                formato.classe_sinal(movimento["valor"]),
                            ),
                        ],
                        classe="detalhe",
                        nivel=1,
                        atributos=linha_detalhe(alvo),
                    )
                )
        else:
            linhas.append(Linha(celulas))

    return tabela(colunas, linhas, identificador="captacao-grupos", filtravel=True)
