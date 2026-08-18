"""Aba: Officers.

Ranking completo com drill-down: clicar na linha abre o detalhe daquele officer
no mês — AUM por segmento, receita, ROA, IN/OUT, portfólios por tipo e grupos
como titular e como backup.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import (
    Coluna,
    Linha,
    fonte,
    grafico,
    linha_detalhe,
    linha_expansivel,
    nota,
    num,
    secao,
    tabela,
)

#: Linhas do bloco `cons_officer` que abrem no drill-down, com o formatador.
DETALHE = (
    ("aum_onshore_rs", "AUM onshore (R$)", formato.numero),
    ("mfo", "· MFO (R$)", formato.numero, "aum_onshore_rs"),
    ("institucional", "· Institucional (R$)", formato.numero, "aum_onshore_rs"),
    ("estruturado", "· Estruturado (R$)", formato.numero, "aum_onshore_rs"),
    ("aum_offshore_usd", "AUM offshore (US$)", formato.numero),
    ("receita_onshore_rs", "Receita onshore, competência (R$)", formato.numero),
    ("receita_offshore_usd", "Receita offshore (US$)", formato.numero),
    ("roa_onshore_pct", "ROA onshore", formato.percentual),
    ("roa_offshore_pct", "ROA offshore", formato.percentual),
    ("in_out_total_rs", "IN/OUT no mês (R$)", formato.numero),
    ("qtd_portfolios", "Qtd. portfólios", formato.inteiro),
    ("qtd_grupos_officer", "Qtd. grupos como titular", formato.inteiro),
    ("qtd_grupos_backup", "Qtd. grupos como backup", formato.inteiro),
)


@pagina(
    identificador="officers",
    titulo="Officers",
    grupo="Carteira",
    ordem=10,
    subtitulo="AUM, receita e ROA por officer. Clique em uma linha para abrir o detalhe do mês.",
)
def render(ctx: Contexto) -> str:
    return "".join(
        [
            secao(
                "Ranking",
                _tabela(ctx),
                fonte("CEO-Dashboard e cons_officer", ctx.rotulo_mes),
                _ressalvas(),
            ),
            secao("AUM por officer", _barras(ctx)),
            secao("Rede de backup", _backup(ctx)),
        ]
    )


def _blocos_por_nome(ctx: Contexto) -> dict[str, dict[str, Any]]:
    return {bloco["nome"]: bloco for bloco in ctx.bloco("officers", "blocos") if bloco["nome"]}


def _tabela(ctx: Contexto) -> str:
    tabela_ceo = ctx.bloco("officers", "tabela_ceo")
    blocos = _blocos_por_nome(ctx)

    colunas = [
        Coluna("Officer"),
        Coluna("AUM (R$ mi)", numerica=True),
        Coluna("Δ AUM M-1", numerica=True),
        Coluna("% AUM", numerica=True),
        Coluna("Receita (R$)", numerica=True),
        Coluna("Δ Receita M-1", numerica=True),
        Coluna("ROA (%)", numerica=True),
        Coluna("ROA MFO (%)", numerica=True),
        Coluna("IN/OUT mês (R$ mi)", numerica=True),
        Coluna("Qtd. portf.", numerica=True),
    ]

    linhas = []
    for registro in tabela_ceo:
        celulas = [
            registro["nome"],
            num(formato.numero(registro["aum_mi"]), ordem=registro["aum_mi"]),
            num(
                formato.variacao(registro["aum_var_pct"]),
                formato.classe_sinal(registro["aum_var_pct"]),
                ordem=registro["aum_var_pct"],
            ),
            num(formato.percentual(registro["pct_aum"]), ordem=registro["pct_aum"]),
            num(formato.numero(registro["receita"], 0), ordem=registro["receita"]),
            num(
                formato.variacao(registro["receita_var_pct"]),
                formato.classe_sinal(registro["receita_var_pct"]),
                ordem=registro["receita_var_pct"],
            ),
            num(formato.percentual(registro["roa"]), ordem=registro["roa"]),
            num(formato.percentual(registro["roa_mfo"]) if registro["roa_mfo"] else formato.NAO_APLICAVEL),
            num(
                formato.numero(registro["in_out_mes_mi"]),
                formato.classe_sinal(registro["in_out_mes_mi"]),
                ordem=registro["in_out_mes_mi"],
            ),
            num(formato.inteiro(registro["qtd_portfolios"]), ordem=registro["qtd_portfolios"]),
        ]

        if registro["tipo"] == "total_ex_fdos":
            # A planilha compara o Ex-Fdos do mes contra o TOTAL do mes anterior
            # (`CEO-Dashboard!Z39`), o que produz uma variacao de -31% sem
            # significado. Melhor nao exibir do que exibir errado.
            celulas[2] = num(formato.NAO_APLICAVEL)
            celulas[5] = num(formato.NAO_APLICAVEL)
            linhas.append(Linha(celulas, classe="total"))
            continue
        if registro["tipo"] == "total":
            linhas.append(Linha(celulas, classe="total"))
            continue

        alvo = f"officer-{formato.mes_curto(ctx.mes_base)}-{len(linhas)}"
        classe = "destaque" if registro["tipo"] == "fdos_alocacao" else ""
        bloco = blocos.get(registro["nome"])
        if bloco:
            linhas.append(Linha(celulas, classe=classe, atributos=linha_expansivel(alvo)))
            linhas.extend(_linhas_detalhe(ctx, bloco, alvo, len(colunas)))
        else:
            linhas.append(Linha(celulas, classe=classe))

    return tabela(colunas, linhas, identificador="officers")


def _linhas_detalhe(ctx: Contexto, bloco: dict[str, Any], alvo: str, total_colunas: int) -> list[Linha]:
    posicao = ctx.posicao(bloco, ctx.mes_base)
    if posicao is None:
        return []

    itens = []
    for especificacao in DETALHE:
        chave, rotulo, formatador = especificacao[0], especificacao[1], especificacao[2]
        pai = especificacao[3] if len(especificacao) > 3 else None
        serie = ctx.serie(bloco, chave, pai)
        if not serie or posicao >= len(serie):
            continue
        itens.append((rotulo, formatador(serie[posicao])))

    linhas = []
    for indice in range(0, len(itens), 3):
        trio = itens[indice : indice + 3]
        celulas: list[Any] = [""]
        for rotulo, valor in trio:
            celulas.extend([rotulo, num(valor)])
        celulas.extend([""] * (total_colunas - len(celulas)))
        linhas.append(Linha(celulas, classe="detalhe", atributos=linha_detalhe(alvo)))
    return linhas


def _barras(ctx: Contexto) -> str:
    carteiras = [
        (registro["nome"], registro["aum_mi"])
        for registro in ctx.bloco("officers", "tabela_ceo")
        if registro["tipo"] in ("officer", "fdos_alocacao")
    ]
    carteiras.sort(key=lambda item: item[1] or 0, reverse=True)
    return grafico(
        graficos.barras_horizontais(
            carteiras,
            formatador=lambda v: f"{formato.numero(v, 0)} mi",
            titulo="AUM por officer",
        ),
        itens_legenda=[("AUM (R$ mi)", graficos.SERIES[0])],
        rodape=fonte("CEO-Dashboard", ctx.rotulo_mes),
    )


def _backup(ctx: Contexto) -> str:
    """Titular × backup — o corte que nenhuma métrica da planilha mostra hoje."""
    linhas_tabela = []
    for bloco in ctx.bloco("officers", "blocos"):
        posicao = ctx.posicao(bloco, ctx.mes_base)
        if posicao is None or bloco["e_fdos_alocacao"]:
            continue
        titular = ctx.serie(bloco, "qtd_grupos_officer")
        backup = ctx.serie(bloco, "qtd_grupos_backup")
        if not titular and not backup:
            continue
        como_titular = titular[posicao] if posicao < len(titular) else None
        como_backup = backup[posicao] if posicao < len(backup) else None
        linhas_tabela.append(
            Linha(
                [
                    bloco["nome"],
                    num(formato.inteiro(como_titular), ordem=como_titular),
                    num(formato.inteiro(como_backup), ordem=como_backup),
                ]
            )
        )

    colunas = [
        Coluna("Officer"),
        Coluna("Grupos como titular", numerica=True),
        Coluna("Grupos como backup", numerica=True),
    ]
    return "".join(
        [
            tabela(colunas, linhas_tabela, identificador="backup-officers"),
            fonte("cons_officer", ctx.rotulo_mes, "Grupos com AUM ou receita > 0 no mês."),
            nota(
                "<strong>Não somar a coluna de titular.</strong> Um grupo econômico pode ter "
                "portfólios sob officers diferentes, então a soma excede o total de grupos "
                f"distintos ({formato.inteiro(ctx.bloco('consolidado', 'roa_grupo')['total']['qtd'])})."
            ),
        ]
    )


def _ressalvas() -> str:
    return nota(
        "<strong>ROA MFO não é diretamente comparável ao ROA.</strong> A fórmula da planilha "
        "conta todo o offshore como MFO, nos dois lados da razão, e não mensaliza o numerador — "
        "o que infla a coluna na proporção <code>dias úteis ÷ 21</code>. Reproduzimos como está "
        "para os números baterem com a fonte. As variações M-1 da linha "
        "<em>Total Ex- Fdos Alocação</em> saem como “—”: na planilha, a base de comparação dessa "
        "linha é o total do mês anterior, não o próprio ex-fundos."
    )
