"""Download ProcessBench from Hugging Face and save as JSON in dataset/.
- gsm8k: run with no args (or --split gsm8k); saves dataset/gsm8k.json (no gold_answer from HF; use repo file for gold).
- math, olympiadbench, omnimath: use --split math olympiadbench omnimath to download each, randomly sample 400, save dataset/<split>.json.
"""
import argparse
import json
import os
import random
import re
from pathlib import Path

SUPPORTED_SPLITS = ("gsm8k", "math", "olympiadbench", "omnimath")
SAMPLE_SIZE = 400
RANDOM_SEED = 42


def _to_serializable(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, list):
        return [_to_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj


def _extract_gold_from_steps(steps: list) -> str | None:
    """Try to extract final answer from last step (e.g. \\boxed{42})."""
    if not steps:
        return None
    last = steps[-1] if isinstance(steps[-1], str) else str(steps[-1])
    m = re.search(r"\\boxed\{([^}]+)\}", last)
    if m:
        return m.group(1).strip()
    return None


def main():
    try:
        from datasets import load_dataset
    except ImportError:
        raise SystemExit("Install datasets: pip install datasets")

    parser = argparse.ArgumentParser(description="Download ProcessBench; use --split to get math, olympiadbench, omnimath (400 random each).")
    parser.add_argument("--split", nargs="+", default=["gsm8k"], metavar="SPLIT", help=f"Split(s) to download: {', '.join(SUPPORTED_SPLITS)} (default: gsm8k)")
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE, help=f"Max items to keep per split for math/olympiadbench/omnimath (default: {SAMPLE_SIZE})")
    parser.add_argument("--seed", type=int, default=RANDOM_SEED, help=f"Random seed for sampling (default: {RANDOM_SEED})")
    args = parser.parse_args()

    for s in args.split:
        if s not in SUPPORTED_SPLITS:
            raise SystemExit(f"Unsupported split: {s}. Use one of {SUPPORTED_SPLITS}")

    root = Path(__file__).resolve().parent.parent
    dataset_dir = root / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = root / ".cache" / "hf"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir)

    for split in args.split:
        print(f"Loading Qwen/ProcessBench (split={split}) from Hugging Face...")
        ds = load_dataset("Qwen/ProcessBench", split=split, cache_dir=str(cache_dir))
        n_total = len(ds)
        indices = list(range(n_total))
        if split != "gsm8k" and n_total > args.sample_size:
            rng = random.Random(args.seed)
            rng.shuffle(indices)
            indices = indices[: args.sample_size]
            print(f"  Randomly sampled {args.sample_size} of {n_total} (seed={args.seed})")
        else:
            indices = indices[:n_total]

        records = []
        for i in indices:
            row = ds[i]
            steps = _to_serializable(row["steps"])
            gold = _extract_gold_from_steps(steps) if steps else None
            records.append({
                "id": _to_serializable(row["id"]),
                "generator": _to_serializable(row["generator"]),
                "problem": _to_serializable(row["problem"]),
                "steps": _to_serializable(row["steps"]),
                "final_answer_correct": _to_serializable(row["final_answer_correct"]),
                "label": _to_serializable(row["label"]),
                "gold_answer": gold,
            })

        out_file = dataset_dir / f"{split}.json"
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        print(f"Saved {len(records)} examples to {out_file}")
    print("Done. dataset/ contains one .json per requested split.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main() or 0)
