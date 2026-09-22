"""Aba: Portfólios Onshore.

Base de posição em R$, uma linha por portfólio com todas as dimensões. A
composição de AUM e receita por tipo de veículo e por segmento abre a página;
a tabela cheia fica abaixo, com filtro.
"""

from __future__ import annotations

from .. import formato
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import faixa_kpis, fonte, kpi, secao
from .comum import par_composicao, tabela_portfolios

#: Escala e formatador de cada gráfico do par: AUM e receita.
ESCALAS = (
    ("R$ bi", lambda v: formato.em_bilhoes(v, 2)),
    ("R$ mil", lambda v: formato.numero(v / 1e3, 0)),
)


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
                "Composição de AUM e Receita",
                par_composicao(base, "tipo", posicao, "Tipo de veículo", ESCALAS),
                par_composicao(base, "segmento", posicao, "Segmento", ESCALAS),
                fonte("ar_onshore", ctx.rotulo_mes, "Receita do mês por competência."),
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
        kpi("Portfólios ativos", formato.inteiro(len(ativos))),
        kpi("AUM onshore", formato.bilhoes(aum)),
        kpi("Receita do mês (competência)", formato.milhoes(receita)),
        kpi("ROA anualizado", formato.percentual(receita * 12 / aum if aum and receita else None)),
    )

