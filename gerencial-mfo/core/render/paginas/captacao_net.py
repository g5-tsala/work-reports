"""Aba: Net In/Out.

Captação **de cliente** — base sem as movimentações do próprio grupo G5. Três
faixas de KPI (consolidado em R$, onshore, offshore), o fluxo mensal com um
seletor entre os três universos e o detalhe por tipo de veículo, com a
abertura de cada tipo recolhida.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    alternador,
    expandir_todos,
    faixa_kpis,
    fonte,
    grafico,
    kpi,
    linha_detalhe,
    linha_expansivel,
    nota,
    num,
    secao,
    tabela,
)

SECOES = ("IN", "OUT", "NET")


@pagina(
    identificador="captacao-net",
    titulo="Net In/Out",
    grupo="Captação",
    ordem=10,
    subtitulo="Entradas e saídas de cliente, mês a mês. Não inclui movimentação dos fundos "
    "próprios da G5.",
)
def render(ctx: Contexto) -> str:
    onshore = ctx.bloco("captacao", "net_in_out", "onshore")
    offshore = ctx.bloco("captacao", "net_in_out", "offshore")
    universos = _universos(onshore, offshore)

    return "".join(
        [
            *(_kpis(ctx, universo, principal=indice == 0) for indice, universo in enumerate(universos)),
            secao(
                "Fluxo mensal",
                alternador(
                    "net-fluxo",
                    "Universo do gráfico",
                    [
                        (universo["chave"], universo["titulo"], _grafico(ctx, universo))
                        for universo in universos
                    ],
                ),
            ),
            secao(
                "Detalhe onshore (R$)",
                expandir_todos("net-onshore"),
                _tabela(ctx, onshore, "net-onshore"),
                fonte("net_in_out", ctx.rotulo_mes, "Base info_net_in_out, sem o grupo G5."),
            ),
            secao(
                "Detalhe offshore (US$)",
                expandir_todos("net-offshore"),
                _tabela(ctx, offshore, "net-offshore"),
                fonte("net_in_out", ctx.rotulo_mes, "Valores em US$; total do ano também em R$."),
            ),
            nota(
                "Esta página usa a base <strong>de cliente</strong>. O NET executado do "
                "<em>Dashboard</em>, que inclui os fundos de alocação da G5, é outra base e não "
                "deve ser somado a esta."
            ),
        ]
    )


def _secao_principal(bloco: dict[str, Any], rotulo: str) -> dict[str, Any] | None:
    for linha in bloco["linhas"]:
        if linha["rotulo"] == rotulo and linha["secao"] == rotulo:
            return linha
    return None


def _universos(onshore: dict[str, Any], offshore: dict[str, Any]) -> list[dict[str, Any]]:
    """Consolidado, onshore e offshore, cada um com IN, OUT e NET mês a mês e no ano.

    O consolidado soma o onshore ao offshore convertido **pelo câmbio de cada
    mês** (`offshore.dolar`), não pelo do mês-base. É a conta da própria
    planilha: a coluna `Ano (R$)` do offshore (`net_in_out!P`) é exatamente
    Σ valor do mês × câmbio do mês. Assim o NET no ano consolidado soma o
    total onshore com esse `total_reais`, sem reconverter.
    """
    meses = onshore["meses"]
    cambio = dict(zip(offshore["meses"], offshore["dolar"]))

    def series(bloco: dict[str, Any], converter: bool) -> dict[str, dict[str, Any]]:
        saida = {}
        for rotulo in SECOES:
            linha = _secao_principal(bloco, rotulo) or {"valores": [], "total": None}
            por_mes = dict(zip(bloco["meses"], linha["valores"]))
            valores = [
                (por_mes.get(mes) or 0.0) * (cambio.get(mes) or 0.0) if converter else por_mes.get(mes)
                for mes in meses
            ]
            saida[rotulo] = {
                "valores": valores,
                "total": linha.get("total_reais") if converter else linha.get("total"),
            }
        return saida

    on, off_reais = series(onshore, False), series(offshore, True)
    consolidado = {
        rotulo: {
            "valores": [(a or 0.0) + (b or 0.0) for a, b in zip(on[rotulo]["valores"], off_reais[rotulo]["valores"])],
            "total": (on[rotulo]["total"] or 0.0) + (off_reais[rotulo]["total"] or 0.0),
        }
        for rotulo in SECOES
    }
    return [
        {
            "chave": "consolidado",
            "titulo": "Consolidado (R$)",
            "moeda": "R$",
            "meses": meses,
            "series": consolidado,
            "observacao": "Offshore convertido pelo câmbio de cada mês.",
        },
        {"chave": "onshore", "titulo": "Onshore (R$)", "moeda": "R$", "meses": meses, "series": on, "observacao": ""},
        {
            "chave": "offshore",
            "titulo": "Offshore (US$)",
            "moeda": "US$",
            "meses": offshore["meses"],
            "series": series(offshore, False),
            "observacao": "",
        },
    ]


def _kpis(ctx: Contexto, universo: dict[str, Any], principal: bool) -> str:
    """Uma faixa por universo. Número negativo sai em vermelho; positivo, não.

    Uma casa decimal: com o sinal, `R$ -426,48 mi` não cabe no cartão e quebra
    linha, e na casa das centenas de milhões o centésimo não muda leitura.
    """
    posicao = universo["meses"].index(ctx.mes_base) if ctx.mes_base in universo["meses"] else None
    series, moeda = universo["series"], universo["moeda"]

    def cartao(rotulo: str, valor: float | None) -> str:
        return kpi(
            rotulo,
            formato.milhoes(valor, 1, moeda=moeda),
            classe_valor="negativo" if valor is not None and valor < 0 else "",
        )

    def do_mes(secao_: str) -> float | None:
        valores = series[secao_]["valores"]
        return valores[posicao] if posicao is not None and posicao < len(valores) else None

    return faixa_kpis(
        cartao("NET do mês", do_mes("NET")),
        cartao("IN do mês", do_mes("IN")),
        cartao("OUT do mês", do_mes("OUT")),
        cartao("NET no ano", series["NET"]["total"]),
        titulo=universo["titulo"],
        secundaria=not principal,
    )


def _grafico(ctx: Contexto, universo: dict[str, Any]) -> str:
    series, moeda = universo["series"], universo["moeda"]
    if not any(series[rotulo]["valores"] for rotulo in SECOES):
        return ""

    svg = graficos.combo(
        ctx.rotulos(universo["meses"]),
        [
            graficos.Serie("IN", series["IN"]["valores"]),
            graficos.Serie("OUT", series["OUT"]["valores"], cor=graficos.SERIES[1]),
        ],
        graficos.Serie("NET", series["NET"]["valores"], cor=graficos.SERIES[2]),
        formatador_barra=lambda v: formato.em_milhoes(v, 0),
        formatador_linha=lambda v: formato.em_milhoes(v, 0),
        titulo=f"IN, OUT e NET por mês — {universo['titulo']}",
        empilhado=True,
        formatador_dica=lambda v: formato.milhoes(v, 1, moeda=moeda),
    )
    return grafico(
        svg,
        itens_legenda=[
            (f"IN ({moeda} mi)", graficos.SERIES[0]),
            (f"OUT ({moeda} mi)", graficos.SERIES[1]),
            (f"NET ({moeda} mi, linha)", graficos.SERIES[2]),
        ],
        rodape=fonte("net_in_out", ctx.rotulo_mes, universo["observacao"]),
    )


def _tabela(ctx: Contexto, bloco: dict[str, Any], identificador: str) -> str:
    """IN, OUT e NET por tipo de veículo; a abertura de cada tipo fica recolhida.

    As linhas de nível 2 (início no ano, clientes antigos, finalidade, ROA)
    abrem ao clicar no tipo de veículo acima delas — ou todas de uma vez pelo
    botão acima da tabela.
    """
    moeda = bloco["moeda"]
    escala = f"{moeda} mi"
    colunas = (
        [Coluna(f"Linha ({escala})")]
        + [Coluna(rotulo, numerica=True) for rotulo in ctx.rotulos(bloco["meses"])]
        + [Coluna("Ano", numerica=True)]
    )
    tem_reais = any("total_reais" in linha for linha in bloco["linhas"])
    if tem_reais:
        colunas.append(Coluna("Ano (R$ mi)", numerica=True))

    registros = bloco["linhas"]
    linhas = []
    alvo = None
    for indice, registro in enumerate(registros):
        eh_percentual = registro["chave"] == "roa_pct"
        formatador = formato.percentual if eh_percentual else (lambda v: formato.em_milhoes(v, 2))
        celulas: list[Any] = [registro["rotulo"]]
        celulas += [
            num(formatador(valor), formato.classe_sinal(valor) if not eh_percentual else "")
            for valor in registro["valores"]
        ]
        celulas.append(num(formato.NAO_APLICAVEL if eh_percentual else formatador(registro["total"])))
        if tem_reais:
            celulas.append(
                num(
                    formato.NAO_APLICAVEL
                    if eh_percentual
                    else formato.em_milhoes(registro.get("total_reais"), 2)
                )
            )

        nivel = registro["nivel"]
        atributos: dict[str, Any] = {}
        if nivel == 1:
            proxima = registros[indice + 1] if indice + 1 < len(registros) else None
            alvo = f"{identificador}-{indice}" if proxima and proxima["nivel"] > 1 else None
            if alvo:
                atributos = linha_expansivel(alvo)
        elif nivel > 1 and alvo:
            atributos = linha_detalhe(alvo)
        else:
            alvo = None
        classe = "subtotal" if nivel == 0 else ""
        linhas.append(Linha(celulas, classe=classe, nivel=nivel, atributos=atributos))

    return tabela(colunas, linhas, identificador=identificador, ordenavel=False)
