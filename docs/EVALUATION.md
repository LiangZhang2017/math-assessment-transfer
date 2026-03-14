# Evaluating problem-solving and assessment separately

## Two separate conditions

1. **Problem-solving**  
   The model receives only the **problem** and generates a step-by-step solution and final answer.  
   Use: `main.run_problem_solving(problem)`.

2. **Assessment**  
   The model receives the **problem + benchmark solution steps** and identifies the earliest erroneous step (or −1).  
   Use: `main.run_assessment(problem, steps)`.

You can run them independently.

---

## Ground truth

- **Problem-solving**: Each item in `dataset/gsm8k.json` has a **`gold_answer`** field (final answer for that problem). Use it to evaluate the LLM’s problem-solving output.
- **Assessment**: The human annotation is **gold_label** (earliest erroneous step index, or −1). Compare the model’s **llm_label** (from the assessment JSON) to **gold_label**. (In the dataset the field is `label`.)

---

## Solver persona

The problem-solving LLM is given a **persona** in the system prompt (who the agent is). It is defined in **`prompts.py`**:

- **`SOLVER_PERSONA`** – default: *"You are an expert mathematical reasoning agent. You specialize in grade-school level math word problems: you read carefully, reason step by step, and produce a single correct numeric answer."*
- **`get_problem_solving_system(persona=None)`** – builds the full system prompt; pass a custom string to override the persona.

So the solver is a single LLM used with this persona; you can change `SOLVER_PERSONA` or call `get_problem_solving_system("Your custom persona...")` when building messages.

## How the final answer is extracted (no second LLM)

**We do not use another LLM** to get the final answer. The same solver model produces **llm_solution** (full text); we then **parse that text with regex** in **`evaluate_problem_solving.extract_final_answer_from_llm_output()`**:

1. **"Final answer: &lt;number&gt;"** (what we ask for in the prompt)
2. **"#### &lt;number&gt;"** (GSM8K style)
3. **`\boxed{<number>}`**
4. Otherwise, the last line that looks like a number

So: **one solver LLM** → full solution text → **rule-based extraction** → **llm_answer** → compared to **gold_answer** for correctness.

## Evaluating problem-solving

Use **`evaluate_problem_solving.py`**:

- `extract_final_answer_from_llm_output(response)` – rule-based parse (see above).
- `is_correct(predicted, gold)` – compares predicted vs gold (normalized).
- `evaluate_problem_solving_outputs(items, outputs)` – expects each item to have **`gold_answer`**; returns `(num_correct, total_with_gold, results)`.

Example:

```python
from main import load_processbench, run_problem_solving
from evaluate_problem_solving import evaluate_problem_solving_outputs

dataset = load_processbench("gsm8k")  # each row has gold_answer
outputs = [run_problem_solving(row["problem"]) for row in dataset]

num_correct, total_with_gold, results = evaluate_problem_solving_outputs(dataset, outputs)
print(f"Problem-solving accuracy: {num_correct}/{total_with_gold} = {num_correct/total_with_gold:.2%}")
```

## Evaluating assessment

Run `run_assessment(problem, steps)`, parse the model’s JSON, and compare its **llm_label** to the row’s **gold_label** (dataset field `label`; exact-match accuracy).
