"""Aba: Portfólios Offshore.

Mesma estrutura da aba onshore, mas **em US$** — a moeda vem declarada no
cabeçalho de cada coluna e no aviso do topo. A conversão para R$ é do
consolidado, não desta página.
"""

from __future__ import annotations

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import aviso, colunas, faixa_kpis, fonte, grafico, kpi, secao
from .comum import composicao_por_dimensao, tabela_portfolios


@pagina(
    identificador="portfolios-offshore",
    titulo="Portfólios Offshore",
    grupo="Carteira",
    ordem=50,
    subtitulo="Base offshore: AUM e receita do mês por portfólio, com todas as dimensões.",
)
def render(ctx: Contexto) -> str:
    base = ctx.bloco("carteira", "portfolios", "offshore")
    posicao = ctx.posicao(base, ctx.mes_base)
    if posicao is None:
        return ""

    return "".join(
        [
            aviso(
                f"Todos os valores desta página estão em <strong>US$</strong>. "
                f"Câmbio do mês: US$ 1 = R$ {formato.numero(ctx.dolar, 4)}."
            ),
            _kpis(ctx, base, posicao),
            secao(
                "Composição do AUM",
                colunas(
                    _barras(base, "adm", posicao, "Administrador"),
                    _barras(base, "regiao", posicao, "Região"),
                ),
                fonte("ar_offshore", ctx.rotulo_mes),
            ),
            secao(
                "Portfólios",
                tabela_portfolios(ctx, base, "portfolios-offshore"),
                fonte("ar_offshore", ctx.rotulo_mes, "Receita do mês, sem mensalizar."),
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
        kpi("AUM offshore", formato.milhoes(aum, moeda="US$")),
        kpi("Em reais", formato.bilhoes(aum * ctx.dolar if aum else None), detalhe="ao câmbio do mês"),
        kpi(
            "ROA anualizado",
            formato.percentual(receita * 12 / aum if aum and receita else None),
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
                    formatador=lambda v: formato.em_milhoes(v, 1),
                    titulo=f"AUM por {titulo.lower()}",
                    largura=560,
                    largura_rotulo=200,
                ),
                itens_legenda=[("AUM (US$ mi)", graficos.SERIES[0])],
            ),
        ]
    )
