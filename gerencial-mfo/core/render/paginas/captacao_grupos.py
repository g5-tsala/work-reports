"""Aba: Captação por Grupo.

Visão canônica do drill-down: YTD por grupo econômico no nível zero e, ao
clicar, a movimentação mês a mês daquela linha.

Uma linha do YTD não é um grupo: é a combinação grupo + officer + lead externo
+ lead G5 + segmento, e o mesmo grupo aparece em mais de uma linha quando muda
qualquer um deles. O mês a mês casa pela combinação inteira — casando só pelo
grupo, duas linhas do mesmo grupo abriam o mesmo detalhe, somando os dois.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
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

#: Quantos grupos de cada lado no gráfico: os maiores NETs positivos e os
#: maiores negativos.
MAIORES_POR_SINAL = 6
COR_POSITIVO = graficos.SERIES[0]
COR_NEGATIVO = graficos.SERIES[1]

#: Campos que identificam uma linha do YTD e casam com o mês a mês.
CHAVE = ("grupo", "officer", "lead_externo", "lead_g5", "segmento")


@pagina(
    identificador="captacao-grupos",
    titulo="Captação › Grupos",
    grupo="Captação",
    ordem=20,
    subtitulo="Quem captou e quem sacou no ano. Clique em um grupo para ver a movimentação "
    "mês a mês.",
)
def render(ctx: Contexto) -> str:
    ytd = ctx.bloco("captacao", "grupos", "ytd")
    mensal = ctx.bloco("captacao", "grupos", "mensal")

    return "".join(
        [
            _kpis(ytd),
            secao("Maiores movimentações do ano", _barras(ctx, ytd)),
            secao(
                "Por grupo econômico (YTD)",
                _tabela(ctx, ytd, mensal),
                fonte("io_grupos", ctx.rotulo_mes, "Onshore + offshore, em R$, sem o grupo G5."),
                nota(
                    "O valor YTD é a soma das movimentações do ano. Um grupo pode aparecer com "
                    "NET positivo e ainda assim ter sacado em algum mês — o detalhe abre na linha."
                ),
            ),
        ]
    )


def _kpis(ytd: list[dict[str, Any]]) -> str:
    entradas = sum(registro["valor"] for registro in ytd if (registro["valor"] or 0) > 0)
    saidas = sum(registro["valor"] for registro in ytd if (registro["valor"] or 0) < 0)
    liquido = entradas + saidas

    def vermelho_se_negativo(valor: float) -> str:
        return "negativo" if valor < 0 else ""

    return faixa_kpis(
        kpi("Grupos com movimentação", formato.inteiro(len({registro["grupo"] for registro in ytd}))),
        kpi("Entradas no ano", formato.milhoes(entradas)),
        kpi("Saídas no ano", formato.milhoes(saidas), classe_valor=vermelho_se_negativo(saidas)),
        kpi("NET no ano", formato.milhoes(liquido), classe_valor=vermelho_se_negativo(liquido)),
        compacta=True,
    )


def _barras(ctx: Contexto, ytd: list[dict[str, Any]]) -> str:
    """Os maiores NETs do ano de cada lado: positivos primeiro, negativos no fim.

    Aqui a unidade é o grupo, não a linha do YTD — o gráfico responde "quem
    captou e quem sacou", e o mesmo grupo repartido entre leads apareceria
    duas vezes. A ordem é decrescente do começo ao fim: do maior positivo ao
    negativo mais fundo. A barra mede a magnitude; o sinal está no rótulo e na
    cor.
    """
    por_grupo: dict[str, float] = defaultdict(float)
    for registro in ytd:
        por_grupo[registro["grupo"]] += registro["valor"] or 0.0
    positivos = sorted((item for item in por_grupo.items() if item[1] > 0), key=lambda i: i[1], reverse=True)
    negativos = sorted((item for item in por_grupo.items() if item[1] < 0), key=lambda i: i[1])
    itens = positivos[:MAIORES_POR_SINAL] + sorted(negativos[:MAIORES_POR_SINAL], key=lambda i: i[1], reverse=True)
    return grafico(
        graficos.barras_horizontais(
            itens,
            formatador=lambda v: formato.em_milhoes(v, 1),
            titulo="Maiores NETs do ano, positivos e negativos, em R$ mi",
            largura_rotulo=380,
            altura_linha=18,
            cores=[COR_POSITIVO if valor > 0 else COR_NEGATIVO for _, valor in itens],
        ),
        itens_legenda=[("NET positivo (R$ mi)", COR_POSITIVO), ("NET negativo (R$ mi)", COR_NEGATIVO)],
        rodape=fonte(
            "io_grupos",
            ctx.rotulo_mes,
            f"Acumulado do ano até o mês-base. Os {MAIORES_POR_SINAL} maiores de cada sinal, por grupo.",
        ),
    )


def _tabela(ctx: Contexto, ytd: list[dict[str, Any]], mensal: list[dict[str, Any]]) -> str:
    por_chave: dict[tuple, list[dict[str, Any]]] = defaultdict(list)
    for movimento in mensal:
        por_chave[tuple(movimento[campo] for campo in CHAVE)].append(movimento)

    colunas = [
        Coluna("Grupo econômico"),
        Coluna("Officer"),
        Coluna("Segmento"),
        Coluna("Lead externo"),
        Coluna("Lead G5"),
        Coluna("NET no ano (R$)", numerica=True),
    ]

    linhas = []
    for indice, registro in enumerate(sorted(ytd, key=lambda r: r["valor"] or 0, reverse=True)):
        alvo = f"grupo-{indice}"
        chave = tuple(registro[campo] for campo in CHAVE)
        movimentos = sorted(por_chave.get(chave, []), key=lambda m: m["mes"] or "")
        celulas = [
            registro["grupo"],
            registro["officer"] or formato.NAO_APLICAVEL,
            registro["segmento"] or formato.NAO_APLICAVEL,
            registro["lead_externo"] or formato.NAO_APLICAVEL,
            registro["lead_g5"] or formato.NAO_APLICAVEL,
            num(
                formato.numero(registro["valor"], 0),
                formato.classe_sinal(registro["valor"]),
                ordem=registro["valor"],
            ),
        ]
        if movimentos:
            linhas.append(Linha(celulas, atributos=linha_expansivel(alvo)))
            for movimento in movimentos:
                linhas.append(
                    Linha(
                        # Officer, segmento e leads são os da linha-pai — é
                        # por eles que o mês a mês casou —, então ficam vazios.
                        [
                            formato.mes_extenso(movimento["mes"]),
                            "",
                            "",
                            "",
                            "",
                            num(
                                formato.numero(movimento["valor"], 0),
                                formato.classe_sinal(movimento["valor"]),
                            ),
                        ],
                        classe="detalhe",
                        nivel=1,
                        atributos=linha_detalhe(alvo),
                    )
                )
        else:
            linhas.append(Linha(celulas))

    return tabela(colunas, linhas, identificador="captacao-grupos", filtravel=True)
