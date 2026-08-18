"""Nucleo do build do dashboard Gerencial MFO.

Etapas do pipeline, na ordem em que `dashboard.py` as executa:

1. `core.extracao` — planilha do mes -> `outputs/YYYY-MM/data-YYYY-MM.json`
2. `core.validacao` — confere o JSON contra o checklist de `docs/validacao.md`
3. `core.render`    — JSON -> `outputs/YYYY-MM/dashboard-YYYY-MM.html`

A fronteira entre 1 e 3 e o JSON: mudou a planilha, mexe so no extrator; mudou
o layout, mexe so no template.
"""

__all__ = ["config", "extracao", "json_io", "planilha", "render", "validacao"]
