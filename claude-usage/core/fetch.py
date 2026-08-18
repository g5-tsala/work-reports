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
    """Load and concatenate every conversations*.json batch in data/.

    The org export is delivered in batches (conversations-0001.json, -0002.json, …); a
    single-file export is just the one-batch case. Batches are loaded in filename order and
    flattened into one list, matching the shape _conversation_pass() expects.
    """
    conversations = []
    for path in sorted(glob.glob(str(DATA / "conversations*.json"))):
        with open(path) as f:
            conversations.extend(json.load(f))
    return conversations


def load_members():
    """Load the most recent members-*.csv; returns email→{tier, role, status} map."""
    # members-analytics-*.csv also matches "members-*"; it is a different schema loaded
    # separately by load_members_analytics(), so filter it out explicitly.
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
    """Parse an integer count from the analytics CSV, tolerating pt-BR thousands separators."""
    try:
        return int((raw or "0").strip().replace(".", "") or 0)
    except ValueError:
        return 0


def load_members_analytics():
    """Load the most recent members-analytics-*.csv; returns (email→metrics map, period string).

    This is the Console per-member activity export and the only source that reports Cowork
    usage, so it is the authoritative answer to "did this person use Claude at all". It also
    covers every org member, including those absent from the conversations export.
    """
    files = sorted(glob.glob(str(DATA / "members-analytics-*.csv")))
    if not files:
        return {}, ""
    latest = files[-1]
    match = re.search(r'(\d{4}-\d{2}-\d{2})-to-(\d{4}-\d{2}-\d{2})', Path(latest).stem)
    period = f"{match.group(1)} → {match.group(2)}" if match else Path(latest).stem
    result = {}
    # utf-8-sig: the Console writes this file with a BOM, which would otherwise corrupt
    # the first header name and make the "Name" column unreachable.
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
