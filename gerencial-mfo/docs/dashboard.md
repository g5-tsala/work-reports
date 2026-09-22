# Arquitetura do dashboard

> [← Índice](../CLAUDE.md) · Relacionados: [visual.md](visual.md), [metricas.md](metricas.md)

## 1. Navegação — sidebar

Menu lateral fixo (~240px, colapsável), conteúdo renderizado ao centro. Item ativo marcado
com barra wine à esquerda. Agrupamento:

```
VISÃO EXECUTIVA     Visão Geral · Resumo · Histórico AUM × Receita
CARTEIRA            Officers · Grupos Econômicos · Regiões · Portfólios On · Portfólios Off
CAPTAÇÃO            Net In/Out · Grupos · Portfólios
ESTRUTURA           Administradores Onshore · Administradores Offshore
OUTROS              G5 JUS
```

**Uma aba = um script.** Cada item acima é um módulo em `core/render/paginas/`, registrado
pelo decorador `@pagina(...)` com grupo e ordem. O menu e o roteamento saem do registro —
para mexer no conteúdo de uma aba, abre-se o arquivo dela e mais nada.

**Net In/Out reúne a captação de cliente inteira**: KPIs de `net_in_out`, a tabela
*Captação Cliente* (`Dashboard §2`, com o incremento de receita), o fluxo mensal e o NET
executado por segmento (`Dashboard §3`). Os três blocos vêm da mesma base sem o G5 e fecham
entre si. Já houve uma aba "NET Executado" separada, sob a premissa errada de que o §3 usava
a base com o G5 — ver [modelo-de-dados.md](modelo-de-dados.md) §6.

## 1.1 Page furniture — o regime do fechamento

Abaixo do título, uma faixa fixa com **mês-base · dias úteis · câmbio · CDI do mês**, cada
um com o papel que cumpre: "base da mensalização", "converte todo o offshore". Não é
enfeite de cabeçalho — são os parâmetros que governam metade dos números da tela, e viviam
escondidos numa linha de subtítulo. Quem abre o relatório e estranha uma receita já tem ali
o divisor que a produziu.

## 2. Página inicial

Os quatro indicadores principais, com ênfase e **nesta ordem**: **AUM → Run Rate → Projeção
Ano → ROA**. Cada um com valor, variação M-1 (absoluta e %) e cor de sinal. Abaixo, split
Onshore/Offshore; AUM e receita consolidados lado a lado e a linha do Run Rate, todos de
dezembro do ano anterior ao mês-base. A série longa fica no Histórico e o ranking por
officer na aba Officers — a página leva um link para cada (`ui.link_aba()`, atributo
`data-ir-para`, que o `app.js` trata só como navegação; `data-vai-para` é do menu).

A base da comparação fecha a **mesma linha** do delta, em cinza (`kpi(referencia=…)`):
`+1,70% · +0,73 bi · (vs. jul/26)`. Um número com sinal sem a base contra a qual foi medido
não quer dizer nada, e jogar essa base uma linha abaixo separava a pergunta da resposta.

**Officer marcado.** O ranking da aba Officers pinta de wine, com asterisco, o officer que a `CEO-Dashboard`
traz colorido, e repete a nota da planilha na mesma cor. É estado do fechamento — carteira
de quem já saiu e ainda não migrou —, e ele chega pelo `marcado` do JSON
([contrato-json.md](contrato-json.md) §3.3), não por lista de nomes no código.

## 3. Períodos

Toda visão temporal oferece **MTD, Trimestre e YTD**. Não há meta ou orçamento nesta
análise — isso é discutido em outro fórum comercial. O acompanhamento é de **evolução**,
não de atingimento. Não inventar linha de meta.

## 4. Filtros

**Implementado:** busca textual por tabela, que casa contra a linha inteira e mostra quantos
registros restaram; ordenação por qualquer coluna, com a ordenação numérica lendo o valor
cru de `data-valor` em vez do texto formatado.

**Ainda não implementado:** a barra de filtros ágeis combináveis
(**Officer · Tipo de veículo · Segmento · Onshore/Offshore**) e o **toggle global
Ex-Fdos Alocação**. O toggle exige recalcular proporções, ROA médio e rankings no cliente —
enquanto não existir, cada página que compara com o total mostra a linha
`Total Ex- Fdos Alocação` que a própria planilha traz.

## 5. Drill-down

Princípio: **consolidado no nível zero, detalhe sob demanda**. Nunca despejar 939 linhas na
abertura. Linha clicável expande a composição inline.

Exemplo canônico (captação):

```
YTD por grupo econômico          (io_grupos, colunas J–O)   ← visão principal
  └─ mês a mês do grupo          (io_grupos, colunas B–H)
       └─ movimentações do mês   (info_grupos, colunas N–V)
          Data · Portfolio · Valor · Finalidade · Officer · Segmento
```

Mesmo padrão nas demais páginas: administrador → portfólios do administrador → custos;
officer → grupos → portfólios; categoria/faixa PL → veículos.

**Implementado hoje:** captação por grupo (YTD → mês a mês), officer → detalhe do mês
(AUM por segmento, receita, ROA, IN/OUT, portfólios por tipo, grupos como titular e como
backup) e, no Net In/Out, tipo de veículo → abertura (início no ano, clientes antigos,
finalidade, ROA). O terceiro nível da captação (movimentações individuais de `info_grupos`) e os
drill-downs de administrador e de categoria ainda não existem.

A mecânica é a mesma em toda parte: a linha-pai leva `data-abre`, as filhas levam
`data-detalhe` com o mesmo alvo, e o `app.js` alterna o `hidden`. Uma aba nova ganha
drill-down usando `linha_expansivel()` e `linha_detalhe()` do `ui.py`, sem tocar no script.
`expandir_todos(id_da_tabela)` põe acima da tabela o botão que abre ou fecha tudo de uma
vez; o rótulo acompanha o estado real ("Recolher tudo" quando todas estão abertas, mesmo
que o leitor tenha aberto uma a uma).

**Versões do mesmo conteúdo** (consolidado · onshore · offshore nos KPIs e no fluxo
mensal do Net In/Out) usam
`alternador()` do `ui.py`: todos os painéis são renderizados no build, os botões só trocam
o `hidden`. Sem JS fica a primeira opção, que deve ser a leitura principal. Na impressão os
botões somem e sai o painel ativo.

## 5.1 Piso de qualidade

Não é opcional e não aparece em screenshot:

- **Foco de teclado visível** em wine, com `outline-offset`. O contorno default do navegador
  é preto e some sobre o navy do cabeçalho de tabela.
- **`prefers-reduced-motion` respeitado.**
- **Menu em tela estreita vira trilha horizontal rolável.** Empilhados, os itens do menu
  empurravam o primeiro número para baixo da dobra — num relatório executivo aberto no
  celular, isso é o defeito mais caro da página.
- Tabela financeira **não reflui em cards** abaixo de 768px: rola na horizontal, porque
  linha reflowada deixa de ser comparável com a de cima.

## 6. Impressão e distribuição

Distribuição inicial por link para download e abertura local. Em `@media print`: marca
"CONFIDENCIAL — USO INTERNO" no cabeçalho, mês-base e data de geração no rodapé, sidebar e
ferramentas de tabela ocultas.

**Imprime apenas a aba aberta**, não o relatório inteiro: o botão é lido como "imprimir o
que estou vendo". Quem quiser o caderno completo passa aba a aba. Na prática, `.g5-pagina`
escondida continua escondida no papel — o `@media print` não reabre nada.

**A impressão respeita o layout da tela.** Duas regras sustentam isso e não podem ser
afrouxadas:

1. As media queries responsivas são `@media screen and (max-width: …)`. Sem o `screen`, a
   largura da folha (A4 retrato dá ~700px) cai no breakpoint de 768px e a grade de KPIs e
   de colunas empilha — o relatório sai com cara de celular.
2. `print-color-adjust: exact` no `html, body`, senão o navegador descarta o navy do
   cabeçalho de tabela, a faixa de total e o verde/vermelho do delta.

O que muda no papel é escala, não estrutura: fontes em `pt`, KPI menor, `@page` A4
paisagem. Tabela longa quebra entre páginas repetindo o `thead` (`display:
table-header-group`); card, figura e KPI não quebram no meio.

---

[← Índice](../CLAUDE.md)
