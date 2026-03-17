"""
Run one or both tasks for multiple run labels with one command.
Use --task to run only solving, only assessment, or both (separately: run solving for all runs, then assessment for all runs).
Example: python scripts/run_multiple_runs.py --runs run_1 run_2 run_3 --task solving --model gpt-4
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOLVING = ROOT / "scripts" / "run_problem_solving_eval.py"
ASSESSMENT = ROOT / "scripts" / "run_assessment_eval.py"

TASKS = {
    "solving": [("Problem-solving", SOLVING)],
    "assessment": [("Assessment", ASSESSMENT)],
    "both": [("Problem-solving", SOLVING), ("Assessment", ASSESSMENT)],
}


def main():
    parser = argparse.ArgumentParser(
        description="Run one or both tasks for multiple runs. Use --task solving or --task assessment to run tasks separately."
    )
    parser.add_argument("--runs", nargs="+", required=True, metavar="RUN", help="Run labels (e.g. run_1 run_2 run_3)")
    parser.add_argument("--split", type=str, default="gsm8k", help="Dataset split: gsm8k, math, olympiadbench, omnimath (default: gsm8k)")
    parser.add_argument("--task", choices=list(TASKS), default="both", help="Task to run: solving, assessment, or both (default: both)")
    parser.add_argument("--model", type=str, default=None, help="Model deployment name (default: from .env)")
    parser.add_argument("--limit", type=int, default=None, help="Run only first N items per task (default: all)")
    args = parser.parse_args()

    model_args = ["--model", args.model] if args.model else []
    limit_args = ["--limit", str(args.limit)] if args.limit else []
    scripts_to_run = TASKS[args.task]

    for run in args.runs:
        print(f"\n{'='*60}\nRun: {run} (split={args.split})\n{'='*60}")
        for name, script in scripts_to_run:
            print(f"\n--- {name} ---")
            cmd = [sys.executable, str(script), "--run", run, "--split", args.split] + model_args + limit_args
            code = subprocess.run(cmd, cwd=str(ROOT)).returncode
            if code != 0:
                print(f"Exiting due to non-zero return code {code} from {script.name}")
                return code
    print(f"\nDone: {args.task} for {len(args.runs)} run(s): {', '.join(args.runs)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
