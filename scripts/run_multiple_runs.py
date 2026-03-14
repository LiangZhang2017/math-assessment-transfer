"""
Run both tasks (problem-solving and assessment) for multiple run labels with one command.
Example: python scripts/run_multiple_runs.py --runs run_1 run_2 run_3 --model gpt-4
For each run, runs problem-solving then assessment; existing files in each run folder are skipped (resume).
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOLVING = ROOT / "scripts" / "run_problem_solving_eval.py"
ASSESSMENT = ROOT / "scripts" / "run_assessment_eval.py"


def main():
    parser = argparse.ArgumentParser(
        description="Run both tasks for multiple runs (e.g. --runs run_1 run_2 run_3). Each run: solving then assessment."
    )
    parser.add_argument("--runs", nargs="+", required=True, metavar="RUN", help="Run labels (e.g. run_1 run_2 run_3)")
    parser.add_argument("--model", type=str, default=None, help="Model deployment name (default: from .env)")
    parser.add_argument("--limit", type=int, default=None, help="Run only first N items per task (default: all)")
    args = parser.parse_args()

    model_args = ["--model", args.model] if args.model else []
    limit_args = ["--limit", str(args.limit)] if args.limit else []

    for run in args.runs:
        print(f"\n{'='*60}\nRun: {run}\n{'='*60}")
        for name, script in [("Problem-solving", SOLVING), ("Assessment", ASSESSMENT)]:
            print(f"\n--- {name} ---")
            cmd = [sys.executable, str(script), "--run", run] + model_args + limit_args
            code = subprocess.run(cmd, cwd=str(ROOT)).returncode
            if code != 0:
                print(f"Exiting due to non-zero return code {code} from {script.name}")
                return code
    print(f"\nDone: completed {len(args.runs)} run(s): {', '.join(args.runs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
