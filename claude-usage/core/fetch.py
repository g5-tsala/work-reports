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
    with open(DATA / "conversations.json") as f:
        return json.load(f)


def load_members():
    """Load the most recent members-*.csv; returns email→{tier, role, status} map."""
    files = sorted(glob.glob(str(DATA / "members-*.csv")))
    if not files:
        return {}
    result = {}
    with open(files[-1], newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            email = row.get("Email", "").strip()
            if email:
                result[email] = {
                    "tier": row.get("Seat Tier", "").strip(),
                    "role": row.get("Role", "").strip(),
                    "status": row.get("Status", "").strip(),
                }
    return result


def load_claude_code():
    """Load the most recent claude_code_team_*.csv; returns (rows, period_string)."""
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
            # "Lines this Month" is a raw integer line count in Brazilian formatting,
            # where "." is the thousands separator (e.g. "64.230" = 64,230 lines,
            # "317" = 317 lines). Strip the separators to get the true count, then
            # express it in thousands (K) to match the rest of the pipeline.
            raw = row.get("Lines this Month", "0").strip().replace(".", "")
            try:
                lines = int(raw) / 1000 if raw else 0.0
            except ValueError:
                lines = 0.0
            if email:
                rows.append({"email": email, "lines": lines})
    return rows, period
