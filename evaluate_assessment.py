"""
Parse assessment condition output: extract llm_label, rationale, llm_error_type from LLM JSON.
Compare llm_label to gold_label (human annotation) for correctness_llm_label.
"""
import json
import re


def parse_assessment_response(raw: str) -> dict:
    """
    Parse the raw LLM response (JSON with llm_label, rationale, error_type).
    Returns dict with keys: llm_label (int or None), rationale (str or None), llm_error_type (str or None).
    Accepts "llm_label" or "label", and "error_type" (stored as llm_error_type).
    """
    out = {"llm_label": None, "rationale": None, "llm_error_type": None}
    raw = raw.strip()
    # Try to extract JSON (may be wrapped in ```json ... ```)
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if m:
        raw = m.group(1).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return out
    out["llm_label"] = data.get("llm_label") if data.get("llm_label") is not None else data.get("label")
    out["rationale"] = data.get("rationale")
    out["llm_error_type"] = data.get("error_type")
    return out


def correctness_llm_label(llm_label: int | None, gold_label: int) -> bool | None:
    """True if llm_label equals gold_label; False if not; None if llm_label is missing."""
    if llm_label is None:
        return None
    return llm_label == gold_label
