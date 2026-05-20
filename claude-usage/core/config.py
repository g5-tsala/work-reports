from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA = ROOT / "data"
REPORTS = ROOT / "reports"

CLAUDE_CODE_TOOLS = {"bash_tool", "view", "str_replace", "create_file", "str_replace_based_edit_tool"}
