"""Aba: Regiões.

Distribuição geográfica do AUM. Única fonte do corte é a aba oculta `regiao`,
que já traz onshore, offshore e o consolidado somados um a um.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, fonte, grafico, nota, num, secao, tabela

BLOCOS = (
    ("consolidado", "Consolidado (R$)", True),
    ("onshore", "Onshore (R$)", False),
    ("offshore", "Offshore (R$)", False),
)


@pagina(
    identificador="regioes",
    titulo="Regiões",
    grupo="Carteira",
    ordem=30,
    subtitulo="Onde estão os clientes: AUM, receita e quantidade de grupos por região.",
)
def render(ctx: Contexto) -> str:
    regioes = ctx.bloco("carteira", "regioes")
    consolidado = regioes["consolidado"]

    partes = [secao("Distribuição do AUM", _barras(ctx, consolidado))]
    for chave, titulo, com_grupos in BLOCOS:
        partes.append(
            secao(
                titulo,
                _tabela(ctx, regioes[chave], chave, com_grupos),
                fonte("regiao", ctx.rotulo_mes),
            )
        )
    partes.append(
        nota(
            "A linha <strong>—</strong> reúne portfólios sem região atribuída, incluindo os "
            "fundos de alocação. Ela entra no total."
        )
    )
    return "".join(partes)


def _barras(ctx: Contexto, bloco: dict[str, Any]) -> str:
    itens = sorted(
        ((linha["regiao"], linha["aum"]) for linha in bloco["linhas"] if linha["aum"]),
        key=lambda item: item[1],
        reverse=True,
    )
    return grafico(
        graficos.barras_horizontais(
            itens,
            formatador=lambda v: formato.em_bilhoes(v, 2),
            titulo="AUM consolidado por região",
            largura_rotulo=280,
        ),
        itens_legenda=[("AUM (R$ bi)", graficos.SERIES[0])],
        rodape=fonte("regiao", ctx.rotulo_mes, "Offshore convertido ao câmbio do mês."),
    )


def _tabela(ctx: Contexto, bloco: dict[str, Any], identificador: str, com_grupos: bool) -> str:
    colunas = [
        Coluna("Região"),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("% AUM", numerica=True),
        Coluna("Receita (R$)", numerica=True),
        Coluna("ROA anual. (%)", numerica=True),
    ]
    if com_grupos:
        colunas.append(Coluna("Qtd. grupos", numerica=True))

    linhas = []
    for registro in bloco["linhas"]:
        aum, receita = registro["aum"], registro["receita"]
        roa = (receita * 12 / aum) if aum and receita is not None else None
        celulas = [
            registro["regiao"],
            num(formato.em_milhoes(aum), ordem=aum),
            num(formato.percentual(registro["pct_aum"]), ordem=registro["pct_aum"]),
            num(formato.numero(receita, 0), ordem=receita),
            num(formato.percentual(roa), ordem=roa),
        ]
        if com_grupos:
            celulas.append(num(formato.inteiro(registro.get("qtd_grupos")), ordem=registro.get("qtd_grupos")))
        linhas.append(Linha(celulas, classe="destaque" if registro.get("sem_regiao") else ""))

    total = bloco["total"]
    if total:
        celulas = [
            "Total",
            num(formato.em_milhoes(total["aum"])),
            num(formato.percentual(1.0)),
            num(formato.numero(total["receita"], 0)),
            num(
                formato.percentual(
                    total["receita"] * 12 / total["aum"] if total["aum"] and total["receita"] else None
                )
            ),
        ]
        if com_grupos:
            celulas.append(num(formato.inteiro(sum(l.get("qtd_grupos") or 0 for l in bloco["linhas"]))))
        linhas.append(Linha(celulas, classe="total"))

    return tabela(colunas, linhas, identificador=f"regioes-{identificador}")
