# Arquitetura do dashboard

> [← Índice](../CLAUDE.md) · Relacionados: [visual.md](visual.md), [metricas.md](metricas.md)

## 1. Navegação — sidebar

Menu lateral fixo (~240px, colapsável), conteúdo renderizado ao centro. Item ativo marcado
com barra wine à esquerda. Agrupamento:

```
VISÃO EXECUTIVA     Visão Geral · Resumo
PERFORMANCE         Histórico AUM × Receita · ROA Histórico
CARTEIRA            Officers · Grupos Econômicos · Regiões · Portfólios On · Portfólios Off
CAPTAÇÃO            Net In/Out · Grupos · Portfólios
ESTRUTURA           Administradores Onshore · Administradores Offshore
OUTROS              G5 JUS
```

## 2. Página inicial

Os quatro indicadores principais, com ênfase e **nesta ordem**: **AUM → Run Rate → Projeção
Ano → ROA**. Cada um com valor, variação M-1 (absoluta e %) e cor de sinal. Abaixo, split
Onshore/Offshore e o ranking de officers.

## 3. Períodos

Toda visão temporal oferece **MTD, Trimestre e YTD**. Não há meta ou orçamento nesta
análise — isso é discutido em outro fórum comercial. O acompanhamento é de **evolução**,
não de atingimento. Não inventar linha de meta.

## 4. Filtros

Barra de filtros ágeis, persistente por página e aplicável em conjunto:
**Officer · Tipo de veículo · Segmento · Onshore/Offshore**, mais o toggle global
Ex-Fdos Alocação. Filtro limpa em um clique e mostra quantos registros restaram.

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

## 6. Impressão e distribuição

Distribuição inicial por link para download e abertura local. Em `@media print`: marca
"CONFIDENCIAL — USO INTERNO" no cabeçalho, mês-base e data de geração no rodapé, sidebar
oculta, quebras de página por seção.

---

[← Índice](../CLAUDE.md)
