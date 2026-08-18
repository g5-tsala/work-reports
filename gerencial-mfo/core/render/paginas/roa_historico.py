"""Aba: ROA Histórico.

Os dez blocos empilhados da aba `roa_historico`: cinco por categoria de veículo
e cinco por faixa de PL do grupo — quantidade, AUM, receita anualizada, ROA e
participação, cada um com a série inteira desde 2018.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, fonte, grafico, num, secao, tabela

#: Como formatar cada bloco, pela chave do título.
FORMATADORES = {
    "qtd_veiculos": formato.inteiro,
    "qtd_grupos": formato.inteiro,
    "aum_rs": formato.em_milhoes,
    "receita_anualizada_rs": lambda v: formato.numero(v, 0),
    "roa_pct": formato.percentual,
    "aum_pct": formato.percentual,
}
ESCALAS = {"aum_rs": " (R$ mi)", "receita_anualizada_rs": " (R$)"}
BLOCO_DO_GRAFICO = "roa_pct"
SERIES_NO_GRAFICO = 5


@pagina(
    identificador="roa-historico",
    titulo="ROA Histórico",
    grupo="Performance",
    ordem=20,
    subtitulo="Quantidade, AUM, receita anualizada e ROA por categoria e por faixa de PL, "
    "com a série completa desde 2018.",
)
def render(ctx: Contexto) -> str:
    blocos = ctx.bloco("historico", "roa_historico")
    partes = []
    for dimensao, titulo in (("categoria", "Por categoria de veículo"), ("grupo", "Por faixa de PL do grupo")):
        do_grupo = [bloco for bloco in blocos if bloco["dimensao"] == dimensao]
        conteudo = [_grafico(ctx, do_grupo, dimensao)] + [_tabela(ctx, bloco, dimensao) for bloco in do_grupo]
        partes.append(secao(titulo, *conteudo))
    return "".join(partes)


def _grafico(ctx: Contexto, blocos: list[dict[str, Any]], dimensao: str) -> str:
    bloco = next((item for item in blocos if item["chave"] == BLOCO_DO_GRAFICO), None)
    if not bloco:
        return ""

    #: Cinco séries é o teto do design system — escolhidas pelo AUM atual.
    referencia = next((item for item in blocos if item["chave"] == "aum_rs"), bloco)
    maiores = sorted(
        referencia["linhas"],
        key=lambda linha: (linha["valores"][-1] or 0) if linha["valores"] else 0,
        reverse=True,
    )[:SERIES_NO_GRAFICO]

    series = []
    for escolhida in maiores:
        linha = ctx.linha(bloco, escolhida["chave"])
        if linha:
            series.append(graficos.Serie(linha["rotulo"], linha["valores"]))

    return grafico(
        graficos.linhas(
            ctx.rotulos(bloco["meses"]),
            series,
            formatador=formato.percentual,
            titulo=f"ROA por {dimensao}",
        ),
        itens_legenda=[(serie.rotulo, graficos.SERIES[i]) for i, serie in enumerate(series)],
        rodape=fonte("roa_historico", ctx.rotulo_mes, f"Cinco maiores por AUM no mês-base ({dimensao})."),
    )


def _tabela(ctx: Contexto, bloco: dict[str, Any], dimensao: str) -> str:
    formatador = FORMATADORES.get(bloco["chave"], formato.numero)
    rotulo_dimensao = "Categoria" if dimensao == "categoria" else "Faixa"
    colunas = [Coluna(f"{rotulo_dimensao}{ESCALAS.get(bloco['chave'], '')}")] + [
        Coluna(rotulo, numerica=True) for rotulo in ctx.rotulos(bloco["meses"])
    ]

    linhas = [
        Linha([registro["rotulo"]] + [num(formatador(valor)) for valor in registro["valores"]])
        for registro in bloco["linhas"]
    ]
    if bloco["total"]:
        linhas.append(
            Linha(
                [bloco["total"]["rotulo"]] + [num(formatador(valor)) for valor in bloco["total"]["valores"]],
                classe="total",
            )
        )

    identificador = f"roa-hist-{dimensao}-{bloco['chave']}"
    return "".join(
        [
            f'<h3 class="g5-cartao-titulo">{bloco["titulo"]}</h3>',
            tabela(colunas, linhas, identificador=identificador, ordenavel=False),
            fonte("roa_historico", ctx.rotulo_mes),
        ]
    )
