"""Visao por officer — `CEO-Dashboard` (tabela) e `cons_officer` (detalhe).

`Fdos Alocacao` e um pseudo-officer (officer `-`, grupo `G5`) e **sempre entra
nos totais**, para que TOTAL bata entre todas as visoes. A linha
`Total Ex- Fdos Alocacao` da propria planilha e preservada como referencia de
conferencia do toggle global do dashboard.
"""

from __future__ import annotations

from typing import Any

from core.planilha import limites_ref, numero, texto
from core.planilha import mes as ler_mes

from .comum import linhas_rotuladas

ABA_CEO = "CEO-Dashboard"
ABA_CONS = "cons_officer"

#: `CEO-Dashboard` — tabela de officers, da linha 17 ate a ultima linha de total.
CEO_LIN_INICIAL, CEO_LIN_FINAL = 17, 39
CEO_COL_NOME = 2  # B
CEO_CAMPOS = {
    "aum_mi": 3,  # C
    "aum_var_pct": 4,  # D
    "aum_var_mi": 5,  # E
    "receita": 6,  # F
    "receita_var_pct": 7,  # G
    "receita_var": 8,  # H
    "roa": 9,  # I
    "roa_mfo": 10,  # J
    "in_out_mes_mi": 11,  # K
    "qtd_portfolios": 12,  # L
    "pct_aum": 14,  # N
    "pct_receita": 15,  # O
    "aum_mi_m1": 26,  # Z
    "receita_m1": 27,  # AA
}
ROTULO_FDOS = "Fdos Alocação"
ROTULO_TOTAL = "Total"
ROTULO_TOTAL_EX = "Total Ex- Fdos Alocação"

#: `cons_officer` — cabecalho do quadro: login, apelido e o intervalo do bloco
#: de detalhe de cada officer (`docs/calculos.md` §3.5).
CONS_LIN_LOGIN, CONS_LIN_NOME, CONS_LIN_INTERVALO = 5, 6, 7
CONS_COL_INICIAL, CONS_COL_FINAL = 3, 40
CONS_COL_ROTULO = 2  # B


def extrair(ctx) -> dict[str, Any]:
    return {
        "tabela_ceo": _tabela_ceo(ctx),
        "blocos": _blocos_cons_officer(ctx),
    }


def _tabela_ceo(ctx) -> list[dict[str, Any]]:
    ws = ctx.pl.aba(ABA_CEO)
    linhas = []
    for linha in range(CEO_LIN_INICIAL, CEO_LIN_FINAL + 1):
        nome = texto(ws.cell(linha, CEO_COL_NOME).value)
        if nome is None:
            continue
        registro: dict[str, Any] = {"nome": nome, "tipo": _tipo_linha(nome)}
        registro.update(
            {campo: numero(ws.cell(linha, coluna).value) for campo, coluna in CEO_CAMPOS.items()}
        )
        linhas.append(registro)
    return linhas


def _tipo_linha(nome: str) -> str:
    if nome == ROTULO_FDOS:
        return "fdos_alocacao"
    if nome == ROTULO_TOTAL_EX:
        return "total_ex_fdos"
    if nome == ROTULO_TOTAL:
        return "total"
    return "officer"


def _blocos_cons_officer(ctx) -> list[dict[str, Any]]:
    """Um bloco por officer, com as ~30 metricas mensais que a aba calcula."""
    pl = ctx.pl
    ws = pl.aba(ABA_CONS)
    blocos = []

    for coluna in range(CONS_COL_INICIAL, CONS_COL_FINAL + 1):
        referencia = texto(ws.cell(CONS_LIN_INTERVALO, coluna).value)
        if referencia is None:
            continue
        login = texto(ws.cell(CONS_LIN_LOGIN, coluna).value)
        nome = texto(ws.cell(CONS_LIN_NOME, coluna).value)
        lin_ini, col_ini, lin_fim, col_fim = limites_ref(referencia)

        meses = [ler_mes(v) for v in pl.linha(ABA_CONS, lin_ini, col_ini, col_fim)]
        dias_uteis = [numero(v) for v in pl.linha(ABA_CONS, lin_ini - 1, col_ini, col_fim)]

        linhas = linhas_rotuladas(
            pl,
            ABA_CONS,
            lin_ini + 1,
            lin_fim,
            col_rotulo=CONS_COL_ROTULO,
            col_ini=col_ini,
            col_fim=col_fim,
            ignorar_cabecalho_de_bloco=True,
        )

        series = [dias_uteis] + [item["valores"] for item in linhas]
        meses_ok, series_ok = ctx.cortar(meses, *series)
        for item, valores in zip(linhas, series_ok[1:]):
            item["valores"] = valores

        blocos.append(
            {
                "login": login,
                "nome": nome,
                "e_fdos_alocacao": nome == "-" or login == "-",
                "intervalo": referencia,
                "meses": meses_ok,
                "dias_uteis": series_ok[0],
                "linhas": linhas,
            }
        )
    return blocos
