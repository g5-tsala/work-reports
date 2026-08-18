"""Aba: Resumo.

ROA por categoria de veículo e por faixa de PL do grupo econômico — as duas
leituras que a aba `resumo` da planilha entrega prontas.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, faixa_kpis, fonte, grafico, kpi, nota, num, secao, tabela


@pagina(
    identificador="resumo",
    titulo="Resumo",
    grupo="Visão Executiva",
    ordem=20,
    subtitulo="Onde está o AUM e quanto cada corte rende — por categoria de veículo e por "
    "faixa de patrimônio do grupo econômico.",
)
def render(ctx: Contexto) -> str:
    categoria = ctx.bloco("consolidado", "roa_categoria")
    grupo = ctx.bloco("consolidado", "roa_grupo")

    return "".join(
        [
            _kpis(ctx, categoria, grupo),
            secao(
                "Por categoria e faixa de PL",
                _tabela_faixas(categoria, "Categoria", "categoria", "roa-categoria"),
                fonte("resumo", ctx.rotulo_mes, "Receita anualizada."),
                _barras(categoria, "categoria"),
            ),
            secao(
                "Por grupo econômico e faixa de PL",
                _tabela_faixas(grupo, "Faixa", "faixa", "roa-grupo"),
                fonte("resumo", ctx.rotulo_mes, "Faixas excluem o grupo G5, isolado na própria linha."),
                _barras(grupo, "faixa"),
                nota(
                    "As faixas de grupo já excluem o grupo <strong>G5</strong> — os fundos de "
                    "alocação aparecem isolados na linha própria, e é isso que faz o total fechar "
                    "com a visão por categoria."
                ),
            ),
        ]
    )


def _kpis(ctx: Contexto, categoria: dict[str, Any], grupo: dict[str, Any]) -> str:
    total_categoria = categoria["total"]
    total_grupo = grupo["total"]
    zerados = sum(linha["qtd_zerados"] or 0 for linha in categoria["linhas"])

    return faixa_kpis(
        kpi("Veículos", formato.inteiro(total_categoria["qtd"]), detalhe=f"{formato.inteiro(zerados)} zerados fora da contagem"),
        kpi("Grupos econômicos", formato.inteiro(total_grupo["qtd"]), detalhe="distintos, onshore + offshore"),
        kpi("AUM", formato.bilhoes(total_categoria["aum"])),
        kpi("ROA médio", formato.percentual(total_categoria["roa"]), detalhe="receita anualizada ÷ AUM"),
    )


def _tabela_faixas(bloco: dict[str, Any], rotulo: str, campo: str, identificador: str) -> str:
    colunas = [
        Coluna(rotulo),
        Coluna("Qtd.", numerica=True),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("% AUM", numerica=True),
        Coluna("Receita anual. (R$)", numerica=True),
        Coluna("ROA (%)", numerica=True),
    ]
    linhas = [
        Linha(
            [
                registro[campo],
                num(formato.inteiro(registro["qtd"]), ordem=registro["qtd"]),
                num(formato.em_milhoes(registro["aum"]), ordem=registro["aum"]),
                num(formato.percentual(registro["pct_aum"]), ordem=registro["pct_aum"]),
                num(formato.numero(registro["receita_anualizada"], 0), ordem=registro["receita_anualizada"]),
                num(formato.percentual(registro["roa"]), ordem=registro["roa"]),
            ]
        )
        for registro in bloco["linhas"]
    ]
    total = bloco["total"]
    linhas.append(
        Linha(
            [
                "Total",
                num(formato.inteiro(total["qtd"])),
                num(formato.em_milhoes(total["aum"])),
                num(formato.percentual(total["pct_aum"])),
                num(formato.numero(total["receita_anualizada"], 0)),
                num(formato.percentual(total["roa"])),
            ],
            classe="total",
        )
    )
    return tabela(colunas, linhas, identificador=identificador)


def _barras(bloco: dict[str, Any], campo: str) -> str:
    itens = sorted(
        ((registro[campo], registro["aum"]) for registro in bloco["linhas"] if registro["aum"]),
        key=lambda item: item[1],
        reverse=True,
    )
    return grafico(
        graficos.barras_horizontais(
            itens,
            formatador=lambda v: formato.em_bilhoes(v, 2),
            titulo="AUM por faixa",
        ),
        itens_legenda=[("AUM (R$ bi)", graficos.SERIES[0])],
    )
