# Métricas — glossário de negócio

O que cada número significa. Para a fórmula exata e a célula de origem, ver
[calculos.md](calculos.md).

> [← Índice](../CLAUDE.md) · Relacionados: [calculos.md](calculos.md), [modelo-de-dados.md](modelo-de-dados.md)

Fonte primária: notas da aba `resumo` (B17:B22).

| Métrica | Definição |
|---|---|
| **AUM** | Ativos sob gestão: carteira administrada + fundos + estruturados + alocação + previdência + feeder + offshore. |
| **Receita (R$)** | Receita do mês por competência. **Somente receita recorrente** (taxa de gestão) — performance fee e receitas indiretas estão fora. |
| **Receita Mensalizada** | Receita do mês normalizada pelos dias úteis (ver 5.1). **É a métrica default** de KPIs e séries; a receita por competência entra como série secundária. |
| **Run Rate** | Receita mensalizada do último mês × 12. |
| **Projeção de Receita (ano)** | Receita acumulada no ano por competência + último mês anualizado para os meses restantes. |
| **ROA** | Receita anualizada ÷ AUM. Exibir em % com 2 casas. |
| **ROA MFO** | Por officer: mesma conta restrita ao **segmento MFO** no onshore — ignora Institucional e Estruturado. É o ROA da carteira de famílias, sem a diluição dos veículos institucionais e estruturados. **Duas ressalvas confirmadas na fórmula:** todo o offshore entra como MFO (não há filtro de segmento sobre a base offshore), e o numerador não é mensalizado. Ver [calculos.md](calculos.md) §3.5. |
| **Qtd. Grupos (officer / backup)** | Grupos econômicos distintos em que a pessoa é titular ou backup, contando só portfólios com AUM ou receita > 0 no mês. **Não somar entre officers** — um grupo pode ter portfólios sob titulares diferentes, então a soma (376 em jul/26) excede o total de grupos distintos (361). Ver [calculos.md](calculos.md) §3.5. |
| **NET** | IN − OUT do período. |
| **IN** | Decomposto em **Início (no ano)** (primeiro aporte de grupo novo no ano) e **Clientes antigos**. |
| **OUT** | Decomposto em **Uso pessoal** e **Saída para concorrência**. Esta decomposição entra no dashboard — é o dado mais acionável do relatório. |
| **ROA Incremental** | ROA anualizado YTD sobre o volume captado no período. |

## 1. Mensalização da receita

```
receita_mensalizada = receita_competencia / dias_uteis_do_mes * 21     # ONSHORE apenas
receita_mensalizada = receita_competencia                              # OFFSHORE: não mensaliza
receita_anualizada  = receita_mensalizada * 12
```

21 é o mês-padrão; 21 × 12 = 252, e a planilha usa as duas formas indistintamente. Os dias
úteis do mês estão em `info!AQ5` (`nwdays_mes`) e replicados na linha 4 das abas de série
longa — jul/26 teve 23.

Consequência para o build: a coluna "Receita (R$)" da `CEO-Dashboard` **já é mensalizada**
na parte onshore. Não mensalizar de novo.

Detalhe das fórmulas e das exceções em [calculos.md](calculos.md) §3.1.

## 2. Fundos de Alocação

`Fdos Alocação` aparece na `CEO-Dashboard` como pseudo-officer (officer `-`, grupo `G5`),
com ~R$ 14,2 bi — cerca de 33% do AUM — e ROA de ~0,12%, uma ordem de grandeza abaixo dos
officers reais. São os fundos próprios da G5 nos quais as carteiras alocam.

**Regra:** sempre incluído nos totais, para que TOTAL bata entre todas as visões. Um
**toggle global** "Ex-Fdos Alocação" recalcula proporções, ROA médio e rankings sem alterar
os totais absolutos exibidos. A planilha já traz a linha `Total Ex- Fdos Alocação` como
referência de conferência.

## 3. Moeda

Moeda base é **R$** em toda visão consolidada. O câmbio é fixo por mês, gravado em
`resumo!B4` e `regiao!G2` (US$ 1 = R$ 5,08 em jul/26) — extrair, nunca hardcodar. As páginas
puramente offshore (`ar_offshore`, `ar_adm_off`) mantêm **US$** com o símbolo explícito no
cabeçalho de cada coluna e um aviso de moeda no topo da página.

---

[← Índice](../CLAUDE.md)
