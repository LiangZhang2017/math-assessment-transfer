"""
Compute correctness percentage per run and mean across runs for solving and/or assessment.
Example: python scripts/aggregate_run_correctness.py --runs run_1 run_2 run_3 --model gpt-4
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import config


def safe_dirname(model: str) -> str:
    return model.replace("/", "-").strip() or "default"


def collect_solving_correctness(out_dir: Path) -> tuple[int, int]:
    """Return (num_correct, total) from output/<model>/solving/<run>/*.json (field: correctness)."""
    correct, total = 0, 0
    for path in out_dir.glob("*.json"):
        if path.name == "responses.json":
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            total += 1
            if data.get("correctness") is True:
                correct += 1
        except (json.JSONDecodeError, KeyError):
            pass
    return correct, total


def collect_assessment_correctness(out_dir: Path) -> tuple[int, int]:
    """Return (num_correct, total) from output/<model>/assessment/<run>/*.json (field: correctness_llm_label)."""
    correct, total = 0, 0
    for path in out_dir.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            total += 1
            if data.get("correctness_llm_label") is True:
                correct += 1
        except (json.JSONDecodeError, KeyError):
            pass
    return correct, total


def main():
    parser = argparse.ArgumentParser(description="Compute correctness % per run and mean across runs.")
    parser.add_argument("--runs", nargs="+", default=["run_1", "run_2", "run_3"], metavar="RUN", help="Run labels (default: run_1 run_2 run_3)")
    parser.add_argument("--split", type=str, default="gsm8k", help="Dataset split: gsm8k, math, olympiadbench, omnimath (default: gsm8k)")
    parser.add_argument("--model", type=str, default=None, help="Model name (default: from .env)")
    parser.add_argument("--task", choices=["solving", "assessment", "both"], default="both", help="Which task to aggregate (default: both)")
    args = parser.parse_args()

    model = args.model or config.AZURE_OPENAI_MODEL
    base = ROOT / "output" / safe_dirname(model)

    if args.task in ("solving", "both"):
        print(f"Task: Problem-solving (split={args.split}, correctness vs gold_answer)")
        print("-" * 50)
        pct_list = []
        for run in args.runs:
            out_dir = base / "solving" / args.split / run
            if not out_dir.is_dir():
                print(f"  {run}: (no folder)")
                continue
            correct, total = collect_solving_correctness(out_dir)
            pct = (correct / total * 100) if total else 0.0
            pct_list.append(pct)
            print(f"  {run}: {correct}/{total} = {pct:.2f}%")
        # If no run folders found, try split folder directly (output when run without --run)
        if not pct_list:
            split_dir = base / "solving" / args.split
            if split_dir.is_dir():
                correct, total = collect_solving_correctness(split_dir)
                if total:
                    pct = (correct / total * 100)
                    pct_list.append(pct)
                    print(f"  (single run, no run label): {correct}/{total} = {pct:.2f}%")
        if pct_list:
            mean_pct = sum(pct_list) / len(pct_list)
            print(f"  Mean across runs: {mean_pct:.2f}%")
        print()

    if args.task in ("assessment", "both"):
        print(f"Task: Assessment (split={args.split}, correctness_llm_label vs human label)")
        print("-" * 50)
        pct_list = []
        for run in args.runs:
            out_dir = base / "assessment" / args.split / run
            if not out_dir.is_dir():
                print(f"  {run}: (no folder)")
                continue
            correct, total = collect_assessment_correctness(out_dir)
            pct = (correct / total * 100) if total else 0.0
            pct_list.append(pct)
            print(f"  {run}: {correct}/{total} = {pct:.2f}%")
        if not pct_list:
            split_dir = base / "assessment" / args.split
            if split_dir.is_dir():
                correct, total = collect_assessment_correctness(split_dir)
                if total:
                    pct = (correct / total * 100)
                    pct_list.append(pct)
                    print(f"  (single run, no run label): {correct}/{total} = {pct:.2f}%")
        if pct_list:
            mean_pct = sum(pct_list) / len(pct_list)
            print(f"  Mean across runs: {mean_pct:.2f}%")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
