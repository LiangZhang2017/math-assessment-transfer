"""
Main entry for ProcessBench: problem-solving and assessment conditions.
Set the model via AZURE_OPENAI_MODEL in .env or MODEL_OVERRIDE here (default: gpt-4).
"""
from pathlib import Path

import config
from llm_client import get_client, chat_completion

# Model selection: None = use .env AZURE_OPENAI_MODEL (default gpt-4)
MODEL_OVERRIDE: str | None = None
ACTIVE_MODEL = MODEL_OVERRIDE or config.AZURE_OPENAI_MODEL


def run_problem_solving(problem: str, model: str | None = None) -> str:
    """Problem-solving: model gets only the problem and returns solution + final answer (compared to gold_answer for correctness)."""
    from prompts import get_problem_solving_system, problem_solving_user_prompt
    client = get_client()
    messages = [
        {"role": "system", "content": get_problem_solving_system()},
        {"role": "user", "content": problem_solving_user_prompt(problem)},
    ]
    return chat_completion(client, messages, model=model or ACTIVE_MODEL)


def run_assessment(problem: str, steps: list[str], model: str | None = None) -> str:
    """Assessment condition: same agent (shared persona), assessment task. Evaluates given solution steps; returns JSON with llm_label, rationale, error_type."""
    from prompts import get_assessment_system, assessment_user_prompt
    client = get_client()
    messages = [
        {"role": "system", "content": get_assessment_system()},
        {"role": "user", "content": assessment_user_prompt(problem, steps)},
    ]
    return chat_completion(client, messages, model=model or ACTIVE_MODEL)


def load_processbench(split: str = "gsm8k"):
    """Load ProcessBench from local JSON. split in: gsm8k, math, olympiadbench, omnimath.
    Download with: python scripts/download_processbench.py --split gsm8k
    For math/olympiadbench/omnimath (400 random each): python scripts/download_processbench.py --split math olympiadbench omnimath
    """
    allowed = ("gsm8k", "math", "olympiadbench", "omnimath")
    if split not in allowed:
        raise ValueError(f"split must be one of {allowed}; got {split!r}.")
    path = Path(__file__).resolve().parent / "dataset" / f"{split}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"ProcessBench not found at {path}. Run: python scripts/download_processbench.py --split {split}"
        )
    with open(path, encoding="utf-8") as f:
        import json
        return json.load(f)


if __name__ == "__main__":
    # Override: MODEL_OVERRIDE = "gpt-4o" or set AZURE_OPENAI_MODEL in .env
    print(f"Using model: {ACTIVE_MODEL}")

    # Quick sanity check
    try:
        client = get_client()
        r = chat_completion(client, [{"role": "user", "content": "Say 42."}], model=ACTIVE_MODEL)
        print("API check:", r[:80] + "..." if len(r) > 80 else r)
    except Exception as e:
        print("API check failed:", e)
