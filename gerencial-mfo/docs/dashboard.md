# Arquitetura do dashboard

Navegação, abas, interação e impressão. Números, tabelas e gráficos: [visual.md](visual.md).

## 1. Navegação

Menu lateral fixo; item ativo com barra wine à esquerda. Grupos e ordem saem de
`@pagina(grupo=…, ordem=…)` e de `GRUPOS` em `core/render/pagina.py`:

```
VISÃO EXECUTIVA   Visão Geral · Resumo · Histórico AUM × Receita
CARTEIRA          Officers · Grupos Econômicos · Regiões · Portfólios Onshore · Portfólios Offshore
CAPTAÇÃO          Net In/Out · Captação › Grupos
OUTROS            G5 JUS
```

Link entre abas no meio do conteúdo: `ui.link_aba()` → atributo `data-ir-para` (só navega).
`data-vai-para` é exclusivo do menu, que também marca o item ativo e troca o título.

**Faixa de parâmetros** abaixo do título, fixa: mês-base · dias úteis · câmbio · CDI do mês,
cada um com o papel que cumpre ("base da mensalização", "converte todo o offshore").

## 2. Abas

| Aba (`paginas/`) | Conteúdo |
|---|---|
| Visão Geral (`visao_geral`) | 4 KPIs · split on/offshore · AUM e receita empilhados desde dez do ano anterior · linha do Run Rate · links para Histórico e Officers |
| Resumo (`resumo`) | 4 KPIs · ROA por categoria × faixa de PL e por grupo × faixa de PL, cada um com tabela e par de barras AUM × receita |
| Histórico (`historico`) | AUM e receita empilhados desde 2018 · ROA on/offshore · tabelas do ano corrente (on em R$, off em US$) |
| Officers (`officers`) | ranking da `CEO-Dashboard` com drill-down para o bloco de `cons_officer` · officer marcado · par AUM × receita |
| Grupos Econômicos (`grupos`) | KPIs de concentração · Top 10 por AUM e por receita · par da união dos dois · base completa com Δ M-1 |
| Regiões (`regioes`) | par de barras horizontais empilhadas on + off, com tooltip · tabelas consolidado / on / off |
| Portfólios On/Offshore (`portfolios_*`) | KPIs · composição por tipo (e segmento, no on) · tabela de portfólios filtrável (off em US$) |
| Net In/Out (`captacao_net`) | KPIs com alternador consolidado · onshore · offshore (off mostra R$ ao lado do US$) · tabela *Captação Cliente* (`Dashboard` §2) + incremento de receita por segmento · fluxo mensal com alternador · detalhe por segmento (`Dashboard` §3) |
| Captação › Grupos (`captacao_grupos`) | KPIs do ano · maiores NETs positivos e negativos · YTD por linha de `io_grupos` → mês a mês |
| G5 JUS (`g5jus`) | 4 KPIs · combo AUM × receita com eixo próprio e tooltip · tabela de veículos |

**KPI com delta** (AUM e Run Rate na Visão Geral): variação % e absoluta, cor de sinal, e a
base da comparação na mesma linha, em cinza — `+1,70% · +0,73 bi · (vs. jul/26)`
(`kpi(referencia=…)`). Projeção Ano mostra o realizado no ano; ROA mostra a fórmula.

**Officer marcado** (`marcado` do JSON, nunca lista de nomes no código): linha em wine com
asterisco e a nota da planilha repetida abaixo do ranking, na mesma cor. Sem marcado no mês, a
nota some.

## 3. Drill-down

Consolidado no nível zero, detalhe sob demanda — nunca centenas de linhas abertas na abertura.

Existentes: Officers (officer → métricas do mês, incluindo grupos como titular e como backup) ·
Captação › Grupos (linha YTD → mês a mês) · Net In/Out (*Captação Cliente*: ingresso/retirada →
segmentos; detalhe por segmento: mês → início no ano, clientes antigos, uso pessoal, saída para
concorrência). Não existe ainda: 3º nível da captação (`info_grupos`), categoria/faixa →
veículos.

Mecânica: linha-pai com `ui.linha_expansivel(alvo)` (`data-abre`), filhas com
`ui.linha_detalhe(alvo)` (`data-detalhe`, `hidden`); o `app.js` alterna. `ui.expandir_todos(id)`
põe acima da tabela o botão "Expandir tudo", cujo rótulo segue o estado real. Ordenação move as
filhas junto com o pai e mantém `total` no pé.

**Versões do mesmo conteúdo** (`ui.alternador()`): todos os painéis renderizados no build, os
botões só trocam `hidden`. Sem JS fica o primeiro, que deve ser a leitura principal. Na
impressão os botões somem e sai o painel ativo.

## 4. Filtros e períodos

Existe: busca textual por tabela (`tabela(filtravel=True)`, casa contra a linha inteira e mostra
a contagem) e ordenação por coluna, numérica pelo valor cru de `data-valor`.

Não existe (backlog em [MEMORY.md](MEMORY.md)): filtros combináveis (officer · tipo · segmento ·
on/offshore), toggle global Ex-Fdos Alocação (enquanto isso, a linha `Total Ex- Fdos Alocação`
da planilha é a referência) e seletor MTD · trimestre · YTD. Sem meta ou orçamento.

## 5. Piso de qualidade

- Foco de teclado visível em wine com `outline-offset` (o default preto some sobre o navy).
- `prefers-reduced-motion` respeitado.
- Tela estreita (≤ 1024px): menu vira trilha horizontal rolável numa linha só — empilhado,
  empurrava o primeiro número para baixo da dobra.
- Tabela financeira não reflui em cards abaixo de 768px: rola na horizontal, para a linha
  continuar comparável com a de cima.

## 6. Impressão

- Imprime **só a aba aberta**: `.g5-pagina[hidden]` continua escondida no `@media print`.
- Marca "CONFIDENCIAL — USO INTERNO" no topo; sidebar, ferramentas de tabela, alternadores,
  links entre abas e tooltip ocultos.
- **Mesmo layout da tela**, em outra escala (fontes em `pt`, KPI menor, A4 paisagem). Duas regras
  sustentam isso e não podem ser afrouxadas:
  1. Media queries responsivas são `@media screen and (max-width: …)` — sem `screen`, a largura
     da folha (~700px em A4 retrato) cai no breakpoint e a grade empilha.
  2. `print-color-adjust: exact` em `html, body`, senão o navegador descarta o navy do
     cabeçalho, a faixa de total e as cores de sinal.
- Tabela longa quebra entre páginas repetindo o `thead`; KPI, card e figura não quebram no meio.
