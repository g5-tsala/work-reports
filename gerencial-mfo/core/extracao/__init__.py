"""Etapa 1 do pipeline: planilha mensal -> `data-YYYY-MM.json`.

Orquestra os extratores por dominio. Cada um recebe o mesmo `Contexto` e
devolve o pedaco de JSON que lhe cabe; nenhum deles escreve arquivo.

Principio: **extrair, nunca recalcular.** Os numeros ja vieram calculados da
geradora e a conferencia deles e trabalho da etapa de validacao. O unico
tratamento aplicado aqui e o documentado em `docs/validacao.md`: truncar meses
futuros e anular erros do Excel.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from core import config
from core.planilha import Planilha
from core.planilha import mes as ler_mes

from . import (
    captacao,
    carteira,
    checks,
    consolidado,
    estrutura,
    historico,
    officers,
    parametros,
)


class Contexto:
    """Estado compartilhado pelos extratores durante um build."""

    def __init__(self, pl: Planilha, mes_base: str):
        self.pl = pl
        self.mes_base = mes_base
        self.avisos: list[str] = []
        self.parametros: dict[str, Any] = {}

    def avisar(self, mensagem: str) -> None:
        if mensagem not in self.avisos:
            self.avisos.append(mensagem)

    # -- grade temporal --------------------------------------------------

    def no_horizonte(self, mes: str | None) -> bool:
        """`True` se o mes pertence ao periodo ja fechado.

        Regra inviolavel 4: o mes de fechamento vem do nome da pasta. As
        colunas de meses futuros existem na planilha, zeradas, e nao podem
        chegar ao dashboard.
        """
        return bool(mes) and mes <= self.mes_base

    def meses_no_horizonte(self, meses: list[str | None]) -> list[int]:
        """Indices das colunas que ficam depois do corte pelo mes-base."""
        return [i for i, m in enumerate(meses) if self.no_horizonte(m)]

    def cortar(self, meses: list[str | None], *series: list[Any]) -> tuple[list[str], list[list[Any]]]:
        """Aplica o corte temporal aos meses e a todas as series em paralelo."""
        indices = self.meses_no_horizonte(meses)
        meses_ok = [meses[i] for i in indices]
        series_ok = [[serie[i] if i < len(serie) else None for i in indices] for serie in series]
        return meses_ok, series_ok


def extrair(caminho_xlsx: Path, mes_base: str) -> dict[str, Any]:
    """Le a planilha do mes e devolve o dicionario que vira o JSON."""
    pl = Planilha(caminho_xlsx)
    ctx = Contexto(pl, mes_base)
    try:
        ctx.parametros = parametros.extrair(ctx)
        dados: dict[str, Any] = {
            "meta": {
                "mes_base": mes_base,
                "gerado_em": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
                "arquivo_origem": Path(caminho_xlsx).name,
                "versao_extrator": config.VERSAO_EXTRATOR,
                "versao_contrato": config.VERSAO_CONTRATO,
                "moeda_base": "BRL",
                "confidencialidade": "USO INTERNO RESTRITO - dados nominais de clientes",
            },
            "parametros": ctx.parametros,
            "consolidado": consolidado.extrair(ctx),
            "historico": historico.extrair(ctx),
            "officers": officers.extrair(ctx),
            "carteira": carteira.extrair(ctx),
            "captacao": captacao.extrair(ctx),
            "estrutura": estrutura.extrair(ctx),
            "checks_planilha": checks.extrair(ctx),
        }
        dados["avisos"] = ctx.avisos
        return dados
    finally:
        pl.fechar()


__all__ = ["Contexto", "extrair", "ler_mes"]
