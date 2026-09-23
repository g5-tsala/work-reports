"""Serie longa — aba `aum_receita`.

A grade temporal nao e uniforme: colunas C→R sao pontos semestrais de 2018-06 a
2025-12 e S→AD sao mensais de 2026. Quem plota trata como eixo categorico
ordenado (`docs/modelo-de-dados.md` §4); aqui so preservamos a ordem e o rotulo.
"""

from __future__ import annotations

from typing import Any

from core.planilha import mes as ler_mes
from core.planilha import numero

from .comum import linhas_rotuladas

ABA_AUM_RECEITA = "aum_receita"

COL_ROTULO = 2  # B
COL_SERIE_INICIAL = 3  # C
COL_SERIE_FINAL = 30  # AD

#: `aum_receita` — bloco onshore. Linha 4 traz os dias uteis de cada periodo,
#: que e o que sustenta a mensalizacao da receita.
ON_LIN_DIAS_UTEIS, ON_LIN_DATAS = 4, 5
ON_LIN_INICIAL, ON_LIN_FINAL = 6, 35

#: `aum_receita` — bloco offshore. Linha 38 traz o cambio de cada periodo.
OFF_LIN_CAMBIO, OFF_LIN_DATAS = 38, 39
OFF_LIN_INICIAL, OFF_LIN_FINAL = 40, 50


def extrair(ctx) -> dict[str, Any]:
    return {
        "aum_receita": {
            "onshore": _bloco_aum_receita(
                ctx,
                lin_datas=ON_LIN_DATAS,
                lin_ini=ON_LIN_INICIAL,
                lin_fim=ON_LIN_FINAL,
                lin_extra=ON_LIN_DIAS_UTEIS,
                nome_extra="dias_uteis",
            ),
            "offshore": _bloco_aum_receita(
                ctx,
                lin_datas=OFF_LIN_DATAS,
                lin_ini=OFF_LIN_INICIAL,
                lin_fim=OFF_LIN_FINAL,
                lin_extra=OFF_LIN_CAMBIO,
                nome_extra="dolar",
            ),
        },
    }


def _bloco_aum_receita(
    ctx,
    *,
    lin_datas: int,
    lin_ini: int,
    lin_fim: int,
    lin_extra: int,
    nome_extra: str,
) -> dict[str, Any]:
    pl = ctx.pl
    meses = [ler_mes(v) for v in pl.linha(ABA_AUM_RECEITA, lin_datas, COL_SERIE_INICIAL, COL_SERIE_FINAL)]
    extra = [numero(v) for v in pl.linha(ABA_AUM_RECEITA, lin_extra, COL_SERIE_INICIAL, COL_SERIE_FINAL)]
    linhas = _linhas(pl, ABA_AUM_RECEITA, lin_ini, lin_fim)

    series = [extra] + [linha["valores"] for linha in linhas]
    meses_ok, series_ok = ctx.cortar(meses, *series)
    for linha, valores in zip(linhas, series_ok[1:]):
        linha["valores"] = valores

    return {"meses": meses_ok, nome_extra: series_ok[0], "linhas": linhas}


def _linhas(pl, aba: str, lin_ini: int, lin_fim: int) -> list[dict[str, Any]]:
    """Linhas rotuladas nas colunas de serie da aba.

    O rotulo vem da planilha, nao de uma lista fixa no codigo: se a geradora
    ganhar uma quebra nova, ela aparece no JSON sem mudanca aqui.
    """
    return linhas_rotuladas(
        pl,
        aba,
        lin_ini,
        lin_fim,
        col_rotulo=COL_ROTULO,
        col_ini=COL_SERIE_INICIAL,
        col_fim=COL_SERIE_FINAL,
    )
