"""Captacao — `net_in_out`, `io_grupos`, `io_portfolios` e os blocos do `Dashboard`.

Cuidado com a armadilha numero um do modelo (`docs/modelo-de-dados.md` §6):

- **Captacao Cliente** sai das bases `*_net_*`, sem as movimentacoes do proprio
  grupo G5 — e o que alimenta `net_in_out` e `io_portfolios`.
- **NET Executado** sai de `in_out`, com o G5 — e o que alimenta o bloco 3 do
  `Dashboard`.

Sao abas diferentes justamente porque os numeros sao diferentes. Este modulo so
transporta cada uma para o seu lugar no JSON; nada e somado entre elas.
"""

from __future__ import annotations

from typing import Any

from core.planilha import chave, numero, texto
from core.planilha import mes as ler_mes

from .comum import atribuir_pais, nivel

ABA_NET = "net_in_out"
ABA_IO_GRUPOS = "io_grupos"
ABA_IO_PORTFOLIOS = "io_portfolios"
ABA_DASHBOARD = "Dashboard"

#: `net_in_out` — dois blocos, onshore em R$ e offshore em US$ (com total em R$).
NET_COL_ROTULO = 2  # B
NET_COL_INICIAL, NET_COL_FINAL = 3, 14  # C..N, os 12 meses do ano
BLOCOS_NET = (
    {
        "nome": "onshore",
        "moeda": "R$",
        "lin_extra": 4,
        "nome_extra": "dias_uteis",
        "lin_datas": 5,
        "lin_ini": 7,
        "lin_fim": 67,
        "col_total": 15,  # O
        "col_total_reais": None,
    },
    {
        "nome": "offshore",
        "moeda": "US$",
        "lin_extra": 69,
        "nome_extra": "dolar",
        "lin_datas": 70,
        "lin_ini": 72,
        "lin_fim": 90,
        "col_total": 15,  # O
        "col_total_reais": 16,  # P
    },
)
SECOES_NET = ("IN", "OUT", "NET")

#: `io_grupos` — movimentacoes por grupo economico: visao mensal e visao YTD.
IO_GRUPOS_LIN_INICIAL = 8
IO_GRUPOS_MENSAL = {
    "mes": 2,  # B
    "grupo": 3,
    "valor": 4,
    "officer": 5,
    "lead_externo": 6,
    "lead_g5": 7,
    "segmento": 8,
}
IO_GRUPOS_YTD = {
    "grupo": 10,  # J
    "valor": 11,
    "officer": 12,
    "lead_externo": 13,
    "lead_g5": 14,
    "segmento": 15,
}

#: `io_portfolios` — IN/OUT por portfolio, com a taxa contratada que permite
#: estimar a receita incremental sem esperar o fechamento seguinte.
IO_PORTFOLIOS_LIN_INICIAL = 4
IO_PORTFOLIOS_ONSHORE = {
    "portfolio": 2,  # B
    "officer": 3,
    "taxa": 4,
    "tipo": 5,
    "in": 6,
    "out": 7,
    "net": 8,
    "receita_aprox": 9,
    "obs": 10,
}
IO_PORTFOLIOS_OFFSHORE = {
    "portfolio": 12,  # L
    "officer": 13,
    "taxa": 14,
    "in_usd": 15,
    "out_usd": 16,
    "net_usd": 17,
    "receita_aprox_usd": 18,
    "in": 19,
    "out": 20,
    "net": 21,
    "receita_aprox": 22,
    "obs": 23,
}
CAMPOS_TEXTO_IO = {"portfolio", "officer", "tipo", "obs", "grupo", "segmento", "lead_externo", "lead_g5"}

#: `Dashboard` §2 — Captacao Cliente (mes, ano, incremento de receita, ROA incremental).
DASH_CAPTACAO_LIN_INICIAL, DASH_CAPTACAO_LIN_FINAL = 15, 31
DASH_CAPTACAO_COLS = {
    "mes": 3,  # C
    "ano": 4,  # D
    "incremento_receita_mi_ano": 5,  # E
    "roa_incremental": 6,  # F
}

#: `Dashboard` §3 — NET Executado por mes. Cada mes ocupa 5 linhas; a data do
#: bloco fica na coluna K e a linha TOTAL fecha a tabela.
DASH_NET_LIN_INICIAL, DASH_NET_LIN_FINAL = 37, 113
DASH_NET_COL_DATA = 11  # K
DASH_NET_COL_ROTULO = 2  # B
DASH_NET_SEGMENTOS = (
    {"segmento": "MFO", "entrada": 3, "saida": 4},  # C / D
    {"segmento": "Institucional", "entrada": 5, "saida": 6},  # E / F
    {"segmento": "Estruturado", "entrada": 7, "saida": 8},  # G / H
)
DASH_NET_COL_TOTAL = 9  # I
DASH_NET_LINHAS_POR_MES = 5
ROTULO_TOTAL = "TOTAL"


def extrair(ctx) -> dict[str, Any]:
    return {
        "net_in_out": {bloco["nome"]: _bloco_net(ctx, bloco) for bloco in BLOCOS_NET},
        "grupos": {
            "mensal": _tabela(ctx, ABA_IO_GRUPOS, IO_GRUPOS_LIN_INICIAL, IO_GRUPOS_MENSAL, "grupo"),
            "ytd": _tabela(ctx, ABA_IO_GRUPOS, IO_GRUPOS_LIN_INICIAL, IO_GRUPOS_YTD, "grupo"),
        },
        "portfolios": {
            "onshore": _tabela(
                ctx, ABA_IO_PORTFOLIOS, IO_PORTFOLIOS_LIN_INICIAL, IO_PORTFOLIOS_ONSHORE, "portfolio"
            ),
            "offshore": _tabela(
                ctx, ABA_IO_PORTFOLIOS, IO_PORTFOLIOS_LIN_INICIAL, IO_PORTFOLIOS_OFFSHORE, "portfolio"
            ),
        },
        "captacao_cliente": _captacao_cliente(ctx),
        "net_executado": _net_executado(ctx),
    }


def _bloco_net(ctx, bloco: dict[str, Any]) -> dict[str, Any]:
    pl = ctx.pl
    ws = pl.aba(ABA_NET)
    meses = [ler_mes(v) for v in pl.linha(ABA_NET, bloco["lin_datas"], NET_COL_INICIAL, NET_COL_FINAL)]
    extra = [numero(v) for v in pl.linha(ABA_NET, bloco["lin_extra"], NET_COL_INICIAL, NET_COL_FINAL)]

    linhas = []
    secao = None
    for linha in range(bloco["lin_ini"], bloco["lin_fim"] + 1):
        rotulo = texto(ws.cell(linha, NET_COL_ROTULO).value)
        if rotulo is None:
            continue
        if rotulo in SECOES_NET:
            secao = rotulo
        registro = {
            "secao": secao,
            "rotulo": rotulo,
            "chave": chave(rotulo),
            "nivel": nivel(ws, linha, NET_COL_ROTULO),
            "linha": linha,
            "valores": [numero(v) for v in pl.linha(ABA_NET, linha, NET_COL_INICIAL, NET_COL_FINAL)],
            "total": numero(ws.cell(linha, bloco["col_total"]).value),
        }
        if bloco["col_total_reais"]:
            registro["total_reais"] = numero(ws.cell(linha, bloco["col_total_reais"]).value)
        linhas.append(registro)

    atribuir_pais(linhas)
    series = [extra] + [item["valores"] for item in linhas]
    meses_ok, series_ok = ctx.cortar(meses, *series)
    for item, valores in zip(linhas, series_ok[1:]):
        item["valores"] = valores

    return {
        "moeda": bloco["moeda"],
        "meses": meses_ok,
        bloco["nome_extra"]: series_ok[0],
        "linhas": linhas,
    }


def _tabela(ctx, aba: str, lin_inicial: int, colunas: dict[str, int], campo_ancora: str):
    """Le uma tabela linha a linha ate a primeira linha sem o campo-ancora."""
    ws = ctx.pl.aba(aba)
    linhas = []
    for linha in range(lin_inicial, ws.max_row + 1):
        ancora = texto(ws.cell(linha, colunas[campo_ancora]).value)
        if ancora is None:
            continue
        registro: dict[str, Any] = {}
        for campo, coluna in colunas.items():
            bruto = ws.cell(linha, coluna).value
            if campo == "mes":
                registro[campo] = ler_mes(bruto)
            elif campo in CAMPOS_TEXTO_IO:
                registro[campo] = texto(bruto)
            else:
                registro[campo] = numero(bruto)
        if registro.get("mes") and not ctx.no_horizonte(registro["mes"]):
            continue
        linhas.append(registro)
    return linhas


def _captacao_cliente(ctx) -> list[dict[str, Any]]:
    """Bloco 2 do `Dashboard`: Net/Ingresso/Retirada do mes e do ano."""
    ws = ctx.pl.aba(ABA_DASHBOARD)
    linhas = []
    for linha in range(DASH_CAPTACAO_LIN_INICIAL, DASH_CAPTACAO_LIN_FINAL + 1):
        rotulo = texto(ws.cell(linha, DASH_NET_COL_ROTULO).value)
        if rotulo is None:
            continue
        linhas.append(
            {
                "rotulo": rotulo,
                "chave": chave(rotulo),
                "nivel": nivel(ws, linha, DASH_NET_COL_ROTULO),
                "linha": linha,
                **{
                    campo: numero(ws.cell(linha, coluna).value)
                    for campo, coluna in DASH_CAPTACAO_COLS.items()
                },
            }
        )
    return atribuir_pais(linhas)


def _net_executado(ctx) -> dict[str, Any]:
    """Bloco 3 do `Dashboard`: entradas e saidas por segmento, mes a mes.

    Base `in_out` — **com** as movimentacoes do grupo G5. Nao confundir com a
    captacao cliente acima.
    """
    ws = ctx.pl.aba(ABA_DASHBOARD)
    meses = []
    total = None

    for linha in range(DASH_NET_LIN_INICIAL, DASH_NET_LIN_FINAL + 1):
        rotulo = texto(ws.cell(linha, DASH_NET_COL_ROTULO).value)
        if rotulo == ROTULO_TOTAL:
            total = _linha_net_executado(ws, linha)
            continue
        mes = ler_mes(ws.cell(linha, DASH_NET_COL_DATA).value)
        if mes is None or not ctx.no_horizonte(mes):
            continue
        bloco = {"mes": mes, "nome_mes": rotulo, **_linha_net_executado(ws, linha), "componentes": []}
        for deslocamento in range(1, DASH_NET_LINHAS_POR_MES):
            componente = linha + deslocamento
            rotulo_componente = texto(ws.cell(componente, DASH_NET_COL_ROTULO).value)
            if rotulo_componente is None:
                continue
            bloco["componentes"].append(
                {
                    "rotulo": rotulo_componente,
                    "chave": chave(rotulo_componente),
                    **_linha_net_executado(ws, componente),
                }
            )
        meses.append(bloco)

    return {"meses": meses, "total": total}


def _linha_net_executado(ws, linha: int) -> dict[str, Any]:
    return {
        "segmentos": {
            item["segmento"]: {
                "entrada": numero(ws.cell(linha, item["entrada"]).value),
                "saida": numero(ws.cell(linha, item["saida"]).value),
            }
            for item in DASH_NET_SEGMENTOS
        },
        "total": numero(ws.cell(linha, DASH_NET_COL_TOTAL).value),
    }
