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
  conversations.json         # all org conversations — 188 MB, NEVER load in full
  users.json                 # all org members (@g5partners.com); may include removed/unassigned accounts
  memories.json              # per-user memory summaries (7 users with entries)
  projects/                  # 71 project JSON files (small, safe to read)
  design_chats/              # 6 design/artifact conversation files (small, safe to read)
  members-<uuid>-<date>.csv  # team member roster exported from Anthropic admin dashboard
                             # authoritative source for seat tier and active membership
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
        ├── core/fetch.py   load_users(), load_members(), load_conversations(), load_claude_code(), …
        ├── core/metrics.py compute_metrics(users, members, memories, projects, design_chats,
        │                                   conversations, claude_code_data, cc_period)
        │     ├── _filter_users()        billable-only filtering; email→tier map
        │     ├── _project_metrics()     project/design-chat pass; proj_per_user counter
        │     ├── _conversation_pass()   single loop over all conversations; returns all counters
        │     ├── _build_user_rows()     per-user activity table rows (web-active only)
        │     ├── _adoption_funnel()     funnel list; CC + web union logic
        │     ├── _feature_rows()        feature adoption rows in display order
        │     ├── _cc_web_metrics()      CC tool-use stats from web export
        │     ├── _cc_csv_metrics()      Claude Code CLI stats from CSV; returns cc_uids
        │     └── _inactive_rows()       users with no web and no CLI activity
        └── core/render.py  render_html(m) → self-contained HTML string
```

When editing report logic, go directly to the relevant helper in `core/metrics.py` rather than reading the whole file. `_conversation_pass()` is the largest function (~80 lines); everything else is under 30 lines.

---

## CRITICAL: Never Read Full JSON Files

**`conversations.json` is a very big text file. Loading it will exhaust your context window.**

Always use targeted tools to inspect data:

```bash
# Inspect first conversation structure (safe — reads only 500KB)
python3 -c "
import json
f = open('data/conversations.json'); chunk = f.read(500000); f.close()
obj, _ = json.JSONDecoder().raw_decode(chunk[1:])
print(json.dumps(obj, indent=2, ensure_ascii=False)[:3000])
"

# Search conversations by keyword (streaming, no full load)
grep -i "keyword" data/conversations.json | head -5

# For projects and design_chats — files are small, safe to read directly
cat data/projects/019d9c7d-ebcb-725b-9755-a109ab3b8d4d.json
```

For any analysis on `data/conversations.json`, write a Python script that calls `json.load()` in a loop — it fits in memory (~500 MB peak) but must never be printed or injected into the LLM context.

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
| Overview (KPIs) | all sources | Active users = web convs OR ≥1K CLI lines |
| User Activity | data/conversations.json | Sortable table; click file count to see modal |
| Claude Code | data/claude_code_team_*.csv | Lines in thousands (K); cross-refs web convs |
| Inactive Accounts | data/users.json + both sources | Zero web convs AND zero CLI usage |
| Adoption Funnel | data/conversations.json + CSV | See thresholds below |
| Daily Conversation Volume | data/conversations.json | Column chart, 30-day window |
| Conversation Depth | data/conversations.json | Distribution by message count |

### Adoption funnel thresholds

| Tier | Web (conversations.json) | CLI (claude_code_team CSV) |
|---|---|---|
| Active | ≥1 conversation | ≥1K lines (value ≥ 1.0) |
| Engaged | ≥5 conversations | ≥5K lines (value ≥ 5.0) |
| Power user | has persistent memory | ≥10K lines (value ≥ 10.0) |

### Active user definition

A user is counted as **active** if they appear in either source. The KPI card, adoption funnel, and inactive accounts list all use this combined definition. No double-counting.

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

### `data/conversations.json`

Top-level: `array` of conversation objects. **Do not load this file in full.**

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
  ↳ data/members-*.csv Email column       (seat tier, authoritative membership)
  ↳ data/claude_code_team_*.csv User col  (CLI usage)
```

---

## Gotchas

**`tool_use` blocks in `data/conversations.json` are NOT Claude Code CLI.**
Tools like `bash_tool`, `view`, `str_replace`, `create_file` appear in `content` blocks from the claude.ai web interface's built-in code execution environment. They share names with Claude Code CLI tools but are separate. There is no way to distinguish Claude Code CLI sessions from this export — that data only appears in the CSV.

**File uploads are inflated by document conversion.**
When a user uploads a PDF or PowerPoint, Claude converts each page/slide into an individual image (`slide-1.jpg`, `slide-2.jpg`, …). Each image appears as a separate entry in `msg.files`. A single 30-page document generates 30 file entries. The `files_uploaded` count in the report reflects this.

**Conversations inside claude.ai Projects are included in `data/conversations.json`.**
There is no `project_uuid` field on conversation objects — it is not possible to determine from this export which conversations belong to which project.

**"Inactive" means truly inactive — among billable users only.**
The Inactive Accounts section only shows users with zero web conversations AND zero CLI lines. Users with any activity in either channel are excluded. Unassigned seats are excluded entirely and never appear as inactive.

**`data/users.json` may contain stale or unassigned accounts.**
Always cross-reference with `data/members-*.csv` (email join) to determine current membership and seat tier. Users absent from the members CSV have been removed from the org and are excluded from all metrics.
