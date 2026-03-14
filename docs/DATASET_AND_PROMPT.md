# ProcessBench GSM8K: dataset summary and assessment prompt

## 1. Dataset information

| Quantity | Value |
|----------|--------|
| **Total rows (solution traces)** | 400 |
| **Unique problems** | 375 |
| **Unique generators (LLMs)** | 12 |

- Each row is one **LLM-generated** step-by-step solution (from the model in `generator`) for a math problem, with a **human expert** annotation for the earliest erroneous step (or `-1` if all steps are correct). We refer to this human annotation as **gold_label** when evaluating assessment; in the dataset it is stored as the `label` field.
- ProcessBench does **not** contain human student solutions; it contains LLM-generated solutions with human annotations.
- 351 problems have a single solution trace; 24 problems have 2 or 3 traces (same problem, different generator).

**Generators:**  
Llama-3.1-70B-Instruct, Llama-3.1-8B-Instruct, Meta-Llama-3-70B-Instruct, Meta-Llama-3-8B-Instruct, Qwen2-1.5B-Instruct, Qwen2-72B-Instruct, Qwen2-7B-Instruct, Qwen2.5-1.5B-Instruct, Qwen2.5-72B-Instruct, Qwen2.5-7B-Instruct, Qwen2.5-Math-72B-Instruct, Qwen2.5-Math-7B-Instruct.

**Per-row fields in `dataset/gsm8k.json`:**  
`id`, `generator`, `problem`, `steps`, `final_answer_correct`, `label`
- **`label`** (human annotation; we call it **gold_label** when used as ground truth): 1-based index of the earliest erroneous step, or `-1` if all steps are correct.

---

## 2. Assessment prompt for the LLM

The following is the exact system + user prompt used for the **assessment condition** (step-level verifier). The model is asked to output a JSON object with `llm_label`, `rationale`, and `error_type`. Compare **llm_label** to the dataset **gold_label** (field `label`).

### System message

```
You are a step-level mathematical reasoning verifier.

Your task is to evaluate a step-by-step solution to a math problem and identify the earliest step that contains an error.

Evaluation objective:
- Return the index of the earliest erroneous step.
- Return -1 if all steps are correct.

Error criteria:
A step should be considered erroneous if it contains one or more of the following:
1. Mathematical error: incorrect calculation, algebraic manipulation, or formula application.
2. Logical error: invalid deduction, unsupported assumption, or flawed inference.
3. Conceptual error: misunderstanding or misapplication of the mathematical concept or the problem conditions.
4. Completeness error: omission of a necessary condition, constraint, or justification that affects the validity of the step.

Instructions:
1. Read the problem carefully.
2. Evaluate the solution strictly step by step, in order.
3. For each step, judge whether it is valid based on:
   - the problem statement, and
   - the previously verified steps.
4. Stop at the first erroneous step.
5. Do not continue evaluating later steps once the first error is found.
6. If all steps are correct, return -1.
7. Be concise and precise. Do not rewrite the full solution.

Output format:
Return a JSON object with exactly these fields:
{
  "llm_label": <integer>,
  "rationale": "<brief explanation of why this is the earliest error, or why all steps are correct>",
  "error_type": "<mathematical | logical | conceptual | completeness | none>"
}
```

### User message (template)

```
Now evaluate the following example.

Problem:
{problem}

Steps:
{steps}
```

Here `{steps}` is the list of solution steps formatted as:

```
Step 1: <first step text>
Step 2: <second step text>
...
```

In code, the prompt is built in `prompts.py` and used by `main.run_assessment(problem, steps)`.
