#!/usr/bin/env python
"""Gerencial MFO — gerador do dashboard mensal.

Script centralizador do build. Orquestra as etapas, todas em `core/`:

    inputs/YYYY-MM/Gerencial MFO YYYY-MM.xlsx
        -> core.extracao   -> outputs/YYYY-MM/data-YYYY-MM.json
        -> core.validacao  -> checklist bloqueante
        -> core.render     -> outputs/YYYY-MM/dashboard-YYYY-MM.html

Uso:
    python dashboard.py 2026-07                  # pipeline completo
    python dashboard.py 2026-07 --etapa extrair  # so a extracao + validacao
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from core import config, json_io
from core.extracao import extrair
from core.render import renderizar
from core.validacao import Relatorio, validar

CODIGO_ERRO_USO = 2
CODIGO_ERRO_VALIDACAO = 3
CODIGO_ERRO_RENDER = 4


def main(argv: Sequence[str] | None = None) -> int:
    args = _argumentos(argv)
    mes = args.mes

    if not config.mes_valido(mes):
        return _erro(f"mes-base invalido: {mes}. Use o formato YYYY-MM, por exemplo 2026-07.", CODIGO_ERRO_USO)

    caminho_json = config.caminho_json(mes)

    if args.etapa in ("tudo", "extrair"):
        codigo = _extrair(mes, caminho_json)
        if codigo:
            return codigo

    if args.etapa in ("tudo", "validar"):
        if not caminho_json.exists():
            return _erro(f"{caminho_json} nao existe. Rode a etapa de extracao antes.", CODIGO_ERRO_USO)
        if args.etapa == "validar":
            relatorio = validar(json_io.carregar(caminho_json))
            _imprimir_validacao(relatorio)
            if not relatorio.ok:
                return CODIGO_ERRO_VALIDACAO

    if args.etapa in ("tudo", "renderizar"):
        return _renderizar(mes, caminho_json)

    return 0


def _argumentos(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dashboard.py",
        description="Gera o dashboard HTML do Gerencial MFO a partir da planilha do mes.",
    )
    parser.add_argument("mes", help="mes-base no formato YYYY-MM (ex.: 2026-07)")
    parser.add_argument(
        "--etapa",
        choices=("tudo", "extrair", "validar", "renderizar"),
        default="tudo",
        help="etapa a executar (padrao: tudo)",
    )
    return parser.parse_args(argv)


def _extrair(mes: str, caminho_json) -> int:
    caminho_xlsx = config.caminho_planilha(mes)
    if not caminho_xlsx.exists():
        return _erro(
            f"planilha nao encontrada em {caminho_xlsx}. O nome do arquivo precisa seguir "
            "exatamente o padrao 'Gerencial MFO YYYY-MM.xlsx'.",
            CODIGO_ERRO_USO,
        )

    print(f"[1/3] Extraindo {caminho_xlsx.name}...")
    dados = extrair(caminho_xlsx, mes)
    json_io.salvar(caminho_json, dados)
    print(f"      base gravada em {caminho_json}")

    for aviso in dados.get("avisos", []):
        print(f"      [aviso] {aviso}")

    print("[2/3] Validando a base...")
    relatorio = validar(dados)
    _imprimir_validacao(relatorio)
    if not relatorio.ok:
        print(
            "\n[ERRO] A base do mes esta inconsistente. Nenhum dashboard sera gerado.\n"
            "       Confira os itens acima em docs/validacao.md antes de reprocessar.",
            file=sys.stderr,
        )
        return CODIGO_ERRO_VALIDACAO
    return 0


def _renderizar(mes: str, caminho_json) -> int:
    if not caminho_json.exists():
        return _erro(f"{caminho_json} nao existe. Rode a etapa de extracao antes.", CODIGO_ERRO_USO)

    print("[3/3] Renderizando o HTML...")
    dados = json_io.carregar(caminho_json)
    try:
        caminho_html = renderizar(dados, config.caminho_html(mes))
    except (FileNotFoundError, KeyError, RuntimeError) as erro:
        return _erro(f"falha ao renderizar o dashboard: {erro}", CODIGO_ERRO_RENDER)
    tamanho = caminho_html.stat().st_size / 1024
    print(f"      dashboard gravado em {caminho_html} ({tamanho:,.0f} KB)".replace(",", "."))
    return 0


def _imprimir_validacao(relatorio: Relatorio) -> None:
    for item in relatorio.itens:
        marca = {True: "OK  ", False: "FALHA", None: "?   "}[item.ok]
        print(f"      [{marca}] {item.numero:>2}. {item.titulo}")
        if item.detalhe:
            print(f"              {item.detalhe}")


def _erro(mensagem: str, codigo: int) -> int:
    print(f"[ERRO] {mensagem}", file=sys.stderr)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
