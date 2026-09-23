# Métricas e cálculos

O que cada número significa (§0) e como a geradora `Gerencial MFO.xlsm` o calcula (§1–§3).
**Nada aqui é inferência:** cada regra traz a célula de origem entre colchetes. A planilha
mensal é snapshot com valores colados da geradora; o extrator lê valores, este doc explica de
onde vieram. Nomes definidos e colunas das bases: [modelo-de-dados.md](modelo-de-dados.md).

## 0. Glossário

Fonte primária: notas de `resumo!B18:B22`.

| Métrica | Definição |
|---|---|
| **AUM** | Carteira administrada + fundos + estruturados + alocação + previdência + feeder + offshore. |
| **Receita** | Do mês, por competência. **Só recorrente** (taxa de gestão) — sem performance fee nem receitas indiretas. |
| **Receita mensalizada** | Receita normalizada por dias úteis (§3.1). **Default** de KPIs e séries; competência é série secundária. |
| **Run Rate** | Receita mensalizada do mês × 12. |
| **Projeção Ano** | Receita por competência acumulada no ano + mensalizada do último mês × meses restantes. |
| **ROA** | Receita anualizada ÷ AUM. Em %, 2 casas. |
| **ROA MFO** | Por officer, restrito ao segmento MFO no onshore (sem Institucional e Estruturado). Tem dois desvios de fórmula (§3.5). |
| **Qtd. Grupos (officer / backup)** | Grupos econômicos distintos em que a pessoa é titular / backup, contando só portfólios com AUM ou receita > 0 no mês. Não somar entre officers. |
| **IN** | Aberto em **Início (no ano)** (primeiro aporte de grupo novo no ano) e **Clientes antigos**. |
| **OUT** | Aberto em **Uso pessoal** e **Saída para concorrência** — o dado mais acionável do relatório. Negativo na planilha. |
| **NET** | IN + OUT (OUT já negativo). |
| **ROA incremental** | ROA anualizado YTD sobre o volume captado no período. |

**Moeda:** R$ em toda visão consolidada. Offshore convertido pelo câmbio do mês (`dolar`,
§2). Página puramente offshore fica em US$, com a moeda no título e no cabeçalho de cada coluna.

**Fdos Alocação:** pseudo-officer na `CEO-Dashboard` (officer `-`, grupo `G5`) — fundos próprios
da G5 nos quais as carteiras alocam. Sempre nos totais, para o TOTAL bater entre visões.

## 1. Origem dos dados

A geradora puxa de um SQL Server (queries montadas em `info`, coluna AO em diante) e de funções
de um add-in proprietário. Nada disso é replicável em Python, nem precisa: os resultados já vêm
colados na planilha mensal.

| Função | Retorna |
|---|---|
| `getPTAX(data)` | PTAX de fechamento |
| `acCDI(ini, fim)` | CDI acumulado no intervalo |
| `getAcumCDI(data)` | CDI acumulado desde o início da série |
| `NWDAYS(ini, fim)` | dias úteis no intervalo |
| `wEoMonth(data, n)` | último dia útil do mês deslocado em `n` |

Tabelas de origem: onshore `cart_AUX_passivo`, `cart_AUX_gerencial`, `cart_AUX_moviment`,
`cad_carteiras`, `contr_gerencial`, `contr_moviment`; offshore `Movimentacoes`, `ger_cotas`,
`off_MovimentacoesDiaria`. Filtros onshore: `descricao IN ('mov_Aplicação','mov_Resgate',
'mov_bloqueio_judicial')`, `categoria <> 'CarteiraModelo'`, `relatorio_consolidacao = 1`,
`conta_gerencial = 1` e listas de exclusão de administradores, carteiras e bancos. Offshore:
`obs IN ('Transfer In','Transfer Out')`, `cod_ativo = 'curr_USD'`.

## 2. Parâmetros globais — aba `info`

| Nome definido | Célula | Fórmula na geradora | Jul/26 |
|---|---|---|---|
| `data` | `info!AP1` | primeiro dia do mês-base | 2026-07-01 |
| `data_format` | `info!AQ2` | `=TEXT(data,"AAAA-MM-DD")` | 2026-07-01 |
| `dolar` | `info!AQ3` | `=getPTAX(wEoMonth(data))` | 5,0773 |
| `cdi_mes` | `info!AQ4` | `=acCDI(wEoMonth(data,-1), wEoMonth(data))-1` | 0,0121521867 |
| `nwdays_mes` | `info!AQ5` | `=NWDAYS(wEoMonth(data,-1), wEoMonth(data))` | 23 |

Extrair `dolar` de `info!AQ3` (ou `resumo!U26`), nunca do texto arredondado de `resumo!B4`.
`info!AK:AL` é o de-para `login → apelido` do officer (`amendes → Abrahão`, …), que liga
`cons_officer` à `CEO-Dashboard`.

## 3. Fórmulas

### 3.1 Mensalização e anualização

```
Receita Mens.      = Receita_competência / nwdays_mes * 21        [aum_receita!C24]
Receita anualizada = Receita Mens. * 12
                   = Receita_competência / nwdays_mes * 252       [resumo!R9]
```

**Só onshore.** Offshore entra por competência, anualizado com `* 12` puro
[`ar_adm_off!H10`, `resumo!R26`, `cons_officer!C38`]. A coluna "Receita (R$)" da
`CEO-Dashboard` já vem mensalizada no onshore — não mensalizar de novo.

### 3.2 Consolidado — `resumo`

```
AUM onshore  [C7] = HLOOKUP(data, aum_receita_on, 2, FALSE)
AUM offshore [C8] = HLOOKUP(data, aum_receita_off, 2, FALSE) * dolar
AUM total    [C9] = C7 + C8

Run Rate onshore  [K7] = H7 * 12      ; H7 = Receita Mens. do mês
Run Rate offshore [K8] = H8 * 12      ; H8 = receita offshore do mês, em R$
Run Rate total    [K9] = K7 + K8

Projeção Ano [F7] = G7 + (12 - MONTH(data)) * H7
                    G7 = SUM(aum_receita!S17:AD17)   ; competência acumulada no ano

ROA total   [C10] = K9 / C9
ROA onshore [C13] = K7 / C7
```

Série do Run Rate (Visão Geral): a mesma conta em cada mês de `aum_receita` —
`(onshore.receita_mens_rs + offshore.receita_rs) × 12`, offshore em R$ ao câmbio do mês. No
mês-base fecha com `resumo!K9` (ago/26: R$ 105,97 mi).

### 3.3 ROA por Categoria × Faixa de PL — `resumo!O8:T27`

`U` = tipo de veículo, `V` = piso, `W` = teto da faixa:

```
Qtd     [P9] = COUNTIFS(tipo = U9, AUM >= V9, AUM < W9) - X9
Excl.   [X9] = COUNTIFS(tipo = U9, AUM = 0, Receita = 0)     ; veículos zerados
AUM     [Q9] = SUMIFS(AUM; tipo = U9, AUM >= V9, AUM < W9)
Receita [R9] = SUMIFS(Receita; mesmos filtros) / nwdays_mes * 252
ROA     [S9] = IF(Q9 <> 0, R9 / Q9, 0)
% AUM   [T9] = Q9 / Q27
```

Linha Offshore (26): base `ar_off`, `Receita * 12 * dolar`, sem mensalizar.

### 3.4 ROA por Grupo × Faixa de PL — `resumo!Z8:AE17`

Mesma estrutura sobre a base `grupos`, com o grupo `G5` **excluído das faixas**
(`INDEX(grupos_info,,1) <> "G5"`) e isolado na linha 16. A receita de `grupos` **já é
mensalizada**, então a anualização é `* 12` direto [`AC9`] (conferência jul/26: G5 em
`ar_grupos` = R$ 1.437.959 = receita de `Fdos Alocação` na `CEO-Dashboard`).

### 3.5 Por officer — `cons_officer`

Um bloco de **33 linhas** por officer. Intervalos em `cons_officer!C7:W7` (`$C$31:$O$63`,
`$C$64:$O$96`, …), nome em `C6:W6`; a `CEO-Dashboard` endereça via `ADDRESS`/`INDIRECT` a partir
de `cons_officer!A11`. Colunas são meses: `C` = 2025-12 … `O` = 2026-12. Offsets a partir da
primeira linha do bloco (`r0`):

| Offset | Linha |
|---:|---|
| 0 | Data |
| +1 | AUM Total (R$) |
| +2 … +5 | AUM Onshore, MFO, Institucional, Estruturado |
| +6 | AUM Offshore (US$) |
| +7 | Receita Total Mens. (R$) |
| +8 … +11 | Receita Onshore, MFO, Institucional, Estruturado |
| +12 | Receita Offshore (US$) |
| +13 … +16 | ROA, ROA Onshore, ROA Offshore, ROA MFO |
| +17 … +22 | IN/OUT Total, Onshore, MFO, Institucional, Estruturado, Offshore |
| +23 | Qtd. Portfolios |
| +24 … +28 | Qtd. por tipo (Carteira, Fundo, Fundo/Prev., Estruturado, Offshore) |
| +29 | Qtd. Grupos (Officer) |
| +30 | Qtd. Grupos (Backup) |

Com `C29 = dolar`, `C30 = nwdays_mes` (primeiro bloco):

```
AUM Onshore      [C33] = SUM(ar_on WHERE officer = X, data = mês, header = "AUM")
  MFO / Inst. / Estrut. [C34..C36] = idem + segmento
AUM Offshore US$ [C37] = SUM(ar_off WHERE officer = X, data = mês, header = "AUM")
AUM Total R$     [C32] = C33 + dolar * C37

Receita Onshore  [C39] = SUM(ar_on ... header = "Receita")      ; competência
  MFO            [C40] = idem + segmento = "MFO"
Receita Off US$  [C43] = SUM(ar_off ... header = "Receita")
Receita Total Mens. [C38] = C39 / nwdays_mes * 21 + dolar * C43

ROA          [C44] = C38 * 12 / C32
ROA Onshore  [C45] = C39 * 12 / C33
ROA Offshore [C46] = C43 * 12 / C37
ROA MFO      [C47] = (C40 + C43 * dolar) * 12 / (C34 + C37 * dolar)
```

**ROA MFO tem dois desvios, e o dashboard os replica:** (1) todo o offshore conta como MFO nos
dois lados da razão (`C43`, `C37` são totais, sem filtro de segmento); (2) o numerador parte de
`C40` cru, não mensalizado — em jul/26 infla ~9% (23/21) frente ao `ROA`. Por decisão do negócio
(2026-09-22) a ressalva não aparece na interface.

```
Qtd. Portfolios por tipo [C55..C59]
  = COUNTIFS(officer = X, tipo = T, AUM > 0)
  + COUNTIFS(officer = X, tipo = T, Receita > 0)
  - COUNTIFS(officer = X, tipo = T, AUM > 0, Receita > 0)      ; AUM **ou** receita
```

Qtd. Grupos [+29 / +30]:

```
SOMARPRODUTO(--NÃO(ÉERRO(arrUnion(
  FILTRO(ÍNDICE(ar_on_info,,4),  (ÍNDICE(ar_on_info,,5)=officer)
                               * ((ÍNDICE(ar_on,,C$3)>0) + (ÍNDICE(ar_on,,C$3+1)>0))),
  FILTRO(ÍNDICE(ar_off_info,,4), (ÍNDICE(ar_off_info,,5)=officer)
                               * ((ÍNDICE(ar_off,,C$4)>0) + (ÍNDICE(ar_off,,C$4+1)>0)))))))
; backup: troca a coluna 5 (officer) pela 6 (backup) nos dois filtros
```

Grupos distintos (col. 4) com portfólio de AUM > 0 ou receita > 0 no mês, onshore ∪ offshore;
`arrUnion` deduplica. O checklist recalcula isso a partir das bases (item 10). A soma entre
officers excede o total distinto (376 × 361 em jul/26); o total é `resumo!AA17`.

### 3.6 Captação — `net_in_out`

Base `*_net_*` (sem G5). Para o mês na coluna:

```
IN  [C7]  = SUMIF(mês = C5) sobre in_net_onshore col.3
OUT [C25] = SUMIF(mês = C5) sobre out_net_onshore col.3
NET [C43] = C7 + C25

Por tipo de veículo:           + filtro col.6 = rótulo da linha
Início (no ano)       [C9]  = + filtro col.9 (Ano Início) = YEAR(data)
Clientes antigos      [C10] = + filtro col.9 <> YEAR(data)
Uso pessoal / Saída p/ concorrência = + filtro col.10 (Finalidade)

ROA do IN  [C11] = SUMPRODUCT(valor × taxa) / total do IN
ROA do OUT [C29] = SUMPRODUCT(valor × taxa) / total do OUT
ROA do NET [C49] = (ROA_in × IN + ROA_out × OUT) / NET
```

`Taxa` (col. 5) = taxa de gestão contratada, % a.a. — permite estimar receita incremental sem
esperar o fechamento seguinte.

**Offshore em R$ e consolidado.** A coluna `Ano (R$)` do bloco offshore (`net_in_out!P`,
`total_reais` no JSON) é Σ (valor do mês × câmbio **daquele** mês) — confere no centavo em
ago/26. O dashboard usa a mesma regra para o consolidado, que a planilha não traz:

```
consolidado[mês] = onshore[mês] + offshore[mês] × dolar[mês]
consolidado[ano] = onshore.total + offshore.total_reais
```

Converter o ano pelo câmbio do mês-base dá outro número (IN ago/26: R$ 239,5 mi × 237,9 mi).

### 3.7 Captação por portfólio — `io_portfolios` (só no JSON)

```
IN  [F4] = SUMIF(portfolio, in_net_onshore col.3)
OUT [G4] = SUMIF(portfolio, out_net_onshore col.3)
NET [H4] = F4 + G4
Receita Aprox. (R$/ano) [I4] = D4 * H4        ; D4 = Taxa (% a.a.)
```

Offshore usa as col. 12 (IN) e 13 (OUT), já em R$ ao câmbio do mês da movimentação.

### 3.8 Administradores — `ar_adm_on` / `ar_adm_off` (só no JSON)

Blocos de 13 linhas por administrador:

```
Receita Mens. [S9]  = S8 / dias_úteis * 21       ; onshore apenas
ROA G5 (%)    [S11] = S9 * 12 / S6
Custos        [S14] ← custos_adm_on (negativo)
ROA Adm (%)   [S15] = ABS(S14 * 12 / S6)
```

Offshore: `ROA G5 = Receita * 12 / AUM`, sem mensalizar [`ar_adm_off!H10`].

### 3.9 Região — `regiao`

Três blocos: onshore (`A:E`), offshore (`G:K`, `G2 = dolar`), consolidado (`M:S`).

```
% AUM      [D3] = B3 / SUM(B3:B20)
Consolid.  [N3] = VLOOKUP(região, bloco onshore, 2) + VLOOKUP(região, bloco offshore, 2)
Qtd Grupos [R3] = COUNTIF(mapa grupo→região, região)
```

Mapa grupo → região (`A30:B2004`): `ar_on_info` col. 4 e 7 empilhadas com as de `ar_off_info`.

### 3.10 Cotização — `cotas` (backlog)

Base de AUM tratada como portfólio, indexada em 2018-01 = 1,00:

```
Var (%)  [I6] = Rendimento / AUM_anterior
Cota     [J6] = (Var + 1) * Cota_anterior
Offshore em R$: Rendimento [M6] = Rendimento_US$ * dólar_mês
                                + (dólar_mês / dólar_anterior - 1) * AUM_R$_anterior   ; isola o câmbio
AUM G5 consolidado [P6] = AUM_local + AUM_offshore_R$
CDI acumulado      [U]  = getAcumCDI(wEoMonth(data))
```

### 3.11 Top grupos — `ar_grupos`

```
AUM do rank n [D5]  = LARGE(coluna de AUM, n)
Nome          [C5]  = INDEX(nomes, MATCH(D5, coluna de AUM, 0))
G5-TOTAL      [D17] = AUM onshore + AUM offshore do mês
%             [D18] = soma do Top 10 / total
```

Empate de AUM devolve o mesmo nome duas vezes: casar por posição, não por nome.
