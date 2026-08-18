# Arquitetura do dashboard

> [← Índice](../CLAUDE.md) · Relacionados: [visual.md](visual.md), [metricas.md](metricas.md)

## 1. Navegação — sidebar

Menu lateral fixo (~240px, colapsável), conteúdo renderizado ao centro. Item ativo marcado
com barra wine à esquerda. Agrupamento:

```
VISÃO EXECUTIVA     Visão Geral · Resumo
PERFORMANCE         Histórico AUM × Receita · ROA Histórico
CARTEIRA            Officers · Grupos Econômicos · Regiões · Portfólios On · Portfólios Off
CAPTAÇÃO            Net In/Out · Grupos · Portfólios · NET Executado
ESTRUTURA           Administradores Onshore · Administradores Offshore
OUTROS              G5 JUS
```

**Uma aba = um script.** Cada item acima é um módulo em `core/render/paginas/`, registrado
pelo decorador `@pagina(...)` com grupo e ordem. O menu e o roteamento saem do registro —
para mexer no conteúdo de uma aba, abre-se o arquivo dela e mais nada.

`NET Executado` não estava no desenho original: entrou porque o bloco 3 do `Dashboard` usa
a base **com** o grupo G5 e não podia dividir página com a captação de cliente, que é a base
**sem** o G5. Misturar as duas numa aba só é a maneira mais fácil de somar o que não se soma.

## 1.1 Page furniture — o regime do fechamento

Abaixo do título, uma faixa fixa com **mês-base · dias úteis · câmbio · CDI do mês**, cada
um com o papel que cumpre: "base da mensalização", "converte todo o offshore". Não é
enfeite de cabeçalho — são os parâmetros que governam metade dos números da tela, e viviam
escondidos numa linha de subtítulo. Quem abre o relatório e estranha uma receita já tem ali
o divisor que a produziu.

## 2. Página inicial

Os quatro indicadores principais, com ênfase e **nesta ordem**: **AUM → Run Rate → Projeção
Ano → ROA**. Cada um com valor, variação M-1 (absoluta e %) e cor de sinal. Abaixo, split
Onshore/Offshore e o ranking de officers.

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

**Implementado hoje:** captação por grupo (YTD → mês a mês) e officer → detalhe do mês
(AUM por segmento, receita, ROA, IN/OUT, portfólios por tipo, grupos como titular e como
backup). O terceiro nível da captação (movimentações individuais de `info_grupos`) e os
drill-downs de administrador e de categoria ainda não existem.

A mecânica é a mesma em toda parte: a linha-pai leva `data-abre`, as filhas levam
`data-detalhe` com o mesmo alvo, e o `app.js` alterna o `hidden`. Uma aba nova ganha
drill-down usando `linha_expansivel()` e `linha_detalhe()` do `ui.py`, sem tocar no script.

## 5.1 Piso de qualidade

Não é opcional e não aparece em screenshot:

- **Foco de teclado visível** em wine, com `outline-offset`. O contorno default do navegador
  é preto e some sobre o navy do cabeçalho de tabela.
- **`prefers-reduced-motion` respeitado.**
- **Menu em tela estreita vira trilha horizontal rolável.** Dezesseis itens quebrados em
  linhas empurravam o primeiro número para baixo da dobra — num relatório executivo aberto
  no celular, isso é o defeito mais caro da página.
- Tabela financeira **não reflui em cards** abaixo de 768px: rola na horizontal, porque
  linha reflowada deixa de ser comparável com a de cima.

## 6. Impressão e distribuição

Distribuição inicial por link para download e abertura local. Em `@media print`: marca
"CONFIDENCIAL — USO INTERNO" no cabeçalho, mês-base e data de geração no rodapé, sidebar
oculta, quebras de página por seção. **Todas as abas imprimem** — no papel elas deixam de
ser um menu e viram um relatório contínuo, uma por página.

---

[← Índice](../CLAUDE.md)
