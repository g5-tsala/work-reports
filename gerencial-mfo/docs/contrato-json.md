# Contrato do `data-YYYY-MM.json`

> [← Índice](../AGENTS.md) · Relacionados: [modelo-de-dados.md](modelo-de-dados.md), [ambiente.md](ambiente.md), [validacao.md](validacao.md)

O JSON é a **fronteira sagrada** entre as duas etapas (regra inviolável 7). Mudou a
planilha, mexe só no extrator; mudou o layout, mexe só no template. Quem quebrar o formato
sobe `VERSAO_CONTRATO` em `core/config.py`.

Auditar com `jq`:

```bash
jq '.consolidado.aum' outputs/2026-07/data-2026-07.json
jq -r '.avisos[]'     outputs/2026-07/data-2026-07.json
```

## 1. Princípios

1. **Extrair, nunca recalcular.** Os números já vêm calculados da geradora. A única
   aritmética do extrator é a conferência da etapa de validação.
2. **Moeda preservada.** O offshore sai em US$, como na planilha; a conversão é do
   consumidor, com `parametros.dolar`. Converter na extração esconderia a origem.
3. **Nada de meses futuros.** Toda série é truncada pelo mês-base (regra inviolável 4).
4. **Erro do Excel vira `null`.** `#DIV/0!`, `#N/D` e `TBD` nunca chegam ao JSON. Traço
   (`-`) some em campo numérico, mas **sobrevive em campo de texto** — o officer dos
   Fdos Alocação é literalmente `-`.

## 2. Blocos de primeiro nível

| Chave | Origem | Conteúdo |
|---|---|---|
| `meta` | — | mês-base, arquivo de origem, versões, marca de confidencialidade |
| `parametros` | `info` | `dolar`, `cdi_mes`, `nwdays_mes`, de-para `login → apelido` |
| `consolidado` | `resumo`, `CEO-Dashboard` | KPIs, ROA por categoria e por grupo, notas |
| `historico` | `aum_receita`, `roa_historico` | séries longas 2018→mês-base |
| `officers` | `CEO-Dashboard`, `cons_officer` | tabela do ranking e o bloco mensal de cada officer |
| `carteira` | `ar_onshore`, `ar_offshore`, `ar_grupos`, `regiao` | portfólios, grupos e regiões |
| `captacao` | `net_in_out`, `io_grupos`, `io_portfolios`, `Dashboard` | IN/OUT cliente e NET executado |
| `estrutura` | `ar_adm_on`, `ar_adm_off`, `G5JUS` | administradores e FIDCs |
| `checks_planilha` | várias | os checks embutidos, com `ok` por célula |
| `avisos` | — | defeitos conhecidos tratados na extração |

## 3. Dois formatos que se repetem

### 3.1 Bloco de linhas rotuladas

Usado em `aum_receita`, `roa_historico`, `cons_officer`, `ar_adm_*` e `net_in_out`:

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

- `chave` é o slug ASCII do rótulo. `R$`→`rs`, `US$`→`usd`, `%`→`pct`, `Δ`→`delta` — sem
  isso `AUM (R$)` e `Δ AUM` colidiriam na mesma chave.
- `nivel` vem do **recuo da célula** na planilha; `pai` é a chave da linha acima com nível
  menor. É o que sustenta o drill-down sem lista de pais/filhos escrita no código, e é o
  que distingue os três `Carteira` de `aum_receita` (sob `IN/OUT`, sob `Receita` e sob
  `Receita Mens.`).
- `linha` é o número da linha na aba — serve para conferir contra a planilha.
- **Rótulos repetem; chaves repetem.** Casar por `(pai, chave)`, nunca só por `chave`.

### 3.2 Base de posição

`carteira.portfolios.onshore` e `.offshore`, com uma linha por portfólio:

```json
{
  "moeda": "R$",
  "meses": ["2025-12", "…", "2026-07"],
  "linhas": [
    {"portfolio": "…", "tipo": "Fundo", "adm": "BTG", "grupo": "…",
     "officer": "…", "backup": "…", "regiao": "…", "segmento": "MFO",
     "aum": [], "receita": []}
  ],
  "total": {"aum": [], "receita": []}
}
```

Os pares AUM/Receita são conferidos contra a linha de cabeçalho da planilha antes de
serem lidos: uma coluna trocada na geradora viraria uma série invertida sem sintoma.
`backup` vem `null` quando a planilha traz `#N/D` — é "sem backup atribuído", nunca uma
pessoa.

### 3.3 Bloco de administrador

`estrutura.administradores.{onshore,offshore}.blocos[]` traz, além das linhas rotuladas, o
campo **`agrupamento`** — o marcador que a planilha escreve na linha acima do nome do bloco.
Quando dois administradores compartilham o mesmo marcador (`GVA/Daycoval`), a geradora
**repete o AUM e a receita** entre eles; só os custos são próprios. Somar a coluna nesse
caso superestima o AUM.

## 4. Pontos de atenção do consumidor

- **`captacao.net_in_out` e `captacao.captacao_cliente` são cliente (sem G5);
  `captacao.net_executado` é com G5.** Não somar um com o outro. É a armadilha número um
  do modelo ([modelo-de-dados.md](modelo-de-dados.md) §6).
- **`officers.blocos` inclui os Fdos Alocação** com `e_fdos_alocacao: true` e `nome: "-"`.
  Sempre nos totais; o toggle "Ex-Fdos Alocação" recalcula proporções, não totais.
- **`roa_mfo`** não é comparável ao `roa` lado a lado — todo o offshore conta como MFO e o
  numerador não é mensalizado ([calculos.md](calculos.md) §3.5). Sinalizar na interface.
- **Não somar `qtd_grupos_officer` entre officers**: um grupo pode ter portfólios sob
  titulares diferentes. O total correto é `consolidado.roa_grupo.total.qtd`.
- **O eixo de `historico` não é uniforme** (semestral até 2025-12, mensal em 2026). Tratar
  como categórico ordenado.

---

[← Índice](../AGENTS.md)
