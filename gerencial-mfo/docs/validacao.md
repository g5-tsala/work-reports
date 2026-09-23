# Validação

O build **falha** se algum item do checklist falhar — nunca gerar dashboard sobre base
inconsistente. Armadilhas conhecidas da fonte: [MEMORY.md](MEMORY.md) § Armadilhas.

## 1. Checklist do build

`core/validacao.py`, um item por função, nesta numeração. Roda sobre o JSON. Item sem dado para
avaliar sai como `?` (`ok=None`) e não bloqueia, mas aparece no relatório.

1. **Checks da planilha zerados** — todas as células de §2 (`|valor| ≤ TOLERANCIA_CHECK`).
2. **AUM total = onshore + offshore** (`resumo`).
3. **Soma dos officers = Total** na `CEO-Dashboard` (Fdos Alocação incluído), em AUM, receita e
   qtd. de portfólios.
4. **Soma das categorias = Total** em `resumo` (qtd, AUM, receita anualizada).
5. **NET = IN + OUT** (OUT negativo) em `net_in_out`, on e offshore, mês a mês e no acumulado.
6. **Qtd. de portfólios** bate entre `resumo!P27`, o total da `CEO-Dashboard` e a contagem de
   linhas com AUM ou receita > 0 em `ar_onshore` + `ar_offshore`.
7. **Câmbio** de `info!AQ3` bate com `regiao!G2`.
8. **Mês de fechamento** é a última coluna das séries de `aum_receita`, com AUM preenchido.
9. **Mensalização** — `receita_competencia × 21 / dias_uteis` reproduz a receita mensalizada de
   `aum_receita` e `resumo!H7`.
10. **Qtd. Grupos** — o recálculo a partir de `carteira.portfolios` reproduz as linhas +29/+30
    de cada bloco de `cons_officer` ([calculos.md](calculos.md) §3.5), e o total de grupos
    distintos bate com `resumo!AA17`. É o teste mais barato de que o mapeamento das colunas de
    dimensão está certo.

Depois de gerar: abrir o HTML e conferir os 4 KPIs da Visão Geral contra a planilha.

## 2. Checks embutidos na planilha

Diferenças que devem dar zero, extraídas por `core/extracao/checks.py` (`INTERVALOS`):

| Intervalo | Verifica |
|---|---|
| `CEO-Dashboard!C2:L3` | AUM, run rate, Δ e ROA contra a soma dos officers (ex.: `C3` = AUM MFO − Σ officers / 1000; `F3` = Run Rate − Σ receita × 12 / 1e6; `H3` = Δ total − (Δ on + Δ off); `I3` = ROA − ROA recalculado) |
| `Dashboard!K16:L32` | captação cliente contra a soma das quebras |
| `aum_receita!AG6:AG50` | NET e receita contra a soma por tipo de veículo (`AG8`, `AG17`) |
| `net_in_out!R7:S90` | IN − Σ tipos (`R7`), IN − total de `io_portfolios` (`S7`), NET − (IN + OUT) (`R45`) |
| `io_grupos!Q5:Q7` | soma mensal − NET de `net_in_out` (`Q5`), soma mensal − soma YTD (`Q7`) |
| `resumo!AC21:AC24` | total por categoria − total por grupo (AUM e receita) |
