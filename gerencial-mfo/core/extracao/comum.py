"""Leitura compartilhada de blocos rotulados.

Varias abas seguem o mesmo formato: um rotulo na coluna B e uma serie de meses
a direita. `linhas_rotuladas` le esse formato uma vez so, para `aum_receita`,
`roa_historico`, `cons_officer` e `ar_adm_*`.

O nivel de hierarquia vem do recuo da celula (`indent`), que a geradora usa
para aninhar as quebras — `IN/OUT` no nivel 1, os tipos de veiculo no nivel 2.
E informacao da planilha, nao inferencia nossa, e e o que sustenta o drill-down
sem uma lista de pais/filhos escrita no codigo.
"""

from __future__ import annotations

from typing import Any

from core.planilha import chave, numero, texto

COL_ROTULO_PADRAO = 2  # B
ROTULO_DATA = "Data"


def nivel(ws, linha: int, coluna: int = COL_ROTULO_PADRAO) -> int:
    recuo = ws.cell(linha, coluna).alignment.indent
    return int(recuo or 0)


def atribuir_pais(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preenche `pai` com a chave da linha imediatamente acima em nivel menor.

    Resolve a ambiguidade dos rotulos repetidos: `Carteira` aparece tres vezes
    em `aum_receita`, uma sob `IN/OUT`, outra sob `Receita` e outra sob
    `Receita Mens.` — mesma chave, pais diferentes.
    """
    pilha: list[dict[str, Any]] = []
    for item in linhas:
        while pilha and pilha[-1]["nivel"] >= item["nivel"]:
            pilha.pop()
        item["pai"] = pilha[-1]["chave"] if pilha else None
        pilha.append(item)
    return linhas


def linhas_rotuladas(
    pl,
    aba: str,
    lin_ini: int,
    lin_fim: int,
    *,
    col_ini: int,
    col_fim: int,
    col_rotulo: int = COL_ROTULO_PADRAO,
    ignorar_cabecalho_de_bloco: bool = False,
) -> list[dict[str, Any]]:
    """`[{rotulo, chave, nivel, pai, linha, valores}]` das linhas com rotulo.

    `ignorar_cabecalho_de_bloco` descarta a linha que so nomeia o bloco
    seguinte — em `cons_officer` o intervalo de um officer invade o nome do
    proximo, e sem isso o JSON ganharia uma metrica chamada `alexandre`.
    """
    ws = pl.aba(aba)
    linhas = []
    for numero_linha in range(lin_ini, lin_fim + 1):
        rotulo = texto(ws.cell(numero_linha, col_rotulo).value)
        if rotulo is None:
            continue
        if ignorar_cabecalho_de_bloco and texto(ws.cell(numero_linha + 1, col_rotulo).value) == ROTULO_DATA:
            continue
        linhas.append(
            {
                "rotulo": rotulo,
                "chave": chave(rotulo),
                "nivel": nivel(ws, numero_linha, col_rotulo),
                "linha": numero_linha,
                "valores": [numero(v) for v in pl.linha(aba, numero_linha, col_ini, col_fim)],
            }
        )
    return atribuir_pais(linhas)
