"""Graficos em SVG inline, gerados no build.

Sem biblioteca e sem JavaScript: os dados sao fixos no momento em que o HTML e
escrito, entao o grafico pode ser vetor estatico. Ele imprime bem, funciona com
o JS desligado e nao depende de rede. O unico JS que encosta em grafico e o
tooltip: o SVG carrega o conteudo em `data-dica` e o `app.js` so o exibe.

Regras do design system aplicadas aqui: paleta na ordem canonica (no maximo 5
series), gridlines so horizontais em `--g5-line`, eixos em `--g5-slate-aa`
tamanho caption, barras solidas sem contorno, linha de 2px, donut com no maximo
5 fatias. As cores saem como `var(--g5-*)` — o SVG e inline, herda os tokens, e
uma mudanca de paleta continua acontecendo num lugar so.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from html import escape
from typing import Any

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

#: O viewBox nao e pixel: o SVG ocupa 100% da largura e a altura sai da
#: proporcao. Com 1.344px de conteudo (`.g5-main` no maximo), 1200x224 rende
#: ~250px de altura — o teto de `.g5-grafico--serie`. Mexer nesta razao e mexer
#: na altura de todo grafico de serie do dashboard.
LARGURA = 1200
ALTURA = 224
#: `base_inclinada` cobre a diagonal do rotulo girado, que ocupa mais altura
#: que o texto deitado.
MARGEM = {"esquerda": 72, "direita": 16, "topo": 20, "base": 36, "base_inclinada": 50}
DIVISOES = 4

#: Altura minima de um segmento empilhado para caber o rotulo dentro dele —
#: pouco acima do corpo da fonte de `.g5-valor-dentro`, que e o que de fato
#: precisa caber.
ALTURA_MINIMA_ROTULO = 12


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


def _texto(
    x: float,
    y: float,
    conteudo: str,
    classe: str,
    ancora: str = "middle",
    cor: str = "",
    rotacao: float = 0,
) -> str:
    # `style` e nao o atributo `fill`: atributo de apresentacao perde para
    # qualquer regra CSS, e `.g5-valor-barra` ja declara um `fill` proprio.
    preenchimento = f' style="fill:{cor}"' if cor else ""
    giro = f' transform="rotate({rotacao:g} {x:.1f} {y:.1f})"' if rotacao else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{ancora}" class="{classe}"'
        f"{preenchimento}{giro}>{escape(str(conteudo))}</text>"
    )


def _moldura(
    marcas: Sequence[float],
    categorias: Sequence[str],
    formatador: Callable[[float], str],
    largura: int,
    altura: int,
    passo_rotulos: int = 1,
    inclinar: bool = False,
) -> tuple[str, Callable[[float], float], Callable[[int], float], float]:
    """Gridlines, eixos e as funcoes de projecao de valor e categoria."""
    esquerda, direita = MARGEM["esquerda"], largura - MARGEM["direita"]
    base_reservada = MARGEM["base_inclinada"] if inclinar else MARGEM["base"]
    topo, base = MARGEM["topo"], altura - base_reservada
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
        if inclinar:
            # Ancorado no fim e girado -45°, o rotulo desce para a esquerda a
            # partir do tick: termina embaixo da categoria que descreve e nao
            # invade a area de plotagem. E o que permite mostrar todos os
            # pontos de uma serie longa sem pular um sim, um nao.
            partes.append(
                _texto(x(indice), base + 12, categoria, "g5-eixo g5-eixo--inclinado", "end", rotacao=-45)
            )
        elif indice % passo_rotulos == 0:
            partes.append(_texto(x(indice), altura - 12, categoria, "g5-eixo"))
    return "".join(partes), y, x, largura_faixa


#: Os dois eixos de crescimento, que o CSS limita de formas diferentes: serie
#: cresce na horizontal (altura tem teto), ranking cresce na vertical (nao tem).
CLASSE_SERIE = "g5-grafico--serie"
CLASSE_RANKING = "g5-grafico--ranking"
CLASSE_DONUT = "g5-grafico--donut"


def _svg(conteudo: str, titulo: str, largura: int, altura: int, classe: str = CLASSE_SERIE) -> str:
    return (
        f'<svg class="g5-grafico {classe}" viewBox="0 0 {largura} {altura}" role="img" '
        f'aria-label="{escape(titulo)}" preserveAspectRatio="xMidYMid meet">{conteudo}</svg>'
    )


def _dica(titulo: str, linhas: Sequence[Sequence[Any]]) -> str:
    """Conteúdo do tooltip, já escapado para ir num atributo `data-dica`.

    Cada linha é `[rótulo, valor formatado, cor, total?]`: sem cor, ou com o
    quarto item verdadeiro, a linha sai como total — separada por um fio.
    """
    return escape(json.dumps({"titulo": titulo, "linhas": [list(linha) for linha in linhas]}, ensure_ascii=False))


def _camada_dicas(
    categorias: Sequence[str],
    x: Callable[[int], float],
    largura_faixa: float,
    altura: int,
    linhas_por_categoria: Sequence[Sequence[Sequence[Any]]],
) -> list[str]:
    """Um alvo de hover por categoria, cobrindo a faixa inteira dela.

    Desenhado por cima das marcas (`.g5-alvo--sobre`, transparente): o leitor
    mira a coluna, não um ponto de 3px ou uma barra curta.
    """
    topo, base = MARGEM["topo"], altura - MARGEM["base"]
    return [
        f'<g class="g5-com-dica" data-dica="{_dica(categoria, linhas)}">'
        f'<rect class="g5-alvo g5-alvo--sobre" x="{x(posicao) - largura_faixa / 2:.1f}" '
        f'y="{topo}" width="{largura_faixa:.1f}" height="{base - topo}"/></g>'
        for posicao, (categoria, linhas) in enumerate(zip(categorias, linhas_por_categoria))
    ]


def _valor_dica(serie: Serie, posicao: int, formatador: Callable[[float], str]) -> str:
    bruto = serie.valores[posicao] if posicao < len(serie.valores) else None
    return formatador(bruto) if bruto is not None else "—"


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
    rotular_pontos: bool = False,
    ancorar_zero: bool = False,
    rotulos_inclinados: bool = False,
) -> str:
    """Linha categórica. `rotular_ultimo` escreve o valor no último ponto.

    O rótulo direto vale o pixel: tira o vaivém entre legenda e traço, e é o
    que mantém o gráfico legível impresso em preto e branco, onde o azul e o
    wine viram o mesmo cinza.

    `rotular_pontos` escreve **todos** os pontos, acima do traço e na cor da
    série. Só cabe em série curta e de uma série só: com oito pontos os rótulos
    ficam a ~140px um do outro, com trinta eles se sobrepõem e o gráfico fica
    ilegível. Ele dispensa o `rotular_ultimo`, que vira redundante.

    O eixo **não** é ancorado no zero por padrão. Linha codifica variação, não
    magnitude por área: forçar o zero num AUM que anda 2% ao mês achata a série
    numa reta e esconde justamente o que ela existe para mostrar. Barra é o
    contrário — ali o zero é obrigatório, e por isso `barras()` não tem esta
    opção.
    """
    series = list(series)[:MAXIMO_SERIES]
    marcas = _escala_agradavel(*_limites(series, ancorar_zero=ancorar_zero))
    grade, y, x, _ = _moldura(
        marcas,
        categorias,
        formatador,
        largura,
        altura,
        _passo_de_rotulos(len(categorias), largura),
        inclinar=rotulos_inclinados,
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
        # Rotular ponto a ponto pede o ponto marcado: o numero solto sobre o
        # traco nao diz onde a medicao acontece.
        if rotular_pontos or len(pontos) < 20:
            raio = 4 if rotular_pontos else 3
            partes += [
                f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{raio}" fill="{cor}"/>' for px, py in pontos
            ]
        if rotular_pontos:
            valores = [
                valor
                for posicao, valor in enumerate(serie.valores)
                if valor is not None and posicao < len(categorias)
            ]
            # Series alternam acima e abaixo do traco. Duas series proximas —
            # e ROA de duas origens fica proximo — empilhariam os rotulos no
            # mesmo lugar justamente onde elas se cruzam, que e o ponto que o
            # leitor foi conferir.
            acima = indice % 2 == 0
            for (px, py), valor in zip(pontos, valores):
                altura_rotulo = max(py - 12, MARGEM["topo"]) if acima else py + 18
                partes.append(
                    _texto(px, altura_rotulo, formatador(valor), "g5-rotulo-ponto", cor=cor)
                )
        elif rotular_ultimo:
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
    rotular: bool = False,
    formatador_rotulo: Callable[[float], str] | None = None,
    rotulos_inclinados: bool = False,
    formatador_dica: Callable[[float], str] | None = None,
    rotulo_total_dica: str = "",
) -> str:
    """Barra vertical, agrupada ou empilhada.

    `por_sinal` colore cada barra pelo sinal do valor, e só faz sentido em
    série que oscila em torno do zero — variação, fluxo, resultado. Aplicar a
    nível (AUM, receita) inventaria uma leitura de bom/ruim que o dado não tem.

    `rotular` escreve o valor na barra, e **onde** depende do empilhamento:
    solta, ele vai fora — acima quando positivo, abaixo quando negativo —
    porque ali a barra inteira é o valor; empilhada, vai dentro de cada
    segmento, em branco, porque é o segmento que precisa ser identificado e
    fora dele não haveria a qual parcela o número se refere. Segmento curto
    demais para caber o texto fica sem rótulo: o eixo e a tabela respondem.
    Na empilhada, o **total** ainda sai acima da barra — é o número que a pilha
    existe para mostrar, e somar os segmentos de cabeça é o que empilhar
    deveria ter evitado.

    `rotulos_inclinados` gira o rótulo do eixo em -45° e mostra **todas** as
    categorias, em vez de pular de N em N para não sobrepor. É o caminho para
    série longa em que cada ponto precisa ser localizável.

    `formatador_rotulo` separa a escala do rótulo da escala do eixo — o eixo
    aceita marca redonda (`43 bi`), o rótulo costuma querer a casa decimal
    (`43,5 bi`). Sem ele, os dois usam `formatador`.

    `formatador_dica` liga o tooltip por categoria, com o valor de cada série;
    `rotulo_total_dica` acrescenta, separada por um fio, a soma das séries —
    numa pilha de entrada positiva e saída negativa, é o líquido.
    """
    partes, _, x, largura_faixa = _desenhar_barras(
        categorias,
        series,
        formatador=formatador,
        empilhado=empilhado,
        altura=altura,
        largura=largura,
        por_sinal=por_sinal,
        rotular=rotular,
        formatador_rotulo=formatador_rotulo or formatador,
        rotulos_inclinados=rotulos_inclinados,
    )
    if formatador_dica:
        series = list(series)[:MAXIMO_SERIES]
        linhas = []
        for posicao in range(len(categorias)):
            itens: list[list[Any]] = [
                [serie.rotulo, _valor_dica(serie, posicao, formatador_dica), cor_da_serie(indice, serie)]
                for indice, serie in enumerate(series)
            ]
            if rotulo_total_dica:
                soma = sum(
                    (serie.valores[posicao] or 0.0) for serie in series if posicao < len(serie.valores)
                )
                itens.append([rotulo_total_dica, formatador_dica(soma), ""])
            linhas.append(itens)
        partes += _camada_dicas(categorias, x, largura_faixa, altura, linhas)
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
    rotular: bool = False,
    formatador_rotulo: Callable[[float], str] | None = None,
    rotulos_inclinados: bool = False,
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
        marcas,
        categorias,
        formatador,
        largura,
        altura,
        _passo_de_rotulos(len(categorias), largura),
        inclinar=rotulos_inclinados,
    )
    escrever = formatador_rotulo or formatador

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
            if rotular:
                topo_barra, base_barra = min(y1, y2), max(y1, y2)
                if empilhado:
                    # No centro do segmento, so quando ha altura para o texto —
                    # senao ele transborda para o segmento vizinho e passa a
                    # rotular a parcela errada.
                    if base_barra - topo_barra >= ALTURA_MINIMA_ROTULO:
                        partes.append(
                            _texto(
                                px + largura_barra / 2,
                                (topo_barra + base_barra) / 2 + 4,
                                escrever(valor),
                                "g5-valor-dentro",
                            )
                        )
                else:
                    # Fora da barra, do lado para onde ela aponta: a barra
                    # inteira e o valor, e dentro o rotulo some na barra curta.
                    # Na cor da barra porque e dela que o numero fala.
                    partes.append(
                        _texto(
                            px + largura_barra / 2,
                            topo_barra - 6 if valor >= 0 else base_barra + 14,
                            escrever(valor),
                            "g5-valor-barra",
                            cor=cor,
                        )
                    )
        if empilhado and rotular and topo_positivo:
            partes.append(
                _texto(x(posicao), y(topo_positivo) - 6, escrever(topo_positivo), "g5-total-barra")
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
    formatador_dica: Callable[[float], str] | None = None,
) -> str:
    """Barras com uma linha por cima.

    Por padrao a linha divide o **mesmo** eixo das barras. Segundo eixo so e
    aceitavel quando as duas series nao compartilham unidade — IN/OUT em R$ mi
    e um NET tambem em R$ mi nao e esse caso, e dois eixos ali fariam a mesma
    grandeza medir duas alturas diferentes no mesmo desenho. Quando as unidades
    forem realmente distintas (AUM em R$ mi contra receita em R$), passe
    `eixo_proprio=True` e os dois eixos saem rotulados.

    Com `formatador_dica`, cada categoria ganha tooltip com o valor de todas
    as séries naquele ponto — barras primeiro, a linha por último, como total.
    A área de hover é a faixa inteira da categoria, por cima de barras e linha:
    o leitor mira o mês, não um ponto de 3px.
    """
    margem_direita = MARGEM["direita"] + (56 if eixo_proprio else 0)
    partes, y_barra, x, largura_faixa = _desenhar_barras(
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
    if formatador_dica:
        linhas = [
            [
                [serie.rotulo, _valor_dica(serie, posicao, formatador_dica), cor_da_serie(indice, serie)]
                for indice, serie in enumerate(series_barra)
            ]
            + [
                [
                    serie_linha.rotulo,
                    _valor_dica(serie_linha, posicao, formatador_dica),
                    serie_linha.cor or SERIES[1],
                    True,
                ]
            ]
            for posicao in range(len(categorias))
        ]
        partes += _camada_dicas(categorias, x, largura_faixa, altura, linhas)
    return _svg("".join(partes), titulo, largura, altura)


def barras_horizontais(
    itens: Sequence[tuple[str, float | None]],
    *,
    formatador: Callable[[float], str],
    titulo: str = "",
    largura: int = LARGURA,
    cor: str = SERIES[0],
    cores: Sequence[str] = (),
    largura_rotulo: int = 220,
    altura_linha: int = 26,
) -> str:
    """Ranking. É a forma canônica quando um donut passaria de cinco fatias.

    `cores` pinta item a item, na ordem de `itens`, e serve para o caso em que
    as barras pertencem a famílias diferentes — aí a cor carrega a família e
    dispensa reordenar o gráfico para agrupá-las. Item sem cor correspondente
    cai em `cor`. Como sempre, no máximo cinco famílias: acima disso a legenda
    deixa de ser memorizável e a cor vira ruído.

    `altura_linha` afina a barra quando o gráfico vem em par, lado a lado, e a
    altura cheia faria o par ocupar mais tela do que o dado pede.
    """
    pintados = [
        (rotulo, valor, cores[indice] if indice < len(cores) else cor)
        for indice, (rotulo, valor) in enumerate(itens)
    ]
    itens = [(rotulo, valor, tom) for rotulo, valor, tom in pintados if valor is not None]
    if not itens:
        return ""
    espaco = max(4, altura_linha // 4)
    altura = len(itens) * (altura_linha + espaco) + 16
    maximo = max(abs(valor) for _, valor, _ in itens) or 1
    disponivel = largura - largura_rotulo - 140

    partes = []
    for indice, (rotulo, valor, tom) in enumerate(itens):
        y = 8 + indice * (altura_linha + espaco)
        comprimento = abs(valor) / maximo * disponivel
        base_texto = y + altura_linha / 2 + 4
        partes.append(_texto(largura_rotulo - 12, base_texto, rotulo, "g5-rotulo-barra", "end"))
        partes.append(
            f'<rect x="{largura_rotulo}" y="{y}" width="{comprimento:.1f}" '
            f'height="{altura_linha}" fill="{tom}"/>'
        )
        partes.append(
            _texto(largura_rotulo + comprimento + 10, base_texto, formatador(valor), "g5-valor-barra", "start")
        )
    return _svg("".join(partes), titulo, largura, altura, CLASSE_RANKING)


def barras_horizontais_empilhadas(
    rotulos: Sequence[str],
    series: Sequence[Serie],
    *,
    formatador: Callable[[float], str],
    titulo: str = "",
    largura: int = LARGURA,
    largura_rotulo: int = 220,
) -> str:
    """Ranking em que cada barra é a soma de parcelas — onshore + offshore.

    Só o total vai escrito, no fim da pilha: a parcela menor quase nunca tem
    largura para o próprio número, e rotular uma parcela e não a outra deixaria
    a leitura pela metade. O detalhe vai no tooltip (`data-dica`, lido pelo
    `app.js`), e a tabela da página continua sendo o lugar de todos os números
    — sem JS o gráfico perde só o hover.

    Linha mais baixa que a de `barras_horizontais` porque o par empilhado
    costuma vir lado a lado e com muitas categorias: com a altura cheia, vinte
    regiões passariam de 800px.
    """
    series = list(series)[:MAXIMO_SERIES]
    if not rotulos or not series:
        return ""

    def valor(serie: Serie, posicao: int) -> float:
        return (serie.valores[posicao] if posicao < len(serie.valores) else None) or 0.0

    totais = [sum(max(valor(serie, posicao), 0.0) for serie in series) for posicao in range(len(rotulos))]
    maximo = max(totais) or 1
    altura_linha, espaco = 18, 5
    altura = len(rotulos) * (altura_linha + espaco) + 10
    disponivel = largura - largura_rotulo - 90

    partes = []
    for posicao, rotulo in enumerate(rotulos):
        y = 5 + posicao * (altura_linha + espaco)
        dica = _dica(
            rotulo,
            [
                [serie.rotulo, formatador(valor(serie, posicao)), cor_da_serie(indice, serie)]
                for indice, serie in enumerate(series)
            ]
            + [["Total", formatador(totais[posicao]), ""]],
        )
        # O `rect` transparente da faixa inteira é a área de hover: a parcela
        # offshore tem poucos pixels, e mirar nela seria o gesto mais difícil
        # justamente para o número que só o tooltip mostra.
        grupo = [
            (
                f'<rect class="g5-alvo" x="0" y="{y - espaco / 2:.1f}" width="{largura}" '
                f'height="{altura_linha + espaco}"/>'
            ),
            _texto(largura_rotulo - 10, y + 13, rotulo, "g5-rotulo-barra", "end"),
        ]
        inicio = float(largura_rotulo)
        for indice, serie in enumerate(series):
            parcela = max(valor(serie, posicao), 0.0)
            comprimento = parcela / maximo * disponivel
            if comprimento:
                grupo.append(
                    f'<rect x="{inicio:.1f}" y="{y}" width="{comprimento:.1f}" '
                    f'height="{altura_linha}" fill="{cor_da_serie(indice, serie)}"/>'
                )
            inicio += comprimento
        grupo.append(_texto(inicio + 8, y + 13, formatador(totais[posicao]), "g5-valor-barra", "start"))
        partes.append(
            f'<g class="g5-com-dica" data-dica="{dica}">'
            f'{"".join(grupo)}</g>'
        )
    return _svg("".join(partes), titulo, largura, altura, CLASSE_RANKING)


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
    return _svg("".join(partes), titulo, tamanho, tamanho, CLASSE_DONUT)


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
