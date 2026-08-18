# Validação, defeitos e armadilhas

O build **falha** se qualquer item do checklist não passar. Nunca gerar dashboard a partir
de base inconsistente.

> [← Índice](../CLAUDE.md) · Relacionados: [calculos.md](calculos.md), [ambiente.md](ambiente.md)

## 1. Checklist do build

Implementado em `core/validacao.py`, um item por função, na mesma numeração desta lista.
Roda sobre o `data-YYYY-MM.json` já gerado. O build falha se qualquer item não passar.

1. **Checks da planilha zerados** — `CEO-Dashboard!C2:L3`, `Dashboard!K16:L32`,
   `net_in_out!R:S`, `aum_receita!AG`. A planilha se autoconfere; se algum check não for
   zero, a fonte está inconsistente e o dashboard não deve ser gerado.
2. **AUM Total = Onshore + Offshore** dentro de tolerância de arredondamento.
3. **Soma dos officers = Total** na `CEO-Dashboard` (com Fdos Alocação incluído).
4. **Soma das categorias = Total** em `resumo` (Qtd, AUM e Receita).
5. **NET = IN − OUT** em `net_in_out`, mês a mês e no acumulado.
6. **Qtd. de portfólios** bate entre `resumo!P27`, `CEO-Dashboard!L38` e a contagem de
   linhas em `ar_onshore` + `ar_offshore`.
7. **Câmbio** extraído bate entre `resumo!B4` e `regiao!G2`.
8. **Mês de fechamento** presente e não-zerado em todas as séries de 2026.
9. **Mensalização** — `receita_onshore_competencia × 21 / dias_uteis` reproduz `resumo!H7`
   dentro de tolerância de arredondamento.
10. **Qtd. Grupos** — o recálculo a partir de `ar_on_info`/`ar_off_info` reproduz as linhas
    60 e 61 de cada bloco de `cons_officer`, e o total de grupos distintos bate com
    `resumo!AA17`. É o teste mais barato de que o mapeamento de colunas das dimensões está
    correto.

Depois de gerar: abrir o HTML, conferir os 4 KPIs contra a planilha célula a célula, e
verificar que nenhum gráfico ficou com paleta default ou rótulo em locale errado.

## 2. Checks embutidos na geradora

A planilha se autoconfere. Todos devem resultar em zero; qualquer valor diferente indica
base inconsistente e o build deve falhar.

| Onde | Verifica |
|---|---|
| `CEO-Dashboard!C3` | `AUM MFO − soma dos officers / 1000` |
| `CEO-Dashboard!F3` | `Run Rate − soma da receita dos officers × 12 / 1e6` |
| `CEO-Dashboard!H3` | `Δ total − (Δ onshore + Δ offshore)` |
| `CEO-Dashboard!I3` | `ROA total − ROA recalculado dos officers` |
| `aum_receita!AG8` | `NET − soma das quebras por tipo de veículo` |
| `aum_receita!AG17` | `Receita − soma das quebras` |
| `net_in_out!R7` | `IN − soma dos tipos` |
| `net_in_out!S7` | `IN − total de io_portfolios` |
| `net_in_out!R45` | `NET − (IN + OUT)` |
| `io_grupos!Q5` | `soma mensal − NET de net_in_out` |
| `io_grupos!Q7` | `soma mensal − soma YTD` |
| `resumo!AC21:AC24` | `total por categoria − total por grupo` (AUM e receita) |

---

## 3. Armadilhas e defeitos da fonte

1. **`in_out` vs `info_net_in_out`** — ver [modelo-de-dados.md](modelo-de-dados.md). A mais perigosa.
2. **`ROA MFO`** — offshore inteiro conta como MFO, e o numerador não é mensalizado. Ver [calculos.md](calculos.md) §3.5.
3. **Mensalização só no onshore.** Aplicar ao offshore infla a receita em `21/nwdays`.
4. **Câmbio arredondado no texto.** `resumo!B4` mostra 5,08; as contas usam 5,0773.
5. **Backup vazio ou `#N/D`** é "sem backup atribuído", nunca uma pessoa. Vem do de-para
   `info!AK:AL`.
6. **Colunas de meses futuros vêm zeradas**, não vazias. Truncar pelo mês-base.
7. **`#DIV/0!`, `#N/A` e `TBD`** aparecem em células de check e em `aum_receita` linha 32.
   Tratar como nulo na extração; nunca propagar ao JSON.

## 4. Onde cada armadilha aparece

Complementos da seção 3, sem repetir o que já está lá.

- **Câmbio cheio** também está em `resumo!U26`, além de `info!AQ3`.
- **Erros do Excel** aparecem em células de check e em `ar_adm_off!C145`; `TBD` em
  `aum_receita` linha 32 (Icatu, 2026 — fora de escopo).
- **Officers e backups são conjuntos diferentes.** `Yan`, `Felipe F.`, `Dudu` e `Luiz`
  aparecem só como backup e não constam na lista de officers. Não assumir subconjunto.
- **Nota de rodapé** na `CEO-Dashboard` B41: "Ainda existem clientes vinculados" — replicar
  como observação da página de officers.

---

[← Índice](../CLAUDE.md)
