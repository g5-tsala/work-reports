"""Etapa 2 do pipeline: o checklist bloqueante de `docs/validacao.md` §1.

Roda sobre o JSON extraido, nunca sobre a planilha — assim vale tambem quando
so a renderizacao e reexecutada. Regra inviolavel 5: **nenhum dashboard e
gerado sobre base inconsistente**.

Cada item devolve `ok=True/False` e um detalhe legivel. Itens que nao puderam
ser avaliados (dado ausente no JSON) sao marcados `ok=None` e nao bloqueiam,
mas aparecem no relatorio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core import config


@dataclass
class Item:
    numero: int
    titulo: str
    ok: bool | None
    detalhe: str

    @property
    def bloqueia(self) -> bool:
        return self.ok is False


@dataclass
class Relatorio:
    itens: list[Item] = field(default_factory=list)

    def adicionar(self, numero: int, titulo: str, ok: bool | None, detalhe: str = "") -> None:
        self.itens.append(Item(numero, titulo, ok, detalhe))

    @property
    def falhas(self) -> list[Item]:
        return [item for item in self.itens if item.bloqueia]

    @property
    def nao_avaliados(self) -> list[Item]:
        return [item for item in self.itens if item.ok is None]

    @property
    def ok(self) -> bool:
        return not self.falhas


def validar(dados: dict[str, Any]) -> Relatorio:
    relatorio = Relatorio()
    for verificacao in (
        _checks_da_planilha,
        _aum_total,
        _soma_officers,
        _soma_categorias,
        _net_igual_in_mais_out,
        _qtd_portfolios,
        _cambio,
        _mes_de_fechamento,
        _mensalizacao,
        _qtd_grupos,
    ):
        verificacao(dados, relatorio)
    return relatorio


# --------------------------------------------------------------------------
# Auxiliares
# --------------------------------------------------------------------------


def _proximo(a: float | None, b: float | None, tolerancia: float = config.TOLERANCIA_RELATIVA) -> bool:
    if a is None or b is None:
        return False
    escala = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= tolerancia * escala


def _linha_por_chave(linhas: list[dict[str, Any]], chave: str) -> dict[str, Any] | None:
    for linha in linhas:
        if linha.get("chave") == chave:
            return linha
    return None


def _indice_do_mes(meses: list[str], mes: str) -> int | None:
    try:
        return meses.index(mes)
    except ValueError:
        return None


def _formatar(valor: float | None) -> str:
    return "n/d" if valor is None else f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


# --------------------------------------------------------------------------
# Itens do checklist
# --------------------------------------------------------------------------


def _checks_da_planilha(dados, relatorio) -> None:
    checks = dados.get("checks_planilha") or []
    falhos = [c for c in checks if not c["ok"]]
    detalhe = f"{len(checks) - len(falhos)}/{len(checks)} checks zerados"
    if falhos:
        piores = ", ".join(f"{c['origem']}={c['valor']:.6g}" for c in falhos[:5])
        detalhe += f"; fora da tolerancia: {piores}"
    relatorio.adicionar(1, "Checks embutidos na planilha zerados", not falhos if checks else None, detalhe)


def _aum_total(dados, relatorio) -> None:
    aum = dados["consolidado"]["aum"]
    soma = (aum.get("onshore") or 0) + (aum.get("offshore") or 0)
    ok = _proximo(soma, aum.get("total"))
    relatorio.adicionar(
        2,
        "AUM Total = Onshore + Offshore",
        ok,
        f"onshore + offshore = {_formatar(soma)} vs total = {_formatar(aum.get('total'))}",
    )


def _soma_officers(dados, relatorio) -> None:
    tabela = dados["officers"]["tabela_ceo"]
    total = next((linha for linha in tabela if linha["tipo"] == "total"), None)
    partes = [linha for linha in tabela if linha["tipo"] in ("officer", "fdos_alocacao")]
    if total is None or not partes:
        relatorio.adicionar(3, "Soma dos officers = Total (CEO-Dashboard)", None, "tabela ausente no JSON")
        return

    divergencias = []
    for campo in ("aum_mi", "receita", "qtd_portfolios"):
        soma = sum(linha[campo] or 0 for linha in partes)
        if not _proximo(soma, total[campo]):
            divergencias.append(f"{campo}: {_formatar(soma)} vs {_formatar(total[campo])}")
    relatorio.adicionar(
        3,
        "Soma dos officers = Total (CEO-Dashboard)",
        not divergencias,
        "; ".join(divergencias) or f"{len(partes)} linhas somam o total em AUM, receita e qtd.",
    )


def _soma_categorias(dados, relatorio) -> None:
    bloco = dados["consolidado"]["roa_categoria"]
    divergencias = []
    for campo in ("qtd", "aum", "receita_anualizada"):
        soma = sum(linha[campo] or 0 for linha in bloco["linhas"])
        if not _proximo(soma, bloco["total"].get(campo)):
            divergencias.append(f"{campo}: {_formatar(soma)} vs {_formatar(bloco['total'].get(campo))}")
    relatorio.adicionar(
        4,
        "Soma das categorias = Total (resumo)",
        not divergencias,
        "; ".join(divergencias) or "qtd, AUM e receita fecham com o total",
    )


def _net_igual_in_mais_out(dados, relatorio) -> None:
    divergencias = []
    avaliados = 0
    for origem, bloco in dados["captacao"]["net_in_out"].items():
        secoes = {
            linha["rotulo"]: linha
            for linha in bloco["linhas"]
            if linha["rotulo"] in ("IN", "OUT", "NET") and linha["rotulo"] == linha["secao"]
        }
        if len(secoes) != 3:
            continue
        for posicao, mes in enumerate(bloco["meses"]):
            entrada = secoes["IN"]["valores"][posicao] or 0
            saida = secoes["OUT"]["valores"][posicao] or 0
            liquido = secoes["NET"]["valores"][posicao] or 0
            avaliados += 1
            if not _proximo(entrada + saida, liquido):
                divergencias.append(f"{origem} {mes}: IN+OUT={_formatar(entrada + saida)} vs NET={_formatar(liquido)}")
        for campo in ("total",):
            entrada, saida, liquido = (secoes[s][campo] or 0 for s in ("IN", "OUT", "NET"))
            avaliados += 1
            if not _proximo(entrada + saida, liquido):
                divergencias.append(f"{origem} acumulado: IN+OUT={_formatar(entrada + saida)} vs NET={_formatar(liquido)}")

    relatorio.adicionar(
        5,
        "NET = IN + OUT (net_in_out)",
        (not divergencias) if avaliados else None,
        "; ".join(divergencias[:5]) or f"{avaliados} pontos conferidos",
    )


def _qtd_portfolios(dados, relatorio) -> None:
    resumo = dados["consolidado"]["roa_categoria"]["total"].get("qtd")
    tabela = dados["officers"]["tabela_ceo"]
    total_ceo = next((l["qtd_portfolios"] for l in tabela if l["tipo"] == "total"), None)

    mes = dados["meta"]["mes_base"]
    ativos = 0
    for origem in ("onshore", "offshore"):
        base = dados["carteira"]["portfolios"][origem]
        posicao = _indice_do_mes(base["meses"], mes)
        if posicao is None:
            continue
        ativos += sum(
            1
            for linha in base["linhas"]
            if (linha["aum"][posicao] or 0) > 0 or (linha["receita"][posicao] or 0) > 0
        )

    ok = _proximo(resumo, total_ceo) and _proximo(resumo, float(ativos))
    relatorio.adicionar(
        6,
        "Qtd. de portfolios bate entre resumo, CEO-Dashboard e as bases",
        ok,
        f"resumo={_formatar(resumo)} | CEO={_formatar(total_ceo)} | "
        f"ar_onshore+ar_offshore com AUM ou receita > 0 = {ativos}",
    )


def _cambio(dados, relatorio) -> None:
    dolar = dados["parametros"]["dolar"]
    dolar_regiao = dados["carteira"]["regioes"].get("dolar_offshore")
    ok = _proximo(dolar, dolar_regiao)
    relatorio.adicionar(
        7,
        "Cambio consistente entre info!AQ3 e regiao!G2",
        ok if dolar_regiao is not None else None,
        f"info!AQ3={dolar} | regiao!G2={dolar_regiao}",
    )


def _mes_de_fechamento(dados, relatorio) -> None:
    mes = dados["meta"]["mes_base"]
    problemas = []
    for origem in ("onshore", "offshore"):
        bloco = dados["historico"]["aum_receita"][origem]
        if not bloco["meses"] or bloco["meses"][-1] != mes:
            problemas.append(f"aum_receita/{origem}: ultima coluna = {bloco['meses'][-1:] or 'vazia'}")
            continue
        aum = _linha_por_chave(bloco["linhas"], "aum_rs") or _linha_por_chave(bloco["linhas"], "aum_usd")
        if aum is None or not aum["valores"] or not aum["valores"][-1]:
            problemas.append(f"aum_receita/{origem}: AUM do mes-base zerado ou ausente")
    relatorio.adicionar(
        8,
        "Mes de fechamento presente e nao-zerado nas series",
        not problemas,
        "; ".join(problemas) or f"series terminam em {mes} com AUM preenchido",
    )


def _mensalizacao(dados, relatorio) -> None:
    """`receita_competencia * 21 / dias_uteis` reproduz a receita mensalizada.

    Vale so no onshore: o offshore entra por competencia (`docs/calculos.md` §3.1).
    """
    bloco = dados["historico"]["aum_receita"]["onshore"]
    competencia = _linha_por_chave(bloco["linhas"], "receita_rs")
    mensalizada = _linha_por_chave(bloco["linhas"], "receita_mens_rs")
    dias_uteis = bloco["dias_uteis"][-1] if bloco["dias_uteis"] else None
    if not competencia or not mensalizada or not bloco["meses"]:
        relatorio.adicionar(9, "Mensalizacao da receita onshore", None, "linhas nao encontradas no JSON")
        return

    esperado = (competencia["valores"][-1] or 0) / dias_uteis * 21 if dias_uteis else None
    lido = mensalizada["valores"][-1]
    ok = _proximo(esperado, lido, tolerancia=1e-4)

    consolidado = dados["consolidado"]["receita_mens"]["onshore"]
    ok = ok and _proximo(lido, consolidado, tolerancia=1e-4)
    relatorio.adicionar(
        9,
        "Mensalizacao da receita onshore",
        ok,
        f"competencia/{dias_uteis}*21 = {_formatar(esperado)} | aum_receita = {_formatar(lido)} | "
        f"resumo!H7 = {_formatar(consolidado)}",
    )


def _qtd_grupos(dados, relatorio) -> None:
    """Recalcula Qtd. Grupos por officer e por backup a partir das bases.

    E o teste mais barato de que o mapeamento das colunas de dimensao esta
    correto (`docs/validacao.md` §1.10). A regra vem de `docs/calculos.md` §3.5:
    grupos distintos em que a pessoa e titular (ou backup), contando apenas
    portfolios com AUM **ou** receita > 0 no mes, unindo onshore e offshore.
    """
    mes = dados["meta"]["mes_base"]
    por_officer: dict[str, set[str]] = {}
    por_backup: dict[str, set[str]] = {}
    distintos: set[str] = set()

    for origem in ("onshore", "offshore"):
        base = dados["carteira"]["portfolios"][origem]
        posicao = _indice_do_mes(base["meses"], mes)
        if posicao is None:
            relatorio.adicionar(10, "Qtd. Grupos por officer e por backup", None, f"{origem} sem o mes {mes}")
            return
        for linha in base["linhas"]:
            ativo = (linha["aum"][posicao] or 0) > 0 or (linha["receita"][posicao] or 0) > 0
            grupo = linha.get("grupo")
            if not ativo or not grupo:
                continue
            distintos.add(grupo)
            if linha.get("officer"):
                por_officer.setdefault(linha["officer"], set()).add(grupo)
            if linha.get("backup"):
                por_backup.setdefault(linha["backup"], set()).add(grupo)

    divergencias = []
    avaliados = 0
    for bloco in dados["officers"]["blocos"]:
        nome = bloco["nome"]
        posicao = _indice_do_mes(bloco["meses"], mes)
        if posicao is None or nome is None:
            continue
        esperados = {
            "qtd_grupos_officer": len(por_officer.get(nome, set())),
            "qtd_grupos_backup": len(por_backup.get(nome, set())),
        }
        for chave, esperado in esperados.items():
            linha = _linha_por_chave(bloco["linhas"], chave)
            if linha is None:
                continue
            avaliados += 1
            lido = linha["valores"][posicao]
            if lido is None or int(lido) != esperado:
                divergencias.append(f"{nome}/{chave}: planilha={lido} vs recalculo={esperado}")

    total_planilha = dados["consolidado"]["roa_grupo"]["total"].get("qtd")
    avaliados += 1
    if not _proximo(float(len(distintos)), total_planilha):
        divergencias.append(f"total de grupos distintos: planilha={total_planilha} vs recalculo={len(distintos)}")

    relatorio.adicionar(
        10,
        "Qtd. Grupos por officer e por backup",
        (not divergencias) if avaliados else None,
        "; ".join(divergencias[:5]) or f"{avaliados} conferencias, {len(distintos)} grupos distintos",
    )
