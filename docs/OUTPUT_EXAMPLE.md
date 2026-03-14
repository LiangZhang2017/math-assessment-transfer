# Output layout and example

Output lives under **`output/<model>/`** with one subfolder per task: **`solving/`** and **`assessment/`**.

---

## Folder structure

```
output/
  gpt-4o/
    solving/           # Task 1: problem-solving
      gsm8k-0.json
      gsm8k-1.json
      ...
      summary.txt
      responses.json   # only if you ran run_solve_only.py (list of solution strings)
    assessment/        # Task 2: step-level assessment
      gsm8k-0.json
      ...
      summary.txt
```

---

## One file per problem: `<id>.json`

Each **`gsm8k-0.json`**, **`gsm8k-1.json`**, etc. has this shape.

**If you ran solve + evaluate** (e.g. `run_problem_solving_eval.py` or solve then `--no-call`):

```json
{
  "id": "gsm8k-0",
  "problem": "Sue lives in a fun neighborhood.  One weekend, the neighbors decided to play a prank on Sue.  On Friday morning, the neighbors placed 18 pink plastic flamingos out on Sue's front yard.  On Saturday morning, the neighbors took back one third of the flamingos, painted them white, and put these newly painted white flamingos back out on Sue's front yard.  Then, on Sunday morning, they added another 18 pink plastic flamingos to the collection. At noon on Sunday, how many more pink plastic flamingos were out than white plastic flamingos?",
  "llm_solution": "Let's work through this step by step.\n\nOn Friday: 18 pink flamingos are placed.\n\nOn Saturday: The neighbors take back 1/3 of 18 = 6 flamingos, paint them white, and put them back. So there are 18 - 6 = 12 pink left, plus 6 white = 12 pink and 6 white (18 total on the yard). Wait, we need to re-read: they put the 6 white back, so now we have 12 pink + 6 white = 18 pink and 6 white? No: originally 18 pink. They take 6 away, paint those 6 white, put those 6 back. So 12 pink + 6 white on the yard.\n\nOn Sunday: They add 18 more pink. So 12 + 18 = 30 pink and still 6 white.\n\nDifference: 30 - 6 = 24 more pink than white.\n\nFinal answer: 24",
  "llm_answer": "24",
  "gold": "24",
  "correctness": true
}
```

**If you ran solve only** (`run_solve_only.py`), each file has only:

```json
{
  "id": "gsm8k-0",
  "problem": "Sue lives in a fun neighborhood.  One weekend...",
  "llm_solution": "Let's work through this step by step.\n\nOn Friday: 18 pink flamingos..."
}
```

| Field | Meaning |
|-------|--------|
| **id** | Same as in the dataset (e.g. `gsm8k-0`). |
| **problem** | The problem text from the dataset. |
| **llm_solution** | Full step-by-step solution text from the LLM. |
| **llm_answer** | Final answer we extracted from `llm_solution` (only after evaluation). |
| **gold** | Ground-truth answer from the dataset (only after evaluation). |
| **correctness** | `true` or `false` vs gold (only after evaluation). |

---

## Summary file: `summary.txt`

One line with overall accuracy (only after evaluation):

```
Correct: 380 / 400 = 95.00%
```

---

## Optional: `responses.json`

Written by **`run_solve_only.py`**: a JSON array of strings, one per problem in dataset order (same as `llm_solution` for each item). Used later for:

```bash
python scripts/run_problem_solving_eval.py --no-call --responses output/gpt-4o/solving/responses.json --model gpt-4o
```
