"""Numeros consolidados do mes — abas `resumo` e `CEO-Dashboard`.

Cobre os quatro KPIs da home (AUM, Run Rate, Projecao Ano, ROA), o split
onshore/offshore e as duas analises de ROA por faixa de PL.
"""

from __future__ import annotations

from typing import Any

from core.planilha import numero, texto

from .officers import CEO_LIN_FINAL, CEO_LIN_INICIAL, ROTULO_TOTAL_EX

ABA_RESUMO = "resumo"
ABA_CEO = "CEO-Dashboard"

#: `resumo` — bloco de KPIs. Linha 7 = onshore, 8 = offshore, 9 = total.
LIN_ONSHORE, LIN_OFFSHORE, LIN_TOTAL = 7, 8, 9
COL_AUM = 3  # C
COL_PROJECAO = 6  # F
COL_SOMA_ANO = 7  # G
COL_RECEITA_MENS = 8  # H
COL_RUN_RATE = 11  # K

#: `resumo` — ROA por Categoria / Faixa de PL (`O8:X27`).
CAT_LIN_INICIAL, CAT_LIN_FINAL, CAT_LIN_TOTAL = 9, 26, 27
CAT_COLS = {
    "categoria": 15,  # O
    "qtd": 16,  # P
    "aum": 17,  # Q
    "receita_anualizada": 18,  # R
    "roa": 19,  # S
    "pct_aum": 20,  # T
    "tipo": 21,  # U
    "faixa_min": 22,  # V
    "faixa_max": 23,  # W
    "qtd_zerados": 24,  # X
}

#: `resumo` — ROA por Grupo / Faixa de PL (`Z8:AH17`). A linha 16 e o grupo G5
#: isolado; as faixas acima dele ja o excluem (`docs/calculos.md` §3.4).
GRP_LIN_INICIAL, GRP_LIN_FINAL, GRP_LIN_TOTAL = 9, 16, 17
GRP_COLS = {
    "faixa": 26,  # Z
    "qtd": 27,  # AA
    "aum": 28,  # AB
    "receita_anualizada": 29,  # AC
    "roa": 30,  # AD
    "pct_aum": 31,  # AE
    "faixa_min": 32,  # AF
    "faixa_max": 33,  # AG
    "qtd_zerados": 34,  # AH
}

#: `CEO-Dashboard` — cartoes de KPI. Valores em R$ bi / R$ mi, como exibidos.
CEO_LINHAS = {"total": 12, "onshore": 13, "offshore": 14}
CEO_COLS = {
    "aum_bi": 3,  # C
    "aum_var_pct": 4,  # D
    "aum_var_bi": 5,  # E
    "run_rate_mi": 6,  # F
    "run_rate_var_pct": 7,  # G
    "run_rate_var_mi": 8,  # H
    "projecao_ano_mi": 9,  # I
    "roa": 10,  # J
}


def extrair(ctx) -> dict[str, Any]:
    pl = ctx.pl
    return {
        "aum": _por_origem(pl, COL_AUM),
        "receita_mens": _por_origem(pl, COL_RECEITA_MENS, com_total=False),
        "receita_ano_competencia": _por_origem(pl, COL_SOMA_ANO),
        "run_rate": _por_origem(pl, COL_RUN_RATE),
        "projecao_ano": _por_origem(pl, COL_PROJECAO),
        "roa": {
            "total": numero(pl.celula(ABA_RESUMO, "C10")),
            "onshore": numero(pl.celula(ABA_RESUMO, "C13")),
            "offshore": numero(pl.celula(ABA_RESUMO, "C14")),
        },
        "cambio_exibido": texto(pl.celula(ABA_RESUMO, "B4")),
        "kpis_ceo": _kpis_ceo(pl),
        "roa_categoria": _roa_categoria(pl),
        "roa_grupo": _roa_grupo(pl),
        "notas": _notas(pl),
    }


def _por_origem(pl, coluna: int, com_total: bool = True) -> dict[str, float | None]:
    """Le a mesma coluna do `resumo` nas tres linhas de origem."""
    ws = pl.aba(ABA_RESUMO)
    valores = {
        "onshore": numero(ws.cell(LIN_ONSHORE, coluna).value),
        "offshore": numero(ws.cell(LIN_OFFSHORE, coluna).value),
    }
    if com_total:
        valores["total"] = numero(ws.cell(LIN_TOTAL, coluna).value)
    else:
        # A linha 9 da coluna H e rotulo, nao valor: o total e a soma das partes.
        partes = [v for v in valores.values() if v is not None]
        valores["total"] = sum(partes) if partes else None
    return valores


def _kpis_ceo(pl) -> dict[str, Any]:
    """Cartoes da `CEO-Dashboard`, com a variacao M-1 que a aba ja traz pronta."""
    ws = pl.aba(ABA_CEO)
    cartoes = {
        origem: {campo: numero(ws.cell(linha, coluna).value) for campo, coluna in CEO_COLS.items()}
        for origem, linha in CEO_LINHAS.items()
    }
    return {
        "cartoes": cartoes,
        "mes_anterior": {
            "mes": texto(ws.cell(13, 17).value),  # Q13
            "dolar": numero(ws.cell(14, 17).value),  # Q14
            "aum_bi": {
                "total": numero(ws.cell(12, 18).value),
                "onshore": numero(ws.cell(13, 18).value),
                "offshore": numero(ws.cell(14, 18).value),
            },
            "run_rate_mi": {
                "total": numero(ws.cell(12, 19).value),
                "onshore": numero(ws.cell(13, 19).value),
                "offshore": numero(ws.cell(14, 19).value),
            },
        },
    }


def _roa_categoria(pl) -> dict[str, Any]:
    ws = pl.aba(ABA_RESUMO)
    linhas = []
    for linha in range(CAT_LIN_INICIAL, CAT_LIN_FINAL + 1):
        rotulo = texto(ws.cell(linha, CAT_COLS["categoria"]).value)
        if rotulo is None:
            continue
        linhas.append(
            {
                "categoria": rotulo,
                "tipo": texto(ws.cell(linha, CAT_COLS["tipo"]).value),
                "faixa_min": numero(ws.cell(linha, CAT_COLS["faixa_min"]).value),
                "faixa_max": numero(ws.cell(linha, CAT_COLS["faixa_max"]).value),
                "qtd": numero(ws.cell(linha, CAT_COLS["qtd"]).value),
                "qtd_zerados": numero(ws.cell(linha, CAT_COLS["qtd_zerados"]).value),
                "aum": numero(ws.cell(linha, CAT_COLS["aum"]).value),
                "receita_anualizada": numero(ws.cell(linha, CAT_COLS["receita_anualizada"]).value),
                "roa": numero(ws.cell(linha, CAT_COLS["roa"]).value),
                "pct_aum": numero(ws.cell(linha, CAT_COLS["pct_aum"]).value),
            }
        )
    return {"linhas": linhas, "total": _total_faixa(ws, CAT_LIN_TOTAL, CAT_COLS)}


def _roa_grupo(pl) -> dict[str, Any]:
    ws = pl.aba(ABA_RESUMO)
    linhas = []
    for linha in range(GRP_LIN_INICIAL, GRP_LIN_FINAL + 1):
        rotulo = texto(ws.cell(linha, GRP_COLS["faixa"]).value)
        if rotulo is None:
            continue
        linhas.append(
            {
                "faixa": rotulo,
                "faixa_min": numero(ws.cell(linha, GRP_COLS["faixa_min"]).value),
                "faixa_max": numero(ws.cell(linha, GRP_COLS["faixa_max"]).value),
                "qtd": numero(ws.cell(linha, GRP_COLS["qtd"]).value),
                "qtd_zerados": numero(ws.cell(linha, GRP_COLS["qtd_zerados"]).value),
                "aum": numero(ws.cell(linha, GRP_COLS["aum"]).value),
                "receita_anualizada": numero(ws.cell(linha, GRP_COLS["receita_anualizada"]).value),
                "roa": numero(ws.cell(linha, GRP_COLS["roa"]).value),
                "pct_aum": numero(ws.cell(linha, GRP_COLS["pct_aum"]).value),
            }
        )
    return {"linhas": linhas, "total": _total_faixa(ws, GRP_LIN_TOTAL, GRP_COLS)}


def _total_faixa(ws, linha: int, colunas: dict[str, int]) -> dict[str, float | None]:
    campos = ("qtd", "aum", "receita_anualizada", "roa", "pct_aum")
    return {campo: numero(ws.cell(linha, colunas[campo]).value) for campo in campos}


#: `CEO-Dashboard` — a nota de rodape e procurada **abaixo do rotulo**
#: `Total Ex- Fdos Alocacao`, o ultimo da tabela de officers, e nao numa linha
#: fixa da aba. A tabela cresce e encolhe conforme entra e sai officer, e a nota
#: desce e sobe junto: o extrator apontava para B41 e em 2026-08 ela estava em
#: B40 — a nota sumiu do dashboard sem nenhum erro. Ancorada no rotulo, a
#: distancia e estavel: na pratica a nota cai sempre em +2.
NOTA_DESLOCAMENTO_INICIAL, NOTA_DESLOCAMENTO_FINAL = 2, 6


def _notas(pl) -> list[str]:
    """Notas de rodape das duas abas, reproduzidas como estao."""
    ws = pl.aba(ABA_RESUMO)
    notas = [texto(ws.cell(linha, 2).value) for linha in range(18, 23)]
    ws_ceo = pl.aba(ABA_CEO)
    ancora = _linha_total_ex(ws_ceo)
    notas += [
        texto(ws_ceo.cell(ancora + salto, 2).value)
        for salto in range(NOTA_DESLOCAMENTO_INICIAL, NOTA_DESLOCAMENTO_FINAL + 1)
    ]
    return [n for n in notas if n]


def _linha_total_ex(ws) -> int:
    """Linha do `Total Ex- Fdos Alocacao` — o pe da tabela de officers.

    Erro duro se o rotulo nao aparecer: ele fecha a tabela que a aba inteira
    serve para montar. Nao estar la significa que a `CEO-Dashboard` mudou de
    forma, e continuar lendo coordenada por coordenada a partir dai produz
    numero plausivel e errado.
    """
    for linha in range(CEO_LIN_INICIAL, CEO_LIN_FINAL + 1):
        if texto(ws.cell(linha, 2).value) == ROTULO_TOTAL_EX:
            return linha
    raise ValueError(
        f"rotulo '{ROTULO_TOTAL_EX}' nao encontrado em {ABA_CEO}!B"
        f"{CEO_LIN_INICIAL}:B{CEO_LIN_FINAL} — a tabela de officers mudou de forma"
    )
