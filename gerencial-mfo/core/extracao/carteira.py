"""Carteira — portfolios, grupos economicos e regioes.

Fontes: `ar_onshore` / `ar_offshore` (bases de posicao, via nomes definidos),
`ar_grupos` (Top 10 e serie por grupo) e a aba oculta `regiao`, que e a unica
fonte do corte geografico.

O offshore fica em US$, como na planilha. A conversao para R$ e do consumidor,
com o `dolar` de `parametros` — converter aqui esconderia a moeda de origem.
"""

from __future__ import annotations

from typing import Any

from core.planilha import mes as ler_mes
from core.planilha import numero, texto

ABA_GRUPOS = "ar_grupos"
ABA_REGIAO = "regiao"

#: Ordem das colunas de `ar_on_info` / `ar_off_info` (`docs/modelo-de-dados.md` §5).
DIMENSOES = ("portfolio", "tipo", "adm", "grupo", "officer", "backup", "regiao", "segmento")

#: `ar_grupos` — os dois rankings. Cada mes ocupa 3 colunas; a ordem delas muda
#: entre os blocos (AUM/Receita no primeiro, Receita/AUM no segundo), por isso
#: os rotulos sao lidos da propria linha de cabecalho.
TOPS = (
    {"criterio": "aum", "lin_datas": 3, "lin_rotulos": 4, "lin_ini": 5, "lin_fim": 18},
    {"criterio": "receita", "lin_datas": 21, "lin_rotulos": 22, "lin_ini": 23, "lin_fim": 36},
)
TOP_COL_RANK = 2  # B
TOP_COL_INICIAL, TOP_COL_FINAL = 3, 38  # C..AL
COLUNAS_POR_MES = 3

#: `regiao` — tres blocos lado a lado, todos terminando na linha `TOTAL`.
BLOCOS_REGIAO = (
    {"nome": "onshore", "col_regiao": 1, "campos": {"aum": 2, "receita": 3, "pct_aum": 4}},
    {"nome": "offshore", "col_regiao": 7, "campos": {"aum": 8, "receita": 9, "pct_aum": 10}},
    {
        "nome": "consolidado",
        "col_regiao": 13,
        "campos": {"aum": 14, "receita": 15, "pct_aum": 16, "qtd_grupos": 18},
    },
)
REGIAO_LIN_INICIAL = 3
ROTULO_TOTAL = "TOTAL"
ROTULO_SEM_REGIAO = "-"
#: `regiao!G2` guarda o cambio usado no bloco offshore — serve de conferencia
#: cruzada contra `info!AQ3`.
REGIAO_CELULA_DOLAR = "G2"


def extrair(ctx) -> dict[str, Any]:
    return {
        "portfolios": {
            "onshore": _portfolios(ctx, "ar_on", "R$"),
            "offshore": _portfolios(ctx, "ar_off", "US$"),
        },
        "grupos": {
            "rankings": [_top_grupos(ctx, **bloco) for bloco in TOPS],
            "serie": _serie_grupos(ctx),
        },
        "regioes": _regioes(ctx),
    }


# --------------------------------------------------------------------------
# Bases de posicao
# --------------------------------------------------------------------------


def _portfolios(ctx, prefixo: str, moeda: str) -> dict[str, Any]:
    """Uma linha por portfolio, com as dimensoes e as series AUM/Receita."""
    pl = ctx.pl
    datas = [ler_mes(v) for v in pl.bloco_nome(f"{prefixo}_datas")[0]]
    cabecalhos = [texto(v) for v in pl.bloco_nome(f"{prefixo}_headers")[0]]
    info = pl.bloco_nome(f"{prefixo}_info")
    valores = pl.bloco_nome(prefixo)
    total = pl.bloco_nome(f"{prefixo}_total")[0]

    pares = _pares_de_mes(ctx, datas, cabecalhos, prefixo)
    meses = [mes for mes, _, _ in pares]

    linhas = []
    for dimensoes, serie in zip(info, valores):
        registro = {campo: texto(valor) for campo, valor in zip(DIMENSOES, dimensoes)}
        if registro.get("portfolio") is None:
            continue
        registro["aum"] = [numero(serie[i]) for _, i, _ in pares]
        registro["receita"] = [numero(serie[j]) for _, _, j in pares]
        linhas.append(registro)

    return {
        "moeda": moeda,
        "meses": meses,
        "linhas": linhas,
        "total": {
            "aum": [numero(total[i]) for _, i, _ in pares],
            "receita": [numero(total[j]) for _, _, j in pares],
        },
    }


def _pares_de_mes(ctx, datas: list[str | None], cabecalhos: list[str | None], origem: str):
    """`[(mes, indice_aum, indice_receita)]` dentro do horizonte do build.

    As bases guardam AUM e Receita alternados, com a data repetida no par. Os
    cabecalhos sao conferidos em vez de presumidos: uma coluna trocada na
    geradora viraria uma serie invertida sem nenhum sintoma visivel.
    """
    pares = []
    for i in range(0, len(datas) - 1, 2):
        mes = ler_mes(datas[i])
        if not ctx.no_horizonte(mes):
            continue
        if cabecalhos[i] != "AUM" or cabecalhos[i + 1] != "Receita":
            ctx.avisar(
                f"{origem}: par de colunas {i}/{i + 1} do mes {mes} veio como "
                f"{cabecalhos[i]}/{cabecalhos[i + 1]}, nao AUM/Receita. Colunas ignoradas."
            )
            continue
        pares.append((mes, i, i + 1))
    return pares


# --------------------------------------------------------------------------
# Grupos economicos
# --------------------------------------------------------------------------


def _top_grupos(ctx, *, criterio: str, lin_datas: int, lin_rotulos: int, lin_ini: int, lin_fim: int):
    """Ranking Top 10 do mes, mais as linhas G5, SOMA, G5-TOTAL e %."""
    pl = ctx.pl
    ws = pl.aba(ABA_GRUPOS)
    datas = pl.linha(ABA_GRUPOS, lin_datas, TOP_COL_INICIAL, TOP_COL_FINAL)
    rotulos = pl.linha(ABA_GRUPOS, lin_rotulos, TOP_COL_INICIAL, TOP_COL_FINAL)

    por_mes = []
    for deslocamento in range(0, len(datas), COLUNAS_POR_MES):
        mes = ler_mes(datas[deslocamento])
        if not ctx.no_horizonte(mes):
            continue
        colunas = {
            texto(rotulos[deslocamento + i]): TOP_COL_INICIAL + deslocamento + i
            for i in range(COLUNAS_POR_MES)
            if deslocamento + i < len(rotulos)
        }
        linhas = []
        for linha in range(lin_ini, lin_fim + 1):
            rank = texto(ws.cell(linha, TOP_COL_RANK).value)
            grupo = texto(ws.cell(linha, colunas["Grupo"]).value) if "Grupo" in colunas else None
            if rank is None and grupo is None:
                continue
            linhas.append(
                {
                    "rank": rank,
                    "grupo": grupo,
                    "aum": numero(ws.cell(linha, colunas["AUM"]).value) if "AUM" in colunas else None,
                    "receita": (
                        numero(ws.cell(linha, colunas["Receita"]).value) if "Receita" in colunas else None
                    ),
                }
            )
        por_mes.append({"mes": mes, "linhas": linhas})

    return {"criterio": criterio, "por_mes": por_mes}


def _serie_grupos(ctx) -> dict[str, Any]:
    """Serie mensal de AUM e Receita por grupo economico (nome `grupos`)."""
    pl = ctx.pl
    datas = [ler_mes(v) for v in pl.bloco_nome("grupos_datas")[0]]
    cabecalhos = [texto(v) for v in pl.bloco_nome("grupos_headers")[0]]
    nomes = [texto(linha[0]) for linha in pl.bloco_nome("grupos_info")]
    valores = pl.bloco_nome("grupos")

    pares = _pares_de_mes(ctx, datas, cabecalhos, "ar_grupos!grupos")
    linhas = []
    for nome, serie in zip(nomes, valores):
        if nome is None:
            continue
        linhas.append(
            {
                "grupo": nome,
                "aum": [numero(serie[i]) for _, i, _ in pares],
                "receita": [numero(serie[j]) for _, _, j in pares],
            }
        )
    return {"meses": [mes for mes, _, _ in pares], "linhas": linhas}


# --------------------------------------------------------------------------
# Regioes
# --------------------------------------------------------------------------


def _regioes(ctx) -> dict[str, Any]:
    pl = ctx.pl
    ws = pl.aba(ABA_REGIAO)
    resultado: dict[str, Any] = {}

    for bloco in BLOCOS_REGIAO:
        linhas = []
        total = None
        linha = REGIAO_LIN_INICIAL
        while linha <= ws.max_row:
            rotulo = texto(ws.cell(linha, bloco["col_regiao"]).value)
            if rotulo is None:
                break
            registro = {
                "regiao": rotulo,
                **{
                    campo: numero(ws.cell(linha, coluna).value)
                    for campo, coluna in bloco["campos"].items()
                },
            }
            if rotulo == ROTULO_TOTAL:
                total = registro
                break
            registro["sem_regiao"] = rotulo == ROTULO_SEM_REGIAO
            linhas.append(registro)
            linha += 1
        resultado[bloco["nome"]] = {"linhas": linhas, "total": total}

    resultado["dolar_offshore"] = numero(pl.celula(ABA_REGIAO, REGIAO_CELULA_DOLAR))
    return resultado
