"""
Run problem-solving with the configured LLM on dataset/gsm8k.json,
then evaluate correctness vs gold_answer.
Writes one JSON per problem immediately (so reruns can resume from the last written file).
Output: output/<model>/solving/[run/]<id>.json plus summary.txt. Use --run <name> to save to a separate run folder (e.g. run_1). Existing files in that folder are skipped on rerun.
"""
import argparse
import json
import re
import sys
from pathlib import Path

# project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import load_processbench, run_problem_solving
from evaluate_problem_solving import evaluate_problem_solving_outputs
import config


def safe_dirname(model: str) -> str:
    """Use model as directory name; avoid path characters."""
    return model.replace("/", "-").strip() or "default"


def safe_run_dir(run: str | None) -> str:
    """Safe subdirectory name for a run (e.g. run_1, exp_a)."""
    if not (run or "").strip():
        return ""
    return re.sub(r"[^\w\-.]", "_", str(run).strip()).strip("_") or "run"


def safe_filename(item_id: str) -> str:
    """Safe filename from id (e.g. gsm8k-0 -> gsm8k-0.json)."""
    safe = re.sub(r"[^\w\-.]", "_", str(item_id))
    return f"{safe}.json" if not safe.endswith(".json") else safe


def main():
    parser = argparse.ArgumentParser(description="Run LLM problem-solving and evaluate vs gold_answer. Writes one file per problem; rerun skips existing.")
    parser.add_argument("--limit", type=int, default=None, help="Run only first N items (default: all)")
    parser.add_argument("--model", type=str, default=None, help="Model deployment name (default: from .env). Output written to output/<model>/solving/[run/]")
    parser.add_argument("--run", type=str, default=None, help="Run label: save to output/<model>/solving/<run>/ so multiple runs use different folders (e.g. --run run_1)")
    parser.add_argument("--out-dir", type=str, default=None, help="Override output directory (default: output/<model>/solving/ or .../solving/<run>/)")
    parser.add_argument("--no-call", action="store_true", help="Skip API calls; only evaluate (use with --responses)")
    parser.add_argument("--responses", type=str, default=None, help="JSON file of raw LLM responses (same order as dataset)")
    args = parser.parse_args()

    model = args.model or config.AZURE_OPENAI_MODEL
    base = ROOT / "output" / safe_dirname(model) / "solving"
    run_sub = safe_run_dir(args.run)
    out_dir = Path(args.out_dir) if args.out_dir else (base / run_sub if run_sub else base)
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_processbench("gsm8k")
    if args.limit:
        dataset = dataset[: args.limit]
    n = len(dataset)
    print(f"Model: {model}")
    print(f"Output: {out_dir} (one JSON per id, resume by skipping existing)")
    print(f"Items: {n}")

    if args.no_call and args.responses:
        with open(args.responses, encoding="utf-8") as f:
            outputs = json.load(f)
        assert len(outputs) >= n, f"Responses file has {len(outputs)} items, need {n}"
        outputs = outputs[:n]
        num_correct, total_with_gold, results = evaluate_problem_solving_outputs(dataset, outputs)
        for row, out_text, res in zip(dataset, outputs, results):
            path = out_dir / safe_filename(row["id"])
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "id": row["id"],
                    "problem": row["problem"],
                    "llm_solution": out_text,
                    "llm_answer": res["predicted"],
                    "gold": res["gold"],
                    "correctness": res["correct"],
                }, f, indent=2, ensure_ascii=False)
    else:
        # Per-item run with resume: skip ids that already have an output file
        done_ids = {p.stem for p in out_dir.glob("*.json") if p.name != "responses.json"}
        existing_correct = 0
        for path in out_dir.glob("*.json"):
            if path.name == "responses.json":
                continue
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("correctness") is True:
                    existing_correct += 1
            except (json.JSONDecodeError, KeyError):
                pass
        num_correct = existing_correct
        total_with_gold = sum(1 for r in dataset if r.get("gold_answer") is not None)
        ran = 0
        for i, row in enumerate(dataset):
            item_id = row["id"]
            if item_id in done_ids:
                continue
            if (ran + 1) % 50 == 0 or ran == 0:
                print(f"  Running {i + 1}/{n} (writing each immediately, skip existing) ...")
            out_text = run_problem_solving(row["problem"], model=args.model)
            _, _, results = evaluate_problem_solving_outputs([row], [out_text])
            res = results[0]
            num_correct += 1 if res["correct"] is True else 0
            path = out_dir / safe_filename(item_id)
            with open(path, "w", encoding="utf-8") as f:
                json.dump({
                    "id": item_id,
                    "problem": row["problem"],
                    "llm_solution": out_text,
                    "llm_answer": res["predicted"],
                    "gold": res["gold"],
                    "correctness": res["correct"],
                }, f, indent=2, ensure_ascii=False)
            done_ids.add(item_id)
            ran += 1
        print(f"  Ran {ran} new items (skipped {n - ran} already present).")
        total_with_gold = len(done_ids)  # report over items we have results for (partial or full)

    acc = num_correct / total_with_gold if total_with_gold else 0.0
    print()
    print("Correctness (vs gold_answer):")
    print(f"  Correct: {num_correct} / {total_with_gold} = {acc:.2%}")
    num_files = len(list(out_dir.glob("*.json"))) - (1 if (out_dir / "responses.json").exists() else 0)
    print(f"  Files in {out_dir}: {num_files}")

    summary_path = out_dir / "summary.txt"
    summary_path.write_text(f"Correct: {num_correct} / {total_with_gold} = {acc:.2%}\n", encoding="utf-8")
    print(f"  Saved {summary_path}")

    return 0 if total_with_gold else 1


if __name__ == "__main__":
    sys.exit(main())
