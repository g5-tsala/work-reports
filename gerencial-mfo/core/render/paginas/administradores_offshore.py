"""Aba: Administradores Offshore.

Mesma leitura da aba onshore, **em US$** e sem mensalização — o offshore entra
por competência, anualizado com `× 12` puro.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    aviso,
    cartao,
    colunas,
    esc,
    faixa_kpis,
    fonte,
    grafico,
    kpi,
    nota,
    num,
    secao,
    tabela,
)
from .comum import agrupamentos_repetidos, bloco_administrador

GRAFICOS_NA_PAGINA = 6


@pagina(
    identificador="administradores-offshore",
    titulo="Administradores Offshore",
    grupo="Estrutura",
    ordem=20,
    subtitulo="AUM, receita e custo de administração por instituição, em US$.",
)
def render(ctx: Contexto) -> str:
    bloco = ctx.bloco("estrutura", "administradores", "offshore")
    resumos = [bloco_administrador(ctx, item) for item in bloco["blocos"]]
    resumos = [resumo for resumo in resumos if resumo]
    repetidos = agrupamentos_repetidos(resumos)

    return "".join(
        [
            aviso(
                f"Valores em <strong>US$</strong>, por competência — o offshore não é "
                f"mensalizado. Câmbio do mês: US$ 1 = R$ {formato.numero(ctx.dolar, 4)}."
            ),
            _kpis(ctx, resumos),
            secao(
                "Comparativo do mês",
                _tabela(resumos),
                fonte("ar_adm_off e custos_adm_off", ctx.rotulo_mes, "Sem mensalização."),
                _barras(resumos),
                _nota_agrupamento(repetidos),
            ),
            secao("Evolução do AUM", _series(resumos)),
        ]
    )


def _kpis(ctx: Contexto, resumos: list[dict[str, Any]]) -> str:
    aum = sum((resumo["aum"] or 0) for resumo in resumos)
    receita = sum((resumo["receita"] or 0) for resumo in resumos)
    custos = sum((resumo["custos"] or 0) for resumo in resumos)

    return faixa_kpis(
        kpi("Administradores", formato.inteiro(len(resumos))),
        kpi(
            "AUM administrado",
            formato.milhoes(aum, moeda="US$"),
            detalhe=f"{formato.bilhoes(aum * ctx.dolar if aum else None)} ao câmbio do mês",
        ),
        kpi("Receita do mês", formato.numero(receita, 0), detalhe="US$, por competência"),
        kpi("Custo de administração", formato.numero(abs(custos), 0), detalhe="US$ no mês"),
    )


def _tabela(resumos: list[dict[str, Any]]) -> str:
    colunas_tabela = [
        Coluna("Administrador"),
        Coluna("AUM (US$ mi)", numerica=True),
        Coluna("Receita (US$)", numerica=True),
        Coluna("ROA G5 (%)", numerica=True),
        Coluna("Custos (US$)", numerica=True),
        Coluna("ROA Adm (%)", numerica=True),
    ]
    linhas = [
        Linha(
            [
                resumo["nome"],
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
    return tabela(colunas_tabela, linhas, identificador="adm-offshore")


def _barras(resumos: list[dict[str, Any]]) -> str:
    itens = sorted(
        ((resumo["nome"], resumo["aum"]) for resumo in resumos),
        key=lambda item: item[1] or 0,
        reverse=True,
    )
    return grafico(
        graficos.barras_horizontais(
            itens,
            formatador=lambda v: formato.em_milhoes(v, 1),
            titulo="AUM por administrador",
        ),
        itens_legenda=[("AUM (US$ mi)", graficos.SERIES[0])],
    )


def _series(resumos: list[dict[str, Any]]) -> str:
    maiores = sorted(resumos, key=lambda resumo: resumo["aum"] or 0, reverse=True)[:GRAFICOS_NA_PAGINA]
    return colunas(*[cartao(resumo["nome"], resumo["grafico"]) for resumo in maiores])


def _nota_agrupamento(repetidos: list[str]) -> str:
    if not repetidos:
        return ""
    marcadores = ", ".join(f"<strong>{esc(marcador)}</strong>" for marcador in repetidos)
    return nota(
        f"Os administradores marcados com {marcadores} compartilham AUM e receita na origem; "
        "a soma da coluna não equivale ao AUM offshore da casa."
    )
