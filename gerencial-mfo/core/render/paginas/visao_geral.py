"""Aba: Visão Geral.

Os quatro indicadores principais na ordem fechada com o negócio — AUM, Run
Rate, Projeção Ano, ROA — o split onshore/offshore e o ranking de officers.
"""

from __future__ import annotations

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, esc, faixa_kpis, fonte, grafico, kpi, num, secao, tabela

ORIGENS = (("Onshore", "onshore"), ("Offshore", "offshore"), ("Total", "total"))


@pagina(
    identificador="visao-geral",
    titulo="Visão Geral",
    grupo="Visão Executiva",
    ordem=10,
    subtitulo="Fechamento do mês: posição consolidada, evolução no ano e ranking por officer.",
)
def render(ctx: Contexto) -> str:
    return "".join(
        [
            _kpis(ctx),
            secao("Onshore e offshore", _split(ctx), fonte("resumo", ctx.rotulo_mes)),
            secao(
                "Evolução no ano",
                _evolucao(ctx),
                descricao="O que se moveu no ano: variação mensal do AUM e a receita "
                "mensalizada que ela produz.",
            ),
            secao(
                "Ranking por officer",
                _ranking(ctx),
                fonte("CEO-Dashboard", ctx.rotulo_mes),
                _nota_rodape(ctx),
            ),
        ]
    )


def _kpis(ctx: Contexto) -> str:
    cartao = ctx.bloco("consolidado", "kpis_ceo")["cartoes"]["total"]
    consolidado = ctx.bloco("consolidado")
    projecao = consolidado["projecao_ano"]["total"]
    receita_ano = consolidado["receita_ano_competencia"]["total"]

    return faixa_kpis(
        kpi(
            "AUM",
            formato.bilhoes(consolidado["aum"]["total"]),
            delta=f"{formato.variacao(cartao['aum_var_pct'])} · {formato.com_sinal(cartao['aum_var_bi'], formato.numero, casas=2)} bi",
            classe_delta=formato.classe_sinal(cartao["aum_var_pct"]),
            detalhe=f"vs. {formato.mes_curto(ctx.mes_anterior)}",
        ),
        kpi(
            "Run Rate",
            formato.milhoes(consolidado["run_rate"]["total"]),
            delta=f"{formato.variacao(cartao['run_rate_var_pct'])} · {formato.com_sinal(cartao['run_rate_var_mi'], formato.numero, casas=2)} mi",
            classe_delta=formato.classe_sinal(cartao["run_rate_var_pct"]),
            detalhe="receita mensalizada × 12",
        ),
        kpi(
            "Projeção Ano",
            formato.milhoes(projecao),
            detalhe=f"{formato.milhoes(receita_ano)} realizados por competência",
        ),
        kpi(
            "ROA",
            formato.percentual(consolidado["roa"]["total"]),
            detalhe="receita anualizada ÷ AUM",
        ),
    )


def _split(ctx: Contexto) -> str:
    consolidado = ctx.bloco("consolidado")
    cartoes = ctx.bloco("consolidado", "kpis_ceo")["cartoes"]

    colunas = [
        Coluna("Origem"),
        Coluna("AUM (R$ bi)", numerica=True),
        Coluna("Δ AUM M-1", numerica=True),
        Coluna("Receita mens. (R$ mi)", numerica=True),
        Coluna("Run Rate (R$ mi)", numerica=True),
        Coluna("Projeção ano (R$ mi)", numerica=True),
        Coluna("ROA (%)", numerica=True),
    ]

    linhas = []
    for rotulo, chave in ORIGENS:
        variacao = cartoes[chave]["aum_var_pct"]
        linhas.append(
            Linha(
                [
                    rotulo,
                    num(formato.em_bilhoes(consolidado["aum"][chave])),
                    num(formato.variacao(variacao), formato.classe_sinal(variacao)),
                    num(formato.em_milhoes(consolidado["receita_mens"][chave])),
                    num(formato.em_milhoes(consolidado["run_rate"][chave])),
                    num(formato.em_milhoes(consolidado["projecao_ano"][chave])),
                    num(formato.percentual(consolidado["roa"][chave])),
                ],
                classe="total" if chave == "total" else "",
            )
        )
    return tabela(colunas, linhas, ordenavel=False, rolagem=False)


def _evolucao(ctx: Contexto) -> str:
    onshore = ctx.bloco("historico", "aum_receita", "onshore")
    offshore = ctx.bloco("historico", "aum_receita", "offshore")
    ano = ctx.mes_base[:4]

    indices = [i for i, mes in enumerate(onshore["meses"]) if mes.startswith(ano)]
    meses = [onshore["meses"][i] for i in indices]

    def recortar(bloco, chave, pai=None):
        serie = ctx.serie(bloco, chave, pai)
        posicoes = [bloco["meses"].index(mes) if mes in bloco["meses"] else None for mes in meses]
        return [serie[p] if p is not None and p < len(serie) else None for p in posicoes]

    aum_onshore = recortar(onshore, "aum_rs")
    aum_offshore = recortar(offshore, "aum_rs")
    aum_total = [
        (a or 0) + (b or 0) if a is not None or b is not None else None
        for a, b in zip(aum_onshore, aum_offshore)
    ]
    receita = [
        (a or 0) + (b or 0) if a is not None or b is not None else None
        for a, b in zip(recortar(onshore, "receita_mens_rs"), recortar(offshore, "receita_rs"))
    ]

    # O AUM anda pouco de um mês para o outro: plotado como barra desde o zero,
    # vira uma fileira de barras idênticas que não conta nada. Quem se move é a
    # variação — ela vai nas barras, ancoradas no zero e coloridas pelo sinal, e
    # o nível fica na linha, com o valor rotulado no último ponto.
    variacao = [
        None if anterior is None or atual is None else atual - anterior
        for anterior, atual in zip([None, *aum_total], aum_total)
    ]

    # O nível do AUM já está no KPI e na tabela acima; repeti-lo numa linha aqui
    # custaria um segundo eixo em R$ bi contra outro eixo em R$ bi — a mesma
    # grandeza medindo duas alturas no mesmo desenho. Fica só o movimento.
    return "".join(
        [
            grafico(
                graficos.barras(
                    ctx.rotulos(meses),
                    [graficos.Serie("Δ AUM no mês", variacao)],
                    formatador=lambda v: formato.em_bilhoes(v, 1),
                    titulo="Variação mensal do AUM em 2026",
                    altura=240,
                    por_sinal=True,
                ),
                itens_legenda=[
                    ("Mês de entrada (R$ bi)", graficos.COR_POSITIVO),
                    ("Mês de saída (R$ bi)", graficos.COR_NEGATIVO),
                ],
                rodape=fonte(
                    "aum_receita", ctx.rotulo_mes, "Offshore convertido pelo câmbio de cada mês."
                ),
            ),
            grafico(
                graficos.linhas(
                    ctx.rotulos(meses),
                    [graficos.Serie("Receita mensalizada", receita, cor=graficos.SERIES[1])],
                    formatador=lambda v: formato.em_milhoes(v, 1),
                    titulo="Receita mensalizada em 2026",
                    altura=200,
                    rotular_ultimo=True,
                ),
                itens_legenda=[("Receita mensalizada (R$ mi)", graficos.SERIES[1])],
                rodape=fonte("aum_receita", ctx.rotulo_mes, "Onshore mensalizada + offshore por competência."),
            ),
        ]
    )


def _ranking(ctx: Contexto) -> str:
    tabela_ceo = ctx.bloco("officers", "tabela_ceo")
    # Ordem da planilha, sem reordenar: alfabética, com quem saiu e os Fdos
    # Alocação no pé. Quem quer o ranking por AUM clica no cabeçalho da coluna —
    # a ordenação continua lendo o valor cru. Ordenar por AUM na entrega
    # tornava a tabela impossível de conferir contra a CEO-Dashboard linha a
    # linha, que é o uso dela no fechamento.
    carteiras = [linha for linha in tabela_ceo if linha["tipo"] in ("officer", "fdos_alocacao")]
    total = next((linha for linha in tabela_ceo if linha["tipo"] == "total"), None)

    colunas = [
        Coluna("Officer"),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("Δ AUM M-1 (%)", numerica=True),
        Coluna("% AUM", numerica=True),
        Coluna("Receita (R$)", numerica=True),
        Coluna("Δ Receita M-1 (%)", numerica=True),
        Coluna("% Receita", numerica=True),
        Coluna("ROA (%)", numerica=True),
        Coluna("Qtd. portf.", numerica=True),
    ]

    def delta(registro, campo: str):
        """Variação M-1 com uma casa: aqui ela é leitura de ordem de grandeza.

        Duas casas num ranking de vinte linhas viram vinte números de cinco
        dígitos que ninguém compara — quem quiser a precisão abre a aba
        Officers, que traz a mesma variação ao lado da série que a produziu.
        """
        valor = registro[campo]
        return num(formato.variacao(valor, 1), formato.classe_sinal(valor), ordem=valor)

    linhas = [
        Linha(
            [
                f"{registro['nome']} *" if registro.get("marcado") else registro["nome"],
                num(formato.numero(registro["aum_mi"]), ordem=registro["aum_mi"]),
                delta(registro, "aum_var_pct"),
                num(formato.percentual(registro["pct_aum"]), ordem=registro["pct_aum"]),
                num(formato.numero(registro["receita"], 0), ordem=registro["receita"]),
                delta(registro, "receita_var_pct"),
                num(formato.percentual(registro["pct_receita"]), ordem=registro["pct_receita"]),
                num(formato.percentual(registro["roa"]), ordem=registro["roa"]),
                num(formato.inteiro(registro["qtd_portfolios"]), ordem=registro["qtd_portfolios"]),
            ],
            classe=" ".join(
                filter(
                    None,
                    (
                        "destaque" if registro["tipo"] == "fdos_alocacao" else "",
                        "marcada" if registro.get("marcado") else "",
                    ),
                )
            ),
        )
        for registro in carteiras
    ]
    if total:
        linhas.append(
            Linha(
                [
                    "Total",
                    num(formato.numero(total["aum_mi"])),
                    delta(total, "aum_var_pct"),
                    num(formato.percentual(total["pct_aum"])),
                    num(formato.numero(total["receita"], 0)),
                    delta(total, "receita_var_pct"),
                    num(formato.percentual(total["pct_receita"])),
                    num(formato.percentual(ctx.bloco("consolidado", "roa")["total"])),
                    num(formato.inteiro(total["qtd_portfolios"])),
                ],
                classe="total",
            )
        )
    return tabela(colunas, linhas, identificador="ranking-officers")


def _nota_rodape(ctx: Contexto) -> str:
    """A nota que explica o asterisco — na mesma cor das linhas que ele marca.

    O texto sai da própria planilha, não é nosso. Sem officer marcado no mês, a
    nota não tem o que explicar e some.
    """
    marcados = any(
        linha.get("marcado") for linha in ctx.bloco("officers", "tabela_ceo")
    )
    if not marcados:
        return ""
    notas = ctx.bloco("consolidado", "notas")
    rodape = next((texto for texto in notas if texto.startswith("*")), "")
    if not rodape:
        return ""
    return f'<p class="g5-nota g5-nota--marcada">{esc(rodape)}</p>'
