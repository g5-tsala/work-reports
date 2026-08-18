# Memória do projeto

Documento vivo. Estado atual, decisões fechadas e pendências abertas. **Ler no início de
qualquer sessão** e atualizar sempre que uma decisão for tomada ou um fato mudar.

Este arquivo substitui a memória de sessão do Claude: o conhecimento do projeto vive aqui,
versionado junto com o código, não em um armazenamento externo.

> [← Índice](../CLAUDE.md)

## 1. Estado atual

**2026-08-18** — documentação e scaffolding do ambiente concluídos.

| Item | Situação |
|---|---|
| `CLAUDE.md` + `docs/` | pronto |
| `gerar-dashboard.bat`, `pyproject.toml`, `.gitignore` | pronto |
| `gerar-dashboard.sh` (Linux/WSL) | pronto — testado até o ponto em que falta o `build.py` |
| `uv.lock` | gerado no primeiro `uv sync` (2026-08-18) — versionado |
| `build.py` | **não iniciado** |
| `template/` | **não iniciado** |
| Primeiro protótipo sobre `2026-07` | **não iniciado** |

Próximo passo: `build.py` e o JSON intermediário, onde os números se provam antes de
qualquer pixel.

## 2. Decisões fechadas

Não reabrir sem motivo novo.

### Ambiente e pipeline

- **uv, sempre.** Nada de `pip`, `venv`, `requirements.txt` ou conda. `uv.lock` versionado.
- O próprio `uv` é instalado por `pip install uv` (não winget) e invocado como
  `python -m uv`, o que dispensa mexer no `PATH`.
- Ponto de entrada é o `.bat`, dois cliques, sem terminal. **ASCII puro e CRLF** — acento
  vira lixo no console corporativo e terminação LF quebra `goto` em silêncio.
- **Existe também o `gerar-dashboard.sh`**, para desenvolvimento em Linux/WSL, com o mesmo
  fluxo do `.bat` (2026-08-18). Os dois são irmãos: mudou o fluxo em um, muda no outro.
  O `.bat` continua sendo o entregável do usuário final.
- **Nenhum dos dois scripts abre o HTML.** A função deles acaba na geração; imprimem o
  caminho absoluto e param (2026-08-18). No `.bat`, o `pause` virou um
  `set /p "DUMMY=Digite ENTER para finalizar..."`, só para a janela não fechar antes de o
  usuário ler as mensagens.
- `inputs/` e `outputs/` fora do git. Só código é versionado.
- Pipeline em três estágios: extração → validação → renderização, com
  `data-YYYY-MM.json` auditável no meio.

### Produto

- Menu lateral, não abas no topo — são 14 abas visíveis.
- KPIs da home nesta ordem: **AUM → Run Rate → Projeção Ano → ROA**.
- Fdos Alocação sempre nos totais, com toggle global "Ex-Fdos Alocação" para proporções.
- Períodos MTD, Trimestre e YTD. **Não há meta ou orçamento** nesta análise — isso é
  discutido em outro fórum comercial. O acompanhamento é de evolução, não de atingimento.
- Drill-down sob demanda: consolidado no nível zero, detalhe ao clicar na linha.
- Filtros ágeis por officer, tipo de veículo e segmento.
- Nomes reais. Marca de confidencialidade na impressão.
- Distribuição por link para download hoje; `<iframe>` num portal no futuro.

### Técnicas em aberto para revisão

- **Gráficos em módulo SVG próprio**, sem biblioteca. Decisão *provisória*, a revalidar
  depois do primeiro protótipo. Se o custo de manutenção pesar, a alternativa é embarcar
  uma biblioteca minificada inline — nunca via CDN.

## 3. Achados que custaram trabalho

Guardados aqui porque redescobri-los é caro. Detalhe em [calculos.md](calculos.md).

- **`in_out` vs `info_net_in_out`** — duas bases de schema idêntico e conteúdo diferente. A
  segunda exclui as movimentações do próprio grupo G5. Em jul/26: R$ 4,50 bi contra
  R$ 1,92 bi no IN onshore. Trocar uma pela outra produz número plausível e errado por um
  fator de 2,3. É a armadilha número um do modelo.
- **Mensalização** = competência ÷ dias úteis × 21, **só no onshore**. A planilha escreve
  `/nwdays*21` num lugar e `/nwdays*252` em outro — são a mesma coisa, 21 × 12 = 252.
- **ROA MFO** tem dois desvios frente ao ROA: conta todo o offshore como MFO (sem filtro de
  segmento) e não mensaliza o numerador. Replicar assim para os números baterem, e
  sinalizar na interface que as duas colunas não são estritamente comparáveis.
- **Câmbio arredondado.** `resumo!B4` exibe 5,08; as contas usam 5,0773 (`info!AQ3`).
- **Rótulo de data errado** em `aum_receita!C5` e `roa_historico!C5`: dizem `2019-06`, mas a
  série é `2018-06`. Corrigir na extração, avisar, não alterar a planilha.

## 4. Correções aplicadas na geradora

Registro do que mudou na fonte, para saber a partir de quando cada snapshot é confiável.

| Data | O que mudou | Efeito nos snapshots |
|---|---|---|
| 2026-08-18 | `cons_officer` linha 60 tinha fórmula errada (filtrava pela coluna Segmento no onshore e Backup no offshore). Substituída por duas métricas nas linhas 60 e 61: **Qtd. Grupos (Officer)** e **Qtd. Grupos (Backup)**. | Snapshots anteriores trazem o valor antigo numa única linha 60. O de `2026-07` foi regerado. |
| 2026-08-18 | Dois officers/backups sem cadastro no de-para de nomes (`info!AK:AL`) geravam `#N/D` na coluna Backup: `Felipe F.` (14 linhas onshore, 2 offshore) e `Mathias` (10 linhas offshore). Ambos cadastrados. | `2026-07` regerado. **Zero erros na coluna Backup.** |

## 5. Fatos de negócio úteis

- **Officers e backups são conjuntos diferentes.** Cinco pessoas aparecem só como backup,
  sem carteira própria: `Yan` (47 grupos), `Felipe F.` (13), `Mathias`, `Dudu` (3),
  `Luiz` (1). E seis officers não fazem backup de ninguém: Alexandre, Daniel, Waldemar,
  Tainá, Diego, Michael G. O dashboard não pode assumir subconjunto.
- **A rede de backup não aparece em nenhuma métrica atual.** João tem 3 grupos como titular
  e **66 como backup**; Fabietti tem 39 e 69; Gau, 19 e 44. Rodrigo M. é o inverso: 60
  titular, 10 backup. É um corte que o relatório hoje não mostra.
- **Não somar Qtd. Grupos entre officers.** A soma dá 376 contra 361 grupos distintos —
  um grupo pode ter portfólios sob titulares diferentes. O total correto é `resumo!AA17`.
- **Fdos Alocação** são ~33% do AUM (R$ 14,2 bi em jul/26) com ROA de 0,12%, uma ordem de
  grandeza abaixo dos officers reais. É o que justifica o toggle.

## 6. Pendências e backlog

- [ ] `build.py` e `template/`.
- [ ] Revalidar a decisão de gráficos SVG próprios após o primeiro protótipo.
- [ ] Página **Performance da Base** a partir da aba oculta `cotas` — cotiza o AUM como se
      fosse um portfólio e compara com CDI desde 2018-01. Prioridade baixa, mas é a análise
      mais interessante que nenhuma aba visível mostra hoje.
- [ ] Avaliar expor a métrica de backup na página de officers.
