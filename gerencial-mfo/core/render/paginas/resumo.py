"""Aba: Resumo.

ROA por categoria de veículo e por faixa de PL do grupo econômico — as duas
leituras que a aba `resumo` da planilha entrega prontas.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    cartao,
    colunas,
    faixa_kpis,
    fonte,
    grafico,
    kpi,
    legenda,
    num,
    secao,
    tabela,
)

#: Família de produto -> cor. O rótulo da planilha traz a faixa de PL colada na
#: família (`Carteira R$ 10-25 mi`), então a família sai do prefixo — e não do
#: campo `tipo`, que vem com o câmbio no lugar do nome na linha de Offshore.
#: `Fundo` cobre `Fundo / Previdência`; `Alocação`, `Alocação / Previdência`.
CORES_CATEGORIA = {
    "Carteira": graficos.SERIES[0],
    "Fundo": graficos.SERIES[1],
    "Estruturado": graficos.SERIES[2],
    "Alocação": graficos.SERIES[3],
    "Offshore": graficos.SERIES[4],
}
COR_G5 = graficos.SERIES[1]
COR_FAIXA = graficos.SERIES[0]
ROTULO_G5 = "G5"


@pagina(
    identificador="resumo",
    titulo="Resumo",
    grupo="Visão Executiva",
    ordem=20,
)
def render(ctx: Contexto) -> str:
    categoria = ctx.bloco("consolidado", "roa_categoria")
    grupo = ctx.bloco("consolidado", "roa_grupo")

    return "".join(
        [
            _kpis(ctx, categoria, grupo),
            secao(
                "Por categoria e faixa de PL",
                _tabela_faixas(categoria, "Categoria", "categoria", "roa-categoria"),
                fonte("resumo", ctx.rotulo_mes, "Receita anualizada."),
                _par_de_barras(categoria, "categoria", _cores_categoria, _legenda_categoria),
            ),
            secao(
                "Por grupo econômico e faixa de PL",
                _tabela_faixas(grupo, "Faixa", "faixa", "roa-grupo"),
                fonte("resumo", ctx.rotulo_mes, "Faixas excluem o grupo G5, isolado na própria linha."),
                _par_de_barras(grupo, "faixa", _cores_grupo, _legenda_grupo),
            ),
        ]
    )


def _kpis(ctx: Contexto, categoria: dict[str, Any], grupo: dict[str, Any]) -> str:
    total_categoria = categoria["total"]
    total_grupo = grupo["total"]

    return faixa_kpis(
        kpi("Veículos", formato.inteiro(total_categoria["qtd"])),
        kpi("Grupos econômicos", formato.inteiro(total_grupo["qtd"])),
        kpi("AUM", formato.bilhoes(total_categoria["aum"])),
        kpi("ROA médio", formato.percentual(total_categoria["roa"])),
    )


def _tabela_faixas(bloco: dict[str, Any], rotulo: str, campo: str, identificador: str) -> str:
    colunas = [
        Coluna(rotulo),
        Coluna("Qtd.", numerica=True),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("% AUM", numerica=True),
        Coluna("Receita anual. (R$)", numerica=True),
        Coluna("ROA (%)", numerica=True),
    ]
    linhas = [
        Linha(
            [
                registro[campo],
                num(formato.inteiro(registro["qtd"]), ordem=registro["qtd"]),
                num(formato.em_milhoes(registro["aum"]), ordem=registro["aum"]),
                num(formato.percentual(registro["pct_aum"]), ordem=registro["pct_aum"]),
                num(formato.numero(registro["receita_anualizada"], 0), ordem=registro["receita_anualizada"]),
                num(formato.percentual(registro["roa"]), ordem=registro["roa"]),
            ]
        )
        for registro in bloco["linhas"]
    ]
    total = bloco["total"]
    linhas.append(
        Linha(
            [
                "Total",
                num(formato.inteiro(total["qtd"])),
                num(formato.em_milhoes(total["aum"])),
                num(formato.percentual(total["pct_aum"])),
                num(formato.numero(total["receita_anualizada"], 0)),
                num(formato.percentual(total["roa"])),
            ],
            classe="total",
        )
    )
    return tabela(colunas, linhas, identificador=identificador)


def _familia(rotulo: str) -> str | None:
    return next((nome for nome in CORES_CATEGORIA if rotulo.startswith(nome)), None)


#: Fora das cinco famílias: cinza de interface, e não o neutro da paleta de
#: dados, que já é a cor do Estruturado. Sem categoria não é uma categoria.
COR_SEM_FAMILIA = "var(--g5-slate)"


def _cores_categoria(rotulos: list[str]) -> list[str]:
    return [CORES_CATEGORIA.get(_familia(r) or "", COR_SEM_FAMILIA) for r in rotulos]


def _legenda_categoria(rotulos: list[str]) -> list[tuple[str, str]]:
    presentes = {_familia(r) for r in rotulos} - {None}
    return [(nome, cor) for nome, cor in CORES_CATEGORIA.items() if nome in presentes]


def _cores_grupo(rotulos: list[str]) -> list[str]:
    return [COR_G5 if r == ROTULO_G5 else COR_FAIXA for r in rotulos]


def _legenda_grupo(rotulos: list[str]) -> list[tuple[str, str]]:
    itens = [("Faixa de PL do grupo", COR_FAIXA)]
    if ROTULO_G5 in rotulos:
        itens.append(("G5 — fundos próprios", COR_G5))
    return itens


#: Cada gráfico do par: campo do JSON, título do cartão (com a escala) e o
#: formatador que a escala exige.
GRAFICOS = (
    ("aum", "AUM", "R$ bi", lambda v: formato.em_bilhoes(v, 2)),
    ("receita_anualizada", "Receita anualizada", "R$ mi", lambda v: formato.em_milhoes(v, 1)),
)


def _par_de_barras(bloco: dict[str, Any], campo: str, cores, itens_legenda) -> str:
    """AUM e receita lado a lado, **na mesma ordem nos dois gráficos**.

    A ordem sai do AUM e vale para os dois: com cada gráfico ordenado pelo
    próprio valor, a mesma categoria cairia em alturas diferentes e comparar um
    com o outro viraria um exercício de procurar o rótulo. Ordenados juntos, a
    linha horizontal já é a comparação — e onde as duas barras discordam está o
    ROA, que é o que a tabela acima mede.
    """
    linhas = sorted(
        (registro for registro in bloco["linhas"] if registro["aum"]),
        key=lambda registro: registro["aum"],
        reverse=True,
    )
    rotulos = [registro[campo] for registro in linhas]
    paleta = cores(rotulos)

    def desenhar(chave: str, rotulo: str, escala: str, formatador) -> str:
        return cartao(
            f"{rotulo} ({escala})",
            grafico(
                graficos.barras_horizontais(
                    list(zip(rotulos, (registro[chave] for registro in linhas))),
                    formatador=formatador,
                    titulo=f"{rotulo} por {campo}, em {escala}",
                    largura=560,
                    largura_rotulo=170,
                    cores=paleta,
                )
            ),
        )

    return legenda(itens_legenda(rotulos)) + colunas(
        *(desenhar(*definicao) for definicao in GRAFICOS)
    )
