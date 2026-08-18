# Validação, defeitos e armadilhas

O build **falha** se qualquer item do checklist não passar. Nunca gerar dashboard a partir
de base inconsistente.

> [← Índice](../CLAUDE.md) · Relacionados: [calculos.md](calculos.md), [ambiente.md](ambiente.md)

## 1. Checklist do build

O build falha se qualquer item não passar.

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
2. **`ROA MFO`** — offshore inteiro conta como MFO, e o numerador não é mensalizado. Ver 5.5.
3. **Mensalização só no onshore.** Aplicar ao offshore infla a receita em `21/nwdays`.
4. **Câmbio arredondado no texto.** `resumo!B4` mostra 5,08; as contas usam 5,0773.
5. **Rótulo de data errado.** `aum_receita!C5` e `roa_historico!C5` dizem `2019-06`, mas a
   série é `2018-06` — há `2019-06` duplicado em `E5`. Corrigir na extração, avisar, não
   alterar a planilha.
6. **`cons_officer` linhas 60/61 — corrigido em 2026-08-18.** A fórmula original filtrava
   pela coluna errada. Foi substituída por duas métricas (grupos como officer, grupos como
   backup) e o snapshot de 2026-07 foi regerado. **Snapshots anteriores a essa data trazem
   o valor antigo em uma única linha 60.** Ver [calculos.md §3.5](calculos.md).
7. **`#N/D` na coluna Backup — resolvido em 2026-08-18.** Era backup sem cadastro no
   de-para `info!AK:AL` (`Felipe F.` e `Mathias`). Snapshots anteriores a essa data ainda
   trazem `#N/D`; tratar como "sem backup atribuído", nunca como pessoa.
8. **Colunas de meses futuros vêm zeradas**, não vazias. Truncar pelo mês-base.
9. **`#DIV/0!`, `#N/A` e `TBD`** aparecem em células de check e em `aum_receita` linha 32.
   Tratar como nulo na extração; nunca propagar ao JSON.

## 4. Outros pontos de atenção na extração

- **Rótulo de data errado.** Em `aum_receita` e `roa_historico`, a primeira coluna de datas
  (C5) está rotulada `2019-06`, mas a sequência e os valores indicam `2018-06` — há um
  `2019-06` duplicado em E5. Tratar como 2018-06 no build, emitir aviso no console, **não**
  alterar a planilha.
- **Meses futuros zerados.** Colunas de meses ainda não fechados vêm com `0`, não vazias.
  Truncar pelo mês da pasta.
- **`#DIV/0!` e `#N/A`** aparecem em células de check e em `ar_adm_off!C145`. Tratar como
  nulo na extração, nunca propagar para o JSON.
- **Câmbio arredondado no texto.** `resumo!B4` exibe "US$ 1 = R$ 5,08"; as contas usam o
  valor cheio (5,0773). Extrair de `info!AQ3` ou `resumo!U26`, nunca do texto.
- **`cons_officer` linhas 60/61** tinham fórmula errada, corrigida em 2026-08-18 e
  desdobrada em duas métricas (grupos como officer, grupos como backup). O snapshot de
  2026-07 já saiu corrigido; snapshots anteriores trazem o valor antigo numa única linha 60.
- **`#N/D` na coluna Backup** aparece em snapshots anteriores a 2026-08-18. Tratar como
  "sem backup atribuído", nunca como pessoa.
- **Officers e backups são conjuntos diferentes.** `Yan`, `Felipe F.`, `Dudu` e `Luiz`
  aparecem só como backup e não constam na lista de officers. Não assumir subconjunto.
- **`in_out` vs `info_net_in_out`** são duas bases de schema idêntico e conteúdo diferente —
  a segunda exclui as movimentações do próprio grupo G5. Trocar uma pela outra produz
  números plausíveis e errados. É a armadilha número um do modelo; ver
  [modelo-de-dados.md](modelo-de-dados.md).
- **`TBD`** em `aum_receita` linha 32 (Icatu, 2026). Fora de escopo.
- **Nota de rodapé** na `CEO-Dashboard` B41: "Ainda existem clientes vinculados" — replicar
  como observação da página de officers.

---

[← Índice](../CLAUDE.md)
