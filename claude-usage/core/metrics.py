from collections import defaultdict, Counter
from datetime import datetime

from .config import CLAUDE_CODE_TOOLS


def parse_dt(s):
    """Parse an ISO-8601 datetime string, stripping timezone suffixes. Returns None on failure."""
    if not s:
        return None
    s = s.rstrip("Z").split("+")[0]
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def _filter_users(users, members):
    """Return (billable_users, email_to_tier), excluding Unassigned seats and removed members."""
    billable_uids = {
        uid for uid, u in users.items()
        if members.get(u["email_address"], {}).get("tier", "Unassigned") != "Unassigned"
    }
    filtered = {uid: u for uid, u in users.items() if uid in billable_uids}
    email_to_tier = {u["email_address"]: members[u["email_address"]]["tier"]
                     for u in filtered.values() if u["email_address"] in members}
    return filtered, email_to_tier


def _project_metrics(projects, design_chats, users):
    """Return (metrics_dict, proj_per_user counter) from project and design chat data."""
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

    proj_rows = []
    for uid, count in proj_per_user.most_common(10):
        user = users.get(uid, {})
        proj_rows.append({
            "name": user.get("full_name") or user.get("email_address", uid[:8]),
            "projects": count,
        })

    metrics = {
        "total_projects": len(projects),
        "proj_private": proj_private,
        "proj_public": len(projects) - proj_private,
        "proj_with_docs": proj_with_docs,
        "proj_with_artifacts": len([p for p in projects if p["uuid"] in dc_project_uuids]),
        "total_design_chats": len(design_chats),
        "proj_rows": proj_rows,
    }
    return metrics, proj_per_user


def _conversation_pass(conversations):
    """Single pass over all conversations; returns a dict of counters and sets for downstream use."""
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

    # Keys are Claude's internal content block types; MIME-style entries are artifact block types.
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

        conv_has_cc = False  # tracks whether this conv had any CC tool call; avoids counting one conv multiple times
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

    return {
        "active_users": active_users,
        "conv_dates": conv_dates,
        "daily_counts": daily_counts,
        "user_convs": user_convs,
        "user_human_msgs": user_human_msgs,
        "user_files": user_files,
        "user_last_active": user_last_active,
        "user_file_details": user_file_details,
        "feature_users": feature_users,
        "feature_convs": feature_convs,
        "feature_block_count": feature_block_count,
        "tool_name_counts": tool_name_counts,
        "cc_user_convs": cc_user_convs,
        "cc_user_calls": cc_user_calls,
        "cc_tool_breakdown": cc_tool_breakdown,
        "depth_buckets": depth_buckets,
        "total_messages": total_messages,
    }


def _build_user_rows(users, active_users, user_convs, proj_per_user,
                     user_human_msgs, user_files, user_last_active, email_to_tier):
    """Build the per-user activity table rows, limited to web-active users only."""
    rows = []
    for uid, user in users.items():
        if uid not in active_users:
            continue
        last = user_last_active.get(uid)
        email = user.get("email_address", "")
        rows.append({
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
    rows.sort(key=lambda r: r["conversations"], reverse=True)
    return rows


def _adoption_funnel(users, active_users, user_convs, memories, uid_cc_lines):
    """Return the adoption funnel as a list of (label, count) tuples.

    CC thresholds are in K lines; web thresholds are in conversation count — union lets either qualify.
    memories.keys() are account_uuids; intersect with funnel_active to exclude stale memory records.
    """
    # Values are in thousands (CSV column "Lines this Month" is already in K);
    # thresholds (1, 5, 10) therefore mean 1K, 5K, 10K lines.
    cc_funnel_active  = {uid for uid, l in uid_cc_lines.items() if l >= 1}
    cc_funnel_engaged = {uid for uid, l in uid_cc_lines.items() if l >= 5}
    cc_funnel_power   = {uid for uid, l in uid_cc_lines.items() if l >= 10}

    funnel_active  = active_users | cc_funnel_active
    funnel_engaged = {uid for uid, c in user_convs.items() if c >= 5} | cc_funnel_engaged
    funnel_power   = (set(memories.keys()) & funnel_active) | cc_funnel_power
    return [
        ("Registered", len(users)),
        ("Active (≥1 conv or ≥1K lines)", len(funnel_active)),
        ("Engaged (≥5 convs or ≥5K lines)", len(funnel_engaged)),
        ("Power users (memory or ≥10K lines)", len(funnel_power)),
    ]


def _feature_rows(feature_users, feature_convs, feature_block_count, active_users):
    """Return feature adoption rows in display order, skipping features with zero usage."""
    feature_order = [
        "Tool / Skill Calls", "Extended Thinking", "Code Generation",
        "Web Search", "Images", "Rich Content", "File Uploads", "Knowledge Base",
    ]
    rows = []
    for feat in feature_order:
        if feat in feature_users:
            rows.append({
                "feature": feat,
                "users": len(feature_users[feat]),
                "conversations": len(feature_convs[feat]),
                "total_instances": feature_block_count[feat],
                "pct_active_users": round(100 * len(feature_users[feat]) / len(active_users)) if active_users else 0,
            })
    return rows


def _cc_web_metrics(cc_user_calls, cc_user_convs, users):
    """Return Code & Automation metrics derived from tool_use blocks in the web export."""
    cc_rows = []
    for uid, call_count in cc_user_calls.most_common():
        user = users.get(uid, {})
        cc_rows.append({
            "name": user.get("full_name") or user.get("email_address", uid[:8]),
            "email": user.get("email_address", ""),
            "convs": cc_user_convs[uid],
            "calls": call_count,
        })
    return {
        "cc_rows": cc_rows,
        "cc_total_calls": sum(cc_user_calls.values()),
        "cc_total_users": len(cc_user_calls),
        "cc_tool_breakdown": cc_user_calls.most_common(),
    }


def _cc_csv_metrics(claude_code_data, users, user_convs, cc_period):
    """Return (metrics_dict, cc_uids) from the Anthropic Console Claude Code CSV export.

    cc_uids is the set of matched user UUIDs; needed by the caller to update the active_users KPI
    and exclude CLI-only users from the inactive list.
    """
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
    return {
        "cc_csv_rows": cc_csv_rows,
        "cc_total_lines": cc_total_lines,
        "cc_csv_users": len(cc_csv_rows),
        "cc_period": cc_period,
    }, cc_uids


def _inactive_rows(users, all_active, email_to_tier):
    """Return users with no web conversations and no Claude Code CLI activity, sorted by name."""
    rows = []
    for uid, user in users.items():
        if uid not in all_active:
            email = user.get("email_address", "")
            rows.append({
                "name": user.get("full_name") or "—",
                "email": email,
                "tier": email_to_tier.get(email, ""),
            })
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def compute_metrics(users, members, memories, projects, design_chats, conversations,
                    claude_code_data=None, cc_period=""):
    """Aggregate all source data into a flat metrics dict consumed by render_html.

    Delegates to private helpers for each logical section; this function is an orchestrator.
    Returns a dict with keys for KPIs, table rows, funnel, daily activity, and feature adoption.
    """
    users, email_to_tier = _filter_users(users, members)
    m = {"total_users": len(users)}

    # Values are in thousands (CSV column "Lines this Month" is already in K);
    # funnel thresholds below (1, 5, 10) therefore mean 1K, 5K, 10K lines.
    _email_to_uid = {u["email_address"]: uid for uid, u in users.items()}
    uid_cc_lines = {
        _email_to_uid[e["email"]]: e["lines"]
        for e in (claude_code_data or [])
        if e["email"] in _email_to_uid
    }

    proj_metrics, proj_per_user = _project_metrics(projects, design_chats, users)
    m.update(proj_metrics)

    conv = _conversation_pass(conversations)
    active_users = conv["active_users"]

    m["user_file_details"] = {
        uid: sorted(entries, key=lambda x: x["date"], reverse=True)
        for uid, entries in conv["user_file_details"].items()
    }
    m["active_users"] = len(active_users)
    m["total_conversations"] = len(conversations)
    m["total_messages"] = conv["total_messages"]
    m["avg_convs_per_active_user"] = round(len(conversations) / len(active_users), 1) if active_users else 0
    m["avg_msgs_per_conv"] = round(conv["total_messages"] / len(conversations), 1) if conversations else 0

    conv_dates = conv["conv_dates"]
    if conv_dates:
        m["date_start"] = min(conv_dates).strftime("%b %d, %Y")
        m["date_end"] = max(conv_dates).strftime("%b %d, %Y")
    else:
        m["date_start"] = m["date_end"] = "—"

    m["user_rows"] = _build_user_rows(
        users, active_users, conv["user_convs"], proj_per_user,
        conv["user_human_msgs"], conv["user_files"], conv["user_last_active"], email_to_tier,
    )
    m["funnel"] = _adoption_funnel(users, active_users, conv["user_convs"], memories, uid_cc_lines)

    daily_counts = conv["daily_counts"]
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

    m["feature_rows"] = _feature_rows(
        conv["feature_users"], conv["feature_convs"], conv["feature_block_count"], active_users,
    )
    m["top_tools"] = conv["tool_name_counts"].most_common(15)

    m.update(_cc_web_metrics(conv["cc_user_calls"], conv["cc_user_convs"], users))

    depth_order = ["1–2", "3–5", "6–10", "11–20", "21+"]
    m["depth_rows"] = [(b, conv["depth_buckets"][b]) for b in depth_order]

    cc_csv, cc_uids = _cc_csv_metrics(claude_code_data, users, conv["user_convs"], cc_period)
    m.update(cc_csv)
    # Overrides the earlier web-only count to include CLI-only users for the headline KPI.
    m["active_users"] = len(active_users | cc_uids)

    m["inactive_rows"] = _inactive_rows(users, active_users | cc_uids, email_to_tier)

    return m
