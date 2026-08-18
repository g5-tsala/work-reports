"""Aba: NET Executado.

Base `in_out` — **com** as movimentações dos fundos de alocação da G5. É outra
base que a da aba Net In/Out, que é só de cliente. Os dois números convivem no
relatório porque respondem perguntas diferentes; somá-los não responde nenhuma.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    aviso,
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

SEGMENTOS = ("MFO", "Institucional", "Estruturado")


@pagina(
    identificador="captacao-executado",
    titulo="Captação › NET Executado",
    grupo="Captação",
    ordem=40,
    subtitulo="Entradas e saídas executadas por segmento, mês a mês, incluindo os fundos "
    "próprios da G5.",
)
def render(ctx: Contexto) -> str:
    bloco = ctx.bloco("captacao", "net_executado")
    if not bloco["meses"]:
        return ""

    return "".join(
        [
            aviso(
                "Esta página usa a base <strong>com</strong> o grupo G5. A aba "
                "<em>Net In/Out</em> usa a base de cliente, sem o G5 — os totais são "
                "diferentes por construção e não devem ser somados."
            ),
            _kpis(bloco),
            secao("Entradas e saídas por mês", _grafico(ctx, bloco)),
            secao(
                "Detalhe por segmento",
                _tabela(ctx, bloco),
                fonte("Dashboard §3", ctx.rotulo_mes, "Base in_out, com o grupo G5."),
            ),
        ]
    )


def _kpis(bloco: dict[str, Any]) -> str:
    ultimo = bloco["meses"][-1]
    total = bloco["total"] or {}
    entradas = sum((total.get("segmentos", {}).get(s, {}).get("entrada") or 0) for s in SEGMENTOS)
    saidas = sum((total.get("segmentos", {}).get(s, {}).get("saida") or 0) for s in SEGMENTOS)

    return faixa_kpis(
        kpi(
            "NET do mês",
            formato.milhoes(ultimo["total"]),
            classe_delta=formato.classe_sinal(ultimo["total"]),
            detalhe=formato.mes_extenso(ultimo["mes"]),
        ),
        kpi("Entradas no ano", formato.milhoes(entradas)),
        kpi("Saídas no ano", formato.milhoes(saidas)),
        kpi(
            "NET no ano",
            formato.milhoes(total.get("total")),
            classe_delta=formato.classe_sinal(total.get("total")),
        ),
    )


def _grafico(ctx: Contexto, bloco: dict[str, Any]) -> str:
    meses = [item["mes"] for item in bloco["meses"]]
    entradas = [
        sum((item["segmentos"][s]["entrada"] or 0) for s in SEGMENTOS) for item in bloco["meses"]
    ]
    saidas = [sum((item["segmentos"][s]["saida"] or 0) for s in SEGMENTOS) for item in bloco["meses"]]
    liquido = [item["total"] for item in bloco["meses"]]

    svg = graficos.combo(
        ctx.rotulos(meses),
        [
            graficos.Serie("Entradas", entradas),
            graficos.Serie("Saídas", saidas, cor=graficos.SERIES[1]),
        ],
        graficos.Serie("NET", liquido, cor=graficos.SERIES[2]),
        formatador_barra=lambda v: formato.em_milhoes(v, 0),
        formatador_linha=lambda v: formato.em_milhoes(v, 0),
        titulo="NET executado por mês",
        empilhado=True,
        rotular_ultimo=True,
    )
    return grafico(
        svg,
        itens_legenda=[
            ("Entradas (R$ mi)", graficos.SERIES[0]),
            ("Saídas (R$ mi)", graficos.SERIES[1]),
            ("NET (R$ mi, linha)", graficos.SERIES[2]),
        ],
        rodape=fonte("Dashboard §3", ctx.rotulo_mes),
    )


def _tabela(ctx: Contexto, bloco: dict[str, Any]) -> str:
    colunas = [Coluna("Mês")]
    for segmento in SEGMENTOS:
        colunas += [Coluna(f"{segmento} entrada (R$)", numerica=True), Coluna(f"{segmento} saída (R$)", numerica=True)]
    colunas.append(Coluna("Total (R$)", numerica=True))

    linhas = []
    for indice, item in enumerate(bloco["meses"]):
        alvo = f"executado-{indice}"
        linhas.append(
            Linha(
                _celulas(item),
                atributos=linha_expansivel(alvo) if item["componentes"] else {},
            )
        )
        for componente in item["componentes"]:
            linhas.append(
                Linha(
                    _celulas(componente, rotulo=componente["rotulo"]),
                    classe="detalhe",
                    nivel=1,
                    atributos=linha_detalhe(alvo),
                )
            )
    if bloco["total"]:
        linhas.append(Linha(_celulas(bloco["total"], rotulo="Total do ano"), classe="total"))

    return tabela(colunas, linhas, identificador="net-executado", ordenavel=False)


def _celulas(item: dict[str, Any], rotulo: str | None = None) -> list[Any]:
    celulas: list[Any] = [rotulo or formato.mes_extenso(item.get("mes"))]
    for segmento in SEGMENTOS:
        valores = item["segmentos"][segmento]
        celulas.append(num(formato.numero(valores["entrada"], 0)))
        celulas.append(num(formato.numero(valores["saida"], 0), formato.classe_sinal(valores["saida"])))
    celulas.append(num(formato.numero(item["total"], 0), formato.classe_sinal(item["total"])))
    return celulas
