# Ambiente e execução

> [← Índice](../CLAUDE.md) · Relacionados: [validacao.md](validacao.md)

## 1. Gerenciamento de ambiente — uv

O ambiente e as dependências são centralizados no **uv**. Não usar `pip`, `venv`,
`requirements.txt` ou conda neste projeto.

- Dependências declaradas em `pyproject.toml`; versões travadas em `uv.lock`.
- **`uv.lock` é versionado.** É o que garante que o build de agosto rode com as mesmas
  versões do build de julho.
- `.venv/` fica fora do controle de versão.
- Adicionar dependência: `uv add <pacote>` (nunca editar o `pyproject.toml` na mão para isso
  — o comando resolve e atualiza o lock).
- Rodar qualquer coisa no ambiente: `uv run python ...`. Nunca ativar a venv manualmente.

Python mínimo 3.11 para o projeto. A instalação do próprio `uv` é feita por
`pip install uv`, o que **pressupõe um Python já presente na máquina** — é a via escolhida
por ser a que passa mais limpo em ambiente corporativo, sem depender de winget nem de
instalador que baixa binário de fora. Máquina sem Python nenhum é um pré-requisito não
atendido, e o `.bat` diz isso explicitamente em vez de tentar resolver sozinho.

Uma vez instalado, o `uv` cuida do interpretador do *projeto*: se o Python da máquina for
mais antigo que 3.11, o `uv sync` baixa e usa um 3.11+ apenas para este projeto, sem tocar
na instalação do sistema.

## 2. Pontos de entrada

Há dois, com o mesmo fluxo e as mesmas mensagens:

| Script | Ambiente | Uso |
|---|---|---|
| `gerar-dashboard.bat` | Windows | dois cliques, sem terminal — é o do usuário final |
| `gerar-dashboard.sh` | Linux / WSL | `./gerar-dashboard.sh` ou `./gerar-dashboard.sh 2026-07` |

O fluxo é o mesmo nos dois e deve ser alterado em conjunto. **Nenhum dos dois abre o HTML** —
a responsabilidade termina no arquivo gerado, com o caminho absoluto impresso na tela.

### 2.1 `gerar-dashboard.bat`

O usuário final não abre terminal. **Dois cliques no `.bat` fazem tudo**, nesta ordem:

1. Localiza o `uv`. Se não estiver no `PATH`, procura um Python (`py -3`, depois `python`)
   e instala com `pip install --upgrade uv`. Passa a invocar como `<python> -m uv`, o que
   dispensa mexer no `PATH` — o executável do `uv` costuma cair no diretório `Scripts` do
   Python, que raramente está no `PATH` de máquina corporativa.
2. `uv sync` — cria a venv e sincroniza as dependências a partir do lock.
3. Lista as subpastas `inputs/YYYY-MM` existentes, marcando quais já têm a planilha no lugar.
4. Pede o mês-base por `set /p` e valida: pasta existe e planilha com o nome exato existe.
5. `uv run python dashboard.py <YYYY-MM>`.
6. Em caso de sucesso, mostra os caminhos absolutos do JSON e do HTML gerados.
7. `set /p` com "Digite ENTER para finalizar..." no final — a janela nunca fecha sozinha,
   nem no caminho de erro, e o usuário consegue ler as mensagens antes de fechar.

**Regras ao mexer no `.bat`:**

- **ASCII puro, sem acentos.** Codepage do console no Windows corporativo é imprevisível e
  acento em `.bat` vira lixo na tela. As mensagens são em português sem acentuação.
- **CRLF obrigatório.** Batch com terminação LF quebra `goto`/labels de forma silenciosa.
  Ao editar de um ambiente Unix, converter antes de gravar.
- Todo caminho de erro tem label próprio, mensagem acionável e cai no `:fim` com `pause`.
- Nenhum caminho absoluto: `cd /d "%~dp0"` na primeira linha ancora tudo na pasta do script.
- Nada exige privilégio de administrador.
- Expansão atrasada (`!VAR!`) em tudo que é atribuído dentro de bloco `if`/`for`. Usar `%VAR%`
  nesses pontos lê o valor de antes do bloco e falha em silêncio — foi por isso que a
  invocação do `uv` ficou na variável `!UV!`.

### 2.2 `gerar-dashboard.sh`

Os mesmos passos do `.bat`, adaptados ao Linux/WSL. As diferenças que importam:

- **Aceita o mês como argumento** (`./gerar-dashboard.sh 2026-07`) e só pergunta se ele não
  vier. Isso permite rodar sem TTY, em automação.
- Valida o **formato** do mês por regex (`YYYY-MM`, mês de 01 a 12) antes de olhar o disco.
- Busca do `uv`, em ordem: `PATH` → `~/.local/bin/uv` → `python3 -m uv` →
  `pip install --user uv`. O `--user` evita esbarrar no PEP 668 (ambiente gerenciado) das
  distros recentes; se ainda assim falhar, a mensagem sugere `pipx install uv`.
- `set -euo pipefail` ligado; todo caminho de erro passa pela função `erro`, que escreve em
  `stderr` e sai com status 1.
- **UTF-8 com acento é permitido aqui** — a restrição de ASCII vale só para o `.bat`.
  Ainda assim, as mensagens de console foram mantidas sem acento para ficarem idênticas às
  do `.bat`; o que tem acento é só o comentário do código.
- Não há espera por ENTER no final: o terminal continua aberto por natureza.

Para desenvolvimento, o atalho direto continua valendo:

```bash
uv run python dashboard.py 2026-07                     # pipeline completo
uv run python dashboard.py 2026-07 --etapa extrair     # planilha -> JSON + validação
uv run python dashboard.py 2026-07 --etapa validar     # revalida o JSON já gerado
uv run python dashboard.py 2026-07 --etapa renderizar  # JSON -> HTML
```

Códigos de saída: `2` erro de uso (mês inválido, planilha ausente), `3` base reprovada no
checklist, `4` etapa de renderização ainda não implementada.

## 3. Pipeline

Três estágios, nesta ordem, orquestrados por `dashboard.py`:

1. **Extração** — lê `inputs/YYYY-MM/Gerencial MFO YYYY-MM.xlsx` com `openpyxl`
   (`data_only=True`, os valores calculados já estão gravados) e emite
   `outputs/YYYY-MM/data-YYYY-MM.json`.
2. **Validação** — confere os checks embutidos na planilha e a consistência de totais
   ([validacao.md](validacao.md) §1). Falha ruidosamente; nunca gera HTML a partir de base
   inconsistente.
3. **Renderização** — injeta o JSON e os assets de `template/` em `base.html` e escreve
   `outputs/YYYY-MM/dashboard-YYYY-MM.html`.

## 3.1 Organização do código

`dashboard.py` na raiz só orquestra e trata argumentos e códigos de saída. O trabalho vive
em `core/`:

| Módulo | Papel |
|---|---|
| `core/config.py` | caminhos, versões e tolerâncias. Sem layout de planilha. |
| `core/planilha.py` | abertura do xlsx, intervalos, nomes definidos e limpeza de valores. |
| `core/extracao/` | etapa 1, um módulo por domínio (ver abaixo). |
| `core/validacao.py` | o checklist bloqueante, rodando **sobre o JSON**, não sobre o xlsx. |
| `core/render.py` | etapa 2 — ainda não implementada. |
| `core/json_io.py` | leitura e escrita do JSON intermediário. |

Dentro de `core/extracao/`: `parametros` (aba `info`), `consolidado` (`resumo` +
`CEO-Dashboard`), `historico` (`aum_receita`, `roa_historico`), `officers`
(`cons_officer`), `carteira` (bases de posição, grupos, regiões), `captacao` (`net_in_out`,
`io_*`, blocos do `Dashboard`), `estrutura` (administradores, `G5JUS`), `checks` (os checks
embutidos) e `comum` (leitura de blocos rotulados, compartilhada).

**Cada extrator carrega as coordenadas que ele lê**, como constantes no topo do próprio
módulo e com a referência da célula no comentário. Nenhum mapa central de layout: quando a
geradora mexer numa aba, a mudança fica confinada a um arquivo.

Duas coisas são lidas da planilha em vez de escritas no código, e não devem virar lista
fixa: os **rótulos de linha** (viram `rotulo` + `chave`) e o **recuo da célula**, que dá o
nível de hierarquia usado no drill-down. Detalhe em
[contrato-json.md](contrato-json.md) §3.1.

A validação roda sobre o JSON — e não sobre a planilha — de propósito: assim
`--etapa validar` confere uma base já gerada, e a etapa de renderização nunca recebe base
que não passou pelo checklist.

**Regras invioláveis do pipeline:**

- O build de um mês lê **apenas** `inputs/YYYY-MM/`. Nunca lê meses anteriores nem escreve
  fora de `outputs/YYYY-MM/`. A planilha já carrega todo o histórico e o comparativo M-1
  dentro dela.
- Correções retroativas aparecem só na versão mais recente. Não reconciliar contra HTMLs
  antigos, não versionar diffs de números.
- O mês de fechamento vem do **nome da subpasta em `inputs/`**, não do conteúdo. As séries de 2026 já trazem
  colunas de meses futuros zeradas — truncar em `YYYY-MM` e nunca plotar zeros futuros.
- Nada de CDN. O HTML tem que abrir de qualquer lugar, offline, em rede corporativa
  restritiva. CSS, JS e gráficos são inlined. Sem webfonts externas — usar a pilha de
  fallback do design system.
- O HTML precisa funcionar dentro de um `<iframe>` (planejado para um portal futuro).
  Nada de `window.top`, `localStorage` ou navegação que assuma ser documento de topo.

---

[← Índice](../CLAUDE.md)
