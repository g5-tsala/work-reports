"""Componentes de interface.

Tudo que uma pagina precisa desenhar sai daqui, ja no padrao G5: titulo de
secao com regra wine, tabela de header navy, KPI, cartao, legenda e a legenda
de fonte obrigatoria abaixo de cada grafico. Uma pagina nunca escreve HTML de
estrutura na mao — se um componente novo for preciso, ele nasce neste modulo.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from html import escape
from typing import Any


def esc(valor: Any) -> str:
    return escape("" if valor is None else str(valor), quote=True)


def _atributos(mapa: dict[str, Any] | None) -> str:
    if not mapa:
        return ""
    return "".join(f' {nome}="{esc(valor)}"' for nome, valor in mapa.items() if valor is not None)


# --------------------------------------------------------------------------
# Estrutura
# --------------------------------------------------------------------------


def secao(titulo: str, *conteudo: str, descricao: str = "") -> str:
    """Titulo em caixa alta com a regra wine — a assinatura editorial da G5."""
    cabecalho = f'<h2 class="g5-section-title">{esc(titulo)}</h2>'
    if descricao:
        cabecalho += f'<p class="g5-secao-descricao">{descricao}</p>'
    return f'<section class="g5-secao">{cabecalho}{"".join(conteudo)}</section>'


def colunas(*blocos: str, proporcoes: Sequence[int] | None = None) -> str:
    estilo = ""
    if proporcoes:
        estilo = f' style="grid-template-columns: {" ".join(f"{p}fr" for p in proporcoes)}"'
    return f'<div class="g5-colunas"{estilo}>{"".join(blocos)}</div>'


def cartao(titulo: str, *conteudo: str) -> str:
    cabecalho = f'<h3 class="g5-cartao-titulo">{esc(titulo)}</h3>' if titulo else ""
    return f'<div class="g5-card">{cabecalho}{"".join(conteudo)}</div>'


def nota(texto: str) -> str:
    return f'<p class="g5-nota">{texto}</p>'


def aviso(texto: str) -> str:
    return f'<p class="g5-aviso">{texto}</p>'


def fonte(aba: str, mes: str, observacao: str = "") -> str:
    """Legenda obrigatoria abaixo de todo grafico e de toda tabela de origem."""
    complemento = f" {observacao}" if observacao else ""
    return f'<p class="g5-fonte">Fonte: Gerencial MFO — aba {esc(aba)}.{complemento} Base: {esc(mes)}.</p>'


# --------------------------------------------------------------------------
# KPI
# --------------------------------------------------------------------------


def kpi(rotulo: str, valor: str, *, delta: str = "", classe_delta: str = "", detalhe: str = "") -> str:
    partes = [
        f'<span class="g5-kpi__label">{esc(rotulo)}</span>',
        f'<span class="g5-kpi__value">{esc(valor)}</span>',
    ]
    if delta:
        partes.append(f'<span class="g5-kpi__delta {classe_delta}">{esc(delta)}</span>')
    if detalhe:
        partes.append(f'<span class="g5-kpi__detalhe">{esc(detalhe)}</span>')
    return f'<div class="g5-kpi">{"".join(partes)}</div>'


def faixa_kpis(*blocos: str) -> str:
    """Nunca mais de quatro KPIs por linha — o CSS trava em 4 colunas."""
    return f'<div class="g5-kpis">{"".join(blocos)}</div>'


def faixa_parametros(itens: Sequence[tuple[str, str, str]]) -> str:
    """O regime do fechamento: mês, dias úteis, câmbio, CDI.

    Não é enfeite de cabeçalho. São os quatro parâmetros que governam metade
    dos números da página — a mensalização divide pelos dias úteis, o offshore
    inteiro passa pelo câmbio — e ficavam escondidos numa linha de subtítulo.
    Cada item leva o rótulo, o valor e o que ele controla.
    """
    blocos = "".join(
        f'<div class="g5-parametro"><span class="g5-parametro__rotulo">{esc(rotulo)}</span>'
        f'<span class="g5-parametro__valor">{esc(valor)}</span>'
        f'<span class="g5-parametro__papel">{esc(papel)}</span></div>'
        for rotulo, valor, papel in itens
    )
    return f'<div class="g5-parametros" role="group" aria-label="Parâmetros do fechamento">{blocos}</div>'


# --------------------------------------------------------------------------
# Tabela
# --------------------------------------------------------------------------


@dataclass
class Coluna:
    rotulo: str
    numerica: bool = False
    largura: str = ""

    @property
    def classe(self) -> str:
        return "num" if self.numerica else ""

    @property
    def tipo_ordenacao(self) -> str:
        return "numero" if self.numerica else "texto"


@dataclass
class Celula:
    """Conteudo de uma celula.

    `texto` e **escapado por padrao**: os nomes vem digitados na planilha e ja
    aparecem com `&` e apostrofo na base de hoje (`Rose & Oud`, `Grupo DD&L`,
    `Heitor Sant'anna Martins`). Sem escapar, o `&` corrompe o HTML e um nome
    com marcacao viraria execucao de script num arquivo que carrega dado
    nominal de cliente.

    Para o caso raro de fragmento montado por nos, use `html()`.
    """

    texto: str
    classe: str = ""
    ordem: float | None = None
    atributos: dict[str, Any] = field(default_factory=dict)
    eh_html: bool = False

    @property
    def conteudo(self) -> str:
        return self.texto if self.eh_html else esc(self.texto)


@dataclass
class Linha:
    celulas: Sequence[Celula | str]
    classe: str = ""
    nivel: int = 0
    atributos: dict[str, Any] = field(default_factory=dict)


def tabela(
    colunas_tabela: Sequence[Coluna],
    linhas: Iterable[Linha],
    *,
    identificador: str = "",
    filtravel: bool = False,
    ordenavel: bool = True,
    rolagem: bool = True,
) -> str:
    cabecalho = "".join(
        f'<th class="{coluna.classe}"'
        + (f' data-ordena="{coluna.tipo_ordenacao}"' if ordenavel else "")
        + (f' style="width:{coluna.largura}"' if coluna.largura else "")
        + f">{esc(coluna.rotulo)}</th>"
        for coluna in colunas_tabela
    )

    corpo = []
    for linha in linhas:
        celulas = []
        for indice, conteudo in enumerate(linha.celulas):
            celula = conteudo if isinstance(conteudo, Celula) else Celula(str(conteudo))
            coluna = colunas_tabela[indice] if indice < len(colunas_tabela) else Coluna("")
            classes = " ".join(filtro for filtro in (coluna.classe, celula.classe) if filtro)
            atributos = dict(celula.atributos)
            if celula.ordem is not None:
                atributos["data-valor"] = f"{celula.ordem:.6f}"
            if indice == 0 and linha.nivel:
                classes = f"{classes} nivel-{linha.nivel}".strip()
            celulas.append(f'<td class="{classes}"{_atributos(atributos)}>{celula.conteudo}</td>')
        corpo.append(f'<tr class="{linha.classe}"{_atributos(linha.atributos)}>{"".join(celulas)}</tr>')

    ferramentas = ""
    if filtravel and identificador:
        ferramentas = (
            f'<div class="g5-tabela-ferramentas">'
            f'<input type="search" class="g5-filtro" data-filtra="{esc(identificador)}" '
            f'placeholder="Filtrar linhas…" aria-label="Filtrar linhas da tabela">'
            f'<span class="g5-contador" data-contador="{esc(identificador)}"></span></div>'
        )

    tabela_html = (
        f'<table class="g5-table"{_atributos({"id": identificador or None})}>'
        f"<thead><tr>{cabecalho}</tr></thead><tbody>{''.join(corpo)}</tbody></table>"
    )
    if rolagem:
        tabela_html = f'<div class="g5-tabela-rolagem">{tabela_html}</div>'
    return ferramentas + tabela_html


def num(texto: str, classe: str = "", ordem: float | None = None) -> Celula:
    """Celula numerica ja formatada, com o valor cru para a ordenacao."""
    return Celula(texto, classe, ordem)


def html(fragmento: str, classe: str = "") -> Celula:
    """Celula com HTML montado por nos — o unico jeito de escapar do escape.

    Quem usar isto e responsavel por passar `esc()` em cada pedaco que veio da
    planilha.
    """
    return Celula(fragmento, classe, eh_html=True)


def linha_expansivel(alvo: str) -> dict[str, Any]:
    """Atributos da linha-pai de um drill-down."""
    return {"data-abre": alvo, "tabindex": "0", "role": "button"}


def linha_detalhe(alvo: str) -> dict[str, Any]:
    """Atributos das linhas-filhas, escondidas ate o clique."""
    return {"data-detalhe": alvo, "hidden": "hidden"}


# --------------------------------------------------------------------------
# Grafico
# --------------------------------------------------------------------------


def legenda(itens: Sequence[tuple[str, str]]) -> str:
    """Legenda acima do grafico — nunca abaixo."""
    if not itens:
        return ""
    marcas = "".join(
        f'<span class="g5-legenda__item"><i style="background:{cor}"></i>{esc(rotulo)}</span>'
        for rotulo, cor in itens
    )
    return f'<div class="g5-legenda">{marcas}</div>'


def grafico(svg: str, *, itens_legenda: Sequence[tuple[str, str]] = (), rodape: str = "") -> str:
    if not svg:
        return ""
    return f'<figure class="g5-figura">{legenda(itens_legenda)}{svg}{rodape}</figure>'
