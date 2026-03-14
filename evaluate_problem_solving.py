"""
Evaluate problem-solving output: compare LLM final answer to ground truth.

Final-answer extraction: rule-based only (no second LLM). We parse the solver's
llm_solution text with regex to find the final answer, in this order:
  - "Final answer: <number>" (requested in the solver prompt)
  - "#### <number>" (GSM8K style)
  - "\\boxed{<number>}"
  - last line that looks like a number
Gold answers come from each item's "gold_answer" in dataset/gsm8k.json.
"""
import re


def normalize_answer(s: str) -> str:
    """Normalize for comparison: strip, collapse whitespace, remove common punctuation/symbols around numbers."""
    s = " ".join(str(s).strip().split())
    s = re.sub(r"[\$,]", "", s)
    return s


def extract_final_answer_from_llm_output(response: str) -> str | None:
    """
    Extract the final answer from the LLM problem-solving response.
    Looks for: "Final answer: 42", "#### 42", "\\boxed{42}", or last line that looks like a number.
    """
    response = response.strip()
    m = re.search(r"Final answer\s*:\s*(.+?)(?:\.|$)", response, re.IGNORECASE | re.DOTALL)
    if m:
        return normalize_answer(m.group(1).strip())
    m = re.search(r"####\s*(.+)", response)
    if m:
        return normalize_answer(m.group(1).strip())
    m = re.search(r"\\boxed\{([^}]+)\}", response)
    if m:
        return normalize_answer(m.group(1).strip())
    lines = [ln.strip() for ln in response.splitlines() if ln.strip()]
    for ln in reversed(lines):
        if re.match(r"^[\d.,\-\+\/\s]+$", ln) or re.match(r"^-?\d+$", ln):
            return normalize_answer(ln)
    return None


def is_correct(predicted: str | None, gold: str) -> bool:
    """Compare predicted final answer to gold (both normalized)."""
    if predicted is None:
        return False
    pred_n = normalize_answer(predicted)
    gold_n = normalize_answer(gold)
    if pred_n == gold_n:
        return True
    try:
        pn = float(re.sub(r"[^\d.\-]", "", pred_n) or "nan")
        gn = float(re.sub(r"[^\d.\-]", "", gold_n) or "nan")
        return pn == gn
    except ValueError:
        pass
    return False


def evaluate_problem_solving_outputs(
    items: list[dict],
    outputs: list[str],
    *,
    id_key: str = "id",
    gold_key: str = "gold_answer",
) -> tuple[int, int, list[dict]]:
    """
    items: list of rows from gsm8k.json (each must have id and gold_answer).
    outputs: list of raw LLM responses in same order as items.
    Returns (num_correct, total_with_gold, results).
    """
    num_correct = 0
    total_with_gold = 0
    results = []
    for row, out in zip(items, outputs):
        pid = row[id_key]
        gold = row.get(gold_key)
        pred = extract_final_answer_from_llm_output(out)
        correct = is_correct(pred, gold) if gold is not None else None
        if gold is not None:
            total_with_gold += 1
            if correct is True:
                num_correct += 1
        results.append({
            "id": pid,
            "correct": correct,
            "predicted": pred,
            "gold": gold,
        })
    return num_correct, total_with_gold, results
