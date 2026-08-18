"""Etapa 2 do pipeline: `data-YYYY-MM.json` -> `dashboard-YYYY-MM.html`.

**Ainda nao implementada.** O modulo existe para fixar a fronteira: o
renderizador le o JSON e os assets de `template/`, e nunca abre a planilha.
Restricoes que valem quando ele for escrito (`docs/ambiente.md` §3):

- HTML autocontido, sem CDN: CSS, JS e graficos inlined.
- Precisa funcionar dentro de um `<iframe>`: nada de `window.top` nem
  `localStorage`.
- Padrao visual pela skill `g5-design-system` mais `docs/visual.md`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

DISPONIVEL = False


class EtapaNaoImplementada(RuntimeError):
    """Levantada enquanto a renderizacao nao existir."""


def renderizar(dados: dict[str, Any], caminho_html: Path) -> Path:
    raise EtapaNaoImplementada(
        "A etapa de renderizacao (JSON -> HTML) ainda nao foi implementada. "
        "O JSON do mes ja foi gerado e validado."
    )
