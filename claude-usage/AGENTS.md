# Dados de Uso do Claude Team

Este diretório contém um snapshot dos dados de uso do Claude exportados por um admin da organização G5 Partners. Cobre usuários do domínio `@g5partners.com`, principalmente times de investment banking e operações.

## Contexto

A G5 Partners é a maior empresa independente de serviços financeiros do Brasil, atuando em Multi-Family Office (MFO), Assessoria Estratégica Financeira para Fusões e Aquisições (FSA), DCM Capital Solutions e investimentos alternativos em direitos creditórios judiciais (G5 JUS).

O time usa Claude para pesquisa sobre clientes, análise financeira, redação de documentos, fluxos de originação, suporte de TI e engenharia de software.

## Estrutura de diretórios

```
report.py                    # entrypoint enxuto — importa e chama core.main.main()
core/                        # lógica do relatório dividida em módulos focados
  config.py                  # caminhos ROOT / DATA / REPORTS e constante CLAUDE_CODE_TOOLS
  fetch.py                   # todas as funções load_* (usuários, conversas, arquivos CSV, etc.)
  metrics.py                 # orquestrador compute_metrics() + funções auxiliares privadas
  render.py                  # render_html() — CSS, template HTML, JS (sem dependências externas)
  main.py                    # main() — carrega dados, chama compute_metrics, escreve o arquivo de saída
data/                        # fora do git — todos os arquivos brutos da exportação Claude ficam aqui
  conversations-NNNN.json    # conversas da org, entregues em LOTES — 650 MB, NUNCA carregar por inteiro
                             # fetch.py faz glob de conversations*.json e concatena todos os lotes
                             # lotes podem faltar em uma exportação; trate as contagens como piso
  users.json                 # todos os membros da org (@g5partners.com); pode incluir contas removidas/sem assento
  memories.json              # resumos de memória por usuário (7 usuários com entradas)
  projects/                  # 71 arquivos JSON de projeto (pequenos, seguro ler)
  design_chats/              # 6 arquivos de conversas de design/artifact (pequenos, seguro ler)
  members-<uuid>-<date>.csv  # roster de membros exportado do admin dashboard da Anthropic
                             # fonte autoritativa de seat tier e vínculo ativo
                             # fetch.py sempre pega o último arquivo em ordem alfabética (mais recente)
  members-analytics-<uuid>-<from>-to-<to>.csv
                             # exportação de atividade por membro do Anthropic Console — fonte PRIMÁRIA
                             # de atividade do usuário: a ÚNICA exportação que reporta uso de Cowork
                             # cobre todos os membros, inclusive os ausentes dos lotes de conversas
                             # fetch.py sempre pega o último arquivo em ordem alfabética (mais recente)
  claude_code_team_*.csv     # exportação de uso do Claude Code CLI do Anthropic Console
                             # o nome do arquivo codifica o período: claude_code_team_YYYY_MM_DD_to_YYYY_MM_DD.csv
                             # fetch.py sempre pega o último arquivo em ordem alfabética (mais recente)
reports/                     # fora do git — arquivos de saída gerados
  report.html                # relatório executivo HTML autocontido (não editar diretamente)
```

## Arquitetura do código

O pipeline é uma linha reta: `fetch → metrics → render → write`.

```
report.py
  └── core/main.py          main()
        ├── core/fetch.py   load_users(), load_members(), load_members_analytics(),
        │                   load_conversations(), load_claude_code(), …
        ├── core/metrics.py compute_metrics(users, members, memories, projects, design_chats,
        │                                   conversations, claude_code_data, cc_period,
        │                                   analytics, analytics_period)
        │     ├── _filter_users()        filtra só quem é billable; mapa email→tier
        │     ├── _project_metrics()     passada por projetos/design chats; contador proj_per_user
        │     ├── _conversation_pass()   loop único sobre todas as conversas; devolve todos os contadores
        │     ├── _channel_active()      uids ativos em QUALQUER canal — a regra única de atividade
        │     ├── _build_user_rows()     linhas de atividade por usuário; colunas vindas do analytics
        │     ├── _cowork_metrics()      linhas e totais da seção Cowork
        │     ├── _adoption_funnel()     lista do funil; thresholds de dias ativos
        │     ├── _feature_rows()        linhas de adoção de features na ordem de exibição
        │     ├── _cc_web_metrics()      estatísticas de uso de ferramentas CC vindas da exportação web
        │     ├── _cc_csv_metrics()      estatísticas do Claude Code CLI vindas do CSV; devolve cc_uids
        │     └── _inactive_rows()       complemento de _channel_active()
        └── core/render.py  render_html(m) → string HTML autocontida
```

### Qual fonte alimenta qual coluna

O CSV members-analytics é a fonte primária para *se e quanto* alguém usou Claude;
os lotes de conversas continuam sendo a única fonte para *o que aconteceu dentro* de um chat.

| Do CSV members-analytics | Do conversations*.json |
|---|---|
| Dias ativos, Chats, Mensagens enviadas | Projetos, Arquivos enviados (+ modal de detalhe dos uploads) |
| Sessões / Mensagens Cowork | Adoção de features, top ferramentas |
| Sessões Code, File Edits, PRs | Volume diário, profundidade das conversas |
| Último acesso, veredito de atividade/inatividade | — |

`Estimated Spend (USD)` existe no CSV mas vem `0.00` para todo mundo — não é usado.

Ao editar a lógica do relatório, vá direto ao helper relevante em `core/metrics.py` em vez de ler o arquivo inteiro. `_conversation_pass()` é a maior função (~80 linhas); todo o resto tem menos de 30.

---

## CRÍTICO: nunca leia os arquivos JSON por inteiro

**Os lotes `conversations-NNNN.json` são arquivos de texto enormes. Carregá-los esgota sua janela de contexto.**

Use sempre ferramentas direcionadas para inspecionar os dados:

```bash
# Inspecionar a estrutura da primeira conversa (seguro — lê só 500KB de um lote)
python3 -c "
import json, glob
f = open(sorted(glob.glob('data/conversations*.json'))[0]); chunk = f.read(500000); f.close()
obj, _ = json.JSONDecoder().raw_decode(chunk[1:])
print(json.dumps(obj, indent=2, ensure_ascii=False)[:3000])
"

# Buscar conversas por palavra-chave (streaming, sem carga completa)
grep -i "palavra-chave" data/conversations*.json | head -5

# Para projects e design_chats — arquivos pequenos, seguro ler direto
cat data/projects/019d9c7d-ebcb-725b-9755-a109ab3b8d4d.json

# Para perguntas de atividade por usuário, leia o CSV de analytics — 9 KB, sempre seguro
cat data/members-analytics-*.csv
```

Para qualquer análise sobre os lotes de conversas, escreva um script Python que itere sobre
`glob.glob('data/conversations*.json')` e chame `json.load()` por arquivo, liberando cada lote
antes do próximo (`del convs; gc.collect()`). Cabe na memória (~3 GB de pico se todos forem
mantidos ao mesmo tempo), mas nunca deve ser impresso nem injetado no contexto do LLM.

**Prefira `members-analytics-*.csv` sempre que a pergunta for atividade por usuário.** Ele responde
a maioria das perguntas de "quem usou o quê, e quanto" em 9 KB em vez de 650 MB, e é a única fonte
que enxerga Cowork.

---

## Script do relatório

`report.py` é o entrypoint. Rode com:

```bash
python3 report.py        # escreve reports/report-YYYY-MM-DD.html e imprime o resumo no stdout
```

**Dependências:** apenas a stdlib do Python (`json`, `csv`, `re`, `glob`, `collections`, `datetime`, `pathlib`). Nenhum pip install necessário.

### Seções do relatório (em ordem)

A interface do relatório é toda em pt-BR, com números no padrão brasileiro (`.` no milhar, `,` no
decimal, escala em `mil`) e datas em `dd/mm/aaaa`. Nomes de coluna dos CSV de origem permanecem em
inglês — são chaves literais dos arquivos, não rótulos de tela.

| Seção | Fonte | Observações |
|---|---|---|
| Visão geral (KPIs) | todas as fontes | Usuários ativos = qualquer canal (chat, Cowork, Code) |
| Atividade por usuário | CSV members-analytics + conversas | Tabela ordenável; clique na contagem de arquivos para abrir o modal |
| Cowork | CSV members-analytics | Única exportação que enxerga Cowork; sinaliza usuários só-Cowork |
| Claude Code | data/claude_code_team_*.csv | Linhas em milhares (`mil`); cruza com as conversas web |
| Contas inativas | CSV members-analytics | Zero nos três canais |
| Funil de adoção | CSV members-analytics | Veja os thresholds abaixo |
| Volume diário de conversas | conversations*.json | Gráfico de colunas, janela de 30 dias |
| Distribuição de profundidade | conversations*.json | Distribuição por quantidade de mensagens |

### Thresholds do funil de adoção

Medidos por `Days Active`, que conta a pessoa igual tendo ela trabalhado em chat, Cowork ou Code.

| Nível | Threshold |
|---|---|
| Ativos | ≥1 uso em qualquer canal (chat, Cowork, Code) |
| Engajados | ≥10 dias ativos |
| Power users | ≥20 dias ativos (usuário recorrente) |

Cada estágio do funil também mostra sua participação sobre os usuários registrados. Memória é
deliberadamente excluída do escalonamento — ela é criada de forma passiva demais para sinalizar
intensidade de adoção.

Se não houver CSV members-analytics, `_adoption_funnel()` cai no critério antigo, pela união de
contagem de conversas e linhas de código (≥1/≥5 convs, ≥1K/≥5K/≥10K linhas; power = ≥10K linhas).

### Definição de usuário ativo

**Um usuário é ativo se interagiu em QUALQUER canal: chat, Cowork ou Claude Code.**
`_channel_active()` é a única implementação; o card de KPI, a tabela de usuários, o funil de adoção
e a lista de inativos derivam dela, e `_inactive_rows()` é seu complemento exato.

O veredito vem do CSV members-analytics. Usuários ausentes dessa exportação caem para as evidências
dos lotes de conversas e do CSV do Claude Code, e são marcados como *sem cobertura* na tabela de
Contas inativas — a falta de uma linha no analytics nunca pode rebaixar alguém silenciosamente.

**Por que isso importa:** antes de Cowork ser medido, a atividade era inferida da exportação de
conversas (só chat web) somada a `Lines this Month` (só linhas de código). Um usuário que trabalhava
exclusivamente no Cowork não produzia nenhum dos dois, então aparecia em Contas inativas apesar do
uso diário — e ao menos um assento foi recuperado com base nesse falso negativo. Nunca infira
inatividade a partir de uma fonte que não enxerga os três canais.

---

## Schemas JSON

### `data/users.json`

Nível raiz: `array` de objetos de usuário.

```jsonc
[
  {
    "uuid": "string (UUIDv4)",          // casa com account.uuid nas conversas
    "full_name": "string | null",
    "email_address": "string",          // todos @g5partners.com
    "verified_phone_number": "string | null"  // formato E.164, ex. "+5511..."
  }
]
```

### `data/memories.json`

Nível raiz: `array` de objetos de memória. Só usuários que acumularam histórico de conversas têm entrada.

```jsonc
[
  {
    "account_uuid": "string (UUIDv4)",  // chave estrangeira → users[].uuid
    "conversations_memory": "string",   // resumo markdown longo que o Claude montou de sessões passadas;
                                        // cobre contexto de trabalho, deals ativos, preferências, histórico recente
    "project_memories": {               // resumos de memória por projeto (pode não existir se vazio)
      "<project-uuid>": "string"        // UUID do projeto → memória markdown daquele projeto
    }
  }
]
```

### `data/projects/<uuid>.json`

Cada arquivo é um único objeto de projeto (não um array).

```jsonc
{
  "uuid": "string (UUIDv4)",
  "name": "string",
  "description": "string",
  "is_private": "boolean",
  "is_starter_project": "boolean",
  "prompt_template": "string",          // system prompt / instruções do projeto
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "creator": {
    "uuid": "string (UUIDv4)",          // chave estrangeira → users[].uuid
    "full_name": "string"
  },
  "docs": [
    {
      "uuid": "string (UUIDv4)",
      "filename": "string",
      "content": "string",              // texto do documento enviado
      "created_at": "string (ISO 8601)"
    }
  ]
}
```

### `data/design_chats/<uuid>.json`

Cada arquivo é um único objeto de conversa de design/artifact.

```jsonc
{
  "uuid": "string (UUIDv4)",
  "title": "string",
  "project": {
    "uuid": "string (UUIDv4)",          // chave estrangeira → projects/<uuid>.json
    "name": "string"
  },
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "messages": [
    {
      "uuid": "string (UUIDv4)",
      "role": "user | assistant",
      "content": {
        "attachments": "array",
        "authorAccountUuid": "string",
        "authorName": "string",
        "content": "string",            // texto da mensagem
        "id": "string",
        "role": "string",
        "timestamp": "string (ISO 8601)"
      },
      "created_at": "string (ISO 8601)"
    }
  ]
}
```

### `data/conversations-NNNN.json`

Nível raiz: `array` de objetos de conversa, dividido em um ou mais arquivos de lote.
**Não carregue esses arquivos por inteiro.** `load_conversations()` faz glob de `conversations*.json`
e concatena todos os lotes, então uma exportação de arquivo único é só o caso de um lote só.

Lotes podem se perder em uma reexportação; quando a contagem de chats do CSV de analytics supera o que
os lotes mostram, os lotes é que estão incompletos, não o CSV.

```jsonc
[
  {
    "uuid": "string (UUIDv4)",
    "name": "string",                   // título da conversa
    "summary": "string",                // pode vir vazio
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)",
    "account": {
      "uuid": "string (UUIDv4)"         // chave estrangeira → users[].uuid
    },
    "chat_messages": [
      {
        "uuid": "string (UUIDv4)",
        "text": "string",               // texto puro completo da mensagem
        "content": [
          {
            "start_timestamp": "string (ISO 8601)",
            "stop_timestamp": "string (ISO 8601)",
            "flags": "null | object",
            "type": "text | tool_use | tool_result | thinking | ...",
            "text": "string"            // presente quando type == "text"
            // campos adicionais variam por tipo; veja as armadilhas abaixo
          }
        ],
        "sender": "human | assistant",
        "created_at": "string (ISO 8601)",
        "updated_at": "string (ISO 8601)",
        "attachments": "array",         // anexos de arquivo/imagem
        "files": "array",               // lista estruturada de arquivos; veja as armadilhas abaixo
        "parent_message_uuid": "string (UUIDv4)"  // pai na thread; mensagens raiz usam UUID nulo
      }
    ]
  }
]
```

### `data/members-<uuid>-<date>.csv`

Exportado do admin dashboard de team da Anthropic. Esta é a **fonte autoritativa de vínculo** — use o e-mail como chave de join. Se um usuário aparece em `data/users.json` mas não aqui, ele foi removido da org.

```csv
Name,Email,Role,Status,Seat Tier
G5 Partners - Contas-TI,contas-ti@g5partners.com,Primary Owner,Active,Unassigned
Leonardo,lzambello@g5partners.com,User,Active,Standard
...
```

| Coluna | Tipo | Descrição |
|---|---|---|
| `Name` | string | Nome de exibição |
| `Email` | string | Chave de join → `users[].email_address` e coluna `User` de `claude_code_team_*.csv` |
| `Role` | string | `Primary Owner`, `Admin`, `User`, etc. |
| `Status` | string | `Active` ou `Inactive` |
| `Seat Tier` | string | `Standard`, `Premium` ou `Unassigned` |

**`Seat Tier = Unassigned`** significa que o assento não está atribuído a um usuário billable (ex.: contas compartilhadas/de serviço). Esses são excluídos de todas as métricas do relatório — contagem de ativos, de inativos, funil e KPIs. Não são faturados e não devem ser acompanhados.

---

### `data/members-analytics-<uuid>-<from>-to-<to>.csv`

Exportação de atividade por membro do Anthropic Console. **Fonte primária de atividade do usuário** e
a única exportação que reporta Cowork. Cobre todos os membros da org, inclusive os que não têm linha
nos lotes de conversas. O relatório usa o arquivo mais recente (último em ordem alfabética). O nome do
arquivo codifica a janela: `...-2026-06-23-to-2026-07-22.csv`.

Gravado **com BOM UTF-8** — abra com `encoding='utf-8-sig'`, senão o primeiro cabeçalho vira
`﻿Name` e a coluna `Name` passa a ler vazio silenciosamente.

```csv
"Name","Email","Role","Seat Tier","Last Active","Days Active","Chats","Messages",
"Projects Created","Projects Used","Pull Requests","Code sessions","File Edits",
"Cowork Sessions","Cowork Messages","Artifacts Created","Estimated Spend (USD)"
"Caroline","csnit@g5partners.com","User","Standard","2026-07-20","22","0","0",
"0","0","0","0","0","25","61","0","0.00"
```

| Coluna | Tipo | Descrição |
|---|---|---|
| `Email` | string | Chave de join → `users[].email_address` |
| `Last Active` | data `YYYY-MM-DD` | Considerando todos os canais; pode vir vazia |
| `Days Active` | inteiro | Dias distintos com alguma interação — a métrica de engajamento que o funil usa |
| `Chats` | inteiro | Conversas web/desktop tocadas na janela |
| `Messages` | inteiro | **Só mensagens humanas** — corresponde a `user_human_msgs`, não a `len(chat_messages)` |
| `Cowork Sessions` / `Cowork Messages` | inteiro | Uso de Cowork; **invisível em qualquer outra exportação** |
| `Code sessions` / `File Edits` / `Pull Requests` | inteiro | Atividade do Claude Code, mais rica que o CSV de linhas |
| `Projects Created` / `Projects Used` | inteiro | Cruza com a passada sobre os JSON de `projects/` |
| `Artifacts Created` | inteiro | Quantidade de artifacts |
| `Estimated Spend (USD)` | decimal | Vem `0.00` para todo mundo neste plano — não é usado |

Hoje as contagens são inteiros simples; `_csv_int()` também remove `.` caso valores grandes cheguem
com separador de milhar pt-BR, como já acontece em `claude_code_team_*.csv`.

O `Chats` aqui pode superar a contagem dos lotes para o mesmo usuário: o CSV conta chats *tocados* na
janela (um chat de junho usado em julho conta), enquanto o JSON é filtrado por `created_at`. Também
fica mais alto quando faltam lotes de conversas na exportação.

**O `Seat Tier` deste arquivo pode estar defasado em relação ao roster.** Use `members-*.csv` como
autoridade para tier e status; use este arquivo para atividade.

---

### `data/claude_code_team_*.csv`

Exportação CSV do Anthropic Console. O relatório usa o **arquivo mais recente** (último em ordem alfabética por nome). Uma nova exportação substitui a antiga por convenção de nome.

```csv
User,Lines this Month
middle_dev@g5partners.com,64.230
gestao@g5partners.com,48.165
mmedeiros@g5partners.com,526
tcitro@g5partners.com,317
...
```

| Coluna | Tipo | Descrição |
|---|---|---|
| `User` | string | E-mail do usuário; faz join com `users[].email_address` |
| `Lines this Month` | inteiro (formatação brasileira) | **Contagem bruta de linhas em que `.` é separador de milhar** — `64.230` = 64.230 linhas, `526` = 526 linhas. Linhas de código geradas ou modificadas via Claude Code CLI. |

**Armadilha de formato numérico:** o valor NÃO é decimal. O `.` é separador de milhar (formatação pt-BR), então valores ≥ 1000 sempre mostram exatamente três dígitos depois do ponto (`64.230`), enquanto valores < 1000 não têm separador (`526`, `317`). `core/fetch.py` remove o `.` para recuperar o inteiro verdadeiro e depois divide por 1000 para expressar em milhares (K) — a representação que o resto do pipeline (render, thresholds do funil) espera. Parsear o valor com um `float()` simples é errado: funciona por acaso para valores ≥ 1000, mas infla em 1000× as contagens abaixo de 1000 (ex.: `317` renderizaria como 317K em vez de 0,3K).

Só aparecem usuários com atividade no CLI. Usuários ausentes daqui tiveram zero uso de CLI no período.

---

## Relacionamentos-chave

```
data/users[].uuid
  ↳ data/conversations[].account.uuid     (de quem é a conversa)
  ↳ data/memories[].account_uuid          (de quem é o resumo de memória)
  ↳ data/projects[].creator.uuid          (de quem é o projeto)

data/projects[].uuid
  ↳ data/design_chats[].project.uuid      (a que projeto pertence a conversa de design)

data/users[].email_address
  ↳ coluna Email de data/members-*.csv            (seat tier, vínculo autoritativo)
  ↳ coluna Email de data/members-analytics-*.csv  (atividade em todos os canais, incl. Cowork)
  ↳ coluna User de data/claude_code_team_*.csv    (linhas de código no CLI)
```

---

## Armadilhas

**Uso de Cowork aparece em exatamente uma exportação.**
Nem os lotes de conversas nem `claude_code_team_*.csv` o enxergam. Um usuário só-Cowork lê como zero
em tudo, exceto em `members-analytics-*.csv`. Qualquer julgamento de atividade/inatividade construído
sobre as outras duas fontes está errado por construção — veja "Definição de usuário ativo".

**Blocos `tool_use` nos lotes de conversas NÃO são Claude Code CLI.**
Ferramentas como `bash_tool`, `view`, `str_replace`, `create_file` aparecem em blocos de `content` vindos do ambiente de execução de código embutido na interface web do claude.ai. Elas compartilham o nome com ferramentas do Claude Code CLI, mas são coisas separadas. Não há como distinguir sessões de Claude Code CLI a partir desta exportação — esse dado só aparece no CSV.

**Uploads de arquivo são inflados pela conversão de documentos.**
Quando um usuário envia um PDF ou PowerPoint, o Claude converte cada página/slide em uma imagem individual (`slide-1.jpg`, `slide-2.jpg`, …). Cada imagem aparece como uma entrada separada em `msg.files`. Um único documento de 30 páginas gera 30 entradas de arquivo. A contagem `files_uploaded` do relatório reflete isso.

**Conversas dentro de Projects do claude.ai estão incluídas nos lotes de conversas.**
Não existe campo `project_uuid` nos objetos de conversa — não é possível determinar por esta exportação quais conversas pertencem a qual projeto.

**"Inativo" significa realmente inativo — e só entre usuários billable.**
A seção Contas inativas só mostra usuários com zero chats E zero sessões de Cowork E zero sessões de Code. Qualquer atividade em qualquer canal tira o usuário da lista.

Assentos Unassigned são excluídos do relatório por completo e nunca aparecem como inativos — inclusive alguém cujo assento foi *recuperado* depois de ter sido julgado inativo por engano. Assim que o tier vira `Unassigned`, a pessoa some de todas as tabelas, então erros de atribuição não se autocorrigem. Confira `members-analytics-*.csv` diretamente antes de recuperar um assento.

**`data/users.json` pode conter contas obsoletas ou sem assento.**
Sempre cruze com `data/members-*.csv` (join por e-mail) para determinar vínculo atual e seat tier. Usuários ausentes do CSV de members foram removidos da org e são excluídos de todas as métricas.
