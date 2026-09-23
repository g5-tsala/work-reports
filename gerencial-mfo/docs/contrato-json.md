# Contrato do `gerencial-mfo-YYYY-MM.json`

Fronteira entre extração e renderização (regra inviolável 7). Quebrou o formato → sobe
`VERSAO_CONTRATO` em `core/config.py`. Auditar com `jq`:

```bash
jq '.consolidado.aum' outputs/2026-08/gerencial-mfo-2026-08.json
jq -r '.avisos[]'     outputs/2026-08/gerencial-mfo-2026-08.json
```

## 1. Princípios

1. **Extrair, nunca recalcular.** A única aritmética sobre o JSON é a da validação.
2. **Moeda preservada.** O extrator não converte: offshore sai na moeda em que a planilha o
   traz (US$ nas bases; as linhas em R$ que a própria planilha calcula, como `aum_rs` de
   `aum_receita` offshore ou `total_reais` de `net_in_out`, vêm prontas). Conversão é do
   consumidor, com `parametros.dolar`.
3. **Sem meses futuros.** Toda série é truncada no mês-base.
4. **Erro do Excel vira `null`** (`#DIV/0!`, `#N/D`, `TBD`). Traço some em campo numérico e
   sobrevive em texto — o officer dos Fdos Alocação é literalmente `-`.

## 2. Blocos de primeiro nível

| Chave | Origem | Conteúdo |
|---|---|---|
| `meta` | — | mês-base, arquivo de origem, `gerado_em`, versões, confidencialidade |
| `parametros` | `info` | `dolar`, `cdi_mes`, `nwdays_mes`, `officers_de_para` |
| `consolidado` | `resumo`, `CEO-Dashboard` | `aum`, `receita_mens`, `receita_ano_competencia`, `run_rate`, `projecao_ano`, `roa` (on/off/total), `cambio_exibido`, `kpis_ceo`, `roa_categoria`, `roa_grupo`, `notas` |
| `historico.aum_receita` | `aum_receita` | `onshore` (+ `dias_uteis`) e `offshore` (+ `dolar`), 2018→mês-base |
| `officers` | `CEO-Dashboard`, `cons_officer` | `tabela_ceo` (ranking) e `blocos` (métricas mensais por officer) |
| `carteira` | `ar_onshore`, `ar_offshore`, `ar_grupos`, `regiao` | `portfolios`, `grupos.{rankings,serie}`, `regioes` (+ `dolar_offshore`) |
| `captacao` | `net_in_out`, `io_grupos`, `io_portfolios`, `Dashboard` | `net_in_out.{onshore,offshore}`, `grupos.{mensal,ytd}`, `portfolios`, `captacao_cliente`, `net_executado` |
| `estrutura` | `ar_adm_on`, `ar_adm_off`, `G5JUS` | `administradores.{onshore,offshore}`, `g5jus` |
| `checks_planilha` | várias | um item por célula de check, com `ok` |
| `avisos` | — | defeitos da fonte tratados na extração |

## 3. Formatos recorrentes

### 3.1 Bloco de linhas rotuladas

`aum_receita`, `cons_officer`, `ar_adm_*` e `net_in_out` (que acrescenta `secao` e `total`).
`captacao_cliente` é uma lista direta de linhas no mesmo formato, com `mes`, `ano`,
`incremento_receita_mi_ano` e `roa_incremental` no lugar de `valores`.

```json
{
  "meses": ["2026-06", "2026-07"],
  "dias_uteis": [21, 23],
  "linhas": [
    {"rotulo": "AUM (R$)", "chave": "aum_rs", "nivel": 0, "pai": null,
     "linha": 6, "valores": [38028500000, 39130347654]}
  ]
}
```

- `chave`: slug ASCII do rótulo; `R$`→`rs`, `US$`→`usd`, `%`→`pct`, `Δ`→`delta` (evita colisão
  entre `AUM (R$)` e `Δ AUM`).
- `nivel`: recuo da célula na planilha. `pai`: chave da linha acima com nível menor. Sustenta o
  drill-down sem lista de pais no código.
- `linha`: número da linha na aba, para conferência.
- **Rótulos e chaves repetem** (`Carteira` aparece sob `IN/OUT`, `Receita` e `Receita Mens.`):
  casar por `(pai, chave)` — `Contexto.linha(bloco, chave, pai)`.

### 3.2 Base de posição

`carteira.portfolios.{onshore,offshore}`, uma linha por portfólio:

```json
{
  "moeda": "R$",
  "meses": ["2025-12", "…", "2026-08"],
  "linhas": [
    {"portfolio": "…", "tipo": "Fundo", "adm": "BTG", "grupo": "…",
     "officer": "…", "backup": "…", "regiao": "…", "segmento": "MFO",
     "aum": [], "receita": []}
  ],
  "total": {"aum": [], "receita": []}
}
```

Os pares AUM/Receita são conferidos contra o cabeçalho antes da leitura (par trocado vira
aviso e é ignorado). `backup` é `null` quando a planilha traz `#N/D`. A receita é por competência.

### 3.3 Officer marcado

`officers.tabela_ceo[].marcado = true` quando o nome tem cor de fonte explícita diferente de
preto na `CEO-Dashboard` ([MEMORY.md](MEMORY.md), armadilha 8). A nota que explica a marca
(`"* Ainda existem clientes vinculados"`) entra em `consolidado.notas`, lida de +2 a +6 linhas
abaixo do rótulo `Total Ex- Fdos Alocação`.

### 3.4 Bloco de administrador

`estrutura.administradores.{onshore,offshore}.blocos[]` traz, além das linhas rotuladas,
`agrupamento` — o marcador da linha acima do nome. Mesmo marcador (`GVA/Daycoval`) = AUM e
receita repetidos entre os blocos; somar superestima o AUM.

## 4. Pontos de atenção do consumidor

- `captacao.net_in_out`, `captacao_cliente` e `net_executado` são **todos cliente** (sem G5):
  três cortes da mesma captação, que fecham entre si. Não somar um com o outro.
- `officers.blocos` inclui os Fdos Alocação (`e_fdos_alocacao: true`, `nome: "-"`).
- `roa_mfo` não é comparável a `roa` ([calculos.md](calculos.md) §3.5); a interface não exibe a
  ressalva por decisão do negócio.
- Não somar `qtd_grupos_officer` entre officers; o total é `consolidado.roa_grupo.total.qtd`.
- `historico` tem eixo não uniforme (semestral até 2025-12, mensal em 2026): categórico ordenado.
