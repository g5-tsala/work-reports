"""Formatacao PT-BR.

Regra do design system: milhar `.`, decimal `,`, uma escala por tabela declarada
no cabecalho. Zero e `0,00`; traco `—` e "nao aplicavel"; celula vazia e "dado
ausente". Sao coisas diferentes e alguem vai perguntar.
"""

from __future__ import annotations

MESES_ABREVIADOS = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)
MESES_EXTENSO = (
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
)

NAO_APLICAVEL = "—"
AUSENTE = ""

BILHAO = 1_000_000_000
MILHAO = 1_000_000


def numero(valor: float | None, casas: int = 2) -> str:
    """`1234567.891` -> `1.234.567,89`. `None` vira celula vazia."""
    if valor is None:
        return AUSENTE
    # Formata em en-US e inverte os separadores de uma vez, com um marcador
    # temporario para nao trocar duas vezes o mesmo caractere.
    return f"{valor:,.{casas}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def inteiro(valor: float | None) -> str:
    return numero(valor, 0)


def reais(valor: float | None, casas: int = 2) -> str:
    return AUSENTE if valor is None else f"R$ {numero(valor, casas)}"


def bilhoes(valor: float | None, casas: int = 2, moeda: str = "R$") -> str:
    """Valor absoluto -> `R$ 42,78 bi`."""
    if valor is None:
        return AUSENTE
    return f"{moeda} {numero(valor / BILHAO, casas)} bi"


def milhoes(valor: float | None, casas: int = 2, moeda: str = "R$") -> str:
    if valor is None:
        return AUSENTE
    return f"{moeda} {numero(valor / MILHAO, casas)} mi"


def em_bilhoes(valor: float | None, casas: int = 2) -> str:
    """So o numero, para colunas cuja escala ja esta no cabecalho."""
    return AUSENTE if valor is None else numero(valor / BILHAO, casas)


def em_milhoes(valor: float | None, casas: int = 2) -> str:
    return AUSENTE if valor is None else numero(valor / MILHAO, casas)


def percentual(fracao: float | None, casas: int = 2) -> str:
    """`0.0024263` -> `0,24%`."""
    return AUSENTE if fracao is None else f"{numero(fracao * 100, casas)}%"


def variacao(fracao: float | None, casas: int = 2) -> str:
    """Variacao percentual com sinal explicito: `+2,46%`."""
    if fracao is None:
        return AUSENTE
    return f"{'+' if fracao >= 0 else ''}{numero(fracao * 100, casas)}%"


def pontos_percentuais(diferenca: float | None, casas: int = 2) -> str:
    """Diferenca entre percentuais e **p.p.**, nunca `%`."""
    if diferenca is None:
        return AUSENTE
    return f"{'+' if diferenca >= 0 else ''}{numero(diferenca * 100, casas)} p.p."


def com_sinal(valor: float | None, formatador=numero, **kwargs) -> str:
    if valor is None:
        return AUSENTE
    return f"{'+' if valor >= 0 else ''}{formatador(valor, **kwargs)}"


def classe_sinal(valor: float | None) -> str:
    """Classe CSS de cor por sinal. Zero e neutro, nao positivo."""
    if valor is None or valor == 0:
        return ""
    return "positivo" if valor > 0 else "negativo"


def mes_curto(mes: str | None) -> str:
    """`2026-07` -> `jul/26`."""
    if not mes:
        return AUSENTE
    ano, numero_mes = mes.split("-")
    return f"{MESES_ABREVIADOS[int(numero_mes) - 1]}/{ano[2:]}"


def mes_extenso(mes: str | None) -> str:
    """`2026-07` -> `Julho/2026`."""
    if not mes:
        return AUSENTE
    ano, numero_mes = mes.split("-")
    return f"{MESES_EXTENSO[int(numero_mes) - 1]}/{ano}"


def mes_anterior(mes: str) -> str:
    ano, numero_mes = (int(parte) for parte in mes.split("-"))
    return f"{ano - 1}-12" if numero_mes == 1 else f"{ano}-{numero_mes - 1:02d}"
