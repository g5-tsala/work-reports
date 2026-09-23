"""Aba: Portfólios Offshore.

Mesma estrutura da aba onshore, mas **em US$** — a moeda vem declarada no
card, no título de cada gráfico e no cabeçalho de cada coluna. A conversão para R$ é do
consolidado, não desta página.
"""

from __future__ import annotations

from .. import formato
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import faixa_kpis, fonte, kpi, secao
from .comum import par_composicao, tabela_portfolios

#: Escala e formatador de cada gráfico do par: AUM e receita, em US$.
ESCALAS = (
    ("US$ mi", lambda v: formato.em_milhoes(v, 1)),
    ("US$ mil", lambda v: formato.numero(v / 1e3, 0)),
)


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
            _kpis(ctx, base, posicao),
            secao(
                "Composição de AUM e Receita",
                par_composicao(base, "tipo", posicao, "Tipo de veículo", ESCALAS),
                fonte("ar_offshore", ctx.rotulo_mes),
            ),
            secao(
                "Portfólios",
                tabela_portfolios(ctx, base, "portfolios-offshore"),
                fonte("ar_offshore", ctx.rotulo_mes),
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
        kpi("Portfólios ativos", formato.inteiro(len(ativos))),
        kpi("AUM offshore", formato.milhoes(aum, moeda="US$")),
        kpi("Receita do mês", formato.milhoes(receita, moeda="US$")),
    )

