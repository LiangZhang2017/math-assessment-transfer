# One example output per task

One concrete example for **Task 1 (solving)** and one for **Task 2 (assessment)**.

---

## Task 1: Problem-solving — example output

**Input to the model:** the problem only (no solution steps).

**Example item:** `gsm8k-1` (Cindy's books).

**What the LLM returns (raw):** the full solution text. Example:

```
To find the total weight of the books Cindy is carrying, we add the weight of each type.

Math and science: 2 books × 2 pounds each = 4 pounds; she has 2 math and 2 science, so 4 + 4 = 8 pounds.
French: 4 pounds.
English: 3 pounds.
History: twice the English book = 2 × 3 = 6 pounds.

Total: 8 + 4 + 3 + 6 = 21 pounds.

Final answer: 21
```

**What we save (e.g. in `output/gpt-4o/solving/gsm8k-1.json`):**

```json
{
  "id": "gsm8k-1",
  "problem": "Cindy's math and science books weigh 2 pounds each.  Her French book weighs 4 pounds and her English book weighs 3 pounds.  Her history book weighs twice as much as her English book.  If Cindy carries all of her books at once, what will be the total weight of the books she is carrying?",
  "llm_solution": "To find the total weight of the books Cindy is carrying, we add the weight of each type.\n\nMath and science: 2 books × 2 pounds each = 4 pounds; she has 2 math and 2 science, so 4 + 4 = 8 pounds.\nFrench: 4 pounds.\nEnglish: 3 pounds.\nHistory: twice the English book = 2 × 3 = 6 pounds.\n\nTotal: 8 + 4 + 3 + 6 = 21 pounds.\n\nFinal answer: 21",
  "llm_answer": "21",
  "gold": "17",
  "correctness": false
}
```

Here **gold** is from the dataset (`gold_answer`); **llm_answer** is extracted from **llm_solution**; **correctness** is false because 21 ≠ 17 (dataset gold for this item is 17).

---

## Task 2: Assessment — example output

**Input to the model:** the problem + the benchmark solution steps (from the dataset).

**Example item:** `gsm8k-0` (Sue's flamingos). The benchmark steps have an error (gold_label = 1, i.e. earliest error at step 1 in the dataset convention).

**What the LLM returns (raw):** a JSON string. Example:

```json
{
  "llm_label": 2,
  "rationale": "Step 2 contains a logical error. It correctly computes 6 flamingos taken and painted white and 12 pink remaining, but then states 'Sue has (12 + 6 = 18) pink flamingos and 6 white flamingos.' The 18 is the total count on the yard, not the number of pink flamingos. The number of pink flamingos at end of Saturday is 12, not 18. This error propagates to the final answer.",
  "error_type": "logical"
}
```

**What we save** (e.g. in `output/gpt-4o/assessment/gsm8k-0.json`): **original dataset row** plus **llm_label**, **rationale**, **llm_error_type**, **correctness_llm_label** (true iff llm_label matches human `label`).

```json
{
  "id": "gsm8k-0",
  "generator": "Qwen2-7B-Instruct",
  "problem": "Sue lives in a fun neighborhood...",
  "steps": ["...", "...", "...", "..."],
  "final_answer_correct": false,
  "label": 1,
  "gold_answer": "24",
  "llm_label": 2,
  "rationale": "Step 2 contains a logical error. It correctly computes 6 flamingos taken and painted white and 12 pink remaining, but then states 'Sue has (12 + 6 = 18) pink flamingos and 6 white flamingos.' The 18 is the total count on the yard, not the number of pink flamingos.",
  "llm_error_type": "logical",
  "correctness_llm_label": false
}
```

| Added field | Meaning |
|-------------|--------|
| **llm_label** | Model's predicted earliest error step (1-based) or −1. |
| **rationale** | Model's brief explanation. |
| **llm_error_type** | Model's error type from response `error_type` (e.g. mathematical, logical, conceptual, completeness, none). |
| **correctness_llm_label** | True if llm_label equals human **label** (gold_label); false otherwise. |

Run: `python scripts/run_assessment_eval.py --model gpt-4o` → writes `output/gpt-4o/assessment/<id>.json` and `summary.txt`.
