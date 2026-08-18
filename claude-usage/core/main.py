from datetime import datetime

from .config import REPORTS
from .fetch import (load_users, load_members, load_projects,
                    load_design_chats, load_conversations, load_claude_code,
                    load_members_analytics)
from .metrics import compute_metrics
from .render import render_html, fmt_dec, fmt_int


def main():
    """Carrega os dados de origem, calcula as métricas, renderiza o HTML e escreve o relatório datado."""
    print("Carregando dados...")
    users = load_users()
    members = load_members()
    projects = load_projects()
    design_chats = load_design_chats()

    print("Carregando CSV de members analytics...")
    analytics, analytics_period = load_members_analytics()

    print("Carregando lotes de conversas (pode demorar um pouco)...")
    conversations = load_conversations()

    print("Carregando CSV do Claude Code...")
    claude_code_data, cc_period = load_claude_code()

    print("Calculando métricas...")
    m = compute_metrics(users, members, projects, design_chats, conversations,
                        claude_code_data, cc_period, analytics, analytics_period)

    print("Renderizando relatório...")
    html = render_html(m)

    REPORTS.mkdir(exist_ok=True)
    out = REPORTS / f"report-{datetime.now().strftime('%Y-%m-%d')}.html"
    out.write_text(html, encoding="utf-8")

    print(f"\n✓ Relatório escrito em {out}")
    print(f"  Período      : {m['date_start']} – {m['date_end']}")
    print(f"  Usuários     : {m['active_users']} ativos (qualquer canal) / {m['total_users']} registrados")
    print(f"  Inativos     : {len(m['inactive_rows'])} com zero chat, Cowork e Code")
    print(f"  Cowork       : {m['cowork_users']} usuários, {m['cowork_total_sessions']} sessões "
          f"({m['cowork_only_users']} leriam como inativos sem isso)")
    print(f"  Conversas    : {fmt_int(m['total_conversations'])}")
    print(f"  Mensagens    : {fmt_int(m['total_messages'])}")
    print(f"  Code/auto    : {m['cc_total_users']} usuários, {fmt_int(m['cc_total_calls'])} chamadas de ferramenta")
    print(f"  Claude Code  : {m['cc_csv_users']} usuários, {fmt_dec(m['cc_total_lines'])} mil linhas ({m['cc_period']})")
