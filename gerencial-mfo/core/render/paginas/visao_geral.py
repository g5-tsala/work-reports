"""Aba: Visão Geral.

Os quatro indicadores principais na ordem fechada com o negócio — AUM, Run
Rate, Projeção Ano, ROA —, o split onshore/offshore e a evolução recente: AUM,
receita e run rate desde dezembro do ano anterior. A série longa fica no
Histórico, e o ranking de officers na aba Officers; daqui sai um link para cada.
"""

from __future__ import annotations

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    cartao,
    colunas,
    faixa_kpis,
    fonte,
    grafico,
    kpi,
    link_aba,
    num,
    secao,
    tabela,
)
from .comum import alinhar_meses, grafico_aum_consolidado, grafico_receita_consolidada

ORIGENS = (("Onshore", "onshore"), ("Offshore", "offshore"), ("Total", "total"))


@pagina(
    identificador="visao-geral",
    titulo="Visão Geral",
    grupo="Visão Executiva",
    ordem=10,
    subtitulo="Fechamento do mês: posição consolidada e a evolução desde dezembro.",
)
def render(ctx: Contexto) -> str:
    onshore = ctx.bloco("historico", "aum_receita", "onshore")
    offshore = ctx.bloco("historico", "aum_receita", "offshore")
    meses = _meses_desde_dezembro(ctx, onshore)
    desde = formato.mes_curto(meses[0]) if meses else ""

    return "".join(
        [
            _kpis(ctx),
            secao("Onshore e offshore", _split(ctx), fonte("resumo", ctx.rotulo_mes)),
            secao(
                f"AUM e receita desde {desde}",
                colunas(
                    cartao(
                        "AUM consolidado",
                        grafico_aum_consolidado(ctx, onshore, offshore, meses, inclinar=False, largura=600),
                    ),
                    cartao(
                        "Receita",
                        grafico_receita_consolidada(ctx, onshore, offshore, meses, inclinar=False, largura=600),
                    ),
                ),
                link_aba("historico", "Histórico completo desde 2018 em Histórico AUM × Receita"),
            ),
            secao(f"Run Rate desde {desde}", _run_rate(ctx, onshore, offshore, meses)),
            link_aba("officers", "Ranking por officer na aba Officers"),
        ]
    )


def _meses_desde_dezembro(ctx: Contexto, onshore) -> list[str]:
    """De dezembro do ano anterior ao mês-base: o ano corrente mais o ponto de partida.

    Dezembro entra porque é a base contra a qual o ano se mede — sem ele, janeiro
    não tem de onde ter vindo.
    """
    inicio = f"{int(ctx.mes_base[:4]) - 1}-12"
    return [mes for mes in onshore["meses"] if inicio <= mes <= ctx.mes_base]


def _kpis(ctx: Contexto) -> str:
    cartao = ctx.bloco("consolidado", "kpis_ceo")["cartoes"]["total"]
    consolidado = ctx.bloco("consolidado")
    projecao = consolidado["projecao_ano"]["total"]
    receita_ano = consolidado["receita_ano_competencia"]["total"]

    return faixa_kpis(
        kpi(
            "AUM",
            formato.bilhoes(consolidado["aum"]["total"]),
            delta=f"{formato.variacao(cartao['aum_var_pct'])} · {formato.com_sinal(cartao['aum_var_bi'], formato.numero, casas=2)} bi",
            classe_delta=formato.classe_sinal(cartao["aum_var_pct"]),
            referencia=f"vs. {formato.mes_curto(ctx.mes_anterior)}",
        ),
        kpi(
            "Run Rate",
            formato.milhoes(consolidado["run_rate"]["total"]),
            delta=f"{formato.variacao(cartao['run_rate_var_pct'])} · {formato.com_sinal(cartao['run_rate_var_mi'], formato.numero, casas=2)} mi",
            classe_delta=formato.classe_sinal(cartao["run_rate_var_pct"]),
            referencia=f"vs. {formato.mes_curto(ctx.mes_anterior)}",
            detalhe="receita mensalizada × 12",
        ),
        kpi(
            "Projeção Ano",
            formato.milhoes(projecao),
            detalhe=f"{formato.milhoes(receita_ano)} realizados até {formato.mes_curto(ctx.mes_base)}",
        ),
        kpi(
            "ROA",
            formato.percentual(consolidado["roa"]["total"]),
            detalhe="receita anualizada ÷ AUM",
        ),
    )


def _split(ctx: Contexto) -> str:
    consolidado = ctx.bloco("consolidado")
    cartoes = ctx.bloco("consolidado", "kpis_ceo")["cartoes"]

    colunas = [
        Coluna("Origem"),
        Coluna("AUM (R$ bi)", numerica=True),
        Coluna("Δ AUM M-1", numerica=True),
        Coluna("Receita mens. (R$ mi)", numerica=True),
        Coluna("Run Rate (R$ mi)", numerica=True),
        Coluna("Projeção ano (R$ mi)", numerica=True),
        Coluna("ROA (%)", numerica=True),
    ]

    linhas = []
    for rotulo, chave in ORIGENS:
        variacao = cartoes[chave]["aum_var_pct"]
        linhas.append(
            Linha(
                [
                    rotulo,
                    num(formato.em_bilhoes(consolidado["aum"][chave])),
                    num(formato.variacao(variacao), formato.classe_sinal(variacao)),
                    num(formato.em_milhoes(consolidado["receita_mens"][chave])),
                    num(formato.em_milhoes(consolidado["run_rate"][chave])),
                    num(formato.em_milhoes(consolidado["projecao_ano"][chave])),
                    num(formato.percentual(consolidado["roa"][chave])),
                ],
                classe="total" if chave == "total" else "",
            )
        )
    return tabela(colunas, linhas, ordenavel=False, rolagem=False)


def _run_rate(ctx: Contexto, onshore, offshore, meses: list[str]) -> str:
    """Run rate de cada mês: receita mensalizada do mês × 12, onshore + offshore.

    É a conta do KPI (`resumo!K7:K9`) aplicada a cada mês da série de
    `aum_receita` — o offshore já vem em R$ ao câmbio daquele mês. No mês-base
    fecha com o cartão de Run Rate acima.
    """
    receita_on = alinhar_meses(ctx, onshore, "receita_mens_rs", meses)
    receita_off = alinhar_meses(ctx, offshore, "receita_rs", meses)
    run_rate = [
        ((a or 0.0) + (b or 0.0)) * 12 if a is not None or b is not None else None
        for a, b in zip(receita_on, receita_off)
    ]
    return grafico(
        graficos.linhas(
            ctx.rotulos(meses),
            [graficos.Serie("Run Rate", run_rate, cor=graficos.SERIES[0])],
            formatador=lambda v: formato.em_milhoes(v, 1),
            titulo="Run Rate mês a mês, em R$ mi",
            rotular_pontos=True,
        ),
        itens_legenda=[("Run Rate (R$ mi)", graficos.SERIES[0])],
        rodape=fonte(
            "aum_receita",
            ctx.rotulo_mes,
            "Receita mensalizada do mês × 12; offshore ao câmbio de cada mês.",
        ),
    )
