"""Leitura e escrita do JSON intermediario.

O arquivo e o contrato entre as duas etapas e tambem o artefato de auditoria do
mes: sai indentado e sem escapar acentos, para ser lido no editor e no `jq`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def salvar(caminho: Path, dados: dict[str, Any]) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=1)
        arquivo.write("\n")
    return caminho


def carregar(caminho: Path) -> dict[str, Any]:
    with Path(caminho).open(encoding="utf-8") as arquivo:
        return json.load(arquivo)
