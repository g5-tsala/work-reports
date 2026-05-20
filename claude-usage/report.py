"""
G5 Partners — Claude Usage Executive Report
Reads source data from ./data/ and writes reports/report-YYYY-MM-DD.html.
"""

import csv
import json
import re
import glob
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
REPORTS = BASE / "reports"

CLAUDE_CODE_TOOLS = {"bash_tool", "view", "str_replace", "create_file", "str_replace_based_edit_tool"}


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

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
            try:
                lines = float(row.get("Lines this Month", 0))
            except ValueError:
                lines = 0.0
            if email:
                rows.append({"email": email, "lines": lines})
    return rows, period


# ---------------------------------------------------------------------------
# Metrics computation
# ---------------------------------------------------------------------------

def parse_dt(s):
    if not s:
        return None
    s = s.rstrip("Z").split("+")[0]
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def compute_metrics(users, members, memories, projects, design_chats, conversations,
                    claude_code_data=None, cc_period=""):
    m = {}

    # Filter out Unassigned seats and users removed from the org.
    # members is email→{tier, ...}; anyone absent or with tier "Unassigned" is excluded.
    billable_uids = {
        uid for uid, u in users.items()
        if members.get(u["email_address"], {}).get("tier", "Unassigned") != "Unassigned"
    }
    users = {uid: u for uid, u in users.items() if uid in billable_uids}
    email_to_tier = {u["email_address"]: members[u["email_address"]]["tier"]
                     for u in users.values() if u["email_address"] in members}

    m["total_users"] = len(users)

    # uid→lines map for Claude Code thresholds used in funnel
    _email_to_uid = {u["email_address"]: uid for uid, u in users.items()}
    uid_cc_lines = {
        _email_to_uid[e["email"]]: e["lines"]
        for e in (claude_code_data or [])
        if e["email"] in _email_to_uid
    }

    # --- Projects pass (needed for user_rows) ---
    proj_per_user = Counter()
    proj_with_docs = 0
    proj_private = 0
    for p in projects:
        creator_uuid = p.get("creator", {}).get("uuid", "")
        proj_per_user[creator_uuid] += 1
        if p.get("is_private"):
            proj_private += 1
        docs = [d for d in p.get("docs", []) if d.get("content") or d.get("filename")]
        if docs:
            proj_with_docs += 1

    dc_project_uuids = {dc.get("project", {}).get("uuid") for dc in design_chats}

    m["total_projects"] = len(projects)
    m["proj_private"] = proj_private
    m["proj_public"] = len(projects) - proj_private
    m["proj_with_docs"] = proj_with_docs
    m["proj_with_artifacts"] = len([p for p in projects if p["uuid"] in dc_project_uuids])
    m["total_design_chats"] = len(design_chats)

    proj_rows = []
    for uid, count in proj_per_user.most_common(10):
        user = users.get(uid, {})
        proj_rows.append({
            "name": user.get("full_name") or user.get("email_address", uid[:8]),
            "projects": count,
        })
    m["proj_rows"] = proj_rows

    # --- Conversations pass ---
    active_users = set()
    conv_dates = []
    daily_counts = Counter()

    user_convs = Counter()
    user_human_msgs = Counter()
    user_files = Counter()
    user_last_active = {}
    user_file_details = defaultdict(list)

    feature_users = defaultdict(set)
    feature_convs = defaultdict(set)
    feature_block_count = Counter()

    tool_name_counts = Counter()

    cc_user_convs = Counter()
    cc_user_calls = Counter()
    cc_tool_breakdown = Counter()

    depth_buckets = Counter()
    total_messages = 0

    FEATURE_MAP = {
        "tool_use":                    "Tool / Skill Calls",
        "thinking":                    "Extended Thinking",
        "code_block":                  "Code Generation",
        "application/vnd.ant.code":    "Code Generation",
        "web_search_citation":         "Web Search",
        "webpage_metadata":            "Web Search",
        "image":                       "Images",
        "image_gallery":               "Images",
        "rich_content":                "Rich Content",
        "table":                       "Rich Content",
        "json_block":                  "Rich Content",
        "knowledge":                   "Knowledge Base",
    }

    for conv in conversations:
        uid = conv["account"]["uuid"]
        cid = conv["uuid"]
        active_users.add(uid)
        user_convs[uid] += 1

        dt = parse_dt(conv.get("created_at"))
        if dt:
            conv_dates.append(dt)
            daily_counts[dt.strftime("%Y-%m-%d")] += 1

        upd = parse_dt(conv.get("updated_at"))
        if upd and (uid not in user_last_active or upd > user_last_active[uid]):
            user_last_active[uid] = upd

        msgs = conv.get("chat_messages", [])
        total_messages += len(msgs)

        n = len(msgs)
        if n <= 2:
            depth_buckets["1–2"] += 1
        elif n <= 5:
            depth_buckets["3–5"] += 1
        elif n <= 10:
            depth_buckets["6–10"] += 1
        elif n <= 20:
            depth_buckets["11–20"] += 1
        else:
            depth_buckets["21+"] += 1

        conv_has_cc = False
        for msg in msgs:
            if msg.get("sender") == "human":
                user_human_msgs[uid] += 1

            files = msg.get("files", [])
            if files:
                user_files[uid] += len(files)
                feature_users["File Uploads"].add(uid)
                feature_convs["File Uploads"].add(cid)
                feature_block_count["File Uploads"] += len(files)
                msg_dt_raw = msg.get("created_at") or ""
                msg_dt = parse_dt(msg_dt_raw)
                msg_datetime = msg_dt.strftime("%Y-%m-%d %H:%M") if msg_dt else msg_dt_raw[:16]
                conv_name = conv.get("name") or "(untitled)"
                for fi in files:
                    user_file_details[uid].append({
                        "name": fi.get("file_name") or "(unnamed)",
                        "date": msg_datetime,
                        "conv": conv_name,
                    })

            for block in msg.get("content", []):
                btype = block.get("type", "")

                feat = FEATURE_MAP.get(btype)
                if feat:
                    feature_users[feat].add(uid)
                    feature_convs[feat].add(cid)
                    feature_block_count[feat] += 1

                if btype == "tool_use":
                    tname = block.get("name", "")
                    iname = block.get("integration_name") or ""
                    if tname:
                        label = f"{iname} / {tname}" if iname else tname
                        tool_name_counts[label] += 1
                    if tname in CLAUDE_CODE_TOOLS:
                        cc_user_calls[uid] += 1
                        cc_tool_breakdown[tname] += 1
                        conv_has_cc = True

        if conv_has_cc:
            cc_user_convs[uid] += 1

    m["user_file_details"] = {
        uid: sorted(entries, key=lambda x: x["date"], reverse=True)
        for uid, entries in user_file_details.items()
    }
    m["active_users"] = len(active_users)
    m["total_conversations"] = len(conversations)
    m["total_messages"] = total_messages
    m["avg_convs_per_active_user"] = round(len(conversations) / len(active_users), 1) if active_users else 0
    m["avg_msgs_per_conv"] = round(total_messages / len(conversations), 1) if conversations else 0

    if conv_dates:
        m["date_start"] = min(conv_dates).strftime("%b %d, %Y")
        m["date_end"] = max(conv_dates).strftime("%b %d, %Y")
    else:
        m["date_start"] = m["date_end"] = "—"

    # --- User activity table ---
    user_rows = []
    for uid, user in users.items():
        if uid not in active_users:
            continue
        last = user_last_active.get(uid)
        email = user.get("email_address", "")
        user_rows.append({
            "uid": uid,
            "name": user.get("full_name") or email,
            "email": email,
            "tier": email_to_tier.get(email, ""),
            "conversations": user_convs[uid],
            "projects": proj_per_user.get(uid, 0),
            "human_msgs": user_human_msgs[uid],
            "files_uploaded": user_files[uid],
            "last_active": last.strftime("%Y-%m-%d %H:%M") if last else "—",
            "last_active_ts": last.timestamp() if last else 0,
        })
    user_rows.sort(key=lambda r: r["conversations"], reverse=True)
    m["user_rows"] = user_rows

    # --- Adoption funnel ---
    cc_funnel_active  = {uid for uid, l in uid_cc_lines.items() if l >= 1}
    cc_funnel_engaged = {uid for uid, l in uid_cc_lines.items() if l >= 5}
    cc_funnel_power   = {uid for uid, l in uid_cc_lines.items() if l >= 10}

    funnel_active  = active_users | cc_funnel_active
    funnel_engaged = {uid for uid, c in user_convs.items() if c >= 5} | cc_funnel_engaged
    funnel_power   = (set(memories.keys()) & funnel_active) | cc_funnel_power
    m["funnel"] = [
        ("Registered", len(users)),
        ("Active (≥1 conv or ≥1K lines)", len(funnel_active)),
        ("Engaged (≥5 convs or ≥5K lines)", len(funnel_engaged)),
        ("Power users (memory or ≥10K lines)", len(funnel_power)),
    ]

    # --- Daily activity ---
    if daily_counts:
        all_days = sorted(daily_counts.keys())
        max_count = max(daily_counts.values())
        m["daily_activity"] = [(d, daily_counts[d], max_count) for d in all_days]
        m["most_active_day"] = max(daily_counts, key=daily_counts.get)
        m["most_active_day_count"] = daily_counts[m["most_active_day"]]
    else:
        m["daily_activity"] = []
        m["most_active_day"] = "—"
        m["most_active_day_count"] = 0

    # --- Feature adoption ---
    feature_order = [
        "Tool / Skill Calls", "Extended Thinking", "Code Generation",
        "Web Search", "Images", "Rich Content", "File Uploads", "Knowledge Base",
    ]
    feature_rows = []
    for feat in feature_order:
        if feat in feature_users:
            feature_rows.append({
                "feature": feat,
                "users": len(feature_users[feat]),
                "conversations": len(feature_convs[feat]),
                "total_instances": feature_block_count[feat],
                "pct_active_users": round(100 * len(feature_users[feat]) / len(active_users)) if active_users else 0,
            })
    m["feature_rows"] = feature_rows

    m["top_tools"] = tool_name_counts.most_common(15)

    # --- Code & Automation ---
    cc_rows = []
    for uid, call_count in cc_user_calls.most_common():
        user = users.get(uid, {})
        cc_rows.append({
            "name": user.get("full_name") or user.get("email_address", uid[:8]),
            "email": user.get("email_address", ""),
            "convs": cc_user_convs[uid],
            "calls": call_count,
        })
    m["cc_rows"] = cc_rows
    m["cc_total_calls"] = sum(cc_user_calls.values())
    m["cc_total_users"] = len(cc_user_calls)
    m["cc_tool_breakdown"] = cc_tool_breakdown.most_common()

    # --- Conversation depth ---
    depth_order = ["1–2", "3–5", "6–10", "11–20", "21+"]
    m["depth_rows"] = [(b, depth_buckets[b]) for b in depth_order]

    # --- Claude Code (from CSV) ---
    email_to_user = {u["email_address"]: u for u in users.values()}
    cc_csv_rows = []
    cc_total_lines = 0.0
    cc_uids = set()
    for entry in (claude_code_data or []):
        email = entry["email"]
        lines = entry["lines"]
        cc_total_lines += lines
        user = email_to_user.get(email, {})
        uid = user.get("uuid", "")
        if uid:
            cc_uids.add(uid)
        cc_csv_rows.append({
            "name": user.get("full_name") or email,
            "email": email,
            "lines": lines,
            "web_convs": user_convs.get(uid, 0),
        })
    cc_csv_rows.sort(key=lambda r: r["lines"], reverse=True)
    m["cc_csv_rows"] = cc_csv_rows
    m["cc_total_lines"] = cc_total_lines
    m["cc_csv_users"] = len(cc_csv_rows)
    m["cc_period"] = cc_period
    m["active_users"] = len(active_users | cc_uids)

    # --- Inactive users (excludes anyone active on web OR Claude Code) ---
    all_active = active_users | cc_uids
    inactive_rows = []
    for uid, user in users.items():
        if uid not in all_active:
            email = user.get("email_address", "")
            inactive_rows.append({
                "name": user.get("full_name") or "—",
                "email": email,
                "tier": email_to_tier.get(email, ""),
            })
    inactive_rows.sort(key=lambda r: r["name"].lower())
    m["inactive_rows"] = inactive_rows

    return m


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Source+Serif+4:wght@400;600&display=swap');

:root {
  --g5-navy: #0B2A57;
  --g5-wine: #8B1F3F;
  --g5-ink: #1A1A1A;
  --g5-graphite: #4A4A4A;
  --g5-slate: #8A8A8A;
  --g5-line: #D9DDE3;
  --g5-bg-soft: #F4F6F9;
  --g5-bg-band: #E8ECF1;
  --g5-white: #FFFFFF;
  --g5-data-blue: #1E4D8C;
  --g5-data-wine: #A8344E;
  --g5-data-neutral: #9AA3B0;
  --g5-shadow-card: 0 1px 3px rgba(11,42,87,0.06);
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Inter", -apple-system, "Segoe UI", sans-serif;
       background: var(--g5-bg-soft); color: var(--g5-ink); font-size: 14px; }

.g5-topband { background: var(--g5-navy); padding: 14px 48px;
              display: flex; align-items: center; justify-content: space-between; }
.g5-band-org { font: 600 12px/1 "Inter", sans-serif; letter-spacing: 0.1em;
               text-transform: uppercase; color: var(--g5-white); }
.g5-band-meta { font: 400 11px/1 "Inter", sans-serif; color: rgba(255,255,255,0.55);
                text-transform: uppercase; letter-spacing: 0.06em; }

.wrapper { max-width: 1100px; margin: 0 auto; padding: 40px 32px 48px; }

.page-title { font: 400 34px/1.2 "Source Serif 4", Georgia, serif;
              color: var(--g5-navy); margin-bottom: 4px; }
.page-subtitle { font: 400 11px/1 "Inter", sans-serif; color: var(--g5-slate);
                 text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 36px; }

.section { background: var(--g5-white); border: 1px solid var(--g5-line);
           border-radius: 2px; padding: 28px; margin-bottom: 20px; }

h2 { font: 600 12px/1.2 "Inter", sans-serif; text-transform: uppercase;
     letter-spacing: 0.08em; color: var(--g5-navy); margin-bottom: 20px;
     position: relative; padding-bottom: 12px; }
h2::after { content: ""; position: absolute; left: 0; bottom: 0;
            width: 32px; height: 2px; background: var(--g5-wine); }

.kpi-row { display: grid; gap: 12px; margin-bottom: 12px; }
.kpi-row:last-child { margin-bottom: 0; }
.kpi-row-2 { grid-template-columns: repeat(2, 1fr); }
.kpi-row-3 { grid-template-columns: repeat(3, 1fr); }
.kpi { background: var(--g5-bg-soft); border: 1px solid var(--g5-line);
       border-radius: 2px; padding: 18px 14px; text-align: center; }
.kpi .val { font: 600 30px/1 "Inter", sans-serif; color: var(--g5-navy);
            font-variant-numeric: tabular-nums; letter-spacing: -0.01em; }
.kpi .lbl { font: 400 10px/1 "Inter", sans-serif; color: var(--g5-slate);
            text-transform: uppercase; letter-spacing: 0.06em; margin-top: 6px; }

table { width: 100%; border-collapse: collapse;
        font: 400 13px/1.5 "Inter", sans-serif; color: var(--g5-ink);
        font-variant-numeric: tabular-nums; }
th { background: var(--g5-navy); color: var(--g5-white); font-weight: 600;
     font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em;
     padding: 10px 14px; text-align: left; white-space: nowrap; }
th.sortable { cursor: pointer; user-select: none; }
th.sortable:hover { background: #0d3268; }
th.sortable::after { content: ' ⇅'; opacity: .4; font-size: 9px; }
th.sort-asc::after { content: ' ↑'; opacity: 1; }
th.sort-desc::after { content: ' ↓'; opacity: 1; }
td { padding: 9px 14px; border-bottom: 1px solid var(--g5-line); }
tbody tr:nth-child(even) td { background: var(--g5-bg-soft); }
tbody tr:last-child td { border-bottom: none; }
tbody tr:hover td { background: var(--g5-bg-band); }

.bar-wrap { display: flex; align-items: center; gap: 8px; }
.bar { height: 10px; background: var(--g5-data-blue); border-radius: 1px; min-width: 2px; }
.bar-lbl { font: 400 12px/1 "Inter", sans-serif; color: var(--g5-graphite); white-space: nowrap; }

.chart { display:flex; align-items:flex-end; gap:2px; height:165px; padding-bottom:55px; }
.ccol { display:flex; flex-direction:column; align-items:center; justify-content:flex-end;
        flex:1; height:100%; cursor:default; }
.cbar { width:100%; background:var(--g5-data-blue); border-radius:1px 1px 0 0;
        min-height:2px; position:relative; }
.ccol:hover .cbar { background: var(--g5-navy); }
.ctop { position:absolute; top:-13px; left:0; right:0; text-align:center;
        font:400 8px/1 "Inter",sans-serif; color:var(--g5-graphite); white-space:nowrap; }
.clbl { font:400 8px/1 "Inter",sans-serif; color:var(--g5-slate); margin-top:25px;
        white-space:nowrap; line-height:1; transform:rotate(-45deg); transform-origin:top left; }

.funnel-row { display: flex; align-items: center; margin-bottom: 10px; gap: 14px; }
.funnel-bar { height: 24px; background: var(--g5-data-blue); border-radius: 1px; min-width: 4px; }
.funnel-lbl { font: 400 13px/1 "Inter", sans-serif; color: var(--g5-graphite); white-space: nowrap; }
.funnel-val { font: 600 14px/1 "Inter", sans-serif; color: var(--g5-navy);
              margin-left: auto; white-space: nowrap; font-variant-numeric: tabular-nums; }

.tag { display: inline-block; padding: 2px 8px; border: 1px solid var(--g5-line);
       border-radius: 2px; font: 600 11px/1.6 "Inter", sans-serif; color: var(--g5-navy);
       font-variant-numeric: tabular-nums; }

#user-table th { white-space: normal; vertical-align: bottom; }

.tier-badge { display: inline-block; padding: 2px 8px; border-radius: 2px;
              font: 600 10px/1.6 "Inter", sans-serif; text-transform: uppercase;
              letter-spacing: 0.05em; white-space: nowrap; }
.tier-premium { background: #FDF3E3; color: #8B5E1A; border: 1px solid #E8C97A; }
.tier-standard { background: var(--g5-bg-soft); color: var(--g5-graphite); border: 1px solid var(--g5-line); }

.note { font: 400 12px/1.5 "Inter", sans-serif; color: var(--g5-graphite);
        background: var(--g5-bg-band); border: 1px solid var(--g5-line);
        border-radius: 2px; padding: 10px 14px; margin-bottom: 16px; }

.g5-footer { background: var(--g5-navy); color: rgba(255,255,255,0.5);
             text-align: center; font: 400 11px/1 "Inter", sans-serif;
             padding: 28px; letter-spacing: 0.06em; text-transform: uppercase; }

.clickable { cursor: pointer; color: var(--g5-data-blue); font-weight: 600;
             border-bottom: 1px dotted var(--g5-data-blue); }
.clickable:hover { color: var(--g5-navy); border-bottom-color: var(--g5-navy); }

.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(11,42,87,.5);
                 z-index: 1000; align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal { background: var(--g5-white); border: 1px solid var(--g5-line); border-radius: 2px;
         padding: 28px; width: 760px; max-width: 95vw; max-height: 80vh;
         display: flex; flex-direction: column; box-shadow: 0 8px 32px rgba(11,42,87,0.16); }
.modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
.modal-title { font: 600 14px/1 "Inter", sans-serif; color: var(--g5-navy); }
.modal-close { background: none; border: none; font-size: 18px; cursor: pointer;
               color: var(--g5-slate); padding: 4px 8px; border-radius: 2px; }
.modal-close:hover { background: var(--g5-bg-soft); }
.modal-search { width: 100%; padding: 8px 12px; border: 1px solid var(--g5-line);
                border-radius: 2px; font: 400 13px/1 "Inter", sans-serif;
                color: var(--g5-ink); margin-bottom: 14px; outline: none; }
.modal-search:focus { border-color: var(--g5-navy); }
.modal-body { overflow-y: auto; flex: 1; }
.modal-body table { width: 100%; }
.modal-body th { position: sticky; top: 0; z-index: 1; }
.no-results { text-align: center; color: var(--g5-slate); padding: 24px; font-size: 13px; }

@media (max-width: 1200px) {
  .wrapper { padding: 32px 20px 48px; }
}
@media (max-width: 1100px) {
  .g5-topband { padding: 12px 24px; }
  .wrapper { padding: 28px 16px 40px; }
  .kpi-row-3 { grid-template-columns: repeat(2, 1fr); }
  .section { overflow-x: auto; }
}
@media (max-width: 960px) {
  .g5-topband { padding: 10px 16px; }
  .g5-band-meta { display: none; }
  .wrapper { padding: 24px 12px 36px; }
  .page-title { font-size: 26px; }
  .section { padding: 18px 14px; }
  .kpi-row-2, .kpi-row-3 { grid-template-columns: 1fr 1fr; }
  th, td { padding: 8px 10px; }
  table[style*="width:50%"] { width: 100% !important; }
}
"""


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def kpi_card(val, label):
    return f'<div class="kpi"><div class="val">{esc(val)}</div><div class="lbl">{esc(label)}</div></div>'


def bar_row(day, count, max_count, bar_width=220):
    w = max(2, int(bar_width * count / max_count)) if max_count else 2
    return (f'<tr><td style="color:#64748b;font-size:12px;white-space:nowrap">{esc(day)}</td>'
            f'<td><div class="bar-wrap"><div class="bar" style="width:{w}px"></div>'
            f'<span class="bar-lbl">{count}</span></div></td></tr>')


def render_html(m):
    generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    # KPI rows — 3 rows
    row1 = (kpi_card(m["total_users"], "Registered Users") +
            kpi_card(m["active_users"], "Active Users"))
    row2 = (kpi_card(m["total_projects"], "Projects") +
            kpi_card(m["total_conversations"], "Conversations") +
            kpi_card(m["total_messages"], "Messages"))
    row3 = (kpi_card(m["avg_convs_per_active_user"], "Avg Convs / Active User") +
            kpi_card(m["avg_msgs_per_conv"], "Avg Msgs / Conv"))

    # User activity table — sortable
    user_table_rows = ""
    for r in m["user_rows"]:
        files_cell = (
            f'<span class="clickable" onclick="openModal(\'{esc(r["uid"])}\',\'{esc(r["name"])}\')">'
            f'{r["files_uploaded"]}</span>'
            if r["files_uploaded"] else "—"
        )
        tier = r.get("tier", "")
        tier_cls = "tier-premium" if tier.lower() == "premium" else "tier-standard"
        tier_cell = f'<span class="tier-badge {tier_cls}">{esc(tier)}</span>' if tier else "—"
        user_table_rows += (
            f'<tr>'
            f'<td data-val="{esc(r["name"])}">{esc(r["name"])}</td>'
            f'<td style="color:#64748b;font-size:12px" data-val="{esc(r["email"])}">{esc(r["email"])}</td>'
            f'<td style="text-align:center" data-val="{esc(tier)}">{tier_cell}</td>'
            f'<td style="text-align:center" data-val="{r["conversations"]}"><span class="tag">{r["conversations"]}</span></td>'
            f'<td style="text-align:center" data-val="{r["projects"]}">{r["projects"] or "—"}</td>'
            f'<td style="text-align:center" data-val="{r["human_msgs"]}">{r["human_msgs"]}</td>'
            f'<td style="text-align:center" data-val="{r["files_uploaded"]}">{files_cell}</td>'
            f'<td style="color:var(--g5-slate);font-size:11px" data-val="{r["last_active_ts"]}">{esc(r["last_active"])}</td>'
            f'</tr>'
        )

    # Claude Code section
    cc_period_note = f"Period: <strong>{esc(m['cc_period'])}</strong>. " if m["cc_period"] else ""
    if m["cc_csv_rows"]:
        max_cc_lines = m["cc_csv_rows"][0]["lines"] if m["cc_csv_rows"] else 1
        cc_table_rows = ""
        for i, r in enumerate(m["cc_csv_rows"], 1):
            pct = round(100 * r["lines"] / max_cc_lines) if max_cc_lines else 0
            web = r["web_convs"] if r["web_convs"] else "—"
            cc_table_rows += (
                f'<tr>'
                f'<td style="color:var(--g5-slate);text-align:center;white-space:nowrap">{i}</td>'
                f'<td style="white-space:nowrap">{esc(r["name"])}</td>'
                f'<td style="color:var(--g5-slate);font-size:12px;white-space:nowrap">{esc(r["email"])}</td>'
                f'<td style="width:100%"><div class="bar-wrap" style="width:100%">'
                f'<div class="bar" style="width:{pct}%;background:var(--g5-data-wine);flex-shrink:0"></div>'
                f'<span class="bar-lbl">{r["lines"]:.1f}K</span>'
                f'</div></td>'
                f'<td style="text-align:center;color:var(--g5-slate);white-space:nowrap">{web}</td>'
                f'</tr>'
            )
        cc_kpi_row = (
            kpi_card(m["cc_csv_users"], "Claude Code Users") +
            kpi_card(f'{m["cc_total_lines"]:.1f}K', "Total Lines this Month")
        )
        cc_section = f"""
  <!-- Claude Code -->
  <div class="section">
    <h2>Claude Code</h2>
    <div class="kpi-row kpi-row-2" style="margin-bottom:18px">{cc_kpi_row}</div>
    <p class="note">
      {cc_period_note}Data from Anthropic Console team export.
      <strong>Lines this Month</strong> measures code generated or modified via the Claude Code CLI.
      <em>Web Conversations</em> cross-references activity in the claude.ai export —
      CLI and web usage are independent channels.
    </p>
    <table>
      <thead><tr>
        <th style="width:32px">#</th><th>Name</th><th>Email</th>
        <th style="width:100%">Lines this Month</th>
        <th style="text-align:center">Web Conversations</th>
      </tr></thead>
      <tbody>{cc_table_rows}</tbody>
    </table>
  </div>"""
    else:
        cc_section = ""

    # Adoption funnel
    max_funnel = m["funnel"][0][1] if m["funnel"] else 1
    funnel_html = ""
    for label, val in m["funnel"]:
        w = max(4, int(500 * val / max_funnel)) if max_funnel else 4
        funnel_html += (
            f'<div class="funnel-row">'
            f'<div class="funnel-bar" style="width:{w}px"></div>'
            f'<span class="funnel-lbl">{esc(label)}</span>'
            f'<span class="funnel-val">{val}</span>'
            f'</div>'
        )

    chart_bars = ""
    for d, c, mx in m["daily_activity"]:
        h = max(2, round(90 * c / mx)) if mx else 2
        dt_obj = datetime.strptime(d, "%Y-%m-%d")
        lbl = f"{dt_obj.day:02d}/{dt_obj.month:02d}"
        chart_bars += (
            f'<div class="ccol" title="{d}: {c} conversations">'
            f'<div class="cbar" style="height:{h}%">'
            f'<div class="ctop">{c}</div>'
            f'</div>'
            f'<div class="clbl">{lbl}</div>'
            f'</div>'
        )

    depth_total = sum(c for _, c in m["depth_rows"])
    max_depth = max((c for _, c in m["depth_rows"]), default=1)
    depth_rows = ""
    for bucket, cnt in m["depth_rows"]:
        pct_label = round(100 * cnt / depth_total) if depth_total else 0
        pct_bar = round(100 * cnt / max_depth) if max_depth else 0
        depth_rows += (
            f'<tr><td style="white-space:nowrap">{esc(bucket)} messages</td>'
            f'<td style="width:100%"><div class="bar-wrap" style="width:100%">'
            f'<div class="bar" style="width:{pct_bar}%;background:var(--g5-data-blue);min-width:2px"></div>'
            f'<span class="bar-lbl" style="white-space:nowrap;flex-shrink:0">{cnt} ({pct_label}%)</span></div></td></tr>'
        )

    # Inactive users
    def tier_badge(tier):
        if not tier:
            return "—"
        cls = "tier-premium" if tier.lower() == "premium" else "tier-standard"
        return f'<span class="tier-badge {cls}">{esc(tier)}</span>'

    inactive_rows_html = "".join(
        f'<tr><td>{esc(r["name"])}</td>'
        f'<td style="color:#64748b;font-size:12px">{esc(r["email"])}</td>'
        f'<td style="text-align:center">{tier_badge(r.get("tier",""))}</td></tr>'
        for r in m["inactive_rows"]
    )

    file_data_json = json.dumps(m["user_file_details"], ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>G5 Partners — Claude Usage Report</title>
<style>{CSS}</style>
</head>
<body>

<div class="g5-topband">
  <span class="g5-band-org">G5 Partners</span>
  <span class="g5-band-meta">Claude Usage Report &nbsp;·&nbsp; {esc(m["date_start"])} – {esc(m["date_end"])}</span>
</div>

<div class="wrapper">

  <h1 class="page-title">Claude Usage Report</h1>
  <p class="page-subtitle">Period: {esc(m["date_start"])} – {esc(m["date_end"])} &nbsp;·&nbsp; Generated {esc(generated)}</p>

  <!-- KPIs -->
  <div class="section">
    <h2>Overview</h2>
    <div class="kpi-row kpi-row-2">{row1}</div>
    <div class="kpi-row kpi-row-3">{row2}</div>
    <div class="kpi-row kpi-row-2">{row3}</div>
  </div>

  <!-- User Activity -->
  <div class="section">
    <h2>User Activity</h2>
    <p class="note">
      <strong>Files Uploaded</strong> counts are inflated: when a PDF or PowerPoint is uploaded,
      Claude converts each page or slide into a separate image file, so a 30-page document counts as 30 uploads.
    </p>
    <div style="overflow-x:auto">
    <table id="user-table">
      <thead><tr>
        <th class="sortable" data-col="0" data-type="str">Name</th>
        <th class="sortable" data-col="1" data-type="str">Email</th>
        <th class="sortable" data-col="2" data-type="str" style="text-align:center">Tier</th>
        <th class="sortable" data-col="3" data-type="num" style="text-align:center">Conversations</th>
        <th class="sortable" data-col="4" data-type="num" style="text-align:center">Projects</th>
        <th class="sortable" data-col="5" data-type="num" style="text-align:center">Messages Sent</th>
        <th class="sortable" data-col="6" data-type="num" style="text-align:center">Files Uploaded</th>
        <th class="sortable" data-col="7" data-type="num">Last Active</th>
      </tr></thead>
      <tbody>{user_table_rows}</tbody>
    </table>
    </div>
  </div>

  {cc_section}

  <!-- Inactive Accounts -->
  <div class="section">
    <h2>Inactive Accounts</h2>
    <p class="note">
      These {len(m["inactive_rows"])} users are registered on the org account but had no activity
      in this period — neither web conversations nor Claude Code CLI usage.
    </p>
    <table style="width:auto">
      <thead><tr><th>Name</th><th>Email</th><th style="text-align:center">Tier</th></tr></thead>
      <tbody>{inactive_rows_html}</tbody>
    </table>
  </div>

  <!-- Adoption Funnel -->
  <div class="section">
    <h2>Adoption Funnel</h2>
    {funnel_html}
  </div>

  <!-- Daily Activity -->
  <div class="section">
    <h2>Daily Conversation Volume</h2>
    <p style="font-size:12px;color:#64748b;margin-bottom:14px">
      Most active day: <strong>{esc(m["most_active_day"])}</strong>
      ({m["most_active_day_count"]} conversations)
    </p>
    <div class="chart">{chart_bars}</div>
  </div>

  <!-- Conversation Depth -->
  <div class="section">
    <h2>Conversation Depth Distribution</h2>
    <table style="width:50%">
      <thead><tr><th>Length</th><th style="width:100%">Conversations</th></tr></thead>
      <tbody>{depth_rows}</tbody>
    </table>
  </div>

</div>

<footer class="g5-footer">G5 Partners &nbsp;·&nbsp; Claude Admin Export &nbsp;·&nbsp; {esc(generated)}</footer>

<!-- File uploads modal -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModalOnBg(event)">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title" id="modal-title"></span>
      <button class="modal-close" onclick="closeModal()">&#x2715;</button>
    </div>
    <input class="modal-search" id="modal-search" type="text"
           placeholder="Filter by file name or conversation…" oninput="filterModal()">
    <div class="modal-body">
      <table>
        <thead><tr>
          <th>Date &amp; Time</th>
          <th>File Name</th>
          <th>Conversation</th>
        </tr></thead>
        <tbody id="modal-tbody"></tbody>
      </table>
      <p class="no-results" id="modal-no-results" style="display:none">No files match your filter.</p>
    </div>
  </div>
</div>

<script>
const FILE_DATA = {file_data_json};

let _currentFiles = [];

function openModal(uid, name) {{
  _currentFiles = FILE_DATA[uid] || [];
  document.getElementById('modal-title').textContent =
    name + ' — ' + _currentFiles.length + ' file upload' + (_currentFiles.length !== 1 ? 's' : '');
  document.getElementById('modal-search').value = '';
  document.getElementById('modal-overlay').classList.add('open');
  renderRows(_currentFiles);
  setTimeout(() => document.getElementById('modal-search').focus(), 50);
}}

function closeModal() {{
  document.getElementById('modal-overlay').classList.remove('open');
}}

function closeModalOnBg(e) {{
  if (e.target === document.getElementById('modal-overlay')) closeModal();
}}

document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

function escHtml(s) {{
  return (s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}

function renderRows(rows) {{
  const tbody = document.getElementById('modal-tbody');
  const noRes = document.getElementById('modal-no-results');
  if (!rows.length) {{ tbody.innerHTML = ''; noRes.style.display = ''; return; }}
  noRes.style.display = 'none';
  tbody.innerHTML = rows.map(r =>
    '<tr>' +
    '<td style="white-space:nowrap;color:var(--g5-slate);font-size:11px">' + escHtml(r.date) + '</td>' +
    '<td style="font-family:monospace;font-size:12px">' + escHtml(r.name) + '</td>' +
    '<td style="color:#64748b;font-size:12px">' + escHtml(r.conv) + '</td>' +
    '</tr>'
  ).join('');
}}

function filterModal() {{
  const q = document.getElementById('modal-search').value.toLowerCase();
  if (!q) {{ renderRows(_currentFiles); return; }}
  renderRows(_currentFiles.filter(r =>
    (r.name || '').toLowerCase().includes(q) ||
    (r.conv || '').toLowerCase().includes(q)
  ));
}}

// Table sorting
(function() {{
  const table = document.getElementById('user-table');
  let sortCol = -1, sortAsc = true;

  table.querySelectorAll('th.sortable').forEach(th => {{
    th.addEventListener('click', () => {{
      const col = +th.dataset.col;
      const type = th.dataset.type;
      if (sortCol === col) sortAsc = !sortAsc; else {{ sortCol = col; sortAsc = true; }}

      table.querySelectorAll('th').forEach(h => h.classList.remove('sort-asc','sort-desc'));
      th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');

      const tbody = table.querySelector('tbody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {{
        const av = a.cells[col].dataset.val;
        const bv = b.cells[col].dataset.val;
        let cmp;
        if (type === 'num') cmp = (+av || 0) - (+bv || 0);
        else cmp = av.localeCompare(bv, undefined, {{sensitivity:'base'}});
        return sortAsc ? cmp : -cmp;
      }});
      rows.forEach(r => tbody.appendChild(r));
    }});
  }});
}})();
</script>
</body>
</html>"""
    return html


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading data...")
    users = load_users()
    members = load_members()
    memories = load_memories()
    projects = load_projects()
    design_chats = load_design_chats()

    print("Loading conversations.json (may take a moment)...")
    conversations = load_conversations()

    print("Loading Claude Code CSV...")
    claude_code_data, cc_period = load_claude_code()

    print("Computing metrics...")
    m = compute_metrics(users, members, memories, projects, design_chats, conversations,
                        claude_code_data, cc_period)

    print("Rendering report...")
    html = render_html(m)

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"report-{datetime.now().strftime('%Y-%m-%d')}.html"
    out.write_text(html, encoding="utf-8")

    print(f"\n✓ Report written to {out}")
    print(f"  Period       : {m['date_start']} – {m['date_end']}")
    print(f"  Users        : {m['active_users']} active / {m['total_users']} registered")
    print(f"  Conversations: {m['total_conversations']}")
    print(f"  Messages     : {m['total_messages']}")
    print(f"  Code/auto    : {m['cc_total_users']} users, {m['cc_total_calls']:,} tool calls")
    print(f"  Claude Code  : {m['cc_csv_users']} users, {m['cc_total_lines']:.1f} lines ({m['cc_period']})")


if __name__ == "__main__":
    main()
