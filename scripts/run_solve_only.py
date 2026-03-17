"""
Run the LLM to solve each problem only (no evaluation).
Saves one JSON per problem under output/<model>/solving/ with id, problem, llm_solution.
Also saves responses.json so you can run evaluation later with:
  python scripts/run_problem_solving_eval.py --no-call --responses output/<model>/solving/responses.json --model <model>

Usage:
  python scripts/run_solve_only.py                    # default model, all items
  python scripts/run_solve_only.py --model gpt-4o    # use gpt-4o
  python scripts/run_solve_only.py --limit 20        # first 20 problems only
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import load_processbench, run_problem_solving
import config


def safe_dirname(model: str) -> str:
    return model.replace("/", "-").strip() or "default"


def safe_filename(item_id: str) -> str:
    safe = re.sub(r"[^\w\-.]", "_", str(item_id))
    return f"{safe}.json" if not safe.endswith(".json") else safe


def main():
    parser = argparse.ArgumentParser(description="Run LLM to solve each problem (no evaluation)")
    parser.add_argument("--limit", type=int, default=None, help="Run only first N items")
    parser.add_argument("--split", type=str, default="gsm8k", help="Dataset split: gsm8k, math, olympiadbench, omnimath (default: gsm8k)")
    parser.add_argument("--model", type=str, default=None, help="Model deployment name (default: from .env)")
    parser.add_argument("--out-dir", type=str, default=None, help="Output directory (default: output/<model>/solving/<split>/)")
    args = parser.parse_args()

    model = args.model or config.AZURE_OPENAI_MODEL
    out_dir = Path(args.out_dir) if args.out_dir else ROOT / "output" / safe_dirname(model) / "solving" / args.split
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_processbench(args.split)
    if args.limit:
        dataset = dataset[: args.limit]
    n = len(dataset)
    print(f"Model: {model}")
    print(f"Output: {out_dir}")
    print(f"Solving {n} problems...")

    outputs = []
    for i, row in enumerate(dataset):
        if (i + 1) % 50 == 0 or i == 0:
            print(f"  {i + 1}/{n} ...")
        solution = run_problem_solving(row["problem"], model=args.model)
        outputs.append(solution)
        # Save one JSON per problem: id, problem, llm_solution
        path = out_dir / safe_filename(row["id"])
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                {"id": row["id"], "problem": row["problem"], "llm_solution": solution},
                f,
                indent=2,
                ensure_ascii=False,
            )

    # Save list of solution strings for later evaluation (--no-call --responses)
    responses_path = out_dir / "responses.json"
    with open(responses_path, "w", encoding="utf-8") as f:
        json.dump(outputs, f, indent=2, ensure_ascii=False)
    print(f"Done. Wrote {n} JSONs + {responses_path}")
    print(f"To evaluate later: python scripts/run_problem_solving_eval.py --no-call --responses {responses_path} --model {model}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
