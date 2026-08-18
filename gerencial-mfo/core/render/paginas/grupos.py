"""Aba: Grupos Econômicos.

Top 10 por AUM e por receita no mês, concentração do topo sobre o total, e a
base completa de grupos com filtro.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, faixa_kpis, fonte, grafico, kpi, nota, num, secao, tabela

RANK_G5 = "-"
RANK_SOMA = "SOMA"
RANK_TOTAL = "G5-TOTAL"
RANKS_AGREGADOS = (RANK_SOMA, RANK_TOTAL, "%", "% TOTAL")


@pagina(
    identificador="grupos",
    titulo="Grupos Econômicos",
    grupo="Carteira",
    ordem=20,
    subtitulo="Concentração da base: quem são os maiores grupos e quanto do AUM e da receita "
    "eles representam.",
)
def render(ctx: Contexto) -> str:
    por_aum = _ranking_do_mes(ctx, "aum")
    por_receita = _ranking_do_mes(ctx, "receita")

    return "".join(
        [
            _kpis(ctx, por_aum),
            secao(
                "Top 10 por AUM",
                _tabela_ranking(por_aum, "aum", "top-aum"),
                fonte("ar_grupos", ctx.rotulo_mes),
                _barras(por_aum, "aum"),
            ),
            secao(
                "Top 10 por receita",
                _tabela_ranking(por_receita, "receita", "top-receita"),
                fonte("ar_grupos", ctx.rotulo_mes),
            ),
            secao(
                "Base completa",
                _tabela_base(ctx),
                fonte("ar_grupos", ctx.rotulo_mes, "Receita já mensalizada na origem."),
                nota(
                    "O grupo <strong>G5</strong> agrega os fundos de alocação próprios e por isso "
                    "aparece fora do ranking, na linha marcada."
                ),
            ),
        ]
    )


def _ranking_do_mes(ctx: Contexto, criterio: str) -> list[dict[str, Any]]:
    for ranking in ctx.bloco("carteira", "grupos", "rankings"):
        if ranking["criterio"] != criterio:
            continue
        for mes in ranking["por_mes"]:
            if mes["mes"] == ctx.mes_base:
                return mes["linhas"]
    return []


def _kpis(ctx: Contexto, por_aum: list[dict[str, Any]]) -> str:
    indexado = {linha["rank"]: linha for linha in por_aum}
    soma = indexado.get(RANK_SOMA, {})
    total = indexado.get(RANK_TOTAL, {})
    g5 = indexado.get(RANK_G5, {})
    participacao = (soma.get("aum") or 0) / total["aum"] if total.get("aum") else None

    return faixa_kpis(
        kpi("Grupos econômicos", formato.inteiro(ctx.bloco("consolidado", "roa_grupo")["total"]["qtd"])),
        kpi("AUM do Top 10", formato.bilhoes(soma.get("aum")), detalhe="soma dos dez maiores"),
        kpi("Concentração", formato.percentual(participacao), detalhe="Top 10 sobre o AUM total"),
        kpi("Fdos Alocação (G5)", formato.bilhoes(g5.get("aum")), detalhe="fundos próprios, fora do ranking"),
    )


def _tabela_ranking(linhas_ranking: list[dict[str, Any]], criterio: str, identificador: str) -> str:
    colunas = [
        Coluna("Rank"),
        Coluna("Grupo"),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("Receita (R$)", numerica=True),
        Coluna("ROA anual. (%)", numerica=True),
    ]

    linhas = []
    for registro in linhas_ranking:
        aum, receita = registro["aum"], registro["receita"]
        roa = (receita * 12 / aum) if aum and receita is not None else None
        rank = registro["rank"]
        if rank in RANKS_AGREGADOS:
            classe = "total"
            rotulo = {RANK_SOMA: "Soma Top 10", RANK_TOTAL: "Total G5"}.get(rank, "% do total")
        elif rank == RANK_G5:
            classe, rotulo = "destaque", "Fdos Alocação"
        else:
            classe, rotulo = "", rank

        if rank in ("%", "% TOTAL"):
            linhas.append(
                Linha(
                    [rotulo, "", num(formato.percentual(aum)), num(formato.percentual(receita)), ""],
                    classe=classe,
                )
            )
            continue

        linhas.append(
            Linha(
                [
                    rotulo,
                    registro["grupo"] or formato.NAO_APLICAVEL,
                    num(formato.em_milhoes(aum), ordem=aum),
                    num(formato.numero(receita, 0), ordem=receita),
                    num(formato.percentual(roa), ordem=roa),
                ],
                classe=classe,
            )
        )
    return tabela(colunas, linhas, identificador=identificador, ordenavel=False)


def _barras(linhas_ranking: list[dict[str, Any]], criterio: str) -> str:
    itens = [
        (registro["grupo"], registro[criterio])
        for registro in linhas_ranking
        if registro["rank"] not in RANKS_AGREGADOS and registro["grupo"]
    ]
    return grafico(
        graficos.barras_horizontais(
            itens,
            formatador=lambda v: formato.em_bilhoes(v, 2),
            titulo="Top grupos por AUM",
        ),
        itens_legenda=[("AUM (R$ bi)", graficos.SERIES[0])],
    )


def _tabela_base(ctx: Contexto) -> str:
    base = ctx.bloco("carteira", "grupos", "serie")
    posicao = ctx.posicao(base, ctx.mes_base)
    anterior = ctx.posicao(base, ctx.mes_anterior)
    if posicao is None:
        return ""

    colunas = [
        Coluna("Grupo econômico"),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("Δ AUM M-1", numerica=True),
        Coluna("Receita mens. (R$)", numerica=True),
        Coluna("ROA anual. (%)", numerica=True),
    ]

    linhas = []
    for registro in base["linhas"]:
        aum = registro["aum"][posicao]
        receita = registro["receita"][posicao]
        if not aum and not receita:
            continue
        variacao = ctx.variacao(aum, registro["aum"][anterior] if anterior is not None else None)
        roa = (receita * 12 / aum) if aum and receita is not None else None
        linhas.append(
            Linha(
                [
                    registro["grupo"],
                    num(formato.em_milhoes(aum), ordem=aum),
                    num(formato.variacao(variacao), formato.classe_sinal(variacao), ordem=variacao),
                    num(formato.numero(receita, 0), ordem=receita),
                    num(formato.percentual(roa), ordem=roa),
                ]
            )
        )
    return tabela(colunas, linhas, identificador="grupos-base", filtravel=True)
