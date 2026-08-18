# Claude Team Usage Data

This directory contains a snapshot of Claude usage data exported by a G5 Partners organization admin. It covers users across the `@g5partners.com` domain, primarily investment banking and operations staff.

## Context

G5 Partners is the largest independent financial services firm in Brazil, operating in Multi-Family Office (MFO), Financial Strategic Advisory for Mergers and Acquisitions (FSA), DCM Capital Solutions, and alternative investments in judicial credit rights (G5 JUS).

The team uses Claude for client research, financial analysis, document drafting, origination workflows, IT support, and software engineering.

## Directory Structure

```
report.py                    # thin entrypoint — imports and calls core.main.main()
core/                        # report logic split into focused modules
  config.py                  # ROOT / DATA / REPORTS paths and CLAUDE_CODE_TOOLS constant
  fetch.py                   # all load_* functions (users, conversations, CSV files, etc.)
  metrics.py                 # compute_metrics() orchestrator + private helper functions
  render.py                  # render_html() — CSS, HTML template, JS (no external deps)
  main.py                    # main() — loads data, calls compute_metrics, writes output file
data/                        # gitignored — all raw Claude export files live here
  conversations-NNNN.json    # org conversations, delivered in BATCHES — 650 MB, NEVER load in full
                             # fetch.py globs conversations*.json and concatenates every batch
                             # batches can go missing from an export; treat counts as a lower bound
  users.json                 # all org members (@g5partners.com); may include removed/unassigned accounts
  memories.json              # per-user memory summaries (7 users with entries)
  projects/                  # 71 project JSON files (small, safe to read)
  design_chats/              # 6 design/artifact conversation files (small, safe to read)
  members-<uuid>-<date>.csv  # team member roster exported from Anthropic admin dashboard
                             # authoritative source for seat tier and active membership
                             # fetch.py always picks the alphabetically-last (most recent) file
  members-analytics-<uuid>-<from>-to-<to>.csv
                             # per-member activity export from Anthropic Console — PRIMARY source
                             # for user activity: the ONLY export that reports Cowork usage
                             # covers every member, including those absent from the conversations batches
                             # fetch.py always picks the alphabetically-last (most recent) file
  claude_code_team_*.csv     # Claude Code CLI usage export from Anthropic Console
                             # filename encodes the period: claude_code_team_YYYY_MM_DD_to_YYYY_MM_DD.csv
                             # fetch.py always picks the alphabetically-last (most recent) file
reports/                     # gitignored — generated output files
  report.html                # self-contained HTML executive report (do not edit directly)
```

## Code Architecture

The pipeline is a straight line: `fetch → metrics → render → write`.

```
report.py
  └── core/main.py          main()
        ├── core/fetch.py   load_users(), load_members(), load_members_analytics(),
        │                   load_conversations(), load_claude_code(), …
        ├── core/metrics.py compute_metrics(users, members, memories, projects, design_chats,
        │                                   conversations, claude_code_data, cc_period,
        │                                   analytics, analytics_period)
        │     ├── _filter_users()        billable-only filtering; email→tier map
        │     ├── _project_metrics()     project/design-chat pass; proj_per_user counter
        │     ├── _conversation_pass()   single loop over all conversations; returns all counters
        │     ├── _channel_active()      uids active on ANY channel — the one activity rule
        │     ├── _build_user_rows()     per-user activity rows; analytics-backed columns
        │     ├── _cowork_metrics()      Cowork section rows + totals
        │     ├── _adoption_funnel()     funnel list; days-active thresholds
        │     ├── _feature_rows()        feature adoption rows in display order
        │     ├── _cc_web_metrics()      CC tool-use stats from web export
        │     ├── _cc_csv_metrics()      Claude Code CLI stats from CSV; returns cc_uids
        │     └── _inactive_rows()       complement of _channel_active()
        └── core/render.py  render_html(m) → self-contained HTML string
```

### Which source feeds which column

The members-analytics CSV is the primary source for *whether and how much* someone used Claude;
the conversations batches remain the only source for *what happened inside* a chat.

| From members-analytics CSV | From conversations*.json |
|---|---|
| Days Active, Chats, Messages Sent | Projects, Files Uploaded (+ upload detail modal) |
| Cowork Sessions / Messages | Feature Adoption, Top Tools |
| Code Sessions, File Edits, PRs | Daily Volume, Conversation Depth |
| Last Active, activity/inactivity verdict | — |

`Estimated Spend (USD)` is present in the CSV but reads `0.00` for every member — not used.

When editing report logic, go directly to the relevant helper in `core/metrics.py` rather than reading the whole file. `_conversation_pass()` is the largest function (~80 lines); everything else is under 30 lines.

---

## CRITICAL: Never Read Full JSON Files

**The `conversations-NNNN.json` batches are very big text files. Loading them will exhaust your context window.**

Always use targeted tools to inspect data:

```bash
# Inspect first conversation structure (safe — reads only 500KB of one batch)
python3 -c "
import json, glob
f = open(sorted(glob.glob('data/conversations*.json'))[0]); chunk = f.read(500000); f.close()
obj, _ = json.JSONDecoder().raw_decode(chunk[1:])
print(json.dumps(obj, indent=2, ensure_ascii=False)[:3000])
"

# Search conversations by keyword (streaming, no full load)
grep -i "keyword" data/conversations*.json | head -5

# For projects and design_chats — files are small, safe to read directly
cat data/projects/019d9c7d-ebcb-725b-9755-a109ab3b8d4d.json

# For per-user activity questions, read the analytics CSV instead — 9 KB, always safe
cat data/members-analytics-*.csv
```

For any analysis on the conversation batches, write a Python script that loops over
`glob.glob('data/conversations*.json')` and calls `json.load()` per file, freeing each batch
before the next (`del convs; gc.collect()`). It fits in memory (~3 GB peak across all batches
if held at once) but must never be printed or injected into the LLM context.

**Prefer `members-analytics-*.csv` whenever the question is per-user activity.** It answers most
"who used what, how much" questions in 9 KB instead of 650 MB, and it is the only source that
sees Cowork.

---

## Report Script

`report.py` is the entrypoint. Run with:

```bash
python3 report.py        # writes reports/report-YYYY-MM-DD.html, prints summary to stdout
```

**Dependencies:** Python stdlib only (`json`, `csv`, `re`, `glob`, `collections`, `datetime`, `pathlib`). No pip installs required.

### Report sections (in order)

| Section | Source | Notes |
|---|---|---|
| Overview (KPIs) | all sources | Active users = any channel (chat, Cowork, Code) |
| User Activity | members-analytics CSV + conversations | Sortable table; click file count to see modal |
| Cowork | members-analytics CSV | Only export that sees Cowork; flags Cowork-only users |
| Claude Code | data/claude_code_team_*.csv | Lines in thousands (K); cross-refs web convs |
| Inactive Accounts | members-analytics CSV | Zero on all three channels |
| Adoption Funnel | members-analytics CSV | See thresholds below |
| Daily Conversation Volume | conversations*.json | Column chart, 30-day window |
| Conversation Depth | conversations*.json | Distribution by message count |

### Adoption funnel thresholds

Graded on `Days Active`, which counts a person the same whether they worked in chat, Cowork or Code.

| Tier | Threshold |
|---|---|
| Active | ≥1 use on any channel (chat, Cowork, Code) |
| Engaged | ≥10 days active |
| Power user | ≥20 days active (recurring user) |

Each funnel stage also shows its share of registered users. Memory is intentionally excluded
from the tiering — it is created too passively to signal intensity of adoption.

If no members-analytics CSV is present, `_adoption_funnel()` falls back to the older
conversation-count / lines-of-code union (≥1/≥5 convs, ≥1K/≥5K/≥10K lines; power = ≥10K lines).

### Active user definition

**A user is active if they interacted on ANY channel: chat, Cowork, or Claude Code.**
`_channel_active()` is the single implementation; the KPI card, user table, adoption funnel and
inactive list all derive from it, and `_inactive_rows()` is its exact complement.

The verdict comes from the members-analytics CSV. Users absent from that export fall back to
evidence from the conversation batches and the Claude Code CSV, and are tagged *not covered* in
the Inactive Accounts table — a missing analytics row must never silently demote someone.

**Why this matters:** before Cowork was measured, activity was inferred from the conversations
export (web chat only) plus `Lines this Month` (code lines only). A user working exclusively in
Cowork produced neither, so they appeared under Inactive Accounts despite daily use — and at
least one seat was reclaimed on that false negative. Never infer inactivity from a source that
cannot see all three channels.

---

## JSON Schemas

### `data/users.json`

Top-level: `array` of user objects.

```jsonc
[
  {
    "uuid": "string (UUIDv4)",          // matches account.uuid in conversations
    "full_name": "string | null",
    "email_address": "string",          // all @g5partners.com
    "verified_phone_number": "string | null"  // E.164 format, e.g. "+5511..."
  }
]
```

### `data/memories.json`

Top-level: `array` of memory objects. Only users who have accumulated conversation history have an entry.

```jsonc
[
  {
    "account_uuid": "string (UUIDv4)",  // foreign key → users[].uuid
    "conversations_memory": "string",   // long markdown summary Claude built from past sessions;
                                        // covers work context, active deals, preferences, recent history
    "project_memories": {               // per-project memory summaries (may be absent if empty)
      "<project-uuid>": "string"        // project UUID → markdown memory for that project
    }
  }
]
```

### `data/projects/<uuid>.json`

Each file is a single project object (not an array).

```jsonc
{
  "uuid": "string (UUIDv4)",
  "name": "string",
  "description": "string",
  "is_private": "boolean",
  "is_starter_project": "boolean",
  "prompt_template": "string",          // system prompt / instructions for the project
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "creator": {
    "uuid": "string (UUIDv4)",          // foreign key → users[].uuid
    "full_name": "string"
  },
  "docs": [
    {
      "uuid": "string (UUIDv4)",
      "filename": "string",
      "content": "string",              // uploaded document text
      "created_at": "string (ISO 8601)"
    }
  ]
}
```

### `data/design_chats/<uuid>.json`

Each file is a single design/artifact conversation object.

```jsonc
{
  "uuid": "string (UUIDv4)",
  "title": "string",
  "project": {
    "uuid": "string (UUIDv4)",          // foreign key → projects/<uuid>.json
    "name": "string"
  },
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "messages": [
    {
      "uuid": "string (UUIDv4)",
      "role": "user | assistant",
      "content": {
        "attachments": "array",
        "authorAccountUuid": "string",
        "authorName": "string",
        "content": "string",            // message text
        "id": "string",
        "role": "string",
        "timestamp": "string (ISO 8601)"
      },
      "created_at": "string (ISO 8601)"
    }
  ]
}
```

### `data/conversations-NNNN.json`

Top-level: `array` of conversation objects, split across one or more batch files.
**Do not load these files in full.** `load_conversations()` globs `conversations*.json` and
concatenates every batch, so a single-file export is just the one-batch case.

Batches can be lost when re-exporting; when analytics-CSV chat counts exceed what the batches
show, the batches are incomplete, not the CSV.

```jsonc
[
  {
    "uuid": "string (UUIDv4)",
    "name": "string",                   // conversation title
    "summary": "string",                // may be empty
    "created_at": "string (ISO 8601)",
    "updated_at": "string (ISO 8601)",
    "account": {
      "uuid": "string (UUIDv4)"         // foreign key → users[].uuid
    },
    "chat_messages": [
      {
        "uuid": "string (UUIDv4)",
        "text": "string",               // full plain-text of the message
        "content": [
          {
            "start_timestamp": "string (ISO 8601)",
            "stop_timestamp": "string (ISO 8601)",
            "flags": "null | object",
            "type": "text | tool_use | tool_result | thinking | ...",
            "text": "string"            // present when type == "text"
            // additional fields vary by type; see gotchas below
          }
        ],
        "sender": "human | assistant",
        "created_at": "string (ISO 8601)",
        "updated_at": "string (ISO 8601)",
        "attachments": "array",         // file/image attachments
        "files": "array",               // structured file list; see gotchas below
        "parent_message_uuid": "string (UUIDv4)"  // thread parent; root messages use null UUID
      }
    ]
  }
]
```

### `data/members-<uuid>-<date>.csv`

Exported from the Anthropic team admin dashboard. This is the **authoritative membership source** — use email as the join key. If a user appears in `data/users.json` but not here, they have been removed from the org.

```csv
Name,Email,Role,Status,Seat Tier
G5 Partners - Contas-TI,contas-ti@g5partners.com,Primary Owner,Active,Unassigned
Leonardo,lzambello@g5partners.com,User,Active,Standard
...
```

| Column | Type | Description |
|---|---|---|
| `Name` | string | Display name |
| `Email` | string | Join key → `users[].email_address` and `claude_code_team_*.csv User` |
| `Role` | string | `Primary Owner`, `Admin`, `User`, etc. |
| `Status` | string | `Active` or `Inactive` |
| `Seat Tier` | string | `Standard`, `Premium`, or `Unassigned` |

**`Seat Tier = Unassigned`** means the seat is not assigned to a billable user (e.g., shared/service accounts). These are excluded from all report metrics — active counts, inactive counts, funnel, and KPIs. They are not billed and should not be tracked.

---

### `data/members-analytics-<uuid>-<from>-to-<to>.csv`

Per-member activity export from the Anthropic Console. **Primary source for user activity** and
the only export that reports Cowork. Covers every org member, including those with no rows in the
conversation batches. Report uses the most recent file (alphabetically last). The filename encodes
the window: `...-2026-06-23-to-2026-07-22.csv`.

Written **with a UTF-8 BOM** — open with `encoding='utf-8-sig'`, otherwise the first header
becomes `﻿Name` and the `Name` column silently reads as empty.

```csv
"Name","Email","Role","Seat Tier","Last Active","Days Active","Chats","Messages",
"Projects Created","Projects Used","Pull Requests","Code sessions","File Edits",
"Cowork Sessions","Cowork Messages","Artifacts Created","Estimated Spend (USD)"
"Caroline","csnit@g5partners.com","User","Standard","2026-07-20","22","0","0",
"0","0","0","0","0","25","61","0","0.00"
```

| Column | Type | Description |
|---|---|---|
| `Email` | string | Join key → `users[].email_address` |
| `Last Active` | date `YYYY-MM-DD` | Across all channels; may be empty |
| `Days Active` | integer | Distinct days with any interaction — the engagement metric the funnel grades on |
| `Chats` | integer | Web/desktop conversations touched in the window |
| `Messages` | integer | **Human messages only** — matches `user_human_msgs`, not `len(chat_messages)` |
| `Cowork Sessions` / `Cowork Messages` | integer | Cowork usage; **invisible to every other export** |
| `Code sessions` / `File Edits` / `Pull Requests` | integer | Claude Code activity, richer than the lines CSV |
| `Projects Created` / `Projects Used` | integer | Cross-checks the `projects/` JSON pass |
| `Artifacts Created` | integer | Artifact count |
| `Estimated Spend (USD)` | decimal | Reads `0.00` for every member on this plan — not used |

Counts are plain integers today; `_csv_int()` also strips `.` in case large values arrive with
pt-BR thousands separators, as `claude_code_team_*.csv` already does.

`Chats` here can exceed the batch count for the same user: the CSV counts chats *touched* in the
window (a June chat used in July counts), while the JSON is filtered on `created_at`. It also runs
higher when conversation batches are missing from an export.

**`Seat Tier` in this file can lag the roster.** Use `members-*.csv` as the authority for tier and
status; use this file for activity.

---

### `data/claude_code_team_*.csv`

CSV export from Anthropic Console. Report uses the **most recent file** (alphabetically last by filename). A new export replaces the old one by naming convention.

```csv
User,Lines this Month
middle_dev@g5partners.com,64.230
gestao@g5partners.com,48.165
mmedeiros@g5partners.com,526
tcitro@g5partners.com,317
...
```

| Column | Type | Description |
|---|---|---|
| `User` | string | User email; joins to `users[].email_address` |
| `Lines this Month` | integer (Brazilian formatting) | **Raw line count where `.` is the thousands separator** — `64.230` = 64,230 lines, `526` = 526 lines. Lines of code generated or modified via Claude Code CLI. |

**Number format gotcha:** the value is NOT a decimal. The `.` is a thousands separator (pt-BR formatting), so values ≥ 1000 always show exactly three digits after the dot (`64.230`) while values < 1000 have no separator (`526`, `317`). `core/fetch.py` strips the `.` to recover the true integer, then divides by 1000 to express it in thousands (K) — the representation the rest of the pipeline (render, funnel thresholds) expects. Parsing the value with a plain `float()` is wrong: it happens to work for values ≥ 1000 but inflates sub-1000 counts by 1000× (e.g. `317` would render as 317K instead of 0.3K).

Only users with CLI activity appear. Users absent here had zero CLI usage in the period.

---

## Key Relationships

```
data/users[].uuid
  ↳ data/conversations[].account.uuid     (who had the conversation)
  ↳ data/memories[].account_uuid          (whose memory summary)
  ↳ data/projects[].creator.uuid          (who owns the project)

data/projects[].uuid
  ↳ data/design_chats[].project.uuid      (which project a design chat belongs to)

data/users[].email_address
  ↳ data/members-*.csv Email column           (seat tier, authoritative membership)
  ↳ data/members-analytics-*.csv Email column (all-channel activity, incl. Cowork)
  ↳ data/claude_code_team_*.csv User col      (CLI lines of code)
```

---

## Gotchas

**Cowork usage appears in exactly one export.**
Neither the conversation batches nor `claude_code_team_*.csv` see it. A Cowork-only user reads as
zero everywhere except `members-analytics-*.csv`. Any activity/inactivity judgement built on the
other two sources is wrong by construction — see "Active user definition".

**`tool_use` blocks in the conversation batches are NOT Claude Code CLI.**
Tools like `bash_tool`, `view`, `str_replace`, `create_file` appear in `content` blocks from the claude.ai web interface's built-in code execution environment. They share names with Claude Code CLI tools but are separate. There is no way to distinguish Claude Code CLI sessions from this export — that data only appears in the CSV.

**File uploads are inflated by document conversion.**
When a user uploads a PDF or PowerPoint, Claude converts each page/slide into an individual image (`slide-1.jpg`, `slide-2.jpg`, …). Each image appears as a separate entry in `msg.files`. A single 30-page document generates 30 file entries. The `files_uploaded` count in the report reflects this.

**Conversations inside claude.ai Projects are included in the conversation batches.**
There is no `project_uuid` field on conversation objects — it is not possible to determine from this export which conversations belong to which project.

**"Inactive" means truly inactive — among billable users only.**
The Inactive Accounts section only shows users with zero chats AND zero Cowork sessions AND zero Code sessions. Any activity on any channel excludes a user from the list.

Unassigned seats are excluded from the report entirely and never appear as inactive — including someone whose seat was *reclaimed* after being wrongly judged inactive. Once the tier flips to `Unassigned` they vanish from every table, so reassignment mistakes are not self-correcting. Check `members-analytics-*.csv` directly before reclaiming a seat.

**`data/users.json` may contain stale or unassigned accounts.**
Always cross-reference with `data/members-*.csv` (email join) to determine current membership and seat tier. Users absent from the members CSV have been removed from the org and are excluded from all metrics.
