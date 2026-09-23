# Ambiente e execução

## 1. uv

Ambiente e dependências só pelo **uv** — nada de `pip`, `venv`, `requirements.txt` ou conda.

- Dependências em `pyproject.toml`, travadas em `uv.lock` (**versionado**: garante as mesmas
  versões entre builds de meses diferentes). `.venv/` fora do git.
- Adicionar dependência: `uv add <pacote>` (resolve e atualiza o lock). Rodar: `uv run python …`;
  nunca ativar a venv.
- Python ≥ 3.11 para o projeto; se a máquina tiver um mais antigo, `uv sync` baixa um 3.11+ só
  para o projeto.
- O próprio `uv` é instalado com `pip install uv` — passa limpo em máquina corporativa, sem
  winget nem binário externo — e invocado como `<python> -m uv`, o que dispensa mexer no `PATH`.
  Pressupõe um Python na máquina; sem nenhum, os scripts dizem isso e param.

## 2. Pontos de entrada

`gerar-dashboard.bat` (Windows, dois cliques — entregável do usuário final) e
`gerar-dashboard.sh` (Linux/WSL, dev). **Mesmo fluxo e mesmas mensagens: mudou um, muda o
outro.** Nenhum abre o HTML — imprimem o caminho absoluto de JSON e HTML e param.

Fluxo: localizar/instalar o `uv` → `uv sync` → listar `inputs/YYYY-MM` marcando quais têm a
planilha → pedir o mês e validar pasta e nome exato do arquivo → `uv run python dashboard.py
<mês>` → mostrar os caminhos gerados.

### 2.1 Regras do `.bat`

- **ASCII puro, sem acento** — a codepage do console corporativo é imprevisível.
- **CRLF obrigatório** — com LF, `goto`/labels quebram em silêncio. Ao editar do Unix, converter
  antes de gravar.
- `cd /d "%~dp0"` na primeira linha; nenhum caminho absoluto; nada exige administrador.
- Todo erro tem label próprio e mensagem acionável e cai em `:fim`, que espera ENTER
  (`set /p "DUMMY=Digite ENTER para finalizar..."`) — a janela nunca fecha sozinha.
- Expansão atrasada (`!VAR!`) em tudo que é atribuído dentro de bloco `if`/`for`; `%VAR%` ali lê
  o valor de antes do bloco e falha em silêncio (por isso a invocação fica em `!UV!`).
- Busca do `uv`: `PATH` → `py -3 -m uv` → `python -m uv` → `pip install --upgrade uv`.

### 2.2 Diferenças do `.sh`

- Aceita o mês como argumento e só pergunta se faltar (roda sem TTY); valida o formato
  `YYYY-MM` por regex antes de olhar o disco.
- Busca do `uv`: `PATH` → `~/.local/bin/uv` → `python3 -m uv` → `pip install --user uv`
  (`--user` evita o PEP 668; se falhar, sugere `pipx install uv`).
- `set -euo pipefail`; todo erro passa por `erro()`, que escreve em `stderr` e sai com 1.
- UTF-8 é permitido, mas as mensagens seguem sem acento para ficarem idênticas às do `.bat`.
- Não espera ENTER no final.
