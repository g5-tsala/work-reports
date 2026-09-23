# Padrão visual

A skill **`g5-design-system`** é a fonte de verdade de cores, tipografia, espaçamento, tabelas e
gráficos — não inventar hex. Aqui só o que este projeto acrescenta. Navegação e interação:
[dashboard.md](dashboard.md).

- Navy estrutura, wine pontua (≤ 5% da área), neutros sustentam. Sem gradiente, sem dark mode.
- Tabela G5: header navy com rótulo branco em caixa alta, zebra `--g5-bg-soft`, números à
  direita e tabulares, sem régua vertical.
- Séries na ordem canônica (`graficos.SERIES`), no máximo 5. Composição com mais de 5 partes
  vai em barra horizontal, não em donut.
- Negativo em `--g5-negative`, positivo em `--g5-positive`, nunca sobre navy.
- Todo gráfico e toda tabela de origem levam `ui.fonte()`:
  `Fonte: Gerencial MFO — aba <nome>. Base: <mês>.` Legenda de série vai acima do gráfico.

## 1. Números — PT-BR sempre (`core/render/formato.py`)

- Milhar `.`, decimal `,`: `R$ 42,78 bi` · `0,24%` · `+2,46 p.p.`
- Escala: AUM em **R$ bi** no nível MFO e **R$ mi** em officer/grupo/portfólio; receita e run
  rate em **R$ mi**; ROA em % com 2 casas.
- Uma escala por tabela, declarada no cabeçalho (`AUM (R$ mi)`), nunca por célula.
- Variação não herda a escala do nível: o AUM é R$ bi, mas o delta do mês vai em **R$ mi**.
- Diferença entre percentuais é **p.p.**, nunca `%`.
- Zero é `0,00`; `—` é "não aplicável"; célula vazia é "dado ausente". São coisas diferentes.

## 1.1 Tabelas

- **Sem largura declarada por coluna.** Layout `auto`;
  a folga de `width: 100%` é distribuída por padding: `.num` 8px de cada lado e 32px à direita
  só da **primeira** coluna (o rótulo da linha). Em toda `.text`, a folga multiplica pelas oito
  colunas de texto da tabela de portfólios e espreme nomes longos.
- Descartados, não reabrir: `th:not(.num) { width: 100% }` (vão de 700px no ranking) e
  `width: 20%` (quebra a tabela de portfólios). `width: auto` na tabela funciona, mas deixa
  branco à direita nas tabelas estreitas.
- **Zebra conta só linhas visíveis de nível principal** (`nth-child(even of …)`): sub-linha de
  drill-down e linha filtrada ficam fora da paridade.

## 2. Gráficos (`core/render/graficos.py`)

SVG gerado no build, cores como `var(--g5-*)` (o SVG inline herda os tokens). Tipos: `linhas`,
`barras` (agrupada/empilhada), `combo` (barra + linha, eixo compartilhado ou próprio),
`barras_horizontais`, `barras_horizontais_empilhadas`. Sem donut nem waterfall.

### 2.1 Eixos e cor

- **Barra ancorada no zero; linha não.** Barra codifica magnitude por área. Linha codifica
  variação: zero forçado achata um AUM que anda 2% ao mês. `barras()` não tem opção;
  `linhas(ancorar_zero=False)` por padrão.
- **A última marca do eixo é ≥ o maior valor**, senão o `viewBox` corta a marca sem aviso.
- **Segundo eixo só com unidades realmente distintas:** `combo(eixo_proprio=True)` (G5 JUS: AUM
  em R$ mi × receita em R$). IN, OUT e NET são todos R$ mi → eixo compartilhado.
- **Cor por sinal só em série que oscila em torno do zero** (variação, fluxo). Em nível (AUM,
  receita) inventaria leitura de bom/ruim.
- **Série longa: `rotulos_inclinados`** (-45°, todas as categorias) em vez de pular rótulos.
- **Cor por família em ranking** (`barras_horizontais(cores=…)`) quando o leitor reconhece os
  grupos (família de produto, G5 × terceiros). Mesmo teto de 5 cores.
- **Par lado a lado compartilha a ordem**, tirada do AUM (Resumo, Officers, Grupos, Regiões,
  Portfólios). Rankings que não coincidem (Top 10 por AUM e por receita) → o par mostra a união.
  Na mesma ordem, a linha horizontal já é a comparação, e a discordância entre barras é o ROA.
- **Empilhar é para parcela de um total** (AUM e receita on + off: o topo é o consolidado);
  **razão é linha** (ROA — somar taxas não dá taxa).

### 2.2 Rótulo direto

Mantém o gráfico legível impresso em P&B, onde azul e wine viram o mesmo cinza.

| Opção | Onde | Quando |
|---|---|---|
| `rotular_ultimo` | `linhas()`, `combo()` | série longa: só o valor de fechamento |
| `rotular_pontos` | `linhas()` | o número de cada ponto importa. Ponto marcado maior; séries alternam acima/abaixo do traço para não empilhar rótulos onde se cruzam |
| `rotular` | `barras()` | solta: fora da barra (acima se +, abaixo se −), na cor da barra. Empilhada: dentro de cada segmento, em branco, e o total acima da pilha. Segmento menor que `ALTURA_MINIMA_ROTULO` fica sem rótulo |

- `formatador_rotulo` separa a escala do rótulo (`39,7 bi`) da do eixo (`45 bi`).
- O rótulo herda a cor da marca que descreve; na linha, com halo branco (`paint-order: stroke`).
- Cor do texto via `style="fill:…"`, não atributo `fill`: atributo de apresentação perde para
  qualquer regra CSS (`.g5-valor-barra` declara `fill`).

### 2.3 Altura

O SVG ocupa 100% da largura; a altura sai da proporção do `viewBox`.

| Classe | Tipos | Cresce | Teto |
|---|---|---|---|
| `.g5-grafico--serie` | linha, barra vertical, combo | na horizontal | `max-height: 250px` |
| `.g5-grafico--ranking` | barras horizontais | na vertical (um item por linha) | nenhum — cortaria item |

`LARGURA × ALTURA` = 1200 × 224 faz a série cair em ~250px na largura máxima de `.g5-main`
(1.344px): o teto é rede de segurança. Mudar essa razão muda todo gráfico de série; `altura=`
avulso numa página quebra a calibragem (letterbox lateral).

### 2.4 Tooltip

O grupo SVG leva `data-dica` = JSON `{titulo, linhas: [[rótulo, valor, cor, total?]]}` já
formatado no build; o `app.js` exibe um balão único junto ao ponteiro. Linha sem cor ou com o
4º item `true` é total, separada por um fio. Ligado por `formatador_dica` em `barras()` e
`combo()` e sempre em `barras_horizontais_empilhadas()`. Em uso: Regiões, fluxo mensal e
incremento de receita do Net In/Out, G5 JUS.

- **Complementa, não esconde:** todo número do balão está numa tabela da página. Por isso a
  barra horizontal empilhada escreve só o total; as parcelas se abrem no balão.
- **Área de hover = faixa inteira da categoria** (`.g5-alvo`, transparente). Na barra
  horizontal fica atrás das marcas; no `combo`/`barras` fica por cima (`.g5-alvo--sobre`), com
  destaque translúcido.
- Valor em destaque e à direita, rótulo depois, chave de cor em traço curto.
- Texto por `textContent`, nunca `innerHTML` (rótulo vem da planilha). Some na impressão.
