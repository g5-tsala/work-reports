# work-reports

Scripts that generate self-contained HTML reports.

## Reports

| Directory | Description |
|---|---|
| [`claude-usage/`](claude-usage/) | Claude AI usage across the G5 Partners org — active users, conversations, Claude Code activity, adoption funnel |

## Usage

Each report is self-contained. Navigate to the directory and run its script:

```bash
cd claude-usage
python3 report.py
# → reports/report-YYYY-MM-DD.html
```

See the directory's `AGENTS.md` for data sources, schema reference, and gotchas.
