"""
Run problem-solving with gpt-4o and evaluate vs gold_answer.
Output: output/gpt-4o/solving/<id>.json (one per problem) + summary.txt.

Usage:
  python scripts/run_gpt4o.py              # all 400 items
  python scripts/run_gpt4o.py --limit 20   # first 20 only
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_problem_solving_eval.py"

if __name__ == "__main__":
    cmd = [sys.executable, str(SCRIPT), "--model", "gpt-4o"] + sys.argv[1:]
    sys.exit(subprocess.run(cmd).returncode)
