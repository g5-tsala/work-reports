"""Montagem do HTML final.

Le `template/` e costura menu, paginas, CSS, JS e o logo num unico arquivo.
Nada de CDN: estilo, script e a marca entram inlined, e o arquivo abre offline,
de qualquer pasta, dentro ou fora de um `<iframe>`.

Esta e a unica parte do renderizador que conhece o esqueleto da pagina. Uma aba
nova nao encosta aqui — ela se registra em `paginas/` e aparece sozinha.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from core import config

from . import formato
from . import pagina as registro
from .contexto import Contexto
from .ui import esc, faixa_parametros

DIR_TEMPLATE = config.RAIZ / "template"
ARQUIVO_BASE = DIR_TEMPLATE / "base.html"
ARQUIVO_ESTILOS = DIR_TEMPLATE / "styles.css"
ARQUIVO_SCRIPT = DIR_TEMPLATE / "app.js"
ARQUIVO_LOGO = DIR_TEMPLATE / "logo-g5.txt"


def montar(ctx: Contexto) -> str:
    paginas = registro.registradas()
    if not paginas:
        raise RuntimeError("nenhuma pagina registrada — verifique core/render/paginas/__init__.py")

    substituicoes = {
        "titulo": f"Gerencial MFO — {ctx.rotulo_mes}",
        "estilos": _ler(ARQUIVO_ESTILOS),
        "script": _ler(ARQUIVO_SCRIPT),
        "logo": _ler(ARQUIVO_LOGO).strip(),
        "mes_extenso": ctx.rotulo_mes,
        "cambio": f"R$ {formato.numero(ctx.dolar, 4)}",
        "parametros": _parametros(ctx),
        "menu": _menu(),
        "primeira_pagina": esc(paginas[0].titulo),
        "paginas": _paginas(ctx, paginas),
        "gerado_em": _carimbo(ctx.dados["meta"].get("gerado_em")),
        "arquivo_origem": esc(ctx.dados["meta"].get("arquivo_origem", "")),
    }

    html = _ler(ARQUIVO_BASE)
    for chave, valor in substituicoes.items():
        html = html.replace("{{" + chave + "}}", valor)
    return html


def _ler(caminho: Path) -> str:
    if not caminho.exists():
        raise FileNotFoundError(f"asset do template ausente: {caminho}")
    return caminho.read_text(encoding="utf-8")


def _parametros(ctx: Contexto) -> str:
    dias_uteis = ctx.parametros.get("nwdays_mes")
    cdi = ctx.parametros.get("cdi_mes")
    return faixa_parametros(
        [
            ("Fechamento", ctx.rotulo_mes, "mês-base do build"),
            ("Dias úteis", formato.inteiro(dias_uteis), "base da mensalização"),
            ("Câmbio", f"R$ {formato.numero(ctx.dolar, 4)}", "converte todo o offshore"),
            ("CDI do mês", formato.percentual(cdi), "referência de rendimento"),
        ]
    )


def _menu() -> str:
    partes = []
    for grupo, paginas in registro.por_grupo():
        partes.append(f'<p class="g5-nav__grupo">{esc(grupo)}</p>')
        for item in paginas:
            partes.append(
                f'<button type="button" class="g5-nav__item" '
                f'data-vai-para="{esc(item.identificador)}" data-titulo="{esc(item.titulo)}">'
                f"{esc(item.titulo)}</button>"
            )
    return "".join(partes)


def _paginas(ctx: Contexto, paginas: list[registro.Pagina]) -> str:
    partes = []
    for item in paginas:
        descricao = (
            f'<p class="g5-pagina__descricao">{item.subtitulo}</p>' if item.subtitulo else ""
        )
        partes.append(
            f'<section class="g5-pagina" data-pagina="{esc(item.identificador)}" hidden>'
            f'<h2 class="g5-visualmente-oculto" hidden>{esc(item.titulo)}</h2>'
            f"{descricao}{item.render(ctx)}</section>"
        )
    return "".join(partes)


def _carimbo(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        return esc(iso)


def dados_validos(dados: dict[str, Any]) -> bool:
    return bool(dados.get("meta", {}).get("mes_base"))
