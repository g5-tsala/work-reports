"""Aba: Captação por Portfólio.

IN, OUT e NET por portfólio com a taxa de gestão contratada — é o que permite
estimar a receita incremental sem esperar o fechamento seguinte.
"""

from __future__ import annotations

from typing import Any

from .. import formato
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, faixa_kpis, fonte, kpi, nota, num, secao, tabela


@pagina(
    identificador="captacao-portfolios",
    titulo="Captação › Portfólios",
    grupo="Captação",
    ordem=30,
    subtitulo="Movimentação por portfólio no ano, com a taxa contratada e a receita "
    "incremental estimada.",
)
def render(ctx: Contexto) -> str:
    onshore = ctx.bloco("captacao", "portfolios", "onshore")
    offshore = ctx.bloco("captacao", "portfolios", "offshore")

    return "".join(
        [
            _kpis(onshore, offshore),
            secao(
                "Onshore (R$)",
                _tabela_onshore(onshore),
                fonte("io_portfolios", ctx.rotulo_mes, "Acumulado do ano, base de cliente."),
                nota(
                    "<strong>Receita aproximada</strong> = NET × taxa contratada (% a.a.). É uma "
                    "estimativa de receita incremental anualizada, não receita realizada."
                ),
            ),
            secao(
                "Offshore",
                _tabela_offshore(offshore),
                fonte(
                    "io_portfolios",
                    ctx.rotulo_mes,
                    "Valores em US$ e a conversão em R$ pelo câmbio do mês de cada movimentação.",
                ),
            ),
        ]
    )


def _kpis(onshore: list[dict[str, Any]], offshore: list[dict[str, Any]]) -> str:
    net_on = sum(registro["net"] or 0 for registro in onshore)
    receita_on = sum(registro["receita_aprox"] or 0 for registro in onshore)
    net_off = sum(registro["net"] or 0 for registro in offshore)
    receita_off = sum(registro["receita_aprox"] or 0 for registro in offshore)

    return faixa_kpis(
        kpi("Portfólios com movimento", formato.inteiro(len(onshore) + len(offshore))),
        kpi("NET onshore no ano", formato.milhoes(net_on), classe_delta=formato.classe_sinal(net_on)),
        kpi("NET offshore no ano (R$)", formato.milhoes(net_off), classe_delta=formato.classe_sinal(net_off)),
        kpi(
            "Receita incremental",
            formato.milhoes(receita_on + receita_off),
            detalhe="estimada, R$/ano",
        ),
    )


def _tabela_onshore(registros: list[dict[str, Any]]) -> str:
    colunas = [
        Coluna("Portfólio"),
        Coluna("Officer"),
        Coluna("Tipo"),
        Coluna("Taxa (% a.a.)", numerica=True),
        Coluna("IN (R$)", numerica=True),
        Coluna("OUT (R$)", numerica=True),
        Coluna("NET (R$)", numerica=True),
        Coluna("Receita aprox. (R$/ano)", numerica=True),
    ]
    linhas = [
        Linha(
            [
                registro["portfolio"],
                registro["officer"] or formato.NAO_APLICAVEL,
                registro["tipo"] or formato.NAO_APLICAVEL,
                num(formato.percentual(registro["taxa"]), ordem=registro["taxa"]),
                num(formato.numero(registro["in"], 0), ordem=registro["in"]),
                num(formato.numero(registro["out"], 0), ordem=registro["out"]),
                num(
                    formato.numero(registro["net"], 0),
                    formato.classe_sinal(registro["net"]),
                    ordem=registro["net"],
                ),
                num(
                    formato.numero(registro["receita_aprox"], 0),
                    formato.classe_sinal(registro["receita_aprox"]),
                    ordem=registro["receita_aprox"],
                ),
            ]
        )
        for registro in registros
    ]
    linhas.append(_total(registros, ("in", "out", "net", "receita_aprox"), 4, len(colunas)))
    return tabela(colunas, linhas, identificador="captacao-portf-on", filtravel=True)


def _tabela_offshore(registros: list[dict[str, Any]]) -> str:
    colunas = [
        Coluna("Portfólio"),
        Coluna("Officer"),
        Coluna("Taxa (% a.a.)", numerica=True),
        Coluna("IN (US$)", numerica=True),
        Coluna("OUT (US$)", numerica=True),
        Coluna("NET (US$)", numerica=True),
        Coluna("NET (R$)", numerica=True),
        Coluna("Receita aprox. (R$/ano)", numerica=True),
    ]
    linhas = [
        Linha(
            [
                registro["portfolio"],
                registro["officer"] or formato.NAO_APLICAVEL,
                num(formato.percentual(registro["taxa"]), ordem=registro["taxa"]),
                num(formato.numero(registro["in_usd"], 0), ordem=registro["in_usd"]),
                num(formato.numero(registro["out_usd"], 0), ordem=registro["out_usd"]),
                num(
                    formato.numero(registro["net_usd"], 0),
                    formato.classe_sinal(registro["net_usd"]),
                    ordem=registro["net_usd"],
                ),
                num(
                    formato.numero(registro["net"], 0),
                    formato.classe_sinal(registro["net"]),
                    ordem=registro["net"],
                ),
                num(formato.numero(registro["receita_aprox"], 0), ordem=registro["receita_aprox"]),
            ]
        )
        for registro in registros
    ]
    linhas.append(_total(registros, ("in_usd", "out_usd", "net_usd", "net", "receita_aprox"), 3, len(colunas)))
    return tabela(colunas, linhas, identificador="captacao-portf-off", filtravel=True)


def _total(registros: list[dict[str, Any]], campos: tuple[str, ...], primeira_numerica: int, total_colunas: int) -> Linha:
    celulas: list[Any] = ["Total"] + [""] * (primeira_numerica - 1)
    for campo in campos:
        soma = sum(registro[campo] or 0 for registro in registros)
        celulas.append(num(formato.numero(soma, 0), formato.classe_sinal(soma)))
    celulas.extend([""] * (total_colunas - len(celulas)))
    return Linha(celulas, classe="total")
