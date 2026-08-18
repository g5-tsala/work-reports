"""Aba: Net In/Out.

Captação **de cliente** — base sem as movimentações do próprio grupo G5. A
decomposição do OUT entre uso pessoal e saída para concorrência é o dado mais
acionável do relatório e abre a página.
"""

from __future__ import annotations

from typing import Any

from .. import formato, graficos
from ..contexto import Contexto
from ..pagina import pagina
from ..ui import Coluna, Linha, faixa_kpis, fonte, grafico, kpi, nota, num, secao, tabela

SECOES = ("IN", "OUT", "NET")
MOTIVOS = ("uso_pessoal", "saida_para_concorrencia")


@pagina(
    identificador="captacao-net",
    titulo="Net In/Out",
    grupo="Captação",
    ordem=10,
    subtitulo="Entradas e saídas de cliente, mês a mês. Não inclui movimentação dos fundos "
    "próprios da G5.",
)
def render(ctx: Contexto) -> str:
    onshore = ctx.bloco("captacao", "net_in_out", "onshore")
    offshore = ctx.bloco("captacao", "net_in_out", "offshore")

    return "".join(
        [
            _kpis(ctx, onshore, offshore),
            secao("Fluxo mensal — onshore", _grafico(ctx, onshore, "R$"), _motivos_de_saida(ctx, onshore)),
            secao(
                "Detalhe onshore (R$)",
                _tabela(ctx, onshore, "net-onshore"),
                fonte("net_in_out", ctx.rotulo_mes, "Base info_net_in_out, sem o grupo G5."),
            ),
            secao(
                "Detalhe offshore (US$)",
                _tabela(ctx, offshore, "net-offshore"),
                fonte("net_in_out", ctx.rotulo_mes, "Valores em US$; total do ano também em R$."),
            ),
            nota(
                "Esta página usa a base <strong>de cliente</strong>. O NET executado do "
                "<em>Dashboard</em>, que inclui os fundos de alocação da G5, é outra base e não "
                "deve ser somado a esta."
            ),
        ]
    )


def _secao_principal(ctx: Contexto, bloco: dict[str, Any], rotulo: str) -> dict[str, Any] | None:
    for linha in bloco["linhas"]:
        if linha["rotulo"] == rotulo and linha["secao"] == rotulo:
            return linha
    return None


def _kpis(ctx: Contexto, onshore: dict[str, Any], offshore: dict[str, Any]) -> str:
    posicao = ctx.posicao(onshore, ctx.mes_base)
    entrada = _secao_principal(ctx, onshore, "IN")
    saida = _secao_principal(ctx, onshore, "OUT")
    liquido = _secao_principal(ctx, onshore, "NET")
    liquido_off = _secao_principal(ctx, offshore, "NET")

    net_mes = liquido["valores"][posicao] if liquido and posicao is not None else None
    return faixa_kpis(
        kpi(
            "NET do mês (onshore)",
            formato.milhoes(net_mes),
            classe_delta=formato.classe_sinal(net_mes),
            detalhe=formato.mes_extenso(ctx.mes_base),
        ),
        kpi("IN do mês", formato.milhoes(entrada["valores"][posicao] if entrada else None)),
        kpi("OUT do mês", formato.milhoes(saida["valores"][posicao] if saida else None)),
        kpi(
            "NET no ano",
            formato.milhoes((liquido or {}).get("total")),
            detalhe=f"offshore: {formato.milhoes((liquido_off or {}).get('total_reais'))}",
        ),
    )


def _grafico(ctx: Contexto, bloco: dict[str, Any], moeda: str) -> str:
    entrada = _secao_principal(ctx, bloco, "IN")
    saida = _secao_principal(ctx, bloco, "OUT")
    liquido = _secao_principal(ctx, bloco, "NET")
    if not (entrada and saida and liquido):
        return ""

    svg = graficos.combo(
        ctx.rotulos(bloco["meses"]),
        [
            graficos.Serie("IN", entrada["valores"]),
            graficos.Serie("OUT", saida["valores"], cor=graficos.SERIES[1]),
        ],
        graficos.Serie("NET", liquido["valores"], cor=graficos.SERIES[2]),
        formatador_barra=lambda v: formato.em_milhoes(v, 0),
        formatador_linha=lambda v: formato.em_milhoes(v, 0),
        titulo="IN, OUT e NET por mês",
        empilhado=True,
        rotular_ultimo=True,
    )
    return grafico(
        svg,
        itens_legenda=[
            (f"IN ({moeda} mi)", graficos.SERIES[0]),
            (f"OUT ({moeda} mi)", graficos.SERIES[1]),
            (f"NET ({moeda} mi, linha)", graficos.SERIES[2]),
        ],
        rodape=fonte("net_in_out", ctx.rotulo_mes),
    )


def _motivos_de_saida(ctx: Contexto, bloco: dict[str, Any]) -> str:
    """Uso pessoal × saída para concorrência, somando todos os tipos de veículo."""
    meses = bloco["meses"]
    acumulado = {motivo: [0.0] * len(meses) for motivo in MOTIVOS}
    for linha in bloco["linhas"]:
        if linha["secao"] != "OUT" or linha["chave"] not in MOTIVOS:
            continue
        for posicao, valor in enumerate(linha["valores"]):
            if valor:
                acumulado[linha["chave"]][posicao] += valor

    svg = graficos.barras(
        ctx.rotulos(meses),
        [
            graficos.Serie("Uso pessoal", acumulado["uso_pessoal"]),
            graficos.Serie("Saída para concorrência", acumulado["saida_para_concorrencia"], cor=graficos.SERIES[1]),
        ],
        formatador=lambda v: formato.em_milhoes(v, 0),
        empilhado=True,
        titulo="Saídas por finalidade",
        altura=240,
    )
    return grafico(
        svg,
        itens_legenda=[
            ("Uso pessoal (R$ mi)", graficos.SERIES[0]),
            ("Saída para concorrência (R$ mi)", graficos.SERIES[1]),
        ],
        rodape=fonte("net_in_out", ctx.rotulo_mes, "Soma de todos os tipos de veículo."),
    )


def _tabela(ctx: Contexto, bloco: dict[str, Any], identificador: str) -> str:
    moeda = bloco["moeda"]
    escala = f"{moeda} mi"
    colunas = (
        [Coluna(f"Linha ({escala})")]
        + [Coluna(rotulo, numerica=True) for rotulo in ctx.rotulos(bloco["meses"])]
        + [Coluna("Ano", numerica=True)]
    )
    tem_reais = any("total_reais" in linha for linha in bloco["linhas"])
    if tem_reais:
        colunas.append(Coluna("Ano (R$ mi)", numerica=True))

    linhas = []
    for registro in bloco["linhas"]:
        eh_percentual = registro["chave"] == "roa_pct"
        formatador = formato.percentual if eh_percentual else (lambda v: formato.em_milhoes(v, 2))
        celulas: list[Any] = [registro["rotulo"]]
        celulas += [num(formatador(valor), formato.classe_sinal(valor) if not eh_percentual else "") for valor in registro["valores"]]
        celulas.append(
            num(formato.NAO_APLICAVEL if eh_percentual else formatador(registro["total"]))
        )
        if tem_reais:
            celulas.append(
                num(
                    formato.NAO_APLICAVEL
                    if eh_percentual
                    else formato.em_milhoes(registro.get("total_reais"), 2)
                )
            )
        classe = "subtotal" if registro["nivel"] == 0 else ""
        linhas.append(Linha(celulas, classe=classe, nivel=registro["nivel"]))

    return tabela(colunas, linhas, identificador=identificador, ordenavel=False)
