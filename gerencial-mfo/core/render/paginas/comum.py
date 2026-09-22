"""Peças compartilhadas por abas irmãs.

Só entra aqui o que duas abas usam **do mesmo jeito** — a tabela de portfólios
(onshore e offshore) e o bloco de administrador. Cada aba continua dona da sua
composição; isto evita que uma correção precise ser feita duas vezes em
arquivos gêmeos.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..ui import Coluna, Linha, cartao, colunas, grafico, num, tabela

DIMENSOES_PORTFOLIO = (
    ("portfolio", "Portfólio"),
    ("tipo", "Tipo"),
    ("segmento", "Segmento"),
    ("adm", "Administrador"),
    ("grupo", "Grupo econômico"),
    ("officer", "Officer"),
    ("backup", "Backup"),
    ("regiao", "Região"),
)


def tabela_portfolios(ctx: Contexto, base: dict[str, Any], identificador: str) -> str:
    """Uma linha por portfólio: dimensões, AUM e receita do mês e ROA.

    A série mensal completa fica no JSON; despejar 927 linhas × 8 meses na tela
    contraria o princípio de consolidado no nível zero, detalhe sob demanda.
    """
    moeda = base["moeda"]
    posicao = ctx.posicao(base, ctx.mes_base)
    if posicao is None:
        return ""

    escala = "R$ mi" if moeda == "R$" else "US$ mi"
    colunas = [Coluna(rotulo) for _, rotulo in DIMENSOES_PORTFOLIO] + [
        Coluna(f"AUM ({escala})", numerica=True),
        Coluna(f"Receita ({moeda})", numerica=True),
        Coluna("ROA anual. (%)", numerica=True),
    ]

    linhas = []
    for registro in base["linhas"]:
        aum = registro["aum"][posicao]
        receita = registro["receita"][posicao]
        roa = (receita * 12 / aum) if aum and receita is not None else None

        linhas.append(
            Linha(
                [registro.get(campo) or formato.NAO_APLICAVEL for campo, _ in DIMENSOES_PORTFOLIO]
                + [
                    num(formato.em_milhoes(aum), ordem=aum),
                    num(formato.numero(receita), ordem=receita),
                    num(formato.percentual(roa), ordem=roa),
                ]
            )
        )

    total_aum = base["total"]["aum"][posicao]
    total_receita = base["total"]["receita"][posicao]
    linhas.append(
        Linha(
            ["Total", "", "", "", "", "", "", ""]
            + [
                num(formato.em_milhoes(total_aum)),
                num(formato.numero(total_receita)),
                num(formato.percentual(total_receita * 12 / total_aum if total_aum else None)),
            ],
            classe="total",
        )
    )
    return tabela(colunas, linhas, identificador=identificador, filtravel=True)


def composicao_por_dimensao(
    base: dict[str, Any], campo: str, posicao: int, limite: int = 12
) -> list[tuple[str, float, float]]:
    """Soma AUM e receita do mês por uma dimensão; ranking pelo AUM.

    Entra quem tem AUM ou receita no mês — um veículo zerado de posição mas
    ainda faturando é justamente o que o gráfico de receita precisa mostrar.
    """
    acumulado: dict[str, list[float]] = {}
    for registro in base["linhas"]:
        aum = registro["aum"][posicao] or 0.0
        receita = registro["receita"][posicao] or 0.0
        if not aum and not receita:
            continue
        soma = acumulado.setdefault(registro.get(campo) or "—", [0.0, 0.0])
        soma[0] += aum
        soma[1] += receita
    ranking = sorted(acumulado.items(), key=lambda item: item[1][0], reverse=True)[:limite]
    return [(rotulo, aum, receita) for rotulo, (aum, receita) in ranking]


def par_composicao(
    base: dict[str, Any],
    campo: str,
    posicao: int,
    dimensao: str,
    escalas: tuple[tuple[str, Callable[[float], str]], tuple[str, Callable[[float], str]]],
) -> str:
    """AUM e receita por uma dimensão, lado a lado e na mesma ordem (a do AUM).

    `escalas` traz, para AUM e para receita, o rótulo da escala que vai no
    título do cartão e o formatador que ela exige — a moeda é o que muda entre
    as abas onshore e offshore.
    """
    itens = composicao_por_dimensao(base, campo, posicao)
    if not itens:
        return ""
    rotulos = [rotulo for rotulo, _, _ in itens]

    def desenhar(rotulo: str, valores: list[float], escala: str, formatador) -> str:
        # A dimensão vai no título do cartão: a aba pode empilhar mais de um
        # par, e "AUM (R$ bi)" sozinho não diz qual corte é qual.
        return cartao(
            f"{rotulo} por {dimensao.lower()} ({escala})",
            grafico(
                graficos.barras_horizontais(
                    list(zip(rotulos, valores)),
                    formatador=formatador,
                    titulo=f"{rotulo} por {dimensao.lower()}, em {escala}",
                    largura=560,
                    largura_rotulo=170,
                    altura_linha=18,
                )
            ),
        )

    (escala_aum, formatador_aum), (escala_receita, formatador_receita) = escalas
    return colunas(
        desenhar("AUM", [aum for _, aum, _ in itens], escala_aum, formatador_aum),
        desenhar("Receita", [receita for _, _, receita in itens], escala_receita, formatador_receita),
    )


def bloco_administrador(ctx: Contexto, bloco: dict[str, Any]) -> dict[str, Any] | None:
    """Resumo do administrador no mês, mais o gráfico da série de AUM."""
    posicao = ctx.posicao(bloco, ctx.mes_base)
    if posicao is None:
        return None

    def valor(chave: str) -> float | None:
        serie = ctx.serie(bloco, chave)
        return serie[posicao] if posicao < len(serie) else None

    nome = bloco["administrador"]
    return {
        "nome": nome,
        "agrupamento": bloco.get("agrupamento"),
        "aum": valor("aum"),
        "receita": valor("receita_mens") if ctx.linha(bloco, "receita_mens") else valor("receita"),
        "roa_g5": valor("roa_g5_pct"),
        "custos": valor("custos"),
        "roa_adm": valor("roa_adm_pct"),
        "grafico": graficos.linhas(
            ctx.rotulos(bloco["meses"]),
            [graficos.Serie("AUM", ctx.serie(bloco, "aum"))],
            formatador=lambda v: formato.em_milhoes(v, 0),
            titulo=f"AUM — {nome}",
            altura=180,
            largura=560,
        ),
    }


def agrupamentos_repetidos(resumos: list[dict[str, Any]]) -> list[str]:
    """Marcadores que aparecem em mais de um administrador.

    Nesses casos a geradora repete o AUM e a receita entre os blocos, então a
    soma da coluna **não** é o AUM da casa. Vale dizer isso na cara do leitor.
    """
    contagem: dict[str, int] = {}
    for resumo in resumos:
        marcador = resumo.get("agrupamento")
        if marcador:
            contagem[marcador] = contagem.get(marcador, 0) + 1
    return [marcador for marcador, quantidade in contagem.items() if quantidade > 1]
