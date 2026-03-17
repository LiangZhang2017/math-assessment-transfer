"""
Run the assessment condition: for each item, LLM evaluates the benchmark solution steps.
Writes one JSON per problem immediately (so reruns can resume from the last written file).
Output: output/<model>/assessment/[run/]<id>.json. Use --run <name> to save to a separate run folder (e.g. run_1). Existing files in that folder are skipped on rerun.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from main import load_processbench, run_assessment
from evaluate_assessment import parse_assessment_response, correctness_llm_label
import config


def safe_dirname(model: str) -> str:
    return model.replace("/", "-").strip() or "default"


def safe_run_dir(run: str | None) -> str:
    """Safe subdirectory name for a run (e.g. run_1, exp_a)."""
    if not (run or "").strip():
        return ""
    return re.sub(r"[^\w\-.]", "_", str(run).strip()).strip("_") or "run"


def safe_filename(item_id: str) -> str:
    safe = re.sub(r"[^\w\-.]", "_", str(item_id))
    return f"{safe}.json" if not safe.endswith(".json") else safe


def main():
    parser = argparse.ArgumentParser(description="Run assessment condition; one file per problem, rerun skips existing.")
    parser.add_argument("--limit", type=int, default=None, help="Run only first N items")
    parser.add_argument("--split", type=str, default="gsm8k", help="Dataset split: gsm8k, math, olympiadbench, omnimath (default: gsm8k)")
    parser.add_argument("--model", type=str, default=None, help="Model deployment name (default: from .env)")
    parser.add_argument("--run", type=str, default=None, help="Run label: save to .../assessment/<split>/<run>/ (e.g. --run run_1)")
    parser.add_argument("--out-dir", type=str, default=None, help="Override output directory (default: output/<model>/assessment/ or .../assessment/<run>/)")
    args = parser.parse_args()

    model = args.model or config.AZURE_OPENAI_MODEL
    base = ROOT / "output" / safe_dirname(model) / "assessment" / args.split
    run_sub = safe_run_dir(args.run)
    out_dir = Path(args.out_dir) if args.out_dir else (base / run_sub if run_sub else base)
    out_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_processbench(args.split)
    if args.limit:
        dataset = dataset[: args.limit]
    n = len(dataset)
    print(f"Model: {model}")
    print(f"Output: {out_dir} (one JSON per id, resume by skipping existing)")
    print(f"Items: {n}")

    done_ids = {p.stem for p in out_dir.glob("*.json")}
    existing_correct = 0
    for path in out_dir.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if data.get("correctness_llm_label") is True:
                existing_correct += 1
        except (json.JSONDecodeError, KeyError):
            pass
    num_correct = existing_correct
    ran = 0
    for i, row in enumerate(dataset):
        item_id = row["id"]
        if item_id in done_ids:
            continue
        if (ran + 1) % 50 == 0 or ran == 0:
            print(f"  {i + 1}/{n} (writing each immediately, skip existing) ...")
        raw = run_assessment(row["problem"], row["steps"], model=args.model)
        parsed = parse_assessment_response(raw)
        gold_label = row["label"]
        correct = correctness_llm_label(parsed["llm_label"], gold_label)
        if correct is True:
            num_correct += 1
        out = {
            **row,
            "llm_label": parsed["llm_label"],
            "rationale": parsed["rationale"],
            "llm_error_type": parsed["llm_error_type"],
            "correctness_llm_label": correct,
        }
        path = out_dir / safe_filename(item_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(out, f, indent=2, ensure_ascii=False)
        done_ids.add(item_id)
        ran += 1
    print(f"  Ran {ran} new items (skipped {n - ran} already present).")

    total_done = len(done_ids)
    acc = num_correct / total_done if total_done else 0.0
    print()
    print("Assessment (llm_label vs human label):")
    print(f"  Correct: {num_correct} / {total_done} = {acc:.2%}")
    summary_path = out_dir / "summary.txt"
    summary_path.write_text(f"Correct: {num_correct} / {total_done} = {acc:.2%}\n", encoding="utf-8")
    print(f"  Saved {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
