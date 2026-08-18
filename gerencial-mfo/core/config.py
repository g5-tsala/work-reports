"""Caminhos e constantes globais do build.

Nada de layout de planilha aqui — cada extrator carrega as celulas que ele le,
perto de onde as usa. Este modulo so responde "onde ficam os arquivos" e
"quais limites o build considera".
"""

from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

DIR_INPUTS = RAIZ / "inputs"
DIR_OUTPUTS = RAIZ / "outputs"

VERSAO_EXTRATOR = "1.0.0"

#: Contrato do JSON intermediario. Subir a cada mudanca de formato que quebre
#: o consumo pelo renderizador (etapa 2).
VERSAO_CONTRATO = 1

#: Os checks embutidos na planilha sao diferencas que deveriam ser zero. Sobra
#: ruido de ponto flutuante da ordem de 1e-7 em valores na casa dos bilhoes.
TOLERANCIA_CHECK = 1e-6

#: Tolerancia relativa para conferencia de totais (soma das partes vs. total).
TOLERANCIA_RELATIVA = 1e-6

PADRAO_MES = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def mes_valido(mes: str) -> bool:
    return bool(PADRAO_MES.match(mes))


def dir_input(mes: str) -> Path:
    return DIR_INPUTS / mes


def caminho_planilha(mes: str) -> Path:
    return DIR_INPUTS / mes / f"Gerencial MFO {mes}.xlsx"


def dir_output(mes: str) -> Path:
    return DIR_OUTPUTS / mes


def caminho_json(mes: str) -> Path:
    return dir_output(mes) / f"data-{mes}.json"


def caminho_html(mes: str) -> Path:
    return dir_output(mes) / f"dashboard-{mes}.html"
