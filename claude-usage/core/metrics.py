from collections import defaultdict, Counter
from datetime import datetime

from .config import CLAUDE_CODE_TOOLS


def parse_dt(s):
    """Lê um datetime ISO-8601, removendo o sufixo de timezone. Devolve None se não conseguir."""
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
    """Devolve (usuários billable, email_to_tier), excluindo assentos Unassigned e membros removidos."""
    billable_uids = {
        uid for uid, u in users.items()
        if members.get(u["email_address"], {}).get("tier", "Unassigned") != "Unassigned"
    }
    filtered = {uid: u for uid, u in users.items() if uid in billable_uids}
    email_to_tier = {u["email_address"]: members[u["email_address"]]["tier"]
                     for u in filtered.values() if u["email_address"] in members}
    return filtered, email_to_tier


def _project_metrics(projects, design_chats, users):
    """Devolve (dict de métricas, contador proj_per_user) a partir dos projetos e design chats."""
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
    """Passada única sobre todas as conversas; devolve um dict de contadores e sets para uso posterior."""
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

    # As chaves são os tipos internos de bloco de conteúdo do Claude; entradas em estilo MIME são
    # tipos de bloco de artifact.
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

        conv_has_cc = False  # marca se a conversa teve alguma chamada de ferramenta CC; evita contar a mesma conversa mais de uma vez
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
                conv_name = conv.get("name") or "(sem título)"
                for fi in files:
                    user_file_details[uid].append({
                        "name": fi.get("file_name") or "(sem nome)",
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


CHANNEL_KEYS = ("chats", "messages", "cowork_sessions", "cowork_messages",
                "code_sessions", "file_edits", "pull_requests")


def _channel_active(users, analytics, web_active, cc_uids):
    """Devolve o conjunto de uids que interagiram em QUALQUER canal — chat, Cowork ou Claude Code.

    A exportação members-analytics é a autoridade porque é a única fonte que cobre os três
    canais; um usuário com zero chats mas com sessões de Cowork está ativo. Usuários ausentes
    dessa exportação caem para as evidências dos lotes de conversas e do CSV do Claude Code,
    então um arquivo de analytics parcial nunca rebaixa alguém a inativo silenciosamente.
    """
    active = set()
    for uid, user in users.items():
        entry = analytics.get(user.get("email_address", ""))
        if entry is not None:
            if any(entry[k] for k in CHANNEL_KEYS):
                active.add(uid)
        elif uid in web_active or uid in cc_uids:
            active.add(uid)
    return active


def _build_user_rows(users, analytics, active_uids, user_convs, proj_per_user,
                     user_files, user_last_active, email_to_tier):
    """Monta as linhas da tabela de atividade para cada usuário ativo em qualquer canal.

    Chats/mensagens/último acesso vêm da exportação members-analytics, e não dos lotes de
    conversas: a exportação cobre chat, Cowork e Code em uma janela consistente, enquanto os
    lotes JSON cobrem só o chat web e podem chegar incompletos. Projetos e uploads de arquivo
    continuam vindo do lado JSON, sua única fonte.
    """
    rows = []
    for uid, user in users.items():
        if uid not in active_uids:
            continue
        email = user.get("email_address", "")
        a = analytics.get(email)
        last = user_last_active.get(uid)
        if a and a["last_active"]:
            last_label, last_ts = a["last_active"], a["last_active"]
        else:
            last_label = last.strftime("%Y-%m-%d") if last else "—"
            last_ts = last_label
        rows.append({
            "uid": uid,
            "name": user.get("full_name") or email,
            "email": email,
            "tier": email_to_tier.get(email, ""),
            "days_active": a["days_active"] if a else 0,
            "conversations": a["chats"] if a else user_convs[uid],
            "human_msgs": a["messages"] if a else 0,
            "cowork_sessions": a["cowork_sessions"] if a else 0,
            "code_sessions": a["code_sessions"] if a else 0,
            "projects": proj_per_user.get(uid, 0),
            "files_uploaded": user_files[uid],
            "last_active": last_label,
            "last_active_ts": last_ts,
        })
    rows.sort(key=lambda r: (r["days_active"], r["conversations"]), reverse=True)
    return rows


def _cowork_metrics(users, analytics, email_to_tier):
    """Devolve a seção Cowork: sessões/mensagens por usuário mais os totais.

    O Cowork é invisível tanto para a exportação de conversas quanto para o CSV de linhas do
    Claude Code, então esta seção existe para expor usuários cujo uso inteiro leria como zero.
    """
    rows = []
    for user in users.values():
        email = user.get("email_address", "")
        a = analytics.get(email)
        if not a or not (a["cowork_sessions"] or a["cowork_messages"]):
            continue
        rows.append({
            "name": user.get("full_name") or email,
            "email": email,
            "tier": email_to_tier.get(email, ""),
            "sessions": a["cowork_sessions"],
            "messages": a["cowork_messages"],
            "chats": a["chats"],
            "chat_only_zero": a["chats"] == 0 and a["code_sessions"] == 0,
        })
    rows.sort(key=lambda r: (r["sessions"], r["messages"]), reverse=True)
    return {
        "cowork_rows": rows,
        "cowork_users": len(rows),
        "cowork_total_sessions": sum(r["sessions"] for r in rows),
        "cowork_total_messages": sum(r["messages"] for r in rows),
        "cowork_only_users": sum(1 for r in rows if r["chat_only_zero"]),
    }


def _adoption_funnel(users, analytics, active_uids, user_convs, uid_cc_lines):
    """Devolve o funil de adoção como uma lista de tuplas (rótulo, contagem, pct).

    pct é a participação sobre os usuários registrados, então todo estágio é lido contra a
    mesma base. Com a exportação de analytics disponível, o funil é medido por dias ativos, que
    contam a pessoa igual tendo ela trabalhado em chat, Cowork ou Code. Sem ela, cai no critério
    antigo, pela união de contagem de conversas e linhas de código. Power user é o usuário
    recorrente, medido por dias ativos (≥20); memória é ignorada de propósito, por ser criada de
    forma passiva demais para sinalizar intensidade de adoção.
    """
    total = len(users)

    def rows(stages):
        return [(label, count, (100 * count / total) if total else 0.0)
                for label, count in stages]

    if analytics:
        days = {uid: analytics.get(u.get("email_address", ""), {}).get("days_active", 0)
                for uid, u in users.items()}
        engaged = {uid for uid in active_uids if days.get(uid, 0) >= 10}
        power = {uid for uid in active_uids if days.get(uid, 0) >= 20}
        return rows([
            ("Registrados", total),
            ("Ativos (≥1 uso em qualquer canal)", len(active_uids)),
            ("Engajados (≥10 dias ativos)", len(engaged)),
            ("Power users (≥20 dias ativos)", len(power)),
        ])

    # Os valores estão em milhares (a coluna "Lines this Month" do CSV já vem em K);
    # os thresholds (1, 5, 10) portanto significam 1K, 5K e 10K linhas.
    cc_funnel_engaged = {uid for uid, l in uid_cc_lines.items() if l >= 5}
    cc_funnel_power   = {uid for uid, l in uid_cc_lines.items() if l >= 10}

    funnel_engaged = {uid for uid, c in user_convs.items() if c >= 5} | cc_funnel_engaged
    funnel_power   = cc_funnel_power
    return rows([
        ("Registrados", total),
        ("Ativos (≥1 conversa ou ≥1 mil linhas)", len(active_uids)),
        ("Engajados (≥5 conversas ou ≥5 mil linhas)", len(funnel_engaged)),
        ("Power users (≥10 mil linhas)", len(funnel_power)),
    ])


def _feature_rows(feature_users, feature_convs, feature_block_count, active_users):
    """Devolve as linhas de adoção de features na ordem de exibição, pulando as com uso zero."""
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
    """Devolve as métricas de Code & Automation derivadas dos blocos tool_use da exportação web."""
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


def _cc_csv_metrics(claude_code_data, users, cc_period):
    """Devolve (dict de métricas, cc_uids) a partir do CSV do Claude Code do Anthropic Console.

    cc_uids é o conjunto de UUIDs de usuário casados com linhas > 0 (uso real); o chamador
    precisa dele para atualizar o KPI de active_users e tirar quem usa o CLI da lista de
    inativos. Usuários que apenas constam no CSV com 0 linhas não contam — senão seriam
    marcados como "ativos" e sumiriam tanto de Atividade por usuário (só web) quanto de Contas
    inativas. A seção Claude Code em si só lista usuários com ≥1K linhas no mês; o cc_uids
    continua registrando todo uso real, então a lógica de usuário ativo não é afetada.
    """
    email_to_user = {u["email_address"]: u for u in users.values()}
    cc_csv_rows = []
    cc_uids = set()
    for entry in (claude_code_data or []):
        email = entry["email"]
        lines = entry["lines"]
        user = email_to_user.get(email, {})
        uid = user.get("uuid", "")
        if uid and lines > 0:
            cc_uids.add(uid)
        if lines < 1.0:  # linhas estão em K; esconde da seção quem tem menos de 1K
            continue
        cc_csv_rows.append({
            "name": user.get("full_name") or email,
            "email": email,
            "lines": lines,
        })
    cc_csv_rows.sort(key=lambda r: r["lines"], reverse=True)
    return {
        "cc_csv_rows": cc_csv_rows,
        "cc_total_lines": sum(r["lines"] for r in cc_csv_rows),
        "cc_csv_users": len(cc_csv_rows),
        "cc_period": cc_period,
    }, cc_uids


def _inactive_rows(users, active_uids, analytics, email_to_tier):
    """Devolve os usuários que não interagiram em canal nenhum — chat, Cowork e Code zerados.

    É o complemento exato de _channel_active. Antes de o Cowork ser medido, um usuário só-Cowork
    aparecia aqui como inativo e podia ter o assento recuperado; a flag "covered" registra se o
    veredito é sustentado pela exportação de analytics ou apenas inferido dos lotes de conversas,
    que não enxergam Cowork.
    """
    rows = []
    for uid, user in users.items():
        if uid in active_uids:
            continue
        email = user.get("email_address", "")
        rows.append({
            "name": user.get("full_name") or "—",
            "email": email,
            "tier": email_to_tier.get(email, ""),
            "covered": email in analytics,
        })
    rows.sort(key=lambda r: r["name"].lower())
    return rows


def compute_metrics(users, members, projects, design_chats, conversations,
                    claude_code_data=None, cc_period="", analytics=None, analytics_period=""):
    """Agrega todos os dados de origem em um dict plano de métricas consumido por render_html.

    Delega a helpers privados por seção lógica; esta função é apenas o orquestrador. Devolve um
    dict com chaves para KPIs, linhas de tabela, funil, atividade diária e adoção de features.
    """
    users, email_to_tier = _filter_users(users, members)
    analytics = analytics or {}
    m = {"total_users": len(users), "analytics_period": analytics_period}

    # Os valores estão em milhares (a coluna "Lines this Month" do CSV já vem em K);
    # os thresholds do funil abaixo (1, 5, 10) portanto significam 1K, 5K e 10K linhas.
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
        m["date_start"] = min(conv_dates).strftime("%d/%m/%Y")
        m["date_end"] = max(conv_dates).strftime("%d/%m/%Y")
    else:
        m["date_start"] = m["date_end"] = "—"

    cc_csv, cc_uids = _cc_csv_metrics(claude_code_data, users, cc_period)

    # Fonte única de verdade para "essa pessoa está usando o Claude", cobrindo chat, Cowork e
    # Code; todas as tabelas abaixo derivam daqui.
    active_uids = _channel_active(users, analytics, active_users, cc_uids)

    m["user_rows"] = _build_user_rows(
        users, analytics, active_uids, conv["user_convs"], proj_per_user,
        conv["user_files"], conv["user_last_active"], email_to_tier,
    )
    m.update(_cowork_metrics(users, analytics, email_to_tier))
    m["funnel"] = _adoption_funnel(users, analytics, active_uids, conv["user_convs"],
                                   uid_cc_lines)

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

    m.update(cc_csv)
    # Sobrescreve a contagem só-web feita antes: o KPI de destaque conta qualquer canal.
    m["active_users"] = len(active_uids)
    m["web_active_users"] = len(active_users)

    m["inactive_rows"] = _inactive_rows(users, active_uids, analytics, email_to_tier)

    return m
