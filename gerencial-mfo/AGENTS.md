# Gerencial MFO — Dashboard

Transforma a planilha gerencial mensal da área de MFO (Multi-Family Office) da G5 Partners
em um dashboard HTML autocontido, no padrão visual G5 e com leitura de BI.

- **Público:** executivos da área de negócio e board. Não é material de cliente.
- **Idioma:** PT-BR em toda a interface, incluindo eixos de gráfico e rótulos.
- **Confidencialidade:** dados nominais reais (clientes, grupos econômicos, officers).
  O HTML gerado herda a mesma classificação do xlsx de origem — uso interno restrito.
- **Cadência:** mensal. Uma subpasta `inputs/YYYY-MM/` por mês.

## Como rodar

- **Windows:** dois cliques em `gerar-dashboard.bat`.
- **Linux / WSL:** `./gerar-dashboard.sh` (ou `./gerar-dashboard.sh 2026-07`).

Os dois instalam o `uv` se preciso, sincronizam o ambiente, pedem o mês e geram.
Para desenvolvimento: `uv run python build.py 2026-07`.

## Onde está o quê

| Doc | Leia quando for |
|---|---|
| [docs/MEMORY.md](docs/MEMORY.md) | **Começar qualquer sessão.** Estado atual, decisões fechadas, pendências abertas. |
| [docs/ambiente.md](docs/ambiente.md) | Mexer no `uv`, no `.bat` ou no fluxo de build. |
| [docs/modelo-de-dados.md](docs/modelo-de-dados.md) | Entender abas, dimensões, bases e a grade temporal da planilha. |
| [docs/metricas.md](docs/metricas.md) | Saber o que uma métrica significa para o negócio. |
| [docs/calculos.md](docs/calculos.md) | Implementar ou depurar o cálculo de um número. |
| [docs/dashboard.md](docs/dashboard.md) | Mexer em navegação, filtros, drill-down ou layout. |
| [docs/visual.md](docs/visual.md) | Escolher cor, tipografia, formato numérico ou tipo de gráfico. |
| [docs/validacao.md](docs/validacao.md) | Um número não bater, ou antes de dar um build por bom. |

## Estrutura

```
gerencial-mfo/
├── CLAUDE.md                            # este arquivo — índice e regras invioláveis
├── docs/                                # versionado
├── gerar-dashboard.bat                  # ponto de entrada Windows (2 cliques)
├── gerar-dashboard.sh                   # ponto de entrada Linux/WSL
├── pyproject.toml · uv.lock             # ambiente (uv)
├── build.py                             # extrator + renderizador
├── template/                            # base.html, styles.css, app.js, charts.js
├── inputs/                              # FORA do git
│   ├── Gerencial MFO.xlsm                # geradora (macros) — origem das fórmulas
│   └── YYYY-MM/Gerencial MFO YYYY-MM.xlsx
└── outputs/                             # FORA do git — gerado
    └── YYYY-MM/{data,dashboard}-YYYY-MM.{json,html}
```

## Regras invioláveis

1. **Não deduzir contas.** A lógica de cálculo está documentada em
   [docs/calculos.md](docs/calculos.md), derivada das fórmulas reais da geradora, com a
   célula de origem de cada regra. Se algo não estiver lá, ler a geradora e documentar —
   nunca inferir.
2. **Código é versionado; dado não.** `inputs/` e `outputs/` estão no `.gitignore` porque
   carregam nomes reais de clientes. Versiona-se `build.py`, `template/`, `docs/`,
   `pyproject.toml` e `uv.lock`.
3. **Um build lê apenas o mês dele.** `inputs/YYYY-MM/`, nunca meses anteriores; escreve
   apenas em `outputs/YYYY-MM/`. A planilha já traz todo o histórico e o comparativo M-1.
4. **O mês de fechamento vem do nome da pasta**, não do conteúdo. Colunas de meses futuros
   vêm zeradas e devem ser truncadas.
5. **Build não gera dashboard sobre base inconsistente.** O checklist de
   [docs/validacao.md](docs/validacao.md) é bloqueante.
6. **Sem CDN.** HTML autocontido, offline, e funcional dentro de um `<iframe>`.
7. **A fronteira extrator/template é sagrada.** Mudou a planilha, mexe só no extrator;
   mudou o layout, mexe só no template. O `data-YYYY-MM.json` é o contrato entre os dois.
8. **Documentação anda junto com o código.** Alterou comportamento, atualiza o doc na mesma
   leva e registra em [docs/MEMORY.md](docs/MEMORY.md).

## Padrão visual

Usar a skill **`g5-design-system`** para qualquer decisão visual — é a fonte de verdade de
cores, tipografia, espaçamento e regras de gráfico. O que este projeto acrescenta está em
[docs/visual.md](docs/visual.md).
