from datetime import datetime

from .config import REPORTS
from .fetch import (load_users, load_members, load_projects,
                    load_design_chats, load_conversations, load_claude_code,
                    load_members_analytics)
from .metrics import compute_metrics
from .render import render_html


def main():
    """Load all source data, compute metrics, render HTML, and write the dated report file."""
    print("Loading data...")
    users = load_users()
    members = load_members()
    projects = load_projects()
    design_chats = load_design_chats()

    print("Loading members analytics CSV...")
    analytics, analytics_period = load_members_analytics()

    print("Loading conversations batches (may take a moment)...")
    conversations = load_conversations()

    print("Loading Claude Code CSV...")
    claude_code_data, cc_period = load_claude_code()

    print("Computing metrics...")
    m = compute_metrics(users, members, projects, design_chats, conversations,
                        claude_code_data, cc_period, analytics, analytics_period)

    print("Rendering report...")
    html = render_html(m)

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"report-{datetime.now().strftime('%Y-%m-%d')}.html"
    out.write_text(html, encoding="utf-8")

    print(f"\n✓ Report written to {out}")
    print(f"  Period       : {m['date_start']} – {m['date_end']}")
    print(f"  Users        : {m['active_users']} active (any channel) / {m['total_users']} registered")
    print(f"  Inactive     : {len(m['inactive_rows'])} with zero chat, Cowork and Code")
    print(f"  Cowork       : {m['cowork_users']} users, {m['cowork_total_sessions']} sessions "
          f"({m['cowork_only_users']} would read as inactive without it)")
    print(f"  Conversations: {m['total_conversations']}")
    print(f"  Messages     : {m['total_messages']}")
    print(f"  Code/auto    : {m['cc_total_users']} users, {m['cc_total_calls']:,} tool calls")
    print(f"  Claude Code  : {m['cc_csv_users']} users, {m['cc_total_lines']:.1f} lines ({m['cc_period']})")
