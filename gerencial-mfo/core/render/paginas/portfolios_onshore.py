"""Aba: Portfólios Onshore.

Base de posição em R$, uma linha por portfólio com todas as dimensões. A
composição por tipo e por administrador abre a página; a tabela cheia fica
abaixo, com filtro.
"""

from __future__ import annotations

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import colunas, faixa_kpis, fonte, grafico, kpi, secao
from .comum import composicao_por_dimensao, tabela_portfolios


@pagina(
    identificador="portfolios-onshore",
    titulo="Portfólios Onshore",
    grupo="Carteira",
    ordem=40,
    subtitulo="Base onshore em R$: AUM e receita do mês por portfólio, com todas as dimensões.",
)
def render(ctx: Contexto) -> str:
    base = ctx.bloco("carteira", "portfolios", "onshore")
    posicao = ctx.posicao(base, ctx.mes_base)
    if posicao is None:
        return ""

    return "".join(
        [
            _kpis(ctx, base, posicao),
            secao(
                "Composição do AUM",
                colunas(
                    _barras(base, "tipo", posicao, "Tipo de veículo"),
                    _barras(base, "adm", posicao, "Administrador"),
                ),
                fonte("ar_onshore", ctx.rotulo_mes),
            ),
            secao(
                "Portfólios",
                tabela_portfolios(ctx, base, "portfolios-onshore"),
                fonte("ar_onshore", ctx.rotulo_mes, "Receita do mês por competência."),
            ),
        ]
    )


def _kpis(ctx: Contexto, base, posicao: int) -> str:
    ativos = [
        linha
        for linha in base["linhas"]
        if (linha["aum"][posicao] or 0) > 0 or (linha["receita"][posicao] or 0) > 0
    ]
    aum = base["total"]["aum"][posicao]
    receita = base["total"]["receita"][posicao]
    return faixa_kpis(
        kpi("Portfólios ativos", formato.inteiro(len(ativos)), detalhe=f"de {len(base['linhas'])} na base"),
        kpi("AUM onshore", formato.bilhoes(aum)),
        kpi("Receita do mês", formato.milhoes(receita), detalhe="competência"),
        kpi(
            "ROA anualizado",
            formato.percentual(receita * 12 / aum if aum and receita else None),
            detalhe="sem mensalizar",
        ),
    )


def _barras(base, campo: str, posicao: int, titulo: str) -> str:
    itens = composicao_por_dimensao(base, campo, posicao)
    return "".join(
        [
            f'<h3 class="g5-cartao-titulo">{titulo}</h3>',
            grafico(
                graficos.barras_horizontais(
                    itens,
                    formatador=lambda v: formato.em_bilhoes(v, 2),
                    titulo=f"AUM por {titulo.lower()}",
                    largura=560,
                    largura_rotulo=200,
                ),
                itens_legenda=[("AUM (R$ bi)", graficos.SERIES[0])],
            ),
        ]
    )
