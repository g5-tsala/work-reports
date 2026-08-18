# Padrão visual

> [← Índice](../CLAUDE.md) · Relacionados: [dashboard.md](dashboard.md)

Usar a skill **`g5-design-system`** para qualquer decisão visual. Ela é a fonte de verdade
de cores, tipografia, espaçamento, tabelas e regras de gráfico. Não inventar hex.

Pontos que este projeto reforça:

- Navy estrutura, wine pontua (≤5% da área), neutros sustentam. Sem gradiente, sem dark mode.
- Tabelas no padrão G5: header navy com rótulo branco em caixa alta, zebra `--g5-bg-soft`,
  numéricos à direita e tabulares, sem régua vertical.
- Séries de gráfico na ordem canônica do design system. Máximo 5 séries, máximo 5 fatias
  em donut — acima disso, barra horizontal.
- Toda variação negativa em `--g5-negative`, positiva em `--g5-positive`, nunca sobre navy.
- Todo gráfico carrega legenda de fonte: `Fonte: Gerencial MFO — aba <nome>. Base: <mês>.`

## 1. Números (PT-BR, sem exceção)

- Milhar `.`, decimal `,`. `R$ 42,78 bi` · `0,24%` · `+2,46 p.p.`
- Escala: AUM em **R$ bi** no nível MFO e **R$ mi** no nível officer/grupo/portfólio;
  receita e run rate em **R$ mi**; ROA em **%** com 2 casas.
- Uma escala por tabela, declarada no cabeçalho da coluna (`AUM (R$ mi)`), nunca por célula.
- Diferença entre percentuais é **p.p.**, nunca `%`.
- Zero é `0,00`. Traço `—` significa "não aplicável". Célula vazia significa "dado ausente".
  São coisas diferentes e alguém vai perguntar.

## 2. Gráficos

Módulo SVG próprio, sem biblioteca externa — **gerado no build, em Python**
(`core/render/graficos.py`), não em JavaScript no cliente. Os dados são fixos no momento em
que o HTML é escrito, então o gráfico pode ser vetor estático: imprime bem, abre com o JS
desligado e não depende de rede.

Tipos disponíveis: linha, barra vertical (agrupada e empilhada), combo barra + linha com
segundo eixo, barra horizontal e donut. Waterfall ainda não existe — a captação usa barra
empilhada com linha de NET.

As cores saem como `var(--g5-*)` dentro do SVG inline, que herda os tokens do CSS: trocar a
paleta continua sendo mexer num arquivo só. Se algum dia for preciso interatividade real
(tooltip, brushing, seletor que redesenha), aí sim entra biblioteca — minificada e inline,
nunca via CDN.

### 2.1 Regras de eixo

Quatro decisões que já custaram uma rodada de conserto:

- **Barra é ancorada no zero; linha não.** Barra codifica magnitude por área — cortar a base
  mente. Linha codifica variação: forçar o zero num AUM que anda 2% ao mês achata a série
  numa reta e esconde justamente o que ela existe para mostrar. `barras()` não tem opção;
  `linhas()` tem `ancorar_zero`, que nasce `False`.
- **A última marca do eixo é sempre ≥ o maior valor.** Se ficar abaixo, a barra sai da área
  de plotagem e o `viewBox` corta — sem nenhum sinal visível de que faltou dado.
- **Segundo eixo só quando as unidades são mesmo diferentes.** `combo()` compartilha o eixo
  por padrão; `eixo_proprio=True` é para o caso legítimo (G5 JUS: AUM em R$ mi contra
  receita em R$). IN, OUT e NET são todos R$ mi — dois eixos ali fariam a mesma grandeza
  medir duas alturas no mesmo desenho.
- **Cor por sinal só em série que oscila em torno do zero** — variação, fluxo, resultado.
  Em nível (AUM, receita) inventaria uma leitura de bom/ruim que o dado não tem.

O valor do último ponto sai rotulado direto na linha (`rotular_ultimo`), com halo branco: é
o que dispensa o vaivém até a legenda e o que mantém o gráfico legível impresso em preto e
branco, onde o azul e o wine viram o mesmo cinza.

---

[← Índice](../CLAUDE.md)
