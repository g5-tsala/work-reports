from datetime import datetime

from .config import REPORTS
from .fetch import (load_users, load_members, load_memories, load_projects,
                    load_design_chats, load_conversations, load_claude_code)
from .metrics import compute_metrics
from .render import render_html


def main():
    """Load all source data, compute metrics, render HTML, and write the dated report file."""
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
