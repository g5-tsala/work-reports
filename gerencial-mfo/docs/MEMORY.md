# Memória do projeto

Documento vivo. Estado atual, decisões fechadas e pendências abertas. **Ler no início de
qualquer sessão** e atualizar sempre que uma decisão for tomada ou um fato mudar.

Este arquivo substitui a memória de sessão do Claude: o conhecimento do projeto vive aqui,
versionado junto com o código, não em um armazenamento externo.

**Só entra o que ainda vale.** Defeito corrigido na fonte, cujo snapshot foi regerado, sai
daqui — carregar história morta em todo início de sessão custa atenção e não muda decisão
nenhuma. O histórico de quem mudou o quê é trabalho do `git log`.

> [← Índice](../CLAUDE.md)

## 1. Estado atual

**2026-08-18** — etapa 1 do pipeline (planilha → JSON) pronta e validada sobre `2026-07`.

| Item | Situação |
|---|---|
| `AGENTS.md` + `docs/` | pronto |
| `gerar-dashboard.bat`, `pyproject.toml`, `.gitignore` | pronto |
| `gerar-dashboard.sh` (Linux/WSL) | pronto |
| `uv.lock` | versionado |
| `dashboard.py` + `core/` | pronto para extração e validação |
| **Etapa 1 — extração** | **pronta.** `outputs/2026-07/data-2026-07.json`, ~1,8 MB |
| **Etapa 2 — renderização** | **não iniciada.** `core/render.py` é um stub que falha explícito |
| `template/` | **não iniciado** |

O build de `2026-07` passa nos **10 itens do checklist** de
[validacao.md](validacao.md) §1, incluindo os dois caros: 1.051 portfólios batem entre
`resumo`, `CEO-Dashboard` e a contagem nas bases; e o recálculo de Qtd. Grupos reproduz os
20 officers e os 361 grupos distintos.

Próximo passo: `core/render.py` e `template/`.

## 2. Decisões fechadas

Não reabrir sem motivo novo.

### Ambiente e pipeline

- **uv, sempre.** Nada de `pip`, `venv`, `requirements.txt` ou conda. `uv.lock` versionado.
- O próprio `uv` é instalado por `pip install uv` (não winget) e invocado como
  `python -m uv`, o que dispensa mexer no `PATH`.
- Ponto de entrada é o `.bat`, dois cliques, sem terminal. **ASCII puro e CRLF** — acento
  vira lixo no console corporativo e terminação LF quebra `goto` em silêncio.
- **Existe também o `gerar-dashboard.sh`**, para desenvolvimento em Linux/WSL, com o mesmo
  fluxo do `.bat`. Os dois são irmãos: mudou o fluxo em um, muda no outro. O `.bat`
  continua sendo o entregável do usuário final.
- **Nenhum dos dois scripts abre o HTML.** A função deles acaba na geração; imprimem o
  caminho absoluto e param. O `.bat` fecha com `set /p "DUMMY=Digite ENTER para
  finalizar..."`, só para a janela não sumir antes de o usuário ler as mensagens.
- `inputs/` e `outputs/` fora do git. Só código é versionado.
- Pipeline em três estágios: extração → validação → renderização, com
  `data-YYYY-MM.json` auditável no meio.
- **`dashboard.py` na raiz orquestra; `core/` faz o trabalho.** Um módulo de extração por
  domínio, cada um dono das coordenadas que lê — sem mapa central de layout.
  O contrato do JSON está em [contrato-json.md](contrato-json.md).
- **A validação roda sobre o JSON, não sobre a planilha.** Assim `--etapa validar` confere
  uma base já gerada e a renderização nunca recebe base reprovada.
- **Rótulo e hierarquia vêm da planilha, não do código.** As linhas viram
  `{rotulo, chave, nivel, pai}`, com `nivel` lido do recuo da célula. Uma quebra nova na
  geradora aparece no JSON sem alterar o extrator.

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
- **O intervalo de cada bloco de `cons_officer` invade o nome do bloco seguinte.**
  `$C$31:$O$63` termina na linha 63, que é o rótulo `Alexandre` do próximo officer. Sem
  descartar essa linha, o JSON ganha uma "métrica" com o nome de uma pessoa.
- **`resumo!X` e `resumo!AH` (Qtd 0)** são a contagem de veículos zerados já descontada do
  `Qtd` exibido — extrair como `qtd_zerados`, nunca somar de volta.

## 4. Fatos de negócio úteis

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

## 5. Pendências e backlog

- [ ] `core/render.py` e `template/` — etapa 2.
- [ ] Revalidar a decisão de gráficos SVG próprios após o primeiro protótipo.
- [ ] Página **Performance da Base** a partir da aba oculta `cotas` — cotiza o AUM como se
      fosse um portfólio e compara com CDI desde 2018-01. Prioridade baixa, mas é a análise
      mais interessante que nenhuma aba visível mostra hoje.
- [ ] Avaliar expor a métrica de backup na página de officers.
