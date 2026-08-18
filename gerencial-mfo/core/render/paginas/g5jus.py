"""Aba: G5 JUS.

AUM e receita dos FIDCs de direitos creditórios judiciais. Base pequena e
estável — a página é uma tabela e uma série, sem drill-down.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, faixa_kpis, fonte, grafico, kpi, num, secao, tabela


@pagina(
    identificador="g5jus",
    titulo="G5 JUS",
    grupo="Outros",
    ordem=10,
    subtitulo="Fundos de direitos creditórios judiciais: AUM e receita por veículo.",
)
def render(ctx: Contexto) -> str:
    bloco = ctx.bloco("estrutura", "g5jus")
    posicao = ctx.posicao(bloco, ctx.mes_base)
    if posicao is None:
        return ""

    return "".join(
        [
            _kpis(ctx, bloco, posicao),
            secao("Evolução", _grafico(ctx, bloco)),
            secao(
                "Veículos",
                _tabela(ctx, bloco, posicao),
                fonte("G5JUS", ctx.rotulo_mes),
            ),
        ]
    )


def _kpis(ctx: Contexto, bloco: dict[str, Any], posicao: int) -> str:
    total = bloco["total"] or {"aum": [], "receita": []}
    aum = total["aum"][posicao] if posicao < len(total["aum"]) else None
    receita = total["receita"][posicao] if posicao < len(total["receita"]) else None
    anterior = ctx.posicao(bloco, ctx.mes_anterior)
    aum_anterior = total["aum"][anterior] if anterior is not None and anterior < len(total["aum"]) else None
    variacao = ctx.variacao(aum, aum_anterior)

    return faixa_kpis(
        kpi("Veículos", formato.inteiro(len(bloco["linhas"]))),
        kpi(
            "AUM",
            formato.milhoes(aum),
            delta=formato.variacao(variacao),
            classe_delta=formato.classe_sinal(variacao),
            detalhe=f"vs. {formato.mes_curto(ctx.mes_anterior)}",
        ),
        kpi("Receita do mês", formato.numero(receita, 0), detalhe="R$"),
        kpi("ROA anualizado", formato.percentual(receita * 12 / aum if aum and receita else None)),
    )


def _grafico(ctx: Contexto, bloco: dict[str, Any]) -> str:
    total = bloco["total"] or {"aum": [], "receita": []}
    svg = graficos.combo(
        ctx.rotulos(bloco["meses"]),
        [graficos.Serie("AUM", total["aum"])],
        graficos.Serie("Receita", total["receita"], cor=graficos.SERIES[1]),
        formatador_barra=lambda v: formato.em_milhoes(v, 0),
        formatador_linha=lambda v: formato.numero(v, 0),
        titulo="AUM e receita do G5 JUS",
        empilhado=False,
        eixo_proprio=True,
        rotular_ultimo=True,
    )
    return grafico(
        svg,
        itens_legenda=[("AUM (R$ mi, barras)", graficos.SERIES[0]), ("Receita (R$, linha)", graficos.SERIES[1])],
        rodape=fonte("G5JUS", ctx.rotulo_mes),
    )


def _tabela(ctx: Contexto, bloco: dict[str, Any], posicao: int) -> str:
    colunas = [
        Coluna("Portfólio"),
        Coluna("Tipo"),
        Coluna("Administrador"),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("Receita (R$)", numerica=True),
        Coluna("ROA anual. (%)", numerica=True),
    ]

    linhas = []
    for registro in bloco["linhas"]:
        aum = registro["aum"][posicao] if posicao < len(registro["aum"]) else None
        receita = registro["receita"][posicao] if posicao < len(registro["receita"]) else None
        linhas.append(
            Linha(
                [
                    registro["portfolio"],
                    registro["tipo"] or formato.NAO_APLICAVEL,
                    registro["adm"] or formato.NAO_APLICAVEL,
                    num(formato.em_milhoes(aum), ordem=aum),
                    num(formato.numero(receita, 0), ordem=receita),
                    num(formato.percentual(receita * 12 / aum if aum and receita else None)),
                ]
            )
        )

    total = bloco["total"]
    if total:
        aum = total["aum"][posicao] if posicao < len(total["aum"]) else None
        receita = total["receita"][posicao] if posicao < len(total["receita"]) else None
        linhas.append(
            Linha(
                [
                    "Total",
                    "",
                    "",
                    num(formato.em_milhoes(aum)),
                    num(formato.numero(receita, 0)),
                    num(formato.percentual(receita * 12 / aum if aum and receita else None)),
                ],
                classe="total",
            )
        )
    return tabela(colunas, linhas, identificador="g5jus")
