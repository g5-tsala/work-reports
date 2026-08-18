# Work Reports

Este repositório reúne scripts que geram relatórios HTML autocontidos a partir de dados exportados ou coletados. Cada relatório fica em seu próprio subdiretório, com dependências, dados e saída próprios.

## Idioma

**Escreva em português (pt-BR) por padrão** — documentação, comentários e docstrings de código,
rótulos de interface, textos dos relatórios gerados e mensagens de saída no terminal.

Permanecem em inglês apenas os identificadores literais, porque são chaves reais e traduzi-los
quebra o código: nomes de arquivo, colunas de CSV e campos de JSON das exportações de origem
(`Days Active`, `Lines this Month`, `Seat Tier`, `account_uuid`), além de nomes de variáveis,
funções e módulos.

Um documento tem um idioma só. Números e datas seguem o mesmo locale do texto — em pt-BR, `.` no
milhar, `,` no decimal, escala em `mil`/`MM`/`bi` e datas em `dd/mm/aaaa`.

## Relatórios

### `claude-usage/`

Gera um relatório executivo em HTML sobre o uso de Claude AI na G5 Partners — usuários ativos,
volume de conversas, atividade no Claude Code CLI, funil de adoção e mais.

Leia [`claude-usage/AGENTS.md`](claude-usage/AGENTS.md) para o contexto todo.

### `gerencial-mfo/`

Transforma a planilha gerencial mensal da área de MFO (Multi-Family Office) da G5 Partners
em um dashboard HTML autocontido, no padrão visual G5 e com leitura de BI.

Leia [`gerencial-mfo/AGENTS.md`](gerencial-mfo/AGENTS.md) para o contexto todo.
