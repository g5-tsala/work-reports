# Modelo de dados da planilha

Abas, dimensões, nomes definidos e grade temporal. Como cada número é calculado:
[calculos.md](calculos.md).

28 abas: 14 visíveis (fórmulas sobre as ocultas) e 14 ocultas (bases). Ler preferencialmente a
visível; ir à oculta só quando ela tiver granularidade que a visível agrega.

## 1. Abas visíveis

| Aba | Conteúdo | Uso no dashboard |
|---|---|---|
| `CEO-Dashboard` | cartões de KPI, split on/offshore, tabela por officer | Visão Geral (variação M-1), Officers |
| `resumo` | KPIs, ROA por Categoria/Faixa PL e por Grupo/Faixa PL | Visão Geral, Resumo |
| `aum_receita` | série AUM × Receita × ROA on/offshore, 2018→hoje | Visão Geral, Histórico |
| `ar_grupos` | Top 10 por AUM e por receita, série por grupo | Grupos Econômicos |
| `ar_onshore` | uma linha por portfólio, dimensões + AUM/receita mensais (R$) | Portfólios Onshore; checklist |
| `ar_offshore` | idem, em US$ | Portfólios Offshore; checklist |
| `net_in_out` | IN/OUT mensal por tipo de veículo e finalidade | Net In/Out |
| `Dashboard` | §2 Captação Cliente (mês, ano, incremento de receita) · §3 NET executado por segmento | Net In/Out |
| `io_grupos` | movimentação por grupo econômico, mensal e YTD | Captação › Grupos |
| `G5JUS` | AUM × receita dos FIDCs G5 JUS | G5 JUS |
| `ar_adm_on` / `ar_adm_off` | AUM × receita × custos por administrador (R$ / US$) | só no JSON |
| `io_portfolios` | IN/OUT por portfólio com taxa e receita aproximada | só no JSON |

## 2. Abas ocultas relevantes

| Aba | Papel |
|---|---|
| `regiao` | AUM, receita, % e qtd. de grupos por região (on/offshore/consolidado). Única fonte do corte geográfico → aba Regiões. |
| `cons_officer` | consolidação por officer que alimenta a `CEO-Dashboard` → drill-down de Officers. |
| `info` | parâmetros do mês e de-para login → apelido ([calculos.md](calculos.md) §2). |
| `info_grupos` | movimentações individuais (Data, Portfolio, IN/OUT, Finalidade, Grupo, Officer, Lead, LeadG5, Segmento) + ano de início do grupo. **Não extraída** (backlog: 3º nível do drill-down de captação). |
| `custos_adm_on` / `custos_adm_off` | custo de administração por portfólio; alimentam `ar_adm_*`. Não extraídas. |
| `cotas` | cotização da base de AUM vs CDI desde 2018-01. Backlog. |
| `fees_indiretos` | receitas indiretas (rebates, Icatu). Fora de escopo — zeradas/TBD em 2026. |
| `CHECK`, `check_net`, `in_out`, `info_net_in_out`, `in_out_cons`, `APRESENTACAO` | encanamento e validação. Não expor. |

## 3. Eixos de análise

Duas taxonomias distintas — não confundir:

- **Tipo de veículo** (`ar_onshore` col. C): Carteira, Fundo, Fundo/Previdência, Estruturado,
  Alocação, Alocação/Previdência, Externo, Offshore.
- **Segmento** (col. I): MFO, Institucional, Estruturado, Alocação.

Demais dimensões por portfólio: Adm, Grupo econômico, Officer, Backup, Região.

## 4. Grade temporal

Em `aum_receita` e `ar_adm_on`: datas na **linha 5**, dias úteis do período na **linha 4**.
Colunas C→R são **semestrais** (2018-06 a 2025-12); S→AD são **mensais** (2026-01 a 2026-12).
Eixo não uniforme: plotar como categórico ordenado, nunca como escala temporal.

## 5. Nomes definidos

O motor da planilha são nomes definidos; o extrator os usa para resistir a deslocamento de linhas.

**Bases de posição**

| Nome | Intervalo | Conteúdo |
|---|---|---|
| `ar_on` | `ar_onshore!J5:AI931` | valores, AUM e Receita alternados por mês |
| `ar_on_datas` | `ar_onshore!J3:AI3` | data de cada coluna (repetida no par) |
| `ar_on_headers` | `ar_onshore!J4:AI4` | `"AUM"` ou `"Receita"` |
| `ar_on_info` | `ar_onshore!B5:I931` | 8 dimensões (tabela abaixo) |
| `ar_on_total` | `ar_onshore!J933:AI933` | linha de total |
| `ar_off*` | `ar_offshore!…` | idem, em US$ |
| `grupos` · `grupos_info` · `grupos_datas` · `grupos_headers` | `ar_grupos!…` (`C54:AB500`, `B54:B500`) | AUM/receita por grupo, nome, datas, cabeçalhos |
| `custos_on` / `custos_off` | `custos_adm_*` | AUM e custos por portfólio |
| `cotas` | `cotas!B5:U500` | série de cotização |

**Bases de movimentação**

| Nome | Intervalo | Conteúdo |
|---|---|---|
| `in_onshore` / `out_onshore` | `in_out!B6:K5001` / `M6:W5001` | **todas** as entradas / saídas onshore |
| `in_offshore` / `out_offshore` | `in_out!Y6:AJ5000` / `AL6:AX5000` | idem, offshore |
| `in_net_onshore` / `out_net_onshore` | `info_net_in_out!B6:K5001` / `M6:W5000` | só **cliente** |
| `in_net_offshore` / `out_net_offshore` | `info_net_in_out!Y6:AJ5000` / `AL6:AX5000` | só cliente, offshore |

**Séries consolidadas:** `aum_receita_on` = `aum_receita!B5:AD35` · `aum_receita_off` =
`aum_receita!B39:AD50` · `io_cons_on` = `in_out_cons!B5:O79` · `io_cons_off` =
`in_out_cons!B82:P108`.

**Colunas de `ar_on_info` / `ar_off_info`:** 1 Portfolio · 2 Tipo · 3 Adm · 4 Grupo econômico ·
5 **Officer** · 6 Backup · 7 Região · 8 **Segmento**.

**Colunas das bases de movimentação:**

| # | IN (10 col. on / 12 off) | OUT (11 col. on / 13 off) |
|---|---|---|
| 1–4 | Mês · Portfolio · Valor (R$ on / US$ off) · Officer | idem |
| 5 | **Taxa (% a.a.)** | idem |
| 6–8 | Tipo · Segmento · Grupo | idem |
| 9 | **Ano Início** | idem |
| 10 | Novo? | **Finalidade** (`Uso pessoal` \| `Saída para concorrência` \| `Alocação`) |
| 11 | Dólar *(off)* | Final? |
| 12 | **Valor (R$)** *(off)* | Dólar *(off)* |
| 13 | — | **Valor (R$)** *(off)* |

## 6. `in_out` × `info_net_in_out`

Schema idêntico, conteúdo diferente — a armadilha número um do modelo:

- **`in_out`**: todas as movimentações, inclusive as dos veículos do grupo G5. Jul/26: 781
  linhas de IN onshore, R$ 4,50 bi, 238 do grupo `G5`.
- **`info_net_in_out`**: só **cliente**, sem as linhas do G5. Jul/26: 479 linhas, R$ 1,92 bi.

| Visão | Base | Aba |
|---|---|---|
| Captação Cliente | `*_net_*` | `net_in_out`, `io_portfolios`, `Dashboard` §2 |
| NET Executado | `*_net_*`; offshore pelas col. 12/13, em R$ | `Dashboard` §3 (fórmulas a partir de `Dashboard!C37`) |
| Consolidação com G5 | `in_out` | `in_out_cons` |
| Série `IN/OUT` de `aum_receita` | `io_cons_*` → `in_out` | `aum_receita!S8` |

Por isso o NET do mês e do ano de `Dashboard` §2, §3 e `net_in_out` consolidado batem no centavo
(ago/26: R$ 29,52 mi no mês, R$ 230,98 mi no ano). Não somar um com o outro.
