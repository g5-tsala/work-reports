# Gerencial MFO — Dashboard

Planilha gerencial mensal da área de MFO (G5 Partners) → dashboard HTML autocontido, padrão
visual G5, leitura de BI.

- **Público:** executivos e board. Não é material de cliente.
- **Confidencialidade:** dados nominais reais (clientes, grupos, officers). O HTML herda a
  classificação do xlsx — uso interno restrito.
- **Cadência:** mensal, uma pasta `inputs/YYYY-MM/` por mês.
- **Idioma:** PT-BR em tudo, inclusive eixos e rótulos (regras de idioma no `AGENTS.md` da raiz).

## Rodar

```bash
./gerar-dashboard.sh [2026-08]                          # Linux/WSL (Windows: 2 cliques no .bat)
uv run python dashboard.py 2026-08                      # pipeline completo
uv run python dashboard.py 2026-08 --etapa extrair      # xlsx -> JSON + validação
uv run python dashboard.py 2026-08 --etapa validar      # revalida o JSON existente
uv run python dashboard.py 2026-08 --etapa renderizar   # JSON -> HTML
```

Saída: `2` erro de uso (mês inválido, arquivo ausente) · `3` base reprovada no checklist ·
`4` falha na renderização.

## Pipeline e código

`inputs/YYYY-MM/Gerencial MFO YYYY-MM.xlsx` → **extração** → `outputs/YYYY-MM/gerencial-mfo-YYYY-MM.json`
→ **validação** (bloqueante, roda sobre o JSON) → **renderização** →
`outputs/YYYY-MM/gerencial-mfo-YYYY-MM.html`. `dashboard.py` só orquestra; o trabalho vive em `core/`.

| Caminho | Papel |
|---|---|
| `core/config.py` | caminhos, versões (`VERSAO_CONTRATO`), tolerâncias. Sem layout de planilha. |
| `core/planilha.py` | abre o xlsx (`openpyxl`, `data_only=True`), nomes definidos, limpeza (`numero()` ≠ `texto()`). |
| `core/extracao/` | um módulo por domínio: `parametros` (`info`), `consolidado` (`resumo`, `CEO-Dashboard`), `historico` (`aum_receita`), `officers` (`cons_officer`), `carteira` (`ar_*`, `regiao`), `captacao` (`net_in_out`, `io_*`, `Dashboard`), `estrutura` (`ar_adm_*`, `G5JUS`), `checks`, `comum` (blocos rotulados). Cada módulo declara no topo as coordenadas que lê. |
| `core/validacao.py` | checklist de [docs/validacao.md](docs/validacao.md) §1, um item por função. |
| `core/render/paginas/` | **uma aba do dashboard por arquivo**, registrada por `@pagina(identificador, titulo, grupo, ordem)`; `comum.py` guarda peças de abas irmãs e não se registra. |
| `core/render/` | `ui.py` componentes · `graficos.py` SVG · `formato.py` PT-BR · `contexto.py` leitura do JSON · `pagina.py` registro/menu · `layout.py` costura o HTML. |
| `template/` | `base.html`, `styles.css`, `app.js`, `logo-g5.txt` (data URI) — tudo inlined no HTML. |
| `inputs/`, `outputs/` | **fora do git** (nomes reais). `inputs/Gerencial MFO.xlsm` é a geradora, origem das fórmulas. |

Aba nova: criar `paginas/<nome>.py`, decorar o render com `@pagina(...)`, importar em
`paginas/__init__.py`. Menu, roteamento e impressão vêm do registro.

## Regras invioláveis

1. **Não deduzir contas.** Toda regra de cálculo está em [docs/calculos.md](docs/calculos.md),
   com a célula de origem. Faltou, ler a geradora e documentar — nunca inferir.
2. **Extrair, não recalcular.** Número que a planilha entrega pronto é lido, não refeito.
   Conta feita no render (ROA de uma linha, consolidado do Net In/Out, série do Run Rate) segue a
   fórmula documentada.
3. **Um build lê só o próprio mês** (`inputs/YYYY-MM/`) e escreve só em `outputs/YYYY-MM/`. A
   planilha já traz histórico e M-1. Não reconciliar contra HTMLs antigos.
4. **O mês-base vem do nome da pasta**, não do conteúdo. Colunas de meses futuros vêm zeradas:
   truncar, nunca plotar.
5. **Base inconsistente não vira dashboard.** O checklist é bloqueante.
6. **Sem CDN nem webfont.** HTML offline, funcional em `<iframe>`: nada de `window.top`,
   `localStorage` ou navegação que assuma documento de topo.
7. **O JSON é a fronteira.** Mudou a planilha → só `core/extracao/`; mudou o layout → só
   `core/render/` e `template/`; mudou uma aba → só o arquivo dela. Quebrou o formato → sobe
   `VERSAO_CONTRATO` e atualiza [docs/contrato-json.md](docs/contrato-json.md).
8. **Texto da planilha é escapado por padrão.** Células e componentes de `ui.py` escapam
   sozinhos. `nota()` e `secao(descricao=)` recebem HTML nosso: passar `esc()` em cada pedaço
   vindo do dado (a base tem `&` e apóstrofo em nomes).
9. **Comentário de `styles.css`/`app.js` é genérico:** explica o mecanismo e o porquê, sem citar
   a tabela ou aba que motivou a regra — o caso concreto vai em [docs/visual.md](docs/visual.md).
10. **Doc anda com o código.** Mudou comportamento → atualiza o doc do tema e o
    [docs/MEMORY.md](docs/MEMORY.md) na mesma leva.

## Docs

| Doc | Abrir quando |
|---|---|
| [docs/MEMORY.md](docs/MEMORY.md) | sempre — estado, decisões fechadas, armadilhas, backlog |
| [docs/calculos.md](docs/calculos.md) | glossário de métricas; implementar ou depurar um número |
| [docs/modelo-de-dados.md](docs/modelo-de-dados.md) | abas, dimensões, nomes definidos, grade temporal da planilha |
| [docs/contrato-json.md](docs/contrato-json.md) | ler ou escrever o `gerencial-mfo-YYYY-MM.json` |
| [docs/validacao.md](docs/validacao.md) | número não bate; antes de dar um build por bom |
| [docs/dashboard.md](docs/dashboard.md) | navegação, abas, drill-down, filtros, impressão |
| [docs/visual.md](docs/visual.md) | números, tabelas, gráficos, tooltip |
| [docs/ambiente.md](docs/ambiente.md) | `uv`, `.bat`, `.sh` |

Decisão visual: skill **`g5-design-system`** é a fonte de verdade (cores, tipografia, gráficos);
`docs/visual.md` só acrescenta o que é deste projeto.
