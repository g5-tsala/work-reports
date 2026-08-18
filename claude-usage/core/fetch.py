import csv
import json
import re
import glob
from pathlib import Path

from .config import DATA


def load_users():
    with open(DATA / "users.json") as f:
        users = json.load(f)
    return {u["uuid"]: u for u in users}


def load_memories():
    with open(DATA / "memories.json") as f:
        entries = json.load(f)
    return {e["account_uuid"]: e for e in entries}


def load_projects():
    projects = []
    for path in glob.glob(str(DATA / "projects" / "*.json")):
        with open(path) as f:
            projects.append(json.load(f))
    return projects


def load_design_chats():
    chats = []
    for path in glob.glob(str(DATA / "design_chats" / "*.json")):
        with open(path) as f:
            chats.append(json.load(f))
    return chats


def load_conversations():
    """Carrega e concatena todos os lotes conversations*.json de data/.

    A exportação da org é entregue em lotes (conversations-0001.json, -0002.json, …); uma
    exportação de arquivo único é só o caso de um lote só. Os lotes são carregados em ordem de
    nome de arquivo e achatados em uma lista só, no formato que _conversation_pass() espera.
    """
    conversations = []
    for path in sorted(glob.glob(str(DATA / "conversations*.json"))):
        with open(path) as f:
            conversations.extend(json.load(f))
    return conversations


def load_members():
    """Carrega o members-*.csv mais recente; devolve o mapa email→{tier, role, status}."""
    # members-analytics-*.csv também casa com "members-*"; é outro schema, carregado à parte
    # por load_members_analytics(), então precisa ser filtrado explicitamente.
    files = sorted(p for p in glob.glob(str(DATA / "members-*.csv"))
                   if not Path(p).name.startswith("members-analytics"))
    if not files:
        return {}
    result = {}
    with open(files[-1], newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            email = row.get("Email", "").strip()
            if email:
                result[email] = {
                    "tier": row.get("Seat Tier", "").strip(),
                    "role": row.get("Role", "").strip(),
                    "status": row.get("Status", "").strip(),
                }
    return result


def _csv_int(raw):
    """Lê uma contagem inteira do CSV de analytics, tolerando separador de milhar pt-BR."""
    try:
        return int((raw or "0").strip().replace(".", "") or 0)
    except ValueError:
        return 0


def load_members_analytics():
    """Carrega o members-analytics-*.csv mais recente; devolve (mapa email→métricas, string do período).

    É a exportação de atividade por membro do Console e a única fonte que reporta uso de Cowork,
    então é a resposta autoritativa para "essa pessoa chegou a usar o Claude". Também cobre todos
    os membros da org, inclusive os ausentes da exportação de conversas.
    """
    files = sorted(glob.glob(str(DATA / "members-analytics-*.csv")))
    if not files:
        return {}, ""
    latest = files[-1]
    match = re.search(r'(\d{4}-\d{2}-\d{2})-to-(\d{4}-\d{2}-\d{2})', Path(latest).stem)
    period = f"{match.group(1)} → {match.group(2)}" if match else Path(latest).stem
    result = {}
    # utf-8-sig: o Console grava este arquivo com BOM, que senão corrompe o nome do primeiro
    # cabeçalho e torna a coluna "Name" inacessível.
    with open(latest, newline='', encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            email = row.get("Email", "").strip()
            if not email:
                continue
            result[email] = {
                "name": row.get("Name", "").strip(),
                "tier": row.get("Seat Tier", "").strip(),
                "role": row.get("Role", "").strip(),
                "last_active": row.get("Last Active", "").strip(),
                "days_active": _csv_int(row.get("Days Active")),
                "chats": _csv_int(row.get("Chats")),
                "messages": _csv_int(row.get("Messages")),
                "projects_created": _csv_int(row.get("Projects Created")),
                "projects_used": _csv_int(row.get("Projects Used")),
                "pull_requests": _csv_int(row.get("Pull Requests")),
                "code_sessions": _csv_int(row.get("Code sessions")),
                "file_edits": _csv_int(row.get("File Edits")),
                "cowork_sessions": _csv_int(row.get("Cowork Sessions")),
                "cowork_messages": _csv_int(row.get("Cowork Messages")),
                "artifacts": _csv_int(row.get("Artifacts Created")),
            }
    return result, period


def load_claude_code():
    """Carrega o claude_code_team_*.csv mais recente; devolve (linhas, string_do_período)."""
    files = sorted(glob.glob(str(DATA / "claude_code_team_*.csv")))
    if not files:
        return [], ""
    latest = files[-1]
    stem = Path(latest).stem
    match = re.search(r'(\d{4}_\d{2}_\d{2})_to_(\d{4}_\d{2}_\d{2})', stem)
    period = (f"{match.group(1).replace('_', '-')} → {match.group(2).replace('_', '-')}"
              if match else stem)
    rows = []
    with open(latest, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            email = row.get("User", "").strip()
            # "Lines this Month" é uma contagem inteira de linhas em formatação brasileira,
            # em que "." é o separador de milhar (ex.: "64.230" = 64.230 linhas,
            # "317" = 317 linhas). Remove os separadores para obter a contagem verdadeira e
            # depois expressa em milhares (K), como o resto do pipeline espera.
            raw = row.get("Lines this Month", "0").strip().replace(".", "")
            try:
                lines = int(raw) / 1000 if raw else 0.0
            except ValueError:
                lines = 0.0
            if email:
                rows.append({"email": email, "lines": lines})
    return rows, period
