"""Estrutura — administradores (`ar_adm_on` / `ar_adm_off`) e `G5JUS`.

Nas duas abas de administrador cada instituicao ocupa um bloco proprio, com o
nome numa linha, `Data` na seguinte e as metricas abaixo. A quantidade de
linhas por bloco difere entre onshore e offshore, entao os blocos sao
descobertos por varredura em vez de contados por passo fixo.
"""

from __future__ import annotations

from typing import Any

from core.planilha import mes as ler_mes
from core.planilha import numero, texto

from .comum import linhas_rotuladas

ABA_ADM_ON = "ar_adm_on"
ABA_ADM_OFF = "ar_adm_off"
ABA_G5JUS = "G5JUS"

COL_ROTULO = 2  # B
COL_SERIE_INICIAL = 3  # C
LIN_INICIAL_BLOCOS = 3
ROTULO_DATA = "Data"

#: `G5JUS` — FIDCs do G5 JUS. Dimensoes nas colunas B..E e pares AUM/Receita a
#: partir de F, com a data repetida no par (linha 3) e o rotulo na linha 4.
JUS_LIN_DATAS, JUS_LIN_CABECALHOS = 3, 4
JUS_LIN_INICIAL, JUS_LIN_FINAL = 5, 8
JUS_LIN_TOTAL = 10
JUS_DIMENSOES = {"portfolio": 2, "tipo": 3, "adm": 4, "grupo": 5}
JUS_COL_INICIAL = 6  # F
ROTULO_TOTAL = "TOTAL"


def extrair(ctx) -> dict[str, Any]:
    return {
        "administradores": {
            "onshore": _administradores(ctx, ABA_ADM_ON, "R$"),
            "offshore": _administradores(ctx, ABA_ADM_OFF, "US$"),
        },
        "g5jus": _g5jus(ctx),
    }


def _administradores(ctx, aba: str, moeda: str) -> dict[str, Any]:
    pl = ctx.pl
    ws = pl.aba(aba)
    col_final = ws.max_column
    cabecalhos = _linhas_de_bloco(ws)

    blocos = []
    for posicao, inicio in enumerate(cabecalhos):
        fim = (cabecalhos[posicao + 1] - 1) if posicao + 1 < len(cabecalhos) else ws.max_row
        nome = texto(ws.cell(inicio, COL_ROTULO).value)
        meses = [ler_mes(v) for v in pl.linha(aba, inicio + 1, COL_SERIE_INICIAL, col_final)]
        dias_uteis = [numero(v) for v in pl.linha(aba, inicio, COL_SERIE_INICIAL, col_final)]

        linhas = linhas_rotuladas(
            pl,
            aba,
            inicio + 2,
            fim,
            col_rotulo=COL_ROTULO,
            col_ini=COL_SERIE_INICIAL,
            col_fim=col_final,
        )

        series = [dias_uteis] + [item["valores"] for item in linhas]
        meses_ok, series_ok = ctx.cortar(meses, *series)
        for item, valores in zip(linhas, series_ok[1:]):
            item["valores"] = valores

        blocos.append(
            {
                "administrador": nome,
                # Marcador acima do nome do bloco. Quando dois administradores
                # compartilham o mesmo (`GVA/Daycoval`), a geradora repete o AUM
                # e a receita nos dois — só os custos diferem.
                "agrupamento": texto(ws.cell(inicio - 1, COL_ROTULO).value) if inicio > 1 else None,
                "meses": meses_ok,
                "dias_uteis": series_ok[0],
                "linhas": linhas,
            }
        )

    return {"moeda": moeda, "blocos": blocos}


def _linhas_de_bloco(ws) -> list[int]:
    """Linhas em que comeca um bloco de administrador: nome seguido de `Data`."""
    return [
        linha
        for linha in range(LIN_INICIAL_BLOCOS, ws.max_row)
        if texto(ws.cell(linha, COL_ROTULO).value) is not None
        and texto(ws.cell(linha + 1, COL_ROTULO).value) == ROTULO_DATA
    ]


def _g5jus(ctx) -> dict[str, Any]:
    pl = ctx.pl
    ws = pl.aba(ABA_G5JUS)
    col_final = ws.max_column
    datas = pl.linha(ABA_G5JUS, JUS_LIN_DATAS, JUS_COL_INICIAL, col_final)
    cabecalhos = [texto(v) for v in pl.linha(ABA_G5JUS, JUS_LIN_CABECALHOS, JUS_COL_INICIAL, col_final)]

    pares = []
    for i in range(0, len(datas) - 1, 2):
        mes = ler_mes(datas[i])
        if not ctx.no_horizonte(mes):
            continue
        if cabecalhos[i] != "AUM" or cabecalhos[i + 1] != "Receita":
            ctx.avisar(f"{ABA_G5JUS}: par de colunas do mes {mes} nao veio como AUM/Receita.")
            continue
        pares.append((mes, JUS_COL_INICIAL + i, JUS_COL_INICIAL + i + 1))

    def serie(linha: int) -> dict[str, list[float | None]]:
        return {
            "aum": [numero(ws.cell(linha, col_aum).value) for _, col_aum, _ in pares],
            "receita": [numero(ws.cell(linha, col_receita).value) for _, _, col_receita in pares],
        }

    linhas = []
    for linha in range(JUS_LIN_INICIAL, JUS_LIN_FINAL + 1):
        nome = texto(ws.cell(linha, JUS_DIMENSOES["portfolio"]).value)
        if nome is None:
            continue
        linhas.append(
            {
                **{campo: texto(ws.cell(linha, coluna).value) for campo, coluna in JUS_DIMENSOES.items()},
                **serie(linha),
            }
        )

    total = serie(JUS_LIN_TOTAL) if texto(ws.cell(JUS_LIN_TOTAL, COL_ROTULO).value) == ROTULO_TOTAL else None

    return {"moeda": "R$", "meses": [mes for mes, _, _ in pares], "linhas": linhas, "total": total}
