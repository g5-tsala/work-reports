#!/usr/bin/env bash
#
# Gerencial MFO - Gerador de Dashboard (Linux / WSL)
# G5 Partners - uso interno
#
# Equivalente ao gerar-dashboard.bat. Uso:
#     ./gerar-dashboard.sh            # pergunta o mes-base
#     ./gerar-dashboard.sh 2026-07    # mes-base pela linha de comando
#
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ------------------------------------------------------------
#  Utilitarios
# ------------------------------------------------------------
erro() {
    printf '\n[ERRO] %s\n' "$1" >&2
    shift
    local linha
    for linha in "$@"; do
        printf '       %s\n' "$linha" >&2
    done
    exit 1
}

echo
echo "============================================================"
echo "   GERENCIAL MFO - Gerador de Dashboard"
echo "   G5 Partners - uso interno"
echo "============================================================"
echo

# ------------------------------------------------------------
#  1. Localizar (ou instalar) o uv
#     Instalacao via "pip install --user uv" - depende de um
#     Python ja presente na maquina.
# ------------------------------------------------------------
UV=()
if command -v uv >/dev/null 2>&1; then
    UV=(uv)
elif [[ -x "$HOME/.local/bin/uv" ]]; then
    UV=("$HOME/.local/bin/uv")
else
    PY=""
    for candidato in python3 python; do
        if command -v "$candidato" >/dev/null 2>&1; then
            PY="$candidato"
            break
        fi
    done
    [[ -n "$PY" ]] || erro \
        "Nenhuma instalacao de Python encontrada nesta maquina." \
        "O uv e instalado via \"pip install uv\" e precisa de um Python" \
        "ja presente. Instale o Python 3.11 ou superior (por exemplo," \
        "sudo apt install python3 python3-pip) e rode este script de novo."

    if ! "$PY" -m uv --version >/dev/null 2>&1; then
        echo "[setup] uv nao encontrado. Instalando via pip..."
        "$PY" -m pip install --upgrade --quiet --user uv || erro \
            "Falha ao instalar o uv via pip." \
            "Tente manualmente:" \
            "    $PY -m pip install --user --upgrade uv" \
            "Se o pip recusar por ambiente gerenciado (PEP 668), use:" \
            "    pipx install uv" \
            "Se houver bloqueio de rede ou proxy, fale com a TI."
        echo "[setup] uv instalado."
        echo
    fi

    if "$PY" -m uv --version >/dev/null 2>&1; then
        UV=("$PY" -m uv)
    elif [[ -x "$HOME/.local/bin/uv" ]]; then
        UV=("$HOME/.local/bin/uv")
    else
        erro "O uv foi instalado mas nao pode ser invocado." \
             "Verifique se $HOME/.local/bin esta no PATH."
    fi
fi

# ------------------------------------------------------------
#  2. Sincronizar ambiente e dependencias
# ------------------------------------------------------------
echo "[setup] Sincronizando ambiente virtual e dependencias..."
"${UV[@]}" sync --quiet || erro \
    "Falha ao sincronizar as dependencias." \
    "Verifique a conexao de rede e o arquivo pyproject.toml."
echo "[setup] Ambiente pronto."
echo

# ------------------------------------------------------------
#  3. Escolher o mes-base
# ------------------------------------------------------------
[[ -d inputs ]] || erro \
    "A pasta \"inputs\" nao existe." \
    "Crie a pasta inputs/ e coloque dentro dela uma subpasta" \
    "por mes, no formato YYYY-MM, com a planilha correspondente."

shopt -s nullglob
pastas=(inputs/[0-9][0-9][0-9][0-9]-[0-9][0-9]/)
shopt -u nullglob

echo "Meses disponiveis em inputs/:"
if ((${#pastas[@]} == 0)); then
    echo "   (nenhuma subpasta YYYY-MM encontrada em inputs/)"
else
    for pasta in "${pastas[@]}"; do
        mes="$(basename "$pasta")"
        if [[ -f "inputs/$mes/Gerencial MFO $mes.xlsx" ]]; then
            echo "   $mes   [planilha OK]"
        else
            echo "   $mes   [SEM PLANILHA]"
        fi
    done
fi
echo

MES="${1:-}"
if [[ -z "$MES" ]]; then
    read -r -p "Informe o mes-base no formato YYYY-MM: " MES || MES=""
fi
[[ -n "$MES" ]] || erro "Nenhum mes informado."

[[ "$MES" =~ ^[0-9]{4}-(0[1-9]|1[0-2])$ ]] || erro \
    "Mes-base invalido: $MES" \
    "Use o formato YYYY-MM, por exemplo: 2026-07"

[[ -d "inputs/$MES" ]] || erro \
    "A subpasta \"inputs/$MES\" nao existe." \
    "Use o formato YYYY-MM, por exemplo: 2026-07"

PLANILHA="inputs/$MES/Gerencial MFO $MES.xlsx"
[[ -f "$PLANILHA" ]] || erro \
    "Planilha nao encontrada em:" \
    "$PLANILHA" \
    "O nome do arquivo precisa seguir exatamente esse padrao."

[[ -f build.py ]] || erro \
    "build.py nao encontrado na pasta do projeto." \
    "Este script so orquestra o ambiente; o build em si vive no build.py."

# ------------------------------------------------------------
#  4. Rodar o build
# ------------------------------------------------------------
echo
echo "------------------------------------------------------------"
echo " Processando $MES..."
echo "------------------------------------------------------------"
echo

"${UV[@]}" run python build.py "$MES" || erro \
    "O processamento falhou. Veja as mensagens acima." \
    "Nenhum dashboard foi gerado para $MES."

echo
echo "------------------------------------------------------------"
echo " CONCLUIDO"
echo "------------------------------------------------------------"
echo "  Base:      $PWD/outputs/$MES/data-$MES.json"
echo "  Dashboard: $PWD/outputs/$MES/dashboard-$MES.html"
echo
