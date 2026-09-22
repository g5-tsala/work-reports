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
from .comum import alinhar_meses, grafico_aum_consolidado, grafico_receita_consolidada

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
    grupo="Visão Executiva",
    ordem=30,
    subtitulo="Evolução desde 2018. Pontos semestrais até 2025 e mensais em 2026 — "
    "o eixo é categórico, as distâncias não são proporcionais ao tempo.",
)
def render(ctx: Contexto) -> str:
    onshore = ctx.bloco("historico", "aum_receita", "onshore")
    offshore = ctx.bloco("historico", "aum_receita", "offshore")
    ano = ctx.mes_base[:4]

    return "".join(
        [
            secao("AUM consolidado", grafico_aum_consolidado(ctx, onshore, offshore, onshore["meses"])),
            secao(
                "Receita e ROA",
                grafico_receita_consolidada(ctx, onshore, offshore, onshore["meses"]),
                _grafico_roa(ctx, onshore, offshore),
            ),
            secao(
                f"Série onshore (R$) — {ano}",
                _tabela(ctx, onshore, LINHAS_ONSHORE, "serie-onshore"),
                fonte("aum_receita", ctx.rotulo_mes),
                nota(
                    "A mensalização normaliza a receita pelos dias úteis do período "
                    "(<code>competência ÷ dias úteis × 21</code>) e vale <strong>apenas no "
                    "onshore</strong>."
                ),
            ),
            secao(
                f"Série offshore (US$) — {ano}",
                _tabela(ctx, offshore, LINHAS_OFFSHORE, "serie-offshore"),
                fonte("aum_receita", ctx.rotulo_mes, "Offshore entra por competência, sem mensalizar."),
            ),
        ]
    )


def _grafico_roa(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    """Linha, não barra: ROA é razão, não volume — empilhá-lo somaria taxas."""
    meses = onshore["meses"]
    return grafico(
        graficos.linhas(
            ctx.rotulos(meses),
            [
                graficos.Serie("ROA onshore", ctx.serie(onshore, "roa_pct")),
                graficos.Serie("ROA offshore", alinhar_meses(ctx, offshore, "roa_pct", meses)),
            ],
            formatador=lambda v: formato.percentual(v),
            titulo="ROA onshore e offshore",
            rotular_pontos=True,
            rotulos_inclinados=True,
        ),
        itens_legenda=[("ROA onshore", graficos.SERIES[0]), ("ROA offshore", graficos.SERIES[1])],
        rodape=fonte("aum_receita", ctx.rotulo_mes),
    )


def _tabela(ctx: Contexto, bloco: dict[str, Any], especificacao, identificador: str) -> str:
    """Só o ano corrente, mês a mês.

    A série inteira vai de 2018 a hoje, mas os oito anos anteriores são pontos
    semestrais: numa tabela, misturá-los com os meses de 2026 põe lado a lado
    colunas que medem períodos diferentes e convida à subtração entre elas. O
    histórico longo fica nos gráficos, onde o eixo categórico avisa que as
    distâncias não são proporcionais ao tempo.
    """
    ano = ctx.mes_base[:4]
    recorte = [i for i, mes in enumerate(bloco["meses"]) if mes.startswith(ano)]
    meses = [bloco["meses"][i] for i in recorte]
    colunas = [Coluna("Métrica")] + [Coluna(rotulo, numerica=True) for rotulo in ctx.rotulos(meses)]

    linhas = []
    for chave, rotulo, formatador in especificacao:
        serie = ctx.serie(bloco, chave)
        if not serie:
            continue
        linhas.append(
            Linha(
                [rotulo]
                + [num(formatador(serie[i]) if i < len(serie) else "") for i in recorte]
            )
        )
    return tabela(colunas, linhas, identificador=identificador, ordenavel=False)
