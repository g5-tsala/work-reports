# Referência de cálculos

Documento derivado da leitura das fórmulas de `Gerencial MFO.xlsm`, a planilha geradora.
**Nada aqui é inferência.** Cada regra traz a célula de origem entre colchetes.

Este arquivo existe para que o extrator (`core/extracao/`) reproduza os números sem
adivinhar contas.
Consultar sempre que for implementar ou depurar uma métrica. O o [índice](../CLAUDE.md) é o guia de operação; este é o dicionário de fórmulas.

> A versão mensal (`Gerencial MFO YYYY-MM.xlsx`) é um *snapshot com valores colados* da
> geradora. O extrator lê os valores; este documento explica de onde eles vieram.

---

> [← Índice](../CLAUDE.md) · Relacionados: [metricas.md](metricas.md), [modelo-de-dados.md](modelo-de-dados.md), [validacao.md](validacao.md)

## 1. Origem dos dados

A geradora puxa de um SQL Server via queries montadas na aba `info` (coluna AO em diante) e
de funções de um add-in proprietário. Nenhuma delas é replicável em Python — e não precisa
ser, porque os resultados já vêm colados na planilha mensal.

| Função | O que retorna |
|---|---|
| `getPTAX(data)` | PTAX de fechamento na data |
| `acCDI(ini, fim)` | CDI acumulado no intervalo |
| `getAcumCDI(data)` | CDI acumulado desde o início da série |
| `NWDAYS(ini, fim)` | Dias úteis no intervalo |
| `wEoMonth(data, n)` | Último dia útil do mês deslocado em `n` meses |

Tabelas SQL de origem, para contexto: `cart_AUX_passivo`, `cart_AUX_gerencial`,
`cart_AUX_moviment`, `cad_carteiras`, `contr_gerencial`, `contr_moviment` (onshore);
`Movimentacoes`, `ger_cotas`, `off_MovimentacoesDiaria` (offshore).

As queries onshore filtram explicitamente:
`descricao IN ('mov_Aplicação','mov_Resgate','mov_bloqueio_judicial')`,
`categoria <> 'CarteiraModelo'`, `relatorio_consolidacao = 1`, `conta_gerencial = 1`, e
listas de exclusão de administradores, carteiras e bancos. Offshore filtra
`obs IN ('Transfer In','Transfer Out')` e `cod_ativo = 'curr_USD'`.

## 2. Parâmetros globais — aba `info`

Cinco parâmetros regem todo o cálculo. Na geradora são fórmulas; na planilha mensal já são
valores colados (a própria aba anota "colar como valor").

| Nome definido | Célula | Fórmula na geradora | Jul/26 |
|---|---|---|---|
| `data` | `info!AP1` | primeiro dia do mês-base | 2026-07-01 |
| `data_format` | `info!AQ2` | `=TEXT(data,"AAAA-MM-DD")` | 2026-07-01 |
| `dolar` | `info!AQ3` | `=getPTAX(wEoMonth(data))` | 5,0773 |
| `cdi_mes` | `info!AQ4` | `=acCDI(wEoMonth(data,-1), wEoMonth(data))-1` | 0,0121521867 |
| `nwdays_mes` | `info!AQ5` | `=NWDAYS(wEoMonth(data,-1), wEoMonth(data))` | 23 |

**Atenção:** `resumo!B4` exibe o câmbio arredondado ("US$ 1 = R$ 5,08"). O valor usado nas
contas é o cheio (`dolar` = 5,0773). Extrair de `info!AQ3` ou de `resumo!U26`, nunca do texto.

`info!AK:AL` é o de-para `login → apelido do officer` (`amendes → Abrahão`,
`ffleury → Fabio`, `rmachado → Rodrigo M.`, …). É o que liga `cons_officer` à `CEO-Dashboard`.

## 3. Fórmulas canônicas

### 3.1 Mensalização e anualização

```
Receita Mens. = Receita_competência / nwdays_mes * 21          [aum_receita!C24]
Receita anualizada = Receita Mens. * 12
                   = Receita_competência / nwdays_mes * 252    [resumo!R9]
```

21 é o mês-padrão; 21 × 12 = 252. As duas formas aparecem na planilha e são idênticas.

**A mensalização é aplicada somente ao onshore.** O offshore entra sempre por competência,
anualizado com `* 12` puro — confirmado em `ar_adm_off!H10`, `resumo!R26` e `cons_officer!C38`.

### 3.2 Consolidado — aba `resumo`

```
AUM onshore  [C7] = HLOOKUP(data, aum_receita_on, 2, FALSE)
AUM offshore [C8] = HLOOKUP(data, aum_receita_off, 2, FALSE) * dolar
AUM total    [C9] = C7 + C8

Run Rate onshore  [K7] = H7 * 12          ; H7 = Receita Mens. do mês
Run Rate offshore [K8] = H8 * 12          ; H8 = Receita offshore do mês (US$→R$)
Run Rate total    [K9] = K7 + K8

Projeção Ano [F7] = G7 + (12 - MONTH(data)) * H7
                    G7 = SUM(aum_receita!S17:AD17)   ; receita por competência no ano

ROA total [C10] = K9 / C9                 ; run rate / AUM
ROA onshore [C13] = K7 / C7
```

Note que a Projeção Ano soma **competência** acumulada no ano e projeta os meses restantes
pela **mensalizada** do último mês.

### 3.3 ROA por Categoria × Faixa de PL — `resumo!O8:T27`

Para cada linha, `U` = tipo de veículo, `V` = piso da faixa, `W` = teto:

```
Qtd    [P9] = COUNTIFS(tipo = U9, AUM >= V9, AUM < W9) - X9
Excl.  [X9] = COUNTIFS(tipo = U9, AUM = 0, Receita = 0)     ; veículos zerados
AUM    [Q9] = SUMIFS(AUM;  tipo = U9, AUM >= V9, AUM < W9)
Receita[R9] = SUMIFS(Receita; mesmos filtros) / nwdays_mes * 252
ROA    [S9] = IF(Q9 <> 0, R9 / Q9, 0)
% AUM  [T9] = Q9 / Q27
```

A linha Offshore (26) troca os filtros pela base `ar_off` e aplica `* dolar`, com
`Receita * 12 * dolar` — sem mensalizar.

### 3.4 ROA por Grupo × Faixa de PL — `resumo!Z8:AE17`

Mesma estrutura sobre a base `grupos`, com duas diferenças:

- as faixas **excluem** o grupo `G5` (`INDEX(grupos_info,,1) <> "G5"`);
- o grupo `G5` aparece isolado na linha 16 (`COUNTIFS(... = "G5")`).

A receita em `grupos` **já está mensalizada**, então a anualização é `* 12` direto
[`AC9`] — coerente com o resto, apesar de parecer divergente à primeira vista.
Conferência: `ar_grupos` linha do G5 em jul/26 = R$ 1.437.959, idêntico à receita de
`Fdos Alocação` na `CEO-Dashboard`, que é mensalizada.

### 3.5 Por officer — aba `cons_officer`

Cada officer ocupa um bloco de **33 linhas**; a `CEO-Dashboard` monta os endereços com
`ADDRESS`/`INDIRECT` a partir do índice em `cons_officer!A11`. Os intervalos de cada bloco
estão em `cons_officer!C7:W7` (`$C$31:$O$63`, `$C$64:$O$96`, …), e o nome do officer em
`C6:W6`. As colunas são meses: `C` = 2025-12, `D` = 2026-01, …, `J` = 2026-07, `O` = 2026-12.

Deslocamentos a partir da primeira linha do bloco (`r0`, = 31 no primeiro):

| Offset | Linha |
|---:|---|
| 0 | Data |
| +1 | AUM Total (R$) |
| +2 … +5 | AUM Onshore, MFO, Institucional, Estruturado |
| +6 | AUM Offshore (US$) |
| +7 | Receita Total Mens. (R$) |
| +8 … +11 | Receita Onshore, MFO, Institucional, Estruturado |
| +12 | Receita Offshore (US$) |
| +13 … +16 | ROA, ROA Onshore, ROA Offshore, **ROA MFO** |
| +17 … +22 | IN/OUT Total, Onshore, MFO, Institucional, Estruturado, Offshore |
| +23 | Qtd. Portfolios |
| +24 … +28 | Qtd. por Tipo (Carteira, Fundo, Fundo/Prev., Estruturado, Offshore) |
| +29 | **Qtd. Grupos (Officer)** |
| +30 | **Qtd. Grupos (Backup)** |

Dentro do bloco, com `C29 = dolar` e `C30 = nwdays_mes`:

```
AUM Onshore      [C33] = SUM(ar_on WHERE officer = X, data = mês, header = "AUM")
  MFO            [C34] = idem + segmento = "MFO"
  Institucional  [C35] = idem + segmento = "Institucional"
  Estruturado    [C36] = idem + segmento = "Estruturado"
AUM Offshore US$ [C37] = SUM(ar_off WHERE officer = X, data = mês, header = "AUM")
AUM Total R$     [C32] = C33 + dolar * C37

Receita Onshore  [C39] = SUM(ar_on ... header = "Receita")     ; competência
  MFO            [C40] = idem + segmento = "MFO"
Receita Off US$  [C43] = SUM(ar_off ... header = "Receita")
Receita Total Mens. [C38] = C39 / nwdays_mes * 21 + dolar * C43

ROA          [C44] = C38 * 12 / C32
ROA Onshore  [C45] = C39 * 12 / C33
ROA Offshore [C46] = C43 * 12 / C37
ROA MFO      [C47] = (C40 + C43 * dolar) * 12 / (C34 + C37 * dolar)
```

**Duas particularidades do `ROA MFO` que importam ao reproduzir o número:**

1. **Todo o offshore é contado como MFO**, nos dois lados da razão. Não há filtro de
   segmento sobre `ar_off` — a fórmula usa `C43` e `C37`, que são os totais offshore.
2. **O numerador não é mensalizado.** Enquanto `ROA` [C44] parte de `C38` (mensalizada),
   `ROA MFO` parte de `C40` cru. Em jul/26 isso infla o `ROA MFO` em cerca de 9%
   (fator `nwdays/21` = 23/21) frente à base de comparação do `ROA`.

Reproduzir o comportamento da planilha para que os números confiram, e sinalizar a ressalva
na interface. As duas colunas lado a lado não são estritamente comparáveis.

```
Qtd. Portfolios [C55..C59, por Tipo]
  = COUNTIFS(officer = X, tipo = T, AUM > 0)
  + COUNTIFS(officer = X, tipo = T, Receita > 0)
  - COUNTIFS(officer = X, tipo = T, AUM > 0, Receita > 0)
```

Ou seja: conta o portfólio se tiver **AUM ou receita** — união, não interseção. O terceiro
termo remove a dupla contagem.

#### Qtd. Grupos por officer e por backup

`cons_officer` linhas 60 e 61 — duas métricas, uma por papel.

```
Qtd. Grupos (officer) =
  SOMARPRODUTO( -- NÃO(ÉERRO( arrUnion(
    FILTRO( ÍNDICE(ar_on_info,,4),  (ÍNDICE(ar_on_info,,5)=officer)
                                  * ((ÍNDICE(ar_on,,C$3)>0) + (ÍNDICE(ar_on,,C$3+1)>0)) ),
    FILTRO( ÍNDICE(ar_off_info,,4), (ÍNDICE(ar_off_info,,5)=officer)
                                  * ((ÍNDICE(ar_off,,C$4)>0) + (ÍNDICE(ar_off,,C$4+1)>0)) )
  ) ) ) )

Qtd. Grupos (backup) = idêntica, trocando a coluna 5 pela 6 nos dois filtros.
```

Leitura: **grupos econômicos distintos** (col. 4) em que a pessoa é titular (col. 5) ou
backup (col. 6), considerando apenas portfólios com AUM > 0 **ou** receita > 0 no mês,
unindo onshore e offshore. `arrUnion` deduplica; o `SOMARPRODUTO(--NÃO(ÉERRO(...)))` conta
os elementos válidos da união.

Valores em jul/26, conferidos contra recálculo independente a partir de
`ar_on_info`/`ar_off_info` — **os 20 officers batem exatamente**, e o total de 361 grupos
distintos confere com `resumo!AA17`. É o item 10 do checklist de
[validacao.md](validacao.md):

| Officer | Grupos (officer) | Grupos (backup) | | Officer | Grupos (officer) | Grupos (backup) |
|---|---:|---:|---|---|---:|---:|
| Rodrigo M. | 60 | 10 | | Alexandre | 12 | 0 |
| Guilherme | 46 | 19 | | Waldemar | 9 | 0 |
| Fabio | 45 | 15 | | Diego | 9 | 0 |
| Rosangela | 40 | 8 | | Daniel | 7 | 0 |
| Fabietti | 39 | 69 | | Reno | 4 | 4 |
| Abrahão | 25 | 3 | | André B. | 4 | 24 |
| Thomaz | 24 | 26 | | Pedro S. | 4 | 4 |
| Gau | 19 | 44 | | Lucas M. | 3 | 21 |
| Paula W. | 18 | 1 | | João | 3 | 66 |
| | | | | Tainá | 3 | 0 |
| | | | | Michael G. | 1 | 0 |

**A soma por officer (376) é maior que o total de grupos distintos (361)**, porque um grupo
econômico pode ter portfólios sob officers diferentes. Não somar a coluna — o total correto
de grupos vem de `resumo!AA17`, conferido em 361.

**Backup vazio é "sem backup atribuído", nunca uma pessoa.** A coluna sai de um de-para de
nomes (`info!AK:AL`); quem não estiver cadastrado lá vira `#N/D`, e o extrator anula.

**Officers e backups são conjuntos diferentes.** Cinco pessoas aparecem só na coluna
Backup, sem carteira própria: `Yan` (47 grupos), `Felipe F.` (13), `Mathias`, `Dudu` (3) e
`Luiz` (1). E seis officers não fazem backup de ninguém: Alexandre, Daniel, Waldemar,
Tainá, Diego e Michael G. O dashboard não deve assumir que uma lista é subconjunto da outra.

### 3.6 Captação — aba `net_in_out`

Base `*_net_*` (sem G5). Para o mês na coluna:

```
IN  [C7]  = SUMIF(mês = C5) sobre in_net_onshore col.3
OUT [C25] = SUMIF(mês = C5) sobre out_net_onshore col.3
NET [C43] = C7 + C25                       ; OUT já é negativo

Por tipo de veículo: + filtro col.6 = rótulo da linha
Início (no ano)  [C9]  = + filtro col.9 (Ano Início) = YEAR(data)
Clientes antigos [C10] = + filtro col.9 <> YEAR(data)
Uso pessoal / Saída para concorrência = + filtro col.10 (Finalidade)

ROA do IN  [C11] = SUMPRODUCT(valor × taxa) / total do IN
ROA do OUT [C29] = SUMPRODUCT(valor × taxa) / total do OUT
ROA do NET [C49] = (ROA_in × IN + ROA_out × OUT) / NET
```

A `Taxa` (col. 5) é a taxa de gestão contratada do portfólio, em % a.a. — é o que permite
estimar receita incremental sem esperar o fechamento seguinte.

### 3.7 Captação por portfólio — `io_portfolios`

```
IN   [F4] = SUMIF(portfolio, in_net_onshore col.3)
OUT  [G4] = SUMIF(portfolio, out_net_onshore col.3)
NET  [H4] = F4 + G4
Receita Aprox. (R$/ano) [I4] = D4 * H4          ; D4 = Taxa (% a.a.)
```

Offshore usa as colunas 12 (IN) e 13 (OUT) das bases offshore, que já trazem o valor
convertido em R$ ao câmbio do mês da movimentação — **não** ao câmbio do mês-base.

### 3.8 Administradores — `ar_adm_on` / `ar_adm_off`

Blocos de 13 linhas por administrador:

```
Receita Mens. [S9]  = S8 / dias_úteis * 21          ; onshore apenas
ROA G5 (%)    [S11] = S9 * 12 / S6
Custos        [S14] ← custos_adm_on (negativo)
ROA Adm (%)   [S15] = ABS(S14 * 12 / S6)
```

Offshore: `ROA G5 = Receita * 12 / AUM`, sem mensalizar [`ar_adm_off!H10`].

### 3.9 Região — aba `regiao`

Três blocos: onshore (`A:E`), offshore (`G:K`, com `G2 = dolar`) e consolidado (`M:S`).

```
% AUM     [D3] = B3 / SUM(B3:B20)
Legenda   [E3] = TEXT(D3,"0,0%") & " | " & A3
Consolid. [N3] = VLOOKUP(região, bloco onshore, 2) + VLOOKUP(região, bloco offshore, 2)
Qtd Grupos[R3] = COUNTIF(mapa grupo→região, região)
```

O mapa grupo → região (`A30:B2004`) é montado empilhando `ar_on_info` col.4 e col.7 com
`ar_off_info` equivalentes.

### 3.10 Cotização — aba `cotas` (backlog)

Trata a base de AUM como se fosse um portfólio e a indexa a partir de 2018-01 = 1,00.

```
Var (%)  [I6] = Rendimento / AUM_anterior
Cota     [J6] = (Var + 1) * Cota_anterior

Offshore em R$:
Rendimento [M6] = Rendimento_US$ * dólar_do_mês + (dólar_mês/dólar_anterior - 1) * AUM_R$_anterior
```

A segunda parcela isola o efeito cambial sobre o estoque — a variação da cota em R$
mistura performance e câmbio, e a fórmula separa as duas.

```
AUM G5 consolidado [P6] = AUM_local + AUM_offshore_R$
CDI acumulado      [U]  = getAcumCDI(wEoMonth(data))
```

### 3.11 Top grupos — `ar_grupos`

```
AUM do rank n [D5] = LARGE(coluna de AUM, n)
Nome          [C5] = INDEX(nomes, MATCH(D5, coluna de AUM, 0))
G5-TOTAL      [D17] = AUM onshore + AUM offshore do mês
%             [D18] = soma do Top 10 / total
```

O ranking é por valor, então **empate de AUM devolve o mesmo nome duas vezes**. Improvável
com valores contínuos, mas o extrator deve casar por posição, não por nome.

---

> Os nomes definidos e o de-para de colunas das bases estão em [modelo-de-dados.md](modelo-de-dados.md).

---

[← Índice](../CLAUDE.md)
