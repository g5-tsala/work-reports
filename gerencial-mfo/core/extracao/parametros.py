"""Parametros globais do mes — aba `info`.

Cinco valores regem todo o calculo da planilha (`docs/calculos.md` §2). Aqui
eles sao lidos dos nomes definidos, nunca do texto exibido: `resumo!B4` mostra
o cambio arredondado ("US$ 1 = R$ 5,08") e as contas usam 5,0773.
"""

from __future__ import annotations

from typing import Any

from core.planilha import mes as ler_mes
from core.planilha import numero, texto

#: De-para `login -> apelido` do officer (`info!AK:AL`).
COL_LOGIN, COL_APELIDO = 37, 38
LINHA_INICIAL_DEPARA = 2
LINHA_FINAL_DEPARA = 200


def extrair(ctx) -> dict[str, Any]:
    pl = ctx.pl

    data_planilha = ler_mes(pl.valor_nome("data"))
    if data_planilha != ctx.mes_base:
        ctx.avisar(
            f"info!AP1 (mes da planilha) = {data_planilha}, mas a pasta de origem diz "
            f"{ctx.mes_base}. O mes-base do build e o da pasta."
        )

    dolar = numero(pl.valor_nome("dolar"))
    nwdays = numero(pl.valor_nome("nwdays_mes"))
    if not dolar:
        raise ValueError("cambio (info!AQ3) ausente ou nao numerico")
    if not nwdays:
        raise ValueError("dias uteis do mes (info!AQ5) ausentes ou nao numericos")

    return {
        "mes_base": ctx.mes_base,
        "data_planilha": data_planilha,
        "dolar": dolar,
        "cdi_mes": numero(pl.valor_nome("cdi_mes")),
        "nwdays_mes": int(nwdays),
        "officers_de_para": _de_para_officers(pl),
    }


def _de_para_officers(pl) -> dict[str, str]:
    """`{login: apelido}` — e o que liga `cons_officer` a `CEO-Dashboard`."""
    de_para: dict[str, str] = {}
    for linha in range(LINHA_INICIAL_DEPARA, LINHA_FINAL_DEPARA + 1):
        login = texto(pl.aba("info").cell(linha, COL_LOGIN).value)
        apelido = texto(pl.aba("info").cell(linha, COL_APELIDO).value)
        if login is None and apelido is None:
            continue
        if login:
            de_para[login] = apelido or login
    return de_para
