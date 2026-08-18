"""Graficos em SVG inline, gerados no build.

Sem biblioteca e sem JavaScript: os dados sao fixos no momento em que o HTML e
escrito, entao o grafico pode ser vetor estatico. Ele imprime bem, funciona com
o JS desligado e nao depende de rede.

Regras do design system aplicadas aqui: paleta na ordem canonica (no maximo 5
series), gridlines so horizontais em `--g5-line`, eixos em `--g5-slate-aa`
tamanho caption, barras solidas sem contorno, linha de 2px, donut com no maximo
5 fatias. As cores saem como `var(--g5-*)` — o SVG e inline, herda os tokens, e
uma mudanca de paleta continua acontecendo num lugar so.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from html import escape

SERIES = (
    "var(--g5-data-blue)",
    "var(--g5-data-wine)",
    "var(--g5-data-neutral)",
    "var(--g5-data-blue-light)",
    "var(--g5-data-wine-light)",
)
MAXIMO_SERIES = len(SERIES)
MAXIMO_FATIAS = 5

#: Cores de sinal, para série que oscila em torno do zero.
COR_POSITIVO = "var(--g5-positive)"
COR_NEGATIVO = "var(--g5-negative)"

LARGURA = 880
ALTURA = 300
MARGEM = {"esquerda": 72, "direita": 16, "topo": 12, "base": 36}
DIVISOES = 4


class Serie:
    """Uma serie de dados com o rotulo que aparece na legenda."""

    def __init__(self, rotulo: str, valores: Sequence[float | None], cor: str | None = None):
        self.rotulo = rotulo
        self.valores = list(valores)
        self.cor = cor


def cor_da_serie(indice: int, serie: Serie) -> str:
    return serie.cor or SERIES[indice % MAXIMO_SERIES]


# --------------------------------------------------------------------------
# Escala e eixos
# --------------------------------------------------------------------------


def _limites(
    series: Sequence[Serie], empilhado: bool = False, ancorar_zero: bool = True
) -> tuple[float, float]:
    if empilhado:
        totais_positivos, totais_negativos = [], []
        for posicao in range(max((len(s.valores) for s in series), default=0)):
            valores = [s.valores[posicao] for s in series if posicao < len(s.valores)]
            totais_positivos.append(sum(v for v in valores if v and v > 0))
            totais_negativos.append(sum(v for v in valores if v and v < 0))
        valores = totais_positivos + totais_negativos
    else:
        valores = [v for serie in series for v in serie.valores if v is not None]
    if not valores:
        return 0.0, 1.0
    minimo, maximo = min(valores), max(valores)
    if ancorar_zero:
        minimo, maximo = min(minimo, 0.0), max(maximo, 0.0)
    return (0.0, 1.0) if minimo == maximo else (minimo, maximo)


#: Multiplos aceitos para o passo do eixo, do mais fechado ao mais aberto.
PASSOS = (1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10)


def _escala_agradavel(minimo: float, maximo: float, divisoes: int = DIVISOES) -> list[float]:
    """Marcas de eixo em passos redondos, cobrindo o intervalo inteiro.

    A ultima marca e sempre >= o maior valor: se ela ficasse abaixo, a barra ou
    o ponto correspondente sairia da area de plotagem e seria cortado pelo
    viewBox — sem nenhum sinal visivel de que faltou dado.
    """
    from math import ceil, floor, log10

    amplitude = (maximo - minimo) or 1.0
    bruto = amplitude / divisoes
    magnitude = 10 ** floor(log10(abs(bruto))) if bruto else 1.0
    passo = next((magnitude * m for m in PASSOS if magnitude * m >= bruto), bruto or 1.0)
    primeira, ultima = floor(minimo / passo), ceil(maximo / passo)
    if primeira == ultima:
        ultima += 1
    return [round(passo * indice, 10) for indice in range(primeira, ultima + 1)]


def _texto(x: float, y: float, conteudo: str, classe: str, ancora: str = "middle") -> str:
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{ancora}" class="{classe}">'
        f"{escape(str(conteudo))}</text>"
    )


def _moldura(
    marcas: Sequence[float],
    categorias: Sequence[str],
    formatador: Callable[[float], str],
    largura: int,
    altura: int,
    passo_rotulos: int = 1,
) -> tuple[str, Callable[[float], float], Callable[[int], float], float]:
    """Gridlines, eixos e as funcoes de projecao de valor e categoria."""
    esquerda, direita = MARGEM["esquerda"], largura - MARGEM["direita"]
    topo, base = MARGEM["topo"], altura - MARGEM["base"]
    minimo, maximo = marcas[0], marcas[-1]

    def y(valor: float) -> float:
        return base - (valor - minimo) / (maximo - minimo or 1) * (base - topo)

    largura_faixa = (direita - esquerda) / max(len(categorias), 1)

    def x(indice: int) -> float:
        return esquerda + largura_faixa * (indice + 0.5)

    partes = []
    for marca in marcas:
        altura_marca = y(marca)
        partes.append(
            f'<line x1="{esquerda}" y1="{altura_marca:.1f}" x2="{direita}" '
            f'y2="{altura_marca:.1f}" class="g5-grade"/>'
        )
        partes.append(
            _texto(esquerda - 10, altura_marca + 4, formatador(marca), "g5-eixo", "end")
        )
    for indice, categoria in enumerate(categorias):
        if indice % passo_rotulos == 0:
            partes.append(_texto(x(indice), altura - 12, categoria, "g5-eixo"))
    return "".join(partes), y, x, largura_faixa


def _svg(conteudo: str, titulo: str, largura: int, altura: int) -> str:
    return (
        f'<svg class="g5-grafico" viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="{escape(titulo)}" preserveAspectRatio="xMidYMid meet">{conteudo}</svg>'
    )


def _passo_de_rotulos(quantidade: int, largura: int) -> int:
    """Evita rotulo de eixo sobreposto quando a serie e longa."""
    cabem = max(int((largura - MARGEM["esquerda"] - MARGEM["direita"]) / 56), 1)
    return max(1, -(-quantidade // cabem))


# --------------------------------------------------------------------------
# Tipos de grafico
# --------------------------------------------------------------------------


def linhas(
    categorias: Sequence[str],
    series: Sequence[Serie],
    *,
    formatador: Callable[[float], str],
    titulo: str = "",
    altura: int = ALTURA,
    largura: int = LARGURA,
    rotular_ultimo: bool = False,
    ancorar_zero: bool = False,
) -> str:
    """Linha categórica. `rotular_ultimo` escreve o valor no último ponto.

    O rótulo direto vale o pixel: tira o vaivém entre legenda e traço, e é o
    que mantém o gráfico legível impresso em preto e branco, onde o azul e o
    wine viram o mesmo cinza.

    O eixo **não** é ancorado no zero por padrão. Linha codifica variação, não
    magnitude por área: forçar o zero num AUM que anda 2% ao mês achata a série
    numa reta e esconde justamente o que ela existe para mostrar. Barra é o
    contrário — ali o zero é obrigatório, e por isso `barras()` não tem esta
    opção.
    """
    series = list(series)[:MAXIMO_SERIES]
    marcas = _escala_agradavel(*_limites(series, ancorar_zero=ancorar_zero))
    grade, y, x, _ = _moldura(
        marcas, categorias, formatador, largura, altura, _passo_de_rotulos(len(categorias), largura)
    )

    partes = [grade]
    for indice, serie in enumerate(series):
        pontos = [
            (x(posicao), y(valor))
            for posicao, valor in enumerate(serie.valores)
            if valor is not None and posicao < len(categorias)
        ]
        if not pontos:
            continue
        caminho = " ".join(
            f"{'M' if i == 0 else 'L'}{px:.1f},{py:.1f}" for i, (px, py) in enumerate(pontos)
        )
        cor = cor_da_serie(indice, serie)
        partes.append(f'<path d="{caminho}" fill="none" stroke="{cor}" class="g5-linha"/>')
        if len(pontos) < 20:
            partes += [f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{cor}"/>' for px, py in pontos]
        if rotular_ultimo:
            ultimo_valor = next(
                (v for v in reversed(serie.valores[: len(categorias)]) if v is not None), None
            )
            if ultimo_valor is not None:
                px, py = pontos[-1]
                partes.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{cor}"/>')
                partes.append(
                    f'<text x="{px - 8:.1f}" y="{py - 10:.1f}" text-anchor="end" '
                    f'class="g5-rotulo-ponto" fill="{cor}">{escape(formatador(ultimo_valor))}</text>'
                )
    return _svg("".join(partes), titulo, largura, altura)


def barras(
    categorias: Sequence[str],
    series: Sequence[Serie],
    *,
    formatador: Callable[[float], str],
    empilhado: bool = False,
    titulo: str = "",
    altura: int = ALTURA,
    largura: int = LARGURA,
    por_sinal: bool = False,
) -> str:
    """Barra vertical, agrupada ou empilhada.

    `por_sinal` colore cada barra pelo sinal do valor, e só faz sentido em
    série que oscila em torno do zero — variação, fluxo, resultado. Aplicar a
    nível (AUM, receita) inventaria uma leitura de bom/ruim que o dado não tem.
    """
    partes, _, _, _ = _desenhar_barras(
        categorias,
        series,
        formatador=formatador,
        empilhado=empilhado,
        altura=altura,
        largura=largura,
        por_sinal=por_sinal,
    )
    return _svg("".join(partes), titulo, largura, altura)


def _desenhar_barras(
    categorias: Sequence[str],
    series: Sequence[Serie],
    *,
    formatador: Callable[[float], str],
    empilhado: bool,
    altura: int,
    largura: int,
    por_sinal: bool,
    series_na_escala: Sequence[Serie] = (),
):
    """Constroi as barras e devolve as pecas e a projecao usada.

    Expor a projecao e o que permite a linha do `combo` dividir o **mesmo**
    eixo das barras quando as duas series falam a mesma unidade.
    """
    series = list(series)[:MAXIMO_SERIES]
    minimo, maximo = _limites(series, empilhado)
    for extra in series_na_escala:
        outro_minimo, outro_maximo = _limites([extra])
        minimo, maximo = min(minimo, outro_minimo), max(maximo, outro_maximo)
    marcas = _escala_agradavel(minimo, maximo)
    grade, y, x, largura_faixa = _moldura(
        marcas, categorias, formatador, largura, altura, _passo_de_rotulos(len(categorias), largura)
    )

    partes = [grade]
    linha_zero = y(0)
    partes.append(
        f'<line x1="{MARGEM["esquerda"]}" y1="{linha_zero:.1f}" '
        f'x2="{largura - MARGEM["direita"]}" y2="{linha_zero:.1f}" class="g5-zero"/>'
    )

    quantidade = 1 if empilhado else max(len(series), 1)
    largura_barra = largura_faixa * 0.6 / quantidade

    for posicao in range(len(categorias)):
        topo_positivo = topo_negativo = 0.0
        for indice, serie in enumerate(series):
            valor = serie.valores[posicao] if posicao < len(serie.valores) else None
            if valor is None:
                continue
            cor = COR_POSITIVO if valor >= 0 else COR_NEGATIVO
            if not por_sinal:
                cor = cor_da_serie(indice, serie)
            if empilhado:
                base = topo_positivo if valor >= 0 else topo_negativo
                y1, y2 = y(base), y(base + valor)
                if valor >= 0:
                    topo_positivo += valor
                else:
                    topo_negativo += valor
                px = x(posicao) - largura_barra / 2
            else:
                y1, y2 = linha_zero, y(valor)
                px = x(posicao) - (largura_faixa * 0.6) / 2 + indice * largura_barra
            partes.append(
                f'<rect x="{px:.1f}" y="{min(y1, y2):.1f}" width="{largura_barra:.1f}" '
                f'height="{abs(y2 - y1):.1f}" fill="{cor}"/>'
            )
    return partes, y, x, largura_faixa


def combo(
    categorias: Sequence[str],
    series_barra: Sequence[Serie],
    serie_linha: Serie,
    *,
    formatador_barra: Callable[[float], str],
    formatador_linha: Callable[[float], str],
    empilhado: bool = True,
    titulo: str = "",
    altura: int = ALTURA,
    largura: int = LARGURA,
    por_sinal: bool = False,
    rotular_ultimo: bool = False,
    eixo_proprio: bool = False,
) -> str:
    """Barras com uma linha por cima.

    Por padrao a linha divide o **mesmo** eixo das barras. Segundo eixo so e
    aceitavel quando as duas series nao compartilham unidade — IN/OUT em R$ mi
    e um NET tambem em R$ mi nao e esse caso, e dois eixos ali fariam a mesma
    grandeza medir duas alturas diferentes no mesmo desenho. Quando as unidades
    forem realmente distintas (AUM em R$ mi contra receita em R$), passe
    `eixo_proprio=True` e os dois eixos saem rotulados.
    """
    margem_direita = MARGEM["direita"] + (56 if eixo_proprio else 0)
    partes, y_barra, x, _ = _desenhar_barras(
        categorias,
        series_barra,
        formatador=formatador_barra,
        empilhado=empilhado,
        altura=altura,
        largura=largura - (margem_direita - MARGEM["direita"]),
        por_sinal=por_sinal,
        series_na_escala=() if eixo_proprio else [serie_linha],
    )

    if eixo_proprio:
        marcas = _escala_agradavel(*_limites([serie_linha]))
        minimo, maximo = marcas[0], marcas[-1]
        topo, base = MARGEM["topo"], altura - MARGEM["base"]

        def y(valor: float) -> float:
            return base - (valor - minimo) / (maximo - minimo or 1) * (base - topo)

        borda = largura - margem_direita
        partes += [
            _texto(borda + 8, y(marca) + 4, formatador_linha(marca), "g5-eixo", "start")
            for marca in marcas
        ]
    else:
        y = y_barra

    pontos = [
        (x(posicao), y(valor))
        for posicao, valor in enumerate(serie_linha.valores)
        if valor is not None and posicao < len(categorias)
    ]
    if pontos:
        caminho = " ".join(
            f"{'M' if i == 0 else 'L'}{px:.1f},{py:.1f}" for i, (px, py) in enumerate(pontos)
        )
        cor = serie_linha.cor or SERIES[1]
        partes.append(f'<path d="{caminho}" fill="none" stroke="{cor}" class="g5-linha"/>')
        if len(pontos) < 20:
            partes += [f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{cor}"/>' for px, py in pontos]
        if rotular_ultimo:
            ultimo = next(
                (v for v in reversed(serie_linha.valores[: len(categorias)]) if v is not None), None
            )
            if ultimo is not None:
                px, py = pontos[-1]
                partes.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4" fill="{cor}"/>')
                partes.append(
                    f'<text x="{px - 8:.1f}" y="{py - 10:.1f}" text-anchor="end" '
                    f'class="g5-rotulo-ponto" fill="{cor}">{escape(formatador_linha(ultimo))}</text>'
                )
    return _svg("".join(partes), titulo, largura, altura)


def barras_horizontais(
    itens: Sequence[tuple[str, float | None]],
    *,
    formatador: Callable[[float], str],
    titulo: str = "",
    largura: int = LARGURA,
    cor: str = SERIES[0],
    largura_rotulo: int = 220,
) -> str:
    """Ranking. É a forma canônica quando um donut passaria de cinco fatias."""
    itens = [(rotulo, valor) for rotulo, valor in itens if valor is not None]
    if not itens:
        return ""
    altura_linha, espaco = 26, 6
    altura = len(itens) * (altura_linha + espaco) + 16
    maximo = max(abs(valor) for _, valor in itens) or 1
    disponivel = largura - largura_rotulo - 140

    partes = []
    for indice, (rotulo, valor) in enumerate(itens):
        y = 8 + indice * (altura_linha + espaco)
        comprimento = abs(valor) / maximo * disponivel
        partes.append(_texto(largura_rotulo - 12, y + 17, rotulo, "g5-rotulo-barra", "end"))
        partes.append(
            f'<rect x="{largura_rotulo}" y="{y}" width="{comprimento:.1f}" '
            f'height="{altura_linha}" fill="{cor}"/>'
        )
        partes.append(
            _texto(largura_rotulo + comprimento + 10, y + 17, formatador(valor), "g5-valor-barra", "start")
        )
    return _svg("".join(partes), titulo, largura, altura)


def donut(
    fatias: Sequence[tuple[str, float | None]],
    *,
    formatador: Callable[[float], str],
    titulo: str = "",
    tamanho: int = 260,
) -> str:
    """No maximo 5 fatias, da maior para a menor no sentido horario."""
    fatias = [(rotulo, valor) for rotulo, valor in fatias if valor and valor > 0][:MAXIMO_FATIAS]
    total = sum(valor for _, valor in fatias)
    if not total:
        return ""

    raio_externo, raio_interno = tamanho / 2 - 8, tamanho / 2 - 44
    centro = tamanho / 2
    angulo = -90.0
    partes = []
    for indice, (_, valor) in enumerate(fatias):
        varredura = valor / total * 360
        fim = angulo + varredura
        partes.append(
            f'<path d="{_setor(centro, centro, raio_externo, raio_interno, angulo, fim)}" '
            f'fill="{SERIES[indice % MAXIMO_SERIES]}"/>'
        )
        angulo = fim
    partes.append(_texto(centro, centro + 6, formatador(total), "g5-donut-total"))
    return _svg("".join(partes), titulo, tamanho, tamanho)


def _setor(cx: float, cy: float, externo: float, interno: float, inicio: float, fim: float) -> str:
    from math import cos, pi, sin

    def ponto(raio: float, graus: float) -> tuple[float, float]:
        radianos = graus * pi / 180
        return cx + raio * cos(radianos), cy + raio * sin(radianos)

    maior = 1 if (fim - inicio) > 180 else 0
    x1, y1 = ponto(externo, inicio)
    x2, y2 = ponto(externo, fim)
    x3, y3 = ponto(interno, fim)
    x4, y4 = ponto(interno, inicio)
    return (
        f"M{x1:.2f},{y1:.2f} A{externo:.2f},{externo:.2f} 0 {maior} 1 {x2:.2f},{y2:.2f} "
        f"L{x3:.2f},{y3:.2f} A{interno:.2f},{interno:.2f} 0 {maior} 0 {x4:.2f},{y4:.2f} Z"
    )
