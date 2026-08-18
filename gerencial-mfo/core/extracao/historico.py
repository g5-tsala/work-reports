"""Series longas — abas `aum_receita` e `roa_historico`.

A grade temporal nao e uniforme: colunas C→R sao pontos semestrais de 2018-06 a
2025-12 e S→AD sao mensais de 2026. Quem plota trata como eixo categorico
ordenado (`docs/modelo-de-dados.md` §4); aqui so preservamos a ordem e o rotulo.
"""

from __future__ import annotations

from typing import Any

from core.planilha import chave, numero, texto
from core.planilha import mes as ler_mes

from .comum import linhas_rotuladas

ABA_AUM_RECEITA = "aum_receita"
ABA_ROA_HISTORICO = "roa_historico"

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

#: `roa_historico` — rotulos que abrem e fecham cada bloco empilhado.
CABECALHOS_BLOCO = ("Categoria", "Grupo")
FIM_BLOCO = "Total"
COL_TITULO_ALTERNATIVO = 30  # AD, repete o titulo do bloco a direita


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
        "roa_historico": _blocos_roa_historico(ctx),
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
    """Linhas rotuladas nas colunas de serie destas duas abas.

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


def _blocos_roa_historico(ctx) -> list[dict[str, Any]]:
    """Os blocos empilhados de `roa_historico`, descobertos por varredura.

    Sao dez: cinco por categoria/faixa (Qtd. Veiculos, AUM, Receita Anualizada,
    ROA, AUM %) e cinco por grupo/faixa. Varrer em vez de fixar as linhas evita
    que o extrator quebre quando a aba ganhar mais um bloco.
    """
    pl = ctx.pl
    ws = pl.aba(ABA_ROA_HISTORICO)
    blocos = []

    for linha in range(1, ws.max_row + 1):
        if texto(ws.cell(linha, COL_ROTULO).value) not in CABECALHOS_BLOCO:
            continue
        dimensao = texto(ws.cell(linha, COL_ROTULO).value)
        titulo = texto(ws.cell(linha - 1, COL_ROTULO).value) or texto(
            ws.cell(linha - 1, COL_TITULO_ALTERNATIVO).value
        )
        fim = _fim_do_bloco(ws, linha)
        if fim is None:
            ctx.avisar(f"{ABA_ROA_HISTORICO}: bloco iniciado na linha {linha} nao tem linha 'Total'.")
            continue

        meses = [ler_mes(v) for v in pl.linha(ABA_ROA_HISTORICO, linha, COL_SERIE_INICIAL, COL_SERIE_FINAL)]
        linhas = _linhas(pl, ABA_ROA_HISTORICO, linha + 1, fim - 1)
        total = _linhas(pl, ABA_ROA_HISTORICO, fim, fim)

        series = [item["valores"] for item in linhas + total]
        meses_ok, series_ok = ctx.cortar(meses, *series)
        for item, valores in zip(linhas + total, series_ok):
            item["valores"] = valores

        blocos.append(
            {
                "titulo": titulo,
                "chave": chave(titulo),
                "dimensao": dimensao.lower() if dimensao else None,
                "meses": meses_ok,
                "linhas": linhas,
                "total": total[0] if total else None,
            }
        )
    return blocos


def _fim_do_bloco(ws, cabecalho: int) -> int | None:
    for linha in range(cabecalho + 1, ws.max_row + 1):
        if texto(ws.cell(linha, COL_ROTULO).value) == FIM_BLOCO:
            return linha
    return None
