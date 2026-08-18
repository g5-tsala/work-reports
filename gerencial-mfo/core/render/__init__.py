"""Etapa 3 do pipeline: `data-YYYY-MM.json` -> `dashboard-YYYY-MM.html`.

O renderizador le **apenas o JSON** — nunca a planilha. Essa e a fronteira
sagrada do projeto (regra inviolavel 7): mudou a planilha, mexe no extrator;
mudou o layout, mexe aqui.

Organizacao:

- `paginas/<aba>.py` — uma aba do dashboard por arquivo. Para mudar o que
  aparece numa aba, e o unico arquivo a abrir.
- `ui.py` — componentes (secao, KPI, tabela, cartao, legenda de fonte).
- `graficos.py` — SVG inline, sem biblioteca.
- `formato.py` — numeros e datas em PT-BR.
- `layout.py` — esqueleto, menu e a costura do HTML final.
- `contexto.py` — atalhos de leitura do JSON.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import paginas  # noqa: F401  (importar registra as abas)
from .contexto import Contexto
from .layout import montar

DISPONIVEL = True


def renderizar(dados: dict[str, Any], caminho_html: Path) -> Path:
    """Escreve o dashboard autocontido do mes e devolve o caminho."""
    caminho_html = Path(caminho_html)
    caminho_html.parent.mkdir(parents=True, exist_ok=True)
    caminho_html.write_text(montar(Contexto(dados)), encoding="utf-8")
    return caminho_html


__all__ = ["DISPONIVEL", "Contexto", "renderizar"]
