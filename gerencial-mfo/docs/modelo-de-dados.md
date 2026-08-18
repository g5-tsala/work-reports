# Modelo de dados

Estrutura das abas, dimensões e bases da planilha. Para **como cada número é calculado**,
ver [calculos.md](calculos.md).

> [← Índice](../CLAUDE.md) · Relacionados: [calculos.md](calculos.md), [metricas.md](metricas.md)

28 abas: **14 visíveis** (viram páginas do dashboard) e **14 ocultas** (bases de cálculo).
Na planilha, tudo que é visível é fórmula referenciando as ocultas. No dashboard, ler
preferencialmente a aba visível; recorrer à oculta só quando ela contiver granularidade que
a visível agrega.

## 1. Abas visíveis → páginas

| Aba | Conteúdo | Página do dashboard |
|---|---|---|
| `CEO-Dashboard` | 4 KPIs consolidados, split On/Offshore, tabela por officer | Visão Geral |
| `Dashboard` | Resultado e run rate, captação cliente, NET executado por mês | Visão Geral + Captação |
| `resumo` | ROA por Categoria/Faixa PL e por Grupo/Faixa PL, 4 donuts | Resumo |
| `aum_receita` | Série AUM × Receita × ROA, onshore e offshore, 2018→hoje | Histórico |
| `roa_historico` | Qtd. veículos, AUM e Receita anualizada por categoria/faixa, série longa | ROA Histórico |
| `ar_grupos` | Top 10 AUM por grupo econômico, mês a mês | Grupos Econômicos |
| `ar_adm_on` | AUM × Receita × Custos por administrador, onshore (R$) | Administradores Onshore |
| `ar_adm_off` | AUM × Receita × Custos por administrador, offshore (US$) | Administradores Offshore |
| `ar_onshore` | 939 portfólios com todas as dimensões, AUM e receita mensais | Portfólios Onshore |
| `ar_offshore` | 166 portfólios offshore (US$) | Portfólios Offshore |
| `G5JUS` | AUM × Receita dos FIDCs G5 JUS | G5 JUS |
| `net_in_out` | IN/OUT mensal decomposto por tipo de veículo e finalidade | Captação |
| `io_grupos` | Movimentações por grupo econômico, visão mensal e YTD | Captação › Grupos |
| `io_portfolios` | IN/OUT por portfólio com taxa e receita aproximada | Captação › Portfólios |

## 2. Abas ocultas relevantes

| Aba | Papel |
|---|---|
| `regiao` | Distribuição geográfica (AUM, receita, % e qtd. grupos), onshore / offshore / consolidado. Alimenta os gráficos da aba `resumo`. É a única fonte do corte por região — usar diretamente. |
| `custos_adm_on` / `custos_adm_off` | Custo de administração por portfólio. Alimentam `ar_adm_*`. Usar para o drill-down de custo por administrador. |
| `info_grupos` | Movimentações individuais (Data, Portfolio, IN/OUT, Finalidade, Grupo, Officer, Lead, LeadG5, Segmento) + ano de início de cada grupo. É o nível mais fino do drill-down de captação. |
| `cons_officer` | Consolidação por officer que alimenta a tabela da `CEO-Dashboard`. Mapeia apelido → login (ex.: `Abrahão` → `amendes`). |
| `cotas` | Cotização da própria base de AUM tratada como portfólio (AUM indexado, rendimento, var. %, cota) vs CDI acumulado, desde 2018-01. **Backlog** — vira uma página "Performance da Base" depois que as análises principais estiverem prontas. Prioridade baixa. |
| `fees_indiretos` | Receitas indiretas (rebates, Icatu). **Fora de escopo** — zeradas/TBD em 2026. |
| `CHECK`, `check_net`, `info`, `in_out`, `info_net_in_out`, `in_out_cons`, `APRESENTACAO` | Encanamento e validação. Não expor. |

## 3. Eixos de análise

Duas taxonomias diferentes que não devem ser confundidas:

- **Tipo de veículo** (`ar_onshore` col. C): Carteira, Fundo, Fundo/Previdência, Estruturado,
  Alocação, Alocação/Previdência, Externo, Offshore.
- **Segmento** (col. I): MFO, Institucional, Estruturado, Alocação.

Demais dimensões por portfólio: `Adm` (administrador), `Grupo` (grupo econômico),
`Officer`, `Backup`, `Região`.

## 4. Grade temporal

Nas abas de série longa (`aum_receita`, `roa_historico`, `ar_adm_on`), o cabeçalho de datas
está na **linha 5** e a **linha 4 traz a contagem de dias úteis** do período — é o que
sustenta a mensalização da receita.

- Colunas C→R: pontos **semestrais**, 2018-06 a 2025-12.
- Colunas S→AD: pontos **mensais**, 2026-01 a 2026-12.

O eixo X não é uniforme. Nos gráficos históricos, tratar como categórico ordenado, nunca
como escala temporal linear — senão os 8 anos semestrais comprimem os meses de 2026.

## 5. Nomes definidos

O motor da planilha são nomes definidos, não referências diretas. Reproduzi-los no extrator
torna o código legível e resistente a deslocamento de linhas.

### Bases de posição

| Nome | Intervalo | Conteúdo |
|---|---|---|
| `ar_on` | `ar_onshore!J5:AI931` | matriz de valores (AUM e Receita alternados por mês) |
| `ar_on_datas` | `ar_onshore!J3:AI3` | data de cada coluna (repetida em pares) |
| `ar_on_headers` | `ar_onshore!J4:AI4` | `"AUM"` ou `"Receita"` |
| `ar_on_info` | `ar_onshore!B5:I931` | dimensões, 8 colunas (ver 3.1) |
| `ar_on_total` | `ar_onshore!J933:AI933` | linha de total |
| `ar_off*` | `ar_offshore!…162` | idêntico, em US$ |
| `custos_on` / `custos_off` | `custos_adm_*` | AUM e Custos por portfólio |
| `grupos` | `ar_grupos!C54:AB500` | AUM e Receita por grupo econômico |
| `grupos_info` | `ar_grupos!B54:B500` | nome do grupo |
| `cotas` | `cotas!B5:U500` | série de cotização |

### Bases de movimentação

| Nome | Intervalo | Conteúdo |
|---|---|---|
| `in_onshore` | `in_out!B6:K5001` | **todas** as entradas onshore |
| `out_onshore` | `in_out!M6:W5001` | **todas** as saídas onshore |
| `in_offshore` | `in_out!Y6:AJ5000` | todas as entradas offshore |
| `out_offshore` | `in_out!AL6:AX5000` | todas as saídas offshore |
| `in_net_onshore` | `info_net_in_out!B6:K5001` | entradas **de cliente** |
| `out_net_onshore` | `info_net_in_out!M6:W5000` | saídas **de cliente** |
| `in_net_offshore` | `info_net_in_out!Y6:AJ5000` | idem, offshore |
| `out_net_offshore` | `info_net_in_out!AL6:AX5000` | idem, offshore |

### Séries consolidadas

| Nome | Intervalo |
|---|---|
| `aum_receita_on` | `aum_receita!B5:AD35` |
| `aum_receita_off` | `aum_receita!B39:AD50` |
| `io_cons_on` | `in_out_cons!B5:O79` |
| `io_cons_off` | `in_out_cons!B82:P108` |

### Colunas de `ar_on_info` / `ar_off_info`

| # | Campo |
|---|---|
| 1 | Portfolio |
| 2 | Tipo (Carteira, Fundo, Fundo/Previdência, Estruturado, Alocação, Alocação/Previdência, Externo, Offshore) |
| 3 | Adm (administrador) |
| 4 | Grupo econômico |
| 5 | **Officer** |
| 6 | Backup |
| 7 | Região |
| 8 | **Segmento** (MFO, Institucional, Estruturado, Alocação) |

### Colunas das bases de movimentação

Onshore IN (10 col.) e offshore IN (12 col.):

| # | Campo | | # | Campo |
|---|---|---|---|---|
| 1 | Mês | | 6 | Tipo |
| 2 | Portfolio | | 7 | Segmento |
| 3 | Valor (R$ onshore / US$ offshore) | | 8 | Grupo |
| 4 | Officer | | 9 | **Ano Início** |
| 5 | **Taxa (% a.a.)** | | 10 | Novo? |
| | | | 11 | Dólar *(só offshore)* |
| | | | 12 | **Valor (R$)** *(só offshore)* |

Onshore OUT (11 col.) e offshore OUT (13 col.): mesma ordem até 9, e depois

| # | Campo |
|---|---|
| 10 | **Finalidade** (`Uso pessoal` \| `Saída para concorrência` \| `Alocação`) |
| 11 | Final? |
| 12 | Dólar *(só offshore)* |
| 13 | **Valor (R$)** *(só offshore)* |

## 6. `in_out` vs `info_net_in_out` — a distinção que mais confunde

São duas bases com **schema idêntico** e conteúdo diferente:

- **`in_out`** — todas as movimentações, inclusive as dos veículos do próprio grupo G5
  (fundos de alocação). Em jul/26: 781 linhas de IN onshore, R$ 4,50 bi, das quais 238 são
  do grupo `G5`.
- **`info_net_in_out`** — apenas movimentação **de cliente**: as linhas do grupo `G5` foram
  removidas. Em jul/26: 479 linhas, R$ 1,92 bi, **zero** do grupo `G5`.

Consequência direta:

| Visão | Base | Aba |
|---|---|---|
| **Captação Cliente** | `*_net_*` (sem G5) | `net_in_out`, `io_portfolios`, `Dashboard §2` |
| **NET Executado** | `in_out` (com G5) | `in_out_cons`, `Dashboard §3` |
| Série `IN/OUT` de `aum_receita` | `io_cons_*`, ou seja `in_out` (com G5) | `aum_receita!S8` |

Trocar uma pela outra produz números plausíveis e errados. É a armadilha número um deste
modelo.

---

---

[← Índice](../CLAUDE.md)
