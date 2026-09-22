"""Aba: Net In/Out.

Captação **de cliente** — sem as movimentações dos fundos de alocação da G5 —
em três leituras que vêm da mesma base e por isso fecham entre si:

- faixas de KPI (consolidado em R$, onshore, offshore), de `net_in_out`;
- a tabela *Captação Cliente* do `Dashboard` (§2): mês, ano e o incremento de
  receita que a captação produz, por universo e segmento, ao lado do gráfico
  desse incremento por segmento;
- o fluxo mensal, com seletor entre os três universos;
- o *NET executado* por segmento (§3 do `Dashboard`), mês a mês.

O NET do mês e do ano batem nas três: são a mesma captação, cortada de jeitos
diferentes.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Celula,
    Coluna,
    Linha,
    alternador,
    cartao,
    colunas,
    expandir_todos,
    faixa_kpis,
    fonte,
    grafico,
    kpi,
    linha_detalhe,
    linha_expansivel,
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
            alternador(
                "net-kpis",
                "Universo dos indicadores",
                [(universo["chave"], universo["titulo"], _kpis(ctx, universo)) for universo in universos],
            ),
            secao(
                "Captação cliente — mês e ano",
                # O botão fica fora da grade: dentro da coluna da tabela, ele
                # empurraria a tabela para baixo e o gráfico ao lado ficaria
                # desalinhado dela.
                expandir_todos("net-captacao-cliente"),
                colunas(
                    _tabela_captacao_cliente(ctx),
                    _grafico_incremento(ctx),
                    proporcoes=[3, 2],
                ),
                fonte(
                    "Dashboard §2",
                    ctx.rotulo_mes,
                    "Offshore em R$. Alocação entra só no incremento de receita: o IN/OUT dos "
                    "fundos de alocação não é captação de cliente.",
                ),
            ),
            secao(
                "Fluxo mensal In/Out",
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
                "Detalhe por segmento",
                expandir_todos("net-executado"),
                _tabela_segmentos(ctx),
                fonte("Dashboard §3", ctx.rotulo_mes, "NET executado; offshore em R$ ao câmbio do mês da movimentação."),
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
            "em_reais": off_reais,
            "observacao": "",
        },
    ]


def _kpis(ctx: Contexto, universo: dict[str, Any]) -> str:
    """A faixa de um universo; o seletor acima dela troca entre os três.

    Número negativo sai em vermelho; positivo, não.

    Uma casa decimal: com o sinal, `R$ -426,48 mi` não cabe no cartão e quebra
    linha, e na casa das centenas de milhões o centésimo não muda leitura.
    """
    posicao = universo["meses"].index(ctx.mes_base) if ctx.mes_base in universo["meses"] else None
    series, moeda = universo["series"], universo["moeda"]
    #: Offshore leva o valor em R$ ao lado do US$ — pelo câmbio do mês no mês,
    #: e o `total_reais` da planilha no ano, as mesmas contas do consolidado.
    em_reais = universo.get("em_reais")

    def do_mes(fonte_: dict[str, Any], secao_: str) -> float | None:
        valores = fonte_[secao_]["valores"]
        return valores[posicao] if posicao is not None and posicao < len(valores) else None

    def cartao(rotulo: str, valor: float | None, valor_reais: float | None = None) -> str:
        return kpi(
            rotulo,
            formato.milhoes(valor, 1, moeda=moeda),
            classe_valor="negativo" if valor is not None and valor < 0 else "",
            complemento=formato.milhoes(valor_reais, 1) if em_reais else "",
        )

    def do_mes_cartao(rotulo: str, secao_: str) -> str:
        return cartao(rotulo, do_mes(series, secao_), do_mes(em_reais, secao_) if em_reais else None)

    return faixa_kpis(
        do_mes_cartao("NET do mês", "NET"),
        do_mes_cartao("IN do mês", "IN"),
        do_mes_cartao("OUT do mês", "OUT"),
        cartao("NET no ano", series["NET"]["total"], em_reais["NET"]["total"] if em_reais else None),
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


#: Segmentos da captação cliente, na ordem da planilha. Alocação só aparece no
#: §2, e só com incremento de receita.
SEGMENTOS_CLIENTE = ("mfo", "institucional", "estruturado", "alocacao")
SEGMENTOS_EXECUTADO = ("MFO", "Institucional", "Estruturado")


def _tabela_captacao_cliente(ctx: Contexto) -> str:
    """O §2 do `Dashboard`: Net, e por universo o ingresso e a retirada.

    Ingresso e retirada abrem nos segmentos. Mês e ano já vêm em R$ mi na
    planilha, com o offshore convertido; mês/ano vazios são "—" (a Alocação não
    tem IN/OUT de cliente, só incremento de receita).
    """
    registros = ctx.bloco("captacao", "captacao_cliente")
    colunas_tabela = [
        Coluna("Linha (R$ mi)"),
        Coluna(formato.mes_curto(ctx.mes_base), numerica=True),
        Coluna(ctx.mes_base[:4], numerica=True),
        Coluna("Incr. receita/ano", numerica=True),
        Coluna("ROA incr.", numerica=True),
    ]

    def valor(numero: float | None) -> Any:
        if numero is None:
            return num(formato.NAO_APLICAVEL)
        return num(formato.numero(numero, 1), formato.classe_sinal(numero))

    linhas = []
    alvo = None
    for indice, registro in enumerate(registros):
        celulas = [
            registro["rotulo"],
            valor(registro["mes"]),
            valor(registro["ano"]),
            num(
                formato.numero(registro["incremento_receita_mi_ano"], 2),
                formato.classe_sinal(registro["incremento_receita_mi_ano"]),
            ),
            num(formato.percentual(registro["roa_incremental"]) or formato.NAO_APLICAVEL),
        ]
        nivel = registro["nivel"]
        atributos: dict[str, Any] = {}
        if nivel == 1:
            alvo = f"net-cliente-{indice}"
            atributos = linha_expansivel(alvo)
        elif nivel > 1 and alvo:
            atributos = linha_detalhe(alvo)
        classe = "total" if registro["chave"] == "net" else ("subtotal" if nivel == 0 else "")
        linhas.append(Linha(celulas, classe=classe, nivel=nivel, atributos=atributos))

    return tabela(colunas_tabela, linhas, identificador="net-captacao-cliente", ordenavel=False)


def _grafico_incremento(ctx: Contexto) -> str:
    """Incremento de receita no ano por segmento: ingresso para cima, retirada para baixo.

    Soma onshore e offshore de cada segmento — as linhas do próprio §2. O
    líquido de cada segmento vai no tooltip; a soma dos quatro é o incremento
    da linha Net da tabela ao lado.
    """
    registros = ctx.bloco("captacao", "captacao_cliente")
    rotulos = {registro["chave"]: registro["rotulo"] for registro in registros if registro["nivel"] == 2}
    soma = {movimento: dict.fromkeys(SEGMENTOS_CLIENTE, 0.0) for movimento in ("ingresso", "retirada")}
    for registro in registros:
        if registro["nivel"] == 2 and registro["pai"] in soma and registro["chave"] in SEGMENTOS_CLIENTE:
            soma[registro["pai"]][registro["chave"]] += registro["incremento_receita_mi_ano"] or 0.0

    segmentos = [chave for chave in SEGMENTOS_CLIENTE if chave in rotulos]
    svg = graficos.barras(
        [rotulos[chave] for chave in segmentos],
        [
            graficos.Serie("Ingresso", [soma["ingresso"][chave] for chave in segmentos]),
            graficos.Serie("Retirada", [soma["retirada"][chave] for chave in segmentos], cor=graficos.SERIES[1]),
        ],
        formatador=lambda v: formato.numero(v, 0),
        empilhado=True,
        titulo="Incremento de receita no ano por segmento, em R$ mi/ano",
        altura=300,
        largura=440,
        formatador_dica=lambda v: f"R$ {formato.numero(v, 2)} mi/ano",
        rotulo_total_dica="Líquido",
    )
    return cartao(
        "Incremento de receita no ano (R$ mi/ano)",
        grafico(
            svg,
            itens_legenda=[("Ingresso", graficos.SERIES[0]), ("Retirada", graficos.SERIES[1])],
        ),
    )


def _tabela_segmentos(ctx: Contexto) -> str:
    """NET executado (§3 do `Dashboard`): entradas e saídas por segmento, mês a mês.

    Cada mês abre nos componentes — início no ano, clientes antigos, uso
    pessoal, saída para concorrência. Em R$ mi, como o resto da página.
    """
    bloco = ctx.bloco("captacao", "net_executado")
    colunas_tabela = [Coluna("Mês")]
    for segmento in SEGMENTOS_EXECUTADO:
        colunas_tabela += [
            Coluna(f"{segmento} entrada", numerica=True, separador=True),
            Coluna(f"{segmento} saída", numerica=True),
        ]
    colunas_tabela.append(Coluna("NET (R$ mi)", numerica=True, separador=True))

    linhas = []
    for indice, item in enumerate(bloco["meses"]):
        alvo = f"executado-{indice}"
        linhas.append(
            Linha(
                _celulas_segmento(item),
                classe="destaque",
                atributos=linha_expansivel(alvo) if item["componentes"] else {},
            )
        )
        for componente in item["componentes"]:
            linhas.append(
                Linha(
                    _celulas_segmento(componente, rotulo=componente["rotulo"]),
                    classe="detalhe",
                    nivel=1,
                    atributos=linha_detalhe(alvo),
                )
            )
    if bloco["total"]:
        linhas.append(
            Linha(_celulas_segmento(bloco["total"], rotulo="Total do ano"), classe="total total--maior")
        )

    return tabela(colunas_tabela, linhas, identificador="net-executado", ordenavel=False)


def _celulas_segmento(item: dict[str, Any], rotulo: str | None = None) -> list[Any]:
    def valor(numero: float | None) -> Any:
        return num(formato.em_milhoes(numero, 1), formato.classe_sinal(numero))

    # Sem quebra: "[-] Saída para concorrência" em duas linhas dobrava a altura
    # da sub-linha. A largura da coluna não resolve — a tabela encolhe a coluna.
    celulas: list[Any] = [Celula(rotulo or formato.mes_extenso(item.get("mes")), "sem-quebra")]
    for segmento in SEGMENTOS_EXECUTADO:
        valores = item["segmentos"][segmento]
        celulas += [valor(valores["entrada"]), valor(valores["saida"])]
    celulas.append(valor(item["total"]))
    return celulas
