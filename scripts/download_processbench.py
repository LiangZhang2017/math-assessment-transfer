"""Download ProcessBench GSM8K from Hugging Face and save as JSON in dataset/. Note: HF dataset has no gold_answer; use the existing gsm8k.json in this repo which already includes gold_answer."""
import json
import os
from pathlib import Path


def _to_serializable(obj):
    if hasattr(obj, "item"):
        return obj.item()
    if isinstance(obj, list):
        return [_to_serializable(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_serializable(v) for k, v in obj.items()}
    return obj


def main():
    try:
        from datasets import load_dataset
    except ImportError:
        raise SystemExit("Install datasets: pip install datasets")

    root = Path(__file__).resolve().parent.parent
    out_file = root / "dataset" / "gsm8k.json"
    # Cache outside dataset/ so dataset/ contains only gsm8k.json
    cache_dir = root / ".cache" / "hf"
    cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ["HF_HOME"] = str(cache_dir)

    print("Loading Qwen/ProcessBench (split=gsm8k) from Hugging Face...")
    dataset = load_dataset("Qwen/ProcessBench", split="gsm8k", cache_dir=str(cache_dir))

    records = []
    for i in range(len(dataset)):
        row = dataset[i]
        records.append({
            "id": _to_serializable(row["id"]),
            "generator": _to_serializable(row["generator"]),
            "problem": _to_serializable(row["problem"]),
            "steps": _to_serializable(row["steps"]),
            "final_answer_correct": _to_serializable(row["final_answer_correct"]),
            "label": _to_serializable(row["label"]),
        })

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(records)} GSM8K examples to {out_file} (no gold_answer; use repo gsm8k.json for gold_answer).")


if __name__ == "__main__":
    main()
