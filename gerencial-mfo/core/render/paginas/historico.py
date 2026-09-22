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
            secao("AUM consolidado", _grafico_aum(ctx, onshore, offshore)),
            secao("Receita e ROA", _grafico_receita(ctx, onshore, offshore), _grafico_roa(ctx, onshore, offshore)),
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


def _grafico_aum(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    """Empilhado, não duas linhas: a pergunta aqui é o AUM da casa.

    Em linhas separadas o consolidado ficava implícito — o leitor tinha de
    somar de cabeça um traço de 40 bi com outro de 4 bi para chegar ao número
    que ele veio buscar. Empilhado, o topo da barra é o total e cada parcela
    traz o próprio valor escrito dentro.
    """
    meses = onshore["meses"]
    return grafico(
        graficos.barras(
            ctx.rotulos(meses),
            [
                graficos.Serie("Onshore", ctx.serie(onshore, "aum_rs")),
                graficos.Serie("Offshore (R$)", _alinhar(ctx, offshore, "aum_rs", meses)),
            ],
            formatador=lambda v: formato.em_bilhoes(v, 0),
            formatador_rotulo=lambda v: formato.em_bilhoes(v, 1),
            titulo="AUM onshore e offshore empilhados, em R$ bi",
            empilhado=True,
            rotular=True,
            rotulos_inclinados=True,
        ),
        itens_legenda=[("Onshore (R$ bi)", graficos.SERIES[0]), ("Offshore (R$ bi)", graficos.SERIES[1])],
        rodape=fonte("aum_receita", ctx.rotulo_mes, "Offshore convertido pelo câmbio de cada período."),
    )


def _grafico_receita(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    meses = onshore["meses"]
    return grafico(
        graficos.barras(
            ctx.rotulos(meses),
            [
                graficos.Serie("Onshore mensalizada", ctx.serie(onshore, "receita_mens_rs")),
                graficos.Serie("Offshore (R$)", _alinhar(ctx, offshore, "receita_rs", meses)),
            ],
            formatador=lambda v: formato.em_milhoes(v, 0),
            formatador_rotulo=lambda v: formato.em_milhoes(v, 1),
            titulo="Receita onshore e offshore empilhadas, em R$ mi",
            empilhado=True,
            rotular=True,
            rotulos_inclinados=True,
        ),
        itens_legenda=[
            ("Onshore (R$ mi)", graficos.SERIES[0]),
            ("Offshore (R$ mi)", graficos.SERIES[1]),
        ],
        rodape=fonte("aum_receita", ctx.rotulo_mes),
    )


def _grafico_roa(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    """Linha, não barra: ROA é razão, não volume — empilhá-lo somaria taxas."""
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
            rotular_pontos=True,
            rotulos_inclinados=True,
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
