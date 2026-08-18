"""Peças compartilhadas por abas irmãs.

Só entra aqui o que duas abas usam **do mesmo jeito** — a tabela de portfólios
(onshore e offshore) e o bloco de administrador. Cada aba continua dona da sua
composição; isto evita que uma correção precise ser feita duas vezes em
arquivos gêmeos.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..ui import Coluna, Linha, num, tabela

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
    """Uma linha por portfólio: dimensões, AUM e receita do mês, ROA e Δ M-1.

    A série mensal completa fica no JSON; despejar 927 linhas × 8 meses na tela
    contraria o princípio de consolidado no nível zero, detalhe sob demanda.
    """
    moeda = base["moeda"]
    posicao = ctx.posicao(base, ctx.mes_base)
    anterior = ctx.posicao(base, ctx.mes_anterior)
    if posicao is None:
        return ""

    escala = "R$ mi" if moeda == "R$" else "US$ mi"
    colunas = [Coluna(rotulo) for _, rotulo in DIMENSOES_PORTFOLIO] + [
        Coluna(f"AUM ({escala})", numerica=True),
        Coluna("Δ AUM M-1", numerica=True),
        Coluna(f"Receita ({moeda})", numerica=True),
        Coluna("ROA anual. (%)", numerica=True),
    ]

    linhas = []
    for registro in base["linhas"]:
        aum = registro["aum"][posicao]
        receita = registro["receita"][posicao]
        aum_anterior = registro["aum"][anterior] if anterior is not None else None
        variacao = ctx.variacao(aum, aum_anterior)
        roa = (receita * 12 / aum) if aum and receita is not None else None

        linhas.append(
            Linha(
                [registro.get(campo) or formato.NAO_APLICAVEL for campo, _ in DIMENSOES_PORTFOLIO]
                + [
                    num(formato.em_milhoes(aum), ordem=aum),
                    num(formato.variacao(variacao), formato.classe_sinal(variacao), ordem=variacao),
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
                formato.NAO_APLICAVEL,
                num(formato.numero(total_receita)),
                num(formato.percentual(total_receita * 12 / total_aum if total_aum else None)),
            ],
            classe="total",
        )
    )
    return tabela(colunas, linhas, identificador=identificador, filtravel=True)


def composicao_por_dimensao(base: dict[str, Any], campo: str, posicao: int, limite: int = 12):
    """Soma o AUM do mês por uma dimensão e devolve o ranking."""
    acumulado: dict[str, float] = {}
    for registro in base["linhas"]:
        valor = registro["aum"][posicao]
        if not valor:
            continue
        acumulado[registro.get(campo) or "—"] = acumulado.get(registro.get(campo) or "—", 0) + valor
    return sorted(acumulado.items(), key=lambda item: item[1], reverse=True)[:limite]


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
