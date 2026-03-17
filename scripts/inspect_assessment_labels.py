"""
Inspect how the LLM labeled the solution steps vs human (gold) label.
Prints per-step view: which step human marked as first error, which step LLM marked, and rationale.
Usage:
  python scripts/inspect_assessment_labels.py --split gsm8k --run run_1 --model gpt-4 --limit 3
  python scripts/inspect_assessment_labels.py --split gsm8k --run run_1 --id gsm8k-0 --model gpt-4
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


def main():
    parser = argparse.ArgumentParser(description="Inspect assessment: LLM vs human step labels.")
    parser.add_argument("--split", type=str, default="gsm8k", help="Dataset split (default: gsm8k)")
    parser.add_argument("--run", type=str, default=None, help="Run folder (e.g. run_1); if not set, list available")
    parser.add_argument("--model", type=str, default=None, help="Model name (default: from .env)")
    parser.add_argument("--id", type=str, default=None, help="Single item id to show (e.g. gsm8k-0); if set, only that item")
    parser.add_argument("--limit", type=int, default=5, help="Max number of items to show when not using --id (default: 5)")
    parser.add_argument("--out-dir", type=str, default=None, help="Override assessment dir (default: output/<model>/assessment/<split>/<run>/)")
    args = parser.parse_args()

    model = args.model or config.AZURE_OPENAI_MODEL
    base = ROOT / "output" / safe_dirname(model) / "assessment" / args.split
    if args.out_dir:
        assess_dir = Path(args.out_dir)
    elif args.run:
        assess_dir = base / args.run
    else:
        # List runs and exit
        if not base.is_dir():
            print(f"No directory: {base}")
            return 1
        runs = sorted(d for d in base.iterdir() if d.is_dir())
        print(f"Assessment output for split={args.split}, model={model}:")
        for r in runs:
            n = len(list(r.glob("*.json")))
            print(f"  {r.name}: {n} files")
        return 0

    if not assess_dir.is_dir():
        print(f"Directory not found: {assess_dir}")
        return 1

    # Collect JSONs
    if args.id:
        path = assess_dir / f"{args.id}.json"
        if not path.exists():
            path = assess_dir / f"{args.id.replace('-', '_')}.json"
        paths = [path] if path.exists() else []
    else:
        paths = sorted(assess_dir.glob("*.json"))[: args.limit]

    if not paths:
        print(f"No JSONs found in {assess_dir}" + (f" for id={args.id}" if args.id else ""))
        return 1

    for path in paths:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        item_id = data.get("id", path.stem)
        steps = data.get("steps", [])
        human_label = data.get("label")
        llm_label = data.get("llm_label")
        rationale = data.get("rationale") or "(none)"
        correct = data.get("correctness_llm_label")

        n_steps = len(steps)
        print()
        print("=" * 70)
        print(f"id: {item_id}  |  steps: {n_steps}  |  human (gold) label: {human_label}  |  llm_label: {llm_label}  |  match: {correct}")
        print("=" * 70)
        print("Human = earliest error step (1-based); -1 = all correct. Same for LLM.")
        print()
        for i, step in enumerate(steps, start=1):
            human_err = " <-- HUMAN" if human_label is not None and human_label == i else ""
            llm_err = " <-- LLM" if llm_label is not None and llm_label == i else ""
            text = (step[:120] + "..." if len(step) > 120 else step).replace("\n", " ")
            print(f"  Step {i}:{human_err}{llm_err}")
            print(f"    {text}")
            print()
        print("Rationale:", rationale)
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
