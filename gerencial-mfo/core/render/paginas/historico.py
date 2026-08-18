"""Aba: Histórico AUM × Receita.

Série longa desde 2018. O eixo **não é uniforme** — pontos semestrais até
2025-12 e mensais em 2026 — então é tratado como categórico ordenado. Plotar
como escala temporal comprimiria oito anos contra sete meses.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, fonte, grafico, nota, num, secao, tabela

#: Linhas da aba que valem uma tabela; o resto da série vive no JSON.
LINHAS_ONSHORE = (
    ("aum_rs", "AUM (R$ bi)", formato.em_bilhoes),
    ("in_out", "IN/OUT (R$ mi)", formato.em_milhoes),
    ("rendimentos", "Rendimentos (R$ mi)", formato.em_milhoes),
    ("receita_rs", "Receita competência (R$ mi)", formato.em_milhoes),
    ("receita_mens_rs", "Receita mensalizada (R$ mi)", formato.em_milhoes),
    ("roa_pct", "ROA (%)", formato.percentual),
)
LINHAS_OFFSHORE = (
    ("aum_usd", "AUM (US$ bi)", formato.em_bilhoes),
    ("aum_rs", "AUM (R$ bi)", formato.em_bilhoes),
    ("in_out", "IN/OUT (US$ mi)", formato.em_milhoes),
    ("receita_usd", "Receita (US$ mi)", formato.em_milhoes),
    ("receita_rs", "Receita (R$ mi)", formato.em_milhoes),
    ("roa_pct", "ROA (%)", formato.percentual),
)


@pagina(
    identificador="historico",
    titulo="Histórico AUM × Receita",
    grupo="Performance",
    ordem=10,
    subtitulo="Evolução desde 2018. Pontos semestrais até 2025 e mensais em 2026 — "
    "o eixo é categórico, as distâncias não são proporcionais ao tempo.",
)
def render(ctx: Contexto) -> str:
    onshore = ctx.bloco("historico", "aum_receita", "onshore")
    offshore = ctx.bloco("historico", "aum_receita", "offshore")

    return "".join(
        [
            secao("AUM consolidado", _grafico_aum(ctx, onshore, offshore)),
            secao("Receita e ROA", _grafico_receita(ctx, onshore, offshore), _grafico_roa(ctx, onshore, offshore)),
            secao(
                "Série onshore (R$)",
                _tabela(ctx, onshore, LINHAS_ONSHORE, "serie-onshore"),
                fonte("aum_receita", ctx.rotulo_mes),
                nota(
                    "A mensalização normaliza a receita pelos dias úteis do período "
                    "(<code>competência ÷ dias úteis × 21</code>) e vale <strong>apenas no "
                    "onshore</strong>."
                ),
            ),
            secao(
                "Série offshore (US$)",
                _tabela(ctx, offshore, LINHAS_OFFSHORE, "serie-offshore"),
                fonte("aum_receita", ctx.rotulo_mes, "Offshore entra por competência, sem mensalizar."),
            ),
        ]
    )


def _grafico_aum(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    meses = onshore["meses"]
    return grafico(
        graficos.linhas(
            ctx.rotulos(meses),
            [
                graficos.Serie("Onshore", ctx.serie(onshore, "aum_rs")),
                graficos.Serie("Offshore (R$)", _alinhar(ctx, offshore, "aum_rs", meses)),
            ],
            formatador=lambda v: formato.em_bilhoes(v, 0),
            titulo="AUM onshore e offshore, em R$ bi",
        ),
        itens_legenda=[("Onshore (R$ bi)", graficos.SERIES[0]), ("Offshore (R$ bi)", graficos.SERIES[1])],
        rodape=fonte("aum_receita", ctx.rotulo_mes, "Offshore convertido pelo câmbio de cada período."),
    )


def _grafico_receita(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    meses = onshore["meses"]
    return grafico(
        graficos.linhas(
            ctx.rotulos(meses),
            [
                graficos.Serie("Onshore mensalizada", ctx.serie(onshore, "receita_mens_rs")),
                graficos.Serie("Offshore (R$)", _alinhar(ctx, offshore, "receita_rs", meses)),
            ],
            formatador=lambda v: formato.em_milhoes(v, 1),
            titulo="Receita mensalizada, em R$ mi",
        ),
        itens_legenda=[
            ("Onshore mensalizada (R$ mi)", graficos.SERIES[0]),
            ("Offshore por competência (R$ mi)", graficos.SERIES[1]),
        ],
        rodape=fonte("aum_receita", ctx.rotulo_mes),
    )


def _grafico_roa(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    meses = onshore["meses"]
    return grafico(
        graficos.linhas(
            ctx.rotulos(meses),
            [
                graficos.Serie("ROA onshore", ctx.serie(onshore, "roa_pct")),
                graficos.Serie("ROA offshore", _alinhar(ctx, offshore, "roa_pct", meses)),
            ],
            formatador=lambda v: formato.percentual(v),
            titulo="ROA onshore e offshore",
            altura=240,
        ),
        itens_legenda=[("ROA onshore", graficos.SERIES[0]), ("ROA offshore", graficos.SERIES[1])],
        rodape=fonte("aum_receita", ctx.rotulo_mes),
    )


def _alinhar(ctx: Contexto, bloco: dict[str, Any], chave: str, meses: list[str]) -> list[float | None]:
    """Reposiciona uma série na grade de meses da outra origem.

    Onshore e offshore têm cabeçalhos de data próprios e um ponto divergente em
    2023 — casar por mês, nunca por índice de coluna.
    """
    serie = ctx.serie(bloco, chave)
    return [
        serie[bloco["meses"].index(mes)] if mes in bloco["meses"] and bloco["meses"].index(mes) < len(serie) else None
        for mes in meses
    ]


def _tabela(ctx: Contexto, bloco: dict[str, Any], especificacao, identificador: str) -> str:
    meses = bloco["meses"]
    colunas = [Coluna("Métrica")] + [Coluna(rotulo, numerica=True) for rotulo in ctx.rotulos(meses)]

    linhas = []
    for chave, rotulo, formatador in especificacao:
        serie = ctx.serie(bloco, chave)
        if not serie:
            continue
        linhas.append(
            Linha([rotulo] + [num(formatador(valor)) for valor in serie])
        )
    return tabela(colunas, linhas, identificador=identificador, ordenavel=False)
