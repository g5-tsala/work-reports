"""Aba: Regiões.

Distribuição geográfica do AUM e da receita, com as parcelas onshore e
offshore empilhadas. Única fonte do corte é a aba oculta `regiao`,
que já traz onshore, offshore e o consolidado somados um a um.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, cartao, colunas, fonte, grafico, legenda, num, secao, tabela

#: Rótulo de exibição da linha sem região da planilha (`-`): é onde caem os
#: fundos de alocação próprios, e o negócio lê essa linha como o grupo G5.
ROTULO_SEM_REGIAO = "G5"

#: Parcelas de cada barra, na ordem da pilha: bloco do JSON, rótulo e cor —
#: as mesmas do Histórico AUM × Receita.
PARCELAS = (
    ("onshore", "Onshore", graficos.SERIES[0]),
    ("offshore", "Offshore", graficos.SERIES[1]),
)

#: Cada gráfico do par: campo do JSON, título do cartão (com a escala) e o
#: formatador que a escala exige.
GRAFICOS = (
    ("aum", "AUM", "R$ bi", lambda v: formato.em_bilhoes(v, 2)),
    ("receita", "Receita", "R$ mil", lambda v: formato.numero(v / 1e3, 0)),
)

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

    partes = [secao("Distribuição do AUM e da receita", _barras(ctx, regioes, consolidado))]
    for chave, titulo, com_grupos in BLOCOS:
        partes.append(
            secao(
                titulo,
                _tabela(ctx, regioes[chave], chave, com_grupos),
                fonte("regiao", ctx.rotulo_mes),
            )
        )
    return "".join(partes)


def _rotulo(registro: dict[str, Any]) -> str:
    return ROTULO_SEM_REGIAO if registro.get("sem_regiao") else registro["regiao"]


def _barras(ctx: Contexto, regioes: dict[str, Any], consolidado: dict[str, Any]) -> str:
    """AUM e receita lado a lado, empilhando onshore e offshore.

    A ordem sai do AUM consolidado e vale para os dois gráficos, como nos pares
    de Resumo, Officers e Grupos. As parcelas vêm dos blocos onshore e offshore
    da aba `regiao`, casadas pelo nome da região — o consolidado é a soma delas.
    """
    linhas = sorted(
        (linha for linha in consolidado["linhas"] if linha["aum"]),
        key=lambda linha: linha["aum"],
        reverse=True,
    )
    parcelas = {
        chave: {linha["regiao"]: linha for linha in regioes[chave]["linhas"]} for chave, _, _ in PARCELAS
    }
    rotulos = [_rotulo(linha) for linha in linhas]

    def desenhar(campo: str, rotulo: str, escala: str, formatador) -> str:
        series = [
            graficos.Serie(
                nome,
                [(parcelas[chave].get(linha["regiao"]) or {}).get(campo) for linha in linhas],
                cor,
            )
            for chave, nome, cor in PARCELAS
        ]
        return cartao(
            f"{rotulo} ({escala})",
            grafico(
                graficos.barras_horizontais_empilhadas(
                    rotulos,
                    series,
                    formatador=formatador,
                    titulo=f"{rotulo} por região, onshore e offshore, em {escala}",
                    largura=560,
                    largura_rotulo=180,
                )
            ),
        )

    return (
        legenda([(nome, cor) for _, nome, cor in PARCELAS])
        + colunas(*(desenhar(*definicao) for definicao in GRAFICOS))
        + fonte(
            "regiao",
            ctx.rotulo_mes,
            "Offshore convertido ao câmbio do mês. Passe o mouse na barra para ver as parcelas.",
        )
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
            _rotulo(registro),
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
