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

**Decisão provisória**, a revalidar depois do primeiro modelo de dashboard: módulo SVG
próprio (`charts.js`), sem biblioteca externa. Justificativa: controle total do design
system, arquivo leve, zero dependência de rede, e cada ajuste futuro acontece em código
nosso em vez de contornar defaults de terceiros. Tipos necessários: linha, barra vertical e
horizontal, barra empilhada, combo linha+barra, donut, waterfall (captação). Se o custo de
manutenção se mostrar alto no protótipo, a alternativa é embarcar uma biblioteca minificada
inline — nunca via CDN.

---

[← Índice](../CLAUDE.md)
