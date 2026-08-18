import json
from datetime import datetime


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
.funnel-pct { font-weight: 400; color: var(--g5-graphite); }

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


def fmt_int(n):
    """Formata um inteiro no padrão pt-BR: ponto como separador de milhar."""
    return f"{int(n):,}".replace(",", ".")


def fmt_dec(x, casas=1):
    """Formata um decimal no padrão pt-BR: ponto no milhar, vírgula na casa decimal."""
    return f"{x:,.{casas}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def fmt_date(iso):
    """Converte uma data ISO 'YYYY-MM-DD' para dd/mm/aaaa; devolve a original se não casar."""
    try:
        return datetime.strptime(str(iso)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return str(iso)


def fmt_period(period):
    """Converte um período 'YYYY-MM-DD → YYYY-MM-DD' para o formato pt-BR de datas."""
    return " → ".join(fmt_date(p.strip()) for p in str(period).split("→"))


def kpi_card(val, label):
    return f'<div class="kpi"><div class="val">{esc(val)}</div><div class="lbl">{esc(label)}</div></div>'


def bar_row(day, count, max_count, bar_width=220):
    w = max(2, int(bar_width * count / max_count)) if max_count else 2
    return (f'<tr><td style="color:#64748b;font-size:12px;white-space:nowrap">{esc(day)}</td>'
            f'<td><div class="bar-wrap"><div class="bar" style="width:{w}px"></div>'
            f'<span class="bar-lbl">{count}</span></div></td></tr>')


def render_html(m):
    """Renderiza o HTML completo do relatório a partir do dict de métricas de compute_metrics.

    Devolve uma string HTML autocontida, com CSS e JS inline (sem dependência externa além do
    import do Google Fonts). Inclui uma tabela de usuários ordenável e um modal de uploads.
    """
    generated = datetime.now().strftime("%d/%m/%Y %H:%M")

    row1 = (kpi_card(fmt_int(m["total_users"]), "Usuários registrados") +
            kpi_card(fmt_int(m["active_users"]), "Usuários ativos"))
    row2 = (kpi_card(fmt_int(m["total_projects"]), "Projetos") +
            kpi_card(fmt_int(m["total_conversations"]), "Conversas") +
            kpi_card(fmt_int(m["total_messages"]), "Mensagens"))
    row3 = (kpi_card(fmt_dec(m["avg_convs_per_active_user"]), "Média de conversas / usuário ativo") +
            kpi_card(fmt_dec(m["avg_msgs_per_conv"]), "Média de mensagens / conversa"))

    user_table_rows = ""
    for r in m["user_rows"]:
        files_cell = (
            f'<span class="clickable" onclick="openModal(\'{esc(r["uid"])}\',\'{esc(r["name"])}\')">'
            f'{fmt_int(r["files_uploaded"])}</span>'
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
            f'<td style="text-align:center" data-val="{r["days_active"]}"><span class="tag">{fmt_int(r["days_active"])}</span></td>'
            f'<td style="text-align:center" data-val="{r["conversations"]}">{fmt_int(r["conversations"]) if r["conversations"] else "—"}</td>'
            f'<td style="text-align:center" data-val="{r["human_msgs"]}">{fmt_int(r["human_msgs"]) if r["human_msgs"] else "—"}</td>'
            f'<td style="text-align:center" data-val="{r["cowork_sessions"]}">{fmt_int(r["cowork_sessions"]) if r["cowork_sessions"] else "—"}</td>'
            f'<td style="text-align:center" data-val="{r["code_sessions"]}">{fmt_int(r["code_sessions"]) if r["code_sessions"] else "—"}</td>'
            f'<td style="text-align:center" data-val="{r["projects"]}">{fmt_int(r["projects"]) if r["projects"] else "—"}</td>'
            f'<td style="text-align:center" data-val="{r["files_uploaded"]}">{files_cell}</td>'
            f'<td style="color:var(--g5-slate);font-size:11px" data-val="{esc(str(r["last_active_ts"]))}">{esc(fmt_date(r["last_active"]))}</td>'
            f'</tr>'
        )

    analytics_note = (f"Período: <strong>{esc(fmt_period(m['analytics_period']))}</strong>. "
                      if m.get("analytics_period") else "")

    if m["cowork_rows"]:
        max_cw = max(r["sessions"] for r in m["cowork_rows"]) or 1
        cowork_table_rows = ""
        for i, r in enumerate(m["cowork_rows"], 1):
            pct = round(100 * r["sessions"] / max_cw)
            flag = (' <span class="tag" style="background:var(--g5-data-wine);color:#fff">Só Cowork</span>'
                    if r["chat_only_zero"] else "")
            cowork_table_rows += (
                f'<tr>'
                f'<td style="color:var(--g5-slate);text-align:center;white-space:nowrap">{i}</td>'
                f'<td style="white-space:nowrap">{esc(r["name"])}{flag}</td>'
                f'<td style="color:var(--g5-slate);font-size:12px;white-space:nowrap">{esc(r["email"])}</td>'
                f'<td style="width:100%"><div class="bar-wrap" style="width:100%">'
                f'<div class="bar" style="width:{pct}%;background:var(--g5-data-wine);flex-shrink:0"></div>'
                f'<span class="bar-lbl">{fmt_int(r["sessions"])}</span>'
                f'</div></td>'
                f'<td style="text-align:center;color:var(--g5-slate);white-space:nowrap">{fmt_int(r["messages"])}</td>'
                f'<td style="text-align:center;color:var(--g5-slate);white-space:nowrap">{fmt_int(r["chats"]) if r["chats"] else "—"}</td>'
                f'</tr>'
            )
        cowork_kpi_row = (
            kpi_card(fmt_int(m["cowork_users"]), "Usuários Cowork") +
            kpi_card(fmt_int(m["cowork_total_sessions"]), "Sessões Cowork") +
            kpi_card(fmt_int(m["cowork_total_messages"]), "Mensagens Cowork")
        )
        cowork_section = f"""
  <!-- Cowork -->
  <div class="section">
    <h2>Cowork</h2>
    <div class="kpi-row kpi-row-3" style="margin-bottom:18px">{cowork_kpi_row}</div>
    <p class="note">
      {analytics_note}A atividade de Cowork não aparece em nenhuma outra exportação — nem nos
      dados de conversas do claude.ai, nem no CSV de linhas do Claude Code.
      <strong>{fmt_int(m["cowork_only_users"])}</strong> desses usuários têm zero chats e zero
      sessões de Code, ou seja, antes desta seção existir todo o uso deles lia como inativo.
    </p>
    <table>
      <thead><tr>
        <th style="width:32px">#</th><th>Nome</th><th>E-mail</th>
        <th style="width:100%">Sessões</th>
        <th style="text-align:center">Mensagens</th>
        <th style="text-align:center">Chats</th>
      </tr></thead>
      <tbody>{cowork_table_rows}</tbody>
    </table>
  </div>"""
    else:
        cowork_section = ""

    cc_period_note = (f"Período: <strong>{esc(fmt_period(m['cc_period']))}</strong>. "
                      if m["cc_period"] else "")
    if m["cc_csv_rows"]:
        max_cc_lines = m["cc_csv_rows"][0]["lines"] if m["cc_csv_rows"] else 1
        cc_table_rows = ""
        for i, r in enumerate(m["cc_csv_rows"], 1):
            pct = round(100 * r["lines"] / max_cc_lines) if max_cc_lines else 0
            cc_table_rows += (
                f'<tr>'
                f'<td style="color:var(--g5-slate);text-align:center;white-space:nowrap">{i}</td>'
                f'<td style="white-space:nowrap">{esc(r["name"])}</td>'
                f'<td style="color:var(--g5-slate);font-size:12px;white-space:nowrap">{esc(r["email"])}</td>'
                f'<td style="width:100%"><div class="bar-wrap" style="width:100%">'
                f'<div class="bar" style="width:{pct}%;background:var(--g5-data-wine);flex-shrink:0"></div>'
                f'<span class="bar-lbl">{fmt_dec(r["lines"])} mil</span>'
                f'</div></td>'
                f'</tr>'
            )
        cc_kpi_row = (
            kpi_card(fmt_int(m["cc_csv_users"]), "Usuários do Claude Code") +
            kpi_card(f'{fmt_dec(m["cc_total_lines"])} mil', "Total de linhas no mês")
        )
        cc_section = f"""
  <!-- Claude Code -->
  <div class="section">
    <h2>Claude Code</h2>
    <div class="kpi-row kpi-row-2" style="margin-bottom:18px">{cc_kpi_row}</div>
    <p class="note">
      {cc_period_note}Dados da exportação de team do Anthropic Console.
      <strong>Linhas no mês</strong> mede o código gerado ou modificado via Claude Code CLI.
      Só são listados usuários com pelo menos 1 mil linhas no mês.
    </p>
    <table>
      <thead><tr>
        <th style="width:32px">#</th><th>Nome</th><th>E-mail</th>
        <th style="width:100%">Linhas no mês</th>
      </tr></thead>
      <tbody>{cc_table_rows}</tbody>
    </table>
  </div>"""
    else:
        cc_section = ""

    max_funnel = m["funnel"][0][1] if m["funnel"] else 1
    funnel_html = ""
    for label, val, pct in m["funnel"]:
        w = max(4, int(500 * val / max_funnel)) if max_funnel else 4
        funnel_html += (
            f'<div class="funnel-row">'
            f'<div class="funnel-bar" style="width:{w}px"></div>'
            f'<span class="funnel-lbl">{esc(label)}</span>'
            f'<span class="funnel-val">{fmt_int(val)} <span class="funnel-pct">({pct:.0f}%)</span></span>'
            f'</div>'
        )

    chart_bars = ""
    for d, c, mx in m["daily_activity"]:
        h = max(2, round(90 * c / mx)) if mx else 2
        dt_obj = datetime.strptime(d, "%Y-%m-%d")
        lbl = f"{dt_obj.day:02d}/{dt_obj.month:02d}"
        chart_bars += (
            f'<div class="ccol" title="{fmt_date(d)}: {c} conversas">'
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
            f'<tr><td style="white-space:nowrap">{esc(bucket)} mensagens</td>'
            f'<td style="width:100%"><div class="bar-wrap" style="width:100%">'
            f'<div class="bar" style="width:{pct_bar}%;background:var(--g5-data-blue);min-width:2px"></div>'
            f'<span class="bar-lbl" style="white-space:nowrap;flex-shrink:0">{fmt_int(cnt)} ({pct_label}%)</span></div></td></tr>'
        )

    def tier_badge(tier):
        if not tier:
            return "—"
        cls = "tier-premium" if tier.lower() == "premium" else "tier-standard"
        return f'<span class="tier-badge {cls}">{esc(tier)}</span>'

    not_covered_tag = '<span class="tag">sem cobertura</span>'
    inactive_rows_html = "".join(
        f'<tr><td>{esc(r["name"])} {"" if r.get("covered") else not_covered_tag}</td>'
        f'<td style="color:#64748b;font-size:12px">{esc(r["email"])}</td>'
        f'<td style="text-align:center">{tier_badge(r.get("tier",""))}</td></tr>'
        for r in m["inactive_rows"]
    )

    # As datas chegam como "YYYY-MM-DD HH:MM" para permitir a ordenação por string em
    # compute_metrics; a conversão para dd/mm/aaaa só acontece aqui, na exibição.
    file_data_json = json.dumps(
        {uid: [{**e, "date": f'{fmt_date(e["date"][:10])} {e["date"][11:]}'.strip()} for e in entries]
         for uid, entries in m["user_file_details"].items()},
        ensure_ascii=False,
    )

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>G5 Partners — Relatório de Uso do Claude</title>
<style>{CSS}</style>
</head>
<body>

<div class="g5-topband">
  <span class="g5-band-org">G5 Partners</span>
  <span class="g5-band-meta">Relatório de Uso do Claude &nbsp;·&nbsp; {esc(m["date_start"])} – {esc(m["date_end"])}</span>
</div>

<div class="wrapper">

  <h1 class="page-title">Relatório de Uso do Claude</h1>
  <p class="page-subtitle">Período: {esc(m["date_start"])} – {esc(m["date_end"])} &nbsp;·&nbsp; Gerado em {esc(generated)}</p>

  <!-- KPIs -->
  <div class="section">
    <h2>Visão geral</h2>
    <div class="kpi-row kpi-row-2">{row1}</div>
    <div class="kpi-row kpi-row-3">{row2}</div>
    <div class="kpi-row kpi-row-2">{row3}</div>
  </div>

  <!-- User Activity -->
  <div class="section">
    <h2>Atividade por usuário</h2>
    <p class="note">
      {analytics_note}<strong>Dias ativos</strong>, <strong>Chats</strong>, <strong>Mensagens enviadas</strong>,
      <strong>Cowork</strong> e <strong>Sessões Code</strong> vêm da exportação members-analytics do
      Console, que cobre os três canais em uma mesma janela. <strong>Projetos</strong> e
      <strong>Arquivos enviados</strong> vêm da exportação de conversas do claude.ai.
      A contagem de arquivos enviados é inflada: ao subir um PDF ou PowerPoint, o Claude converte cada
      página ou slide em um arquivo de imagem separado, então um documento de 30 páginas conta como 30 envios.
    </p>
    <div style="overflow-x:auto">
    <table id="user-table">
      <thead><tr>
        <th class="sortable" data-col="0" data-type="str">Nome</th>
        <th class="sortable" data-col="1" data-type="str">E-mail</th>
        <th class="sortable" data-col="2" data-type="str" style="text-align:center">Plano</th>
        <th class="sortable" data-col="3" data-type="num" style="text-align:center">Dias ativos</th>
        <th class="sortable" data-col="4" data-type="num" style="text-align:center">Chats</th>
        <th class="sortable" data-col="5" data-type="num" style="text-align:center">Mensagens enviadas</th>
        <th class="sortable" data-col="6" data-type="num" style="text-align:center">Sessões Cowork</th>
        <th class="sortable" data-col="7" data-type="num" style="text-align:center">Sessões Code</th>
        <th class="sortable" data-col="8" data-type="num" style="text-align:center">Projetos</th>
        <th class="sortable" data-col="9" data-type="num" style="text-align:center">Arquivos enviados</th>
        <th class="sortable" data-col="10" data-type="str">Último acesso</th>
      </tr></thead>
      <tbody>{user_table_rows}</tbody>
    </table>
    </div>
  </div>

  {cowork_section}

  {cc_section}

  <!-- Inactive Accounts -->
  <div class="section">
    <h2>Contas inativas</h2>
    <p class="note">
      Estes {fmt_int(len(m["inactive_rows"]))} usuários estão registrados na conta da organização e não
      interagiram em <strong>canal nenhum</strong> no período — zero chats, zero sessões de Cowork e
      zero sessões de Code. Linhas marcadas como <em>sem cobertura</em> não constam da exportação
      members-analytics, então o uso de Cowork não pôde ser verificado; confira antes de recuperar um assento.
    </p>
    <table style="width:auto">
      <thead><tr><th>Nome</th><th>E-mail</th><th style="text-align:center">Plano</th></tr></thead>
      <tbody>{inactive_rows_html}</tbody>
    </table>
  </div>

  <!-- Adoption Funnel -->
  <div class="section">
    <h2>Funil de adoção</h2>
    {funnel_html}
  </div>

  <!-- Daily Activity -->
  <div class="section">
    <h2>Volume diário de conversas</h2>
    <p style="font-size:12px;color:#64748b;margin-bottom:14px">
      Dia mais ativo: <strong>{esc(fmt_date(m["most_active_day"]))}</strong>
      ({fmt_int(m["most_active_day_count"])} conversas)
    </p>
    <div class="chart">{chart_bars}</div>
  </div>

  <!-- Conversation Depth -->
  <div class="section">
    <h2>Distribuição de profundidade das conversas</h2>
    <table style="width:50%">
      <thead><tr><th>Tamanho</th><th style="width:100%">Conversas</th></tr></thead>
      <tbody>{depth_rows}</tbody>
    </table>
  </div>

</div>

<footer class="g5-footer">G5 Partners &nbsp;·&nbsp; Exportação Admin do Claude &nbsp;·&nbsp; {esc(generated)}</footer>

<!-- File uploads modal -->
<div class="modal-overlay" id="modal-overlay" onclick="closeModalOnBg(event)">
  <div class="modal">
    <div class="modal-header">
      <span class="modal-title" id="modal-title"></span>
      <button class="modal-close" onclick="closeModal()">&#x2715;</button>
    </div>
    <input class="modal-search" id="modal-search" type="text"
           placeholder="Filtrar por nome do arquivo ou conversa…" oninput="filterModal()">
    <div class="modal-body">
      <table>
        <thead><tr>
          <th>Data e hora</th>
          <th>Nome do arquivo</th>
          <th>Conversa</th>
        </tr></thead>
        <tbody id="modal-tbody"></tbody>
      </table>
      <p class="no-results" id="modal-no-results" style="display:none">Nenhum arquivo corresponde ao filtro.</p>
    </div>
  </div>
</div>

<script>
const FILE_DATA = {file_data_json};

let _currentFiles = [];

function openModal(uid, name) {{
  _currentFiles = FILE_DATA[uid] || [];
  document.getElementById('modal-title').textContent =
    name + ' — ' + _currentFiles.length + (_currentFiles.length !== 1 ? ' arquivos enviados' : ' arquivo enviado');
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

// Ordenação da tabela
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
