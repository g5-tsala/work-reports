"""Aba: Administradores Onshore.

Um bloco por administrador na planilha; aqui vira uma tabela comparativa do mês
mais a série de AUM de cada um. `ROA G5` é a receita que fica com a casa;
`ROA Adm` é o custo de administração pago à instituição.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    cartao,
    colunas,
    esc,
    faixa_kpis,
    fonte,
    grafico,
    html,
    kpi,
    nota,
    num,
    secao,
    tabela,
)
from .comum import agrupamentos_repetidos, bloco_administrador

GRAFICOS_NA_PAGINA = 6


@pagina(
    identificador="administradores-onshore",
    titulo="Administradores Onshore",
    grupo="Estrutura",
    ordem=10,
    subtitulo="AUM, receita e custo de administração por instituição, em R$.",
)
def render(ctx: Contexto) -> str:
    bloco = ctx.bloco("estrutura", "administradores", "onshore")
    resumos = [bloco_administrador(ctx, item) for item in bloco["blocos"]]
    resumos = [resumo for resumo in resumos if resumo]
    repetidos = agrupamentos_repetidos(resumos)

    return "".join(
        [
            _kpis(resumos),
            secao(
                "Comparativo do mês",
                _tabela(resumos),
                fonte("ar_adm_on e custos_adm_on", ctx.rotulo_mes, "Receita mensalizada."),
                _barras(resumos),
                nota(
                    "<strong>ROA G5</strong> é a receita de gestão sobre o AUM custodiado na "
                    "instituição. <strong>ROA Adm</strong> é o custo de administração pago a ela, "
                    "em módulo."
                ),
                _nota_agrupamento(repetidos),
            ),
            secao("Evolução do AUM", _series(resumos)),
        ]
    )


def _kpis(resumos: list[dict[str, Any]]) -> str:
    aum = sum((resumo["aum"] or 0) for resumo in resumos)
    receita = sum((resumo["receita"] or 0) for resumo in resumos)
    custos = sum((resumo["custos"] or 0) for resumo in resumos)
    maior = max(resumos, key=lambda resumo: resumo["aum"] or 0)["nome"] if resumos else "—"

    return faixa_kpis(
        kpi("Administradores", formato.inteiro(len(resumos)), detalhe=f"maior: {maior}"),
        kpi("AUM administrado", formato.bilhoes(aum)),
        kpi("Receita mensalizada", formato.milhoes(receita), detalhe="no mês"),
        kpi(
            "Custo de administração",
            formato.milhoes(abs(custos)),
            detalhe=f"{formato.percentual(abs(custos) / receita if receita else None)} da receita",
        ),
    )


def _tabela(resumos: list[dict[str, Any]]) -> str:
    colunas_tabela = [
        Coluna("Administrador"),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("Receita mens. (R$)", numerica=True),
        Coluna("ROA G5 (%)", numerica=True),
        Coluna("Custos (R$)", numerica=True),
        Coluna("ROA Adm (%)", numerica=True),
    ]
    linhas = [
        Linha(
            [
                _nome(resumo),
                num(formato.em_milhoes(resumo["aum"]), ordem=resumo["aum"]),
                num(formato.numero(resumo["receita"], 0), ordem=resumo["receita"]),
                num(formato.percentual(resumo["roa_g5"]), ordem=resumo["roa_g5"]),
                num(formato.numero(resumo["custos"], 0), ordem=resumo["custos"]),
                num(formato.percentual(resumo["roa_adm"]), ordem=resumo["roa_adm"]),
            ]
        )
        for resumo in resumos
    ]

    aum = sum((resumo["aum"] or 0) for resumo in resumos)
    receita = sum((resumo["receita"] or 0) for resumo in resumos)
    custos = sum((resumo["custos"] or 0) for resumo in resumos)
    linhas.append(
        Linha(
            [
                "Total",
                num(formato.em_milhoes(aum)),
                num(formato.numero(receita, 0)),
                num(formato.percentual(receita * 12 / aum if aum else None)),
                num(formato.numero(custos, 0)),
                num(formato.percentual(abs(custos) * 12 / aum if aum else None)),
            ],
            classe="total",
        )
    )
    return tabela(colunas_tabela, linhas, identificador="adm-onshore")


def _nome(resumo: dict[str, Any]):
    """Nome do administrador, com o marcador de agrupamento quando existir."""
    if not resumo["agrupamento"]:
        return resumo["nome"]
    return html(
        f'{esc(resumo["nome"])} '
        f'<span class="g5-marcador">{esc(resumo["agrupamento"])}</span>'
    )


def _barras(resumos: list[dict[str, Any]]) -> str:
    itens = sorted(
        ((resumo["nome"], resumo["aum"]) for resumo in resumos),
        key=lambda item: item[1] or 0,
        reverse=True,
    )
    return grafico(
        graficos.barras_horizontais(
            itens,
            formatador=lambda v: formato.em_bilhoes(v, 2),
            titulo="AUM por administrador",
        ),
        itens_legenda=[("AUM (R$ bi)", graficos.SERIES[0])],
    )


def _series(resumos: list[dict[str, Any]]) -> str:
    maiores = sorted(resumos, key=lambda resumo: resumo["aum"] or 0, reverse=True)[:GRAFICOS_NA_PAGINA]
    return colunas(*[cartao(resumo["nome"], resumo["grafico"]) for resumo in maiores])


def _nota_agrupamento(repetidos: list[str]) -> str:
    if not repetidos:
        return ""
    marcadores = ", ".join(f"<strong>{esc(marcador)}</strong>" for marcador in repetidos)
    return nota(
        f"Os administradores marcados com {marcadores} compartilham o mesmo AUM e a mesma "
        "receita na planilha de origem — só os custos são próprios de cada um. Por isso a soma "
        "da coluna de AUM desta tabela <strong>não</strong> equivale ao AUM onshore da casa."
    )
