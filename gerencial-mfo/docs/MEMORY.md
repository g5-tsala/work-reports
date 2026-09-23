# Memória do projeto

Estado, decisões fechadas, armadilhas e backlog. Substitui a memória de sessão: o que vale para
o projeto fica aqui, versionado. **Só entra o que ainda vale** — defeito corrigido e regerado
sai; histórico é do `git log`. Atualize ao tomar decisão ou quando um fato mudar.

## Estado — 2026-09-23

- Pipeline completo, rodando ponta a ponta em `2026-07` e `2026-08`; os dois passam 10/10 no
  checklist (ago/26: 1.057 portfólios, 362 grupos distintos).
- 11 abas: Visão Geral · Resumo · Histórico AUM × Receita · Officers · Grupos Econômicos ·
  Regiões · Portfólios Onshore · Portfólios Offshore · Net In/Out · Captação › Grupos · G5 JUS.
- Não iniciados: toggle Ex-Fdos Alocação, filtros combináveis, seletor de período (ver Backlog).

## Decisões fechadas

Não reabrir sem motivo novo.

**Técnicas**
- `uv` sempre; `.bat` é o entregável do usuário final, `.sh` é o irmão de dev — detalhes em
  [ambiente.md](ambiente.md). Nenhum dos dois abre o HTML.
- Validação roda sobre o JSON, não sobre o xlsx: `--etapa validar` confere base já gerada e o
  render nunca recebe base reprovada.
- Rótulo e hierarquia vêm da planilha: linhas viram `{rotulo, chave, nivel, pai}`, com `nivel`
  lido do recuo da célula. Quebra nova na geradora aparece no JSON sem mexer no extrator.
- Cada extrator é dono das coordenadas que lê; não existe mapa central de layout.
- Gráficos são SVG gerado no build em Python, sem biblioteca: imprime, abre sem JS, sem rede.
  Tooltip não justifica biblioteca (o SVG leva `data-dica`, o `app.js` só exibe). Biblioteca só
  para interatividade real, e então minificada inline.
- Regras de eixo (barra no zero, linha com eixo ajustado, segundo eixo só com unidades
  distintas) em [visual.md](visual.md) §2.1.
- A faixa de parâmetros do fechamento (mês · dias úteis · câmbio · CDI) é fixa no topo: é o
  regime que governa metade dos números.

**Produto**
- Menu lateral (a lista não cabe no topo). KPIs da home nesta ordem: **AUM → Run Rate →
  Projeção Ano → ROA**.
- Fdos Alocação sempre nos totais; o toggle "Ex-Fdos Alocação" só recalcularia proporções.
- Períodos-alvo: MTD, trimestre, YTD. **Sem meta ou orçamento** — acompanhamento é de evolução,
  não de atingimento; não inventar linha de meta.
- Drill-down sob demanda: consolidado no nível zero, detalhe ao clicar.
- Net In/Out é a aba única da captação de cliente (composição em [dashboard.md](dashboard.md)
  §2). Alocação entra só no incremento de receita: o IN/OUT dos fundos de alocação não é
  captação de cliente e sai "—".
- Fora do HTML, mas ainda extraídos no JSON: Captação › Portfólios e Administradores
  (on/offshore) — saíram em 2026-09-23. O `git log` tem as páginas.
- Fora do HTML **e** do JSON: aba `roa_historico` (corte de escopo; o `git log` tem o extrator).
- Removidos a pedido do negócio em 2026-09-22: seção "Rede de backup" de Officers (a contagem
  por pessoa segue no drill-down) e a ressalva do ROA MFO na interface (a ressalva continua
  valendo — ver Armadilhas).
- **Abas de Portfólios não mostram ROA** (2026-09-23): a receita das bases `ar_*` é por
  competência, e × 12 sem mensalizar distorce a taxa. ROA fica em Resumo, Officers e Grupos.
- Região `-` da aba `regiao` aparece como **G5** em Regiões: é onde caem os fundos de alocação.
- Nomes reais; marca de confidencialidade na impressão. Distribuição por link hoje; `<iframe>`
  num portal no futuro.

## Armadilhas

Redescobrir custa caro. Fórmulas em [calculos.md](calculos.md).

1. **`in_out` ≠ `info_net_in_out`.** Mesmo schema; a segunda exclui o grupo G5. IN onshore
   jul/26: R$ 4,50 bi × R$ 1,92 bi — trocar dá número plausível e errado por 2,3×. Toda a
   captação do dashboard (`net_in_out`, `Dashboard` §2 e §3) é **cliente**
   ([modelo-de-dados.md](modelo-de-dados.md) §6).
2. **Mensalização só no onshore**: competência ÷ dias úteis × 21 (a planilha também escreve
   `× 252` = 21 × 12). Aplicar ao offshore infla por `21/nwdays`.
3. **ROA MFO** conta todo o offshore como MFO e não mensaliza o numerador. Replicar assim; não
   é comparável ao ROA lado a lado.
4. **Câmbio arredondado:** `resumo!B4` exibe 5,08; as contas usam 5,0773 (`info!AQ3`, também em
   `resumo!U26`). Nunca extrair do texto.
5. **Linha de `io_grupos` YTD não é grupo:** é grupo + officer + lead externo + lead G5 +
   segmento. Mês a mês casa pela combinação inteira; gráficos e KPIs contam por grupo.
6. **Não somar Qtd. Grupos entre officers** (376 × 361 distintos em jul/26): um grupo pode ter
   portfólios sob titulares diferentes. Total correto: `resumo!AA17`.
7. **Officers e backups são conjuntos diferentes.** Há quem seja só backup (`Yan`, `Felipe F.`,
   `Mathias`, `Dudu`, `Luiz`) e officers que não fazem backup de ninguém. Backup `#N/D` ou vazio
   = sem backup atribuído → `null`, nunca uma pessoa.
8. **Cor da fonte na `CEO-Dashboard` é dado:** officer pintado = já saiu e ainda tem cliente
   vinculado. Regra: qualquer cor explícita que não seja preto (o tom muda entre meses). Vira
   `officers.tabela_ceo[].marcado`.
9. **Abaixo da tabela de officers da `CEO-Dashboard`, coordenada absoluta é frágil:** a tabela
   cresce e encolhe. A nota de rodapé é buscada de +2 a +6 linhas abaixo do rótulo
   `Total Ex- Fdos Alocação`.
10. **Variação M-1 de `Total Ex- Fdos Alocação`** (`CEO-Dashboard` D39/G39) compara contra o
    **total** do mês anterior (`Z39`): sem significado, exibir "—".
11. **Bloco de `cons_officer` invade o nome do próximo** (`$C$31:$O$63` termina no rótulo do
    officer seguinte): descartar a linha seguida de `Data`.
12. **`resumo!X`/`AH` (Qtd 0)** já estão descontados do `Qtd` exibido — extrair como
    `qtd_zerados`, nunca somar de volta.
13. **`GV Atacama` e `Daycoval` repetem AUM e receita** em `ar_adm_on` (marcador `GVA/Daycoval`
    em `agrupamento`); só custos são próprios. A soma da coluna de AUM não é o AUM da casa.
14. **Meses futuros vêm zerados**, não vazios. `#DIV/0!`, `#N/D`, `TBD` → `null`; traço some em
    número mas sobrevive em texto (o officer dos Fdos Alocação é `-`).
15. **Onshore e offshore de `aum_receita` têm cabeçalhos de data próprios** (divergem em 2023):
    alinhar por mês, nunca por índice.
16. **Ranking de `ar_grupos` é por valor:** empate devolve o mesmo nome duas vezes — casar por
    posição.

## Fatos de negócio

- Fdos Alocação: ~33% do AUM (R$ 14,2 bi em jul/26) com ROA ~0,12%, uma ordem de grandeza abaixo
  dos officers — é o que justifica o toggle.
- A rede de backup não aparece em métrica nenhuma e é grande: em jul/26 João tinha 3 grupos como
  titular e 66 como backup; Fabietti 39/69; Gau 19/44; Rodrigo M. o inverso, 60/10.

## Backlog

- [ ] **Toggle global Ex-Fdos Alocação** — recalcular proporções, ROA médio e rankings no
      cliente. Hoje cada página mostra a linha `Total Ex- Fdos Alocação` da planilha.
- [ ] **Filtros combináveis** (officer · tipo · segmento · on/offshore). Hoje: busca textual e
      ordenação por coluna.
- [ ] **Seletor de período** MTD · trimestre · YTD.
- [ ] **Drill-down de 3º nível na captação** — movimentações individuais da aba oculta
      `info_grupos`, ainda não extraída.
- [ ] **Página Performance da Base** a partir da aba oculta `cotas` (AUM cotizado × CDI desde
      2018-01, [calculos.md](calculos.md) §3.10). Prioridade baixa.
