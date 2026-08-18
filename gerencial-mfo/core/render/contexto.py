"""Contexto de renderizacao.

O que toda pagina recebe: os dados do mes e os atalhos para navegar neles sem
repetir busca por chave em quinze arquivos. Nenhuma conta de negocio aqui —
`docs/calculos.md` é a fonte das contas, e elas já vieram prontas da planilha.
"""

from __future__ import annotations

from typing import Any

from . import formato


class Contexto:
    def __init__(self, dados: dict[str, Any]):
        self.dados = dados
        self.mes_base: str = dados["meta"]["mes_base"]
        self.mes_anterior: str = formato.mes_anterior(self.mes_base)
        self.parametros: dict[str, Any] = dados["parametros"]
        self.dolar: float = self.parametros["dolar"]
        self.rotulo_mes: str = formato.mes_extenso(self.mes_base)

    # -- navegacao no JSON -----------------------------------------------

    def bloco(self, *caminho: str) -> Any:
        """`ctx.bloco("historico", "aum_receita", "onshore")`."""
        atual: Any = self.dados
        for chave in caminho:
            atual = atual[chave]
        return atual

    @staticmethod
    def linha(bloco: dict[str, Any], chave: str, pai: str | None = None) -> dict[str, Any] | None:
        """Uma linha rotulada dentro de um bloco.

        Casar por `(pai, chave)` e nao so por `chave`: rotulos se repetem entre
        secoes — `Carteira` aparece sob `IN/OUT`, sob `Receita` e sob
        `Receita Mens.` (`docs/contrato-json.md` §3.1).
        """
        for linha in bloco.get("linhas", []):
            if linha.get("chave") == chave and (pai is None or linha.get("pai") == pai):
                return linha
        return None

    def serie(self, bloco: dict[str, Any], chave: str, pai: str | None = None) -> list[float | None]:
        linha = self.linha(bloco, chave, pai)
        return linha["valores"] if linha else []

    def ultimo(self, bloco: dict[str, Any], chave: str, pai: str | None = None) -> float | None:
        valores = self.serie(bloco, chave, pai)
        return valores[-1] if valores else None

    def em(self, bloco: dict[str, Any], chave: str, mes: str, pai: str | None = None) -> float | None:
        valores = self.serie(bloco, chave, pai)
        posicao = self.posicao(bloco, mes)
        return valores[posicao] if posicao is not None and posicao < len(valores) else None

    @staticmethod
    def posicao(bloco: dict[str, Any], mes: str) -> int | None:
        meses = bloco.get("meses", [])
        return meses.index(mes) if mes in meses else None

    # -- apresentacao ----------------------------------------------------

    @staticmethod
    def rotulos(meses: list[str]) -> list[str]:
        return [formato.mes_curto(mes) for mes in meses]

    def variacao(self, atual: float | None, anterior: float | None) -> float | None:
        """Variacao relativa M-1. `None` quando nao ha base de comparacao."""
        if atual is None or not anterior:
            return None
        return atual / anterior - 1
