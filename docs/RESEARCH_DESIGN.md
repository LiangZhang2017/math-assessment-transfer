# Research design: Does problem-solving expertise translate into assessment performance?

Your question: **Does mathematical problem-solving expertise in LLMs translate into assessment performance?**

Here are two clean designs and how they relate to the question.

---

## Design 1: Same agent (same model) — recommended for “transfer”

**Setup:** One LLM plays both roles:
- **Solver:** gets the problem only → produces solution + final answer.
- **Assessor:** gets the problem + **benchmark** solution steps → predicts earliest error step (or −1).

So the **same model** is used as solver and as assessor. The assessor always judges the **ProcessBench solution trace** (from the dataset), not its own solution.

**Why same agent?**

1. **Transfer is within-model.** You are asking: “In this model, does being good at solving go hand-in-hand with being good at assessing?” That is exactly what you get by using the same agent for both.
2. **Item-level analysis.** For each item you can ask: when this model **solved** the item correctly, did it also **assess** it correctly? And when it failed at solving, how did it do at assessment? So you can study transfer at the level of items, not only at the level of models.
3. **Matches your two-condition description.** You already have “problem-solving condition” and “assessment condition”; the natural reading is that the **same** model is run in both conditions.

**Analyses you can run:**

- **Model-level (if you have several models):** For each model, compute solving accuracy and assessment accuracy. Then check: do models with higher solving accuracy tend to have higher assessment accuracy? (correlation across models)
- **Item-level (per model):** Split items into “solved correctly” vs “solved incorrectly.” Compare assessment accuracy on those two subsets. If the model assesses better on items it solved correctly, that supports “transfer” within the same agent.

**Conclusion:** For “does **mathematical problem-solving expertise** [in an LLM] **translate into assessment performance**?”, the standard and most direct design is **same agent**: one model is both the solver and the assessor.

---

## Design 2: Different agents (different models)

**Setup:** Model A is the **solver**; Model B is the **assessor**. You might fix one (e.g. always assess with GPT-4o) and vary the solver, or vary both.

**When this is useful:**

- You want to ask: “Do **better solvers** tend to be **better assessors**?” across the **model ecosystem** (e.g. GPT-4 vs Llama vs Qwen). You run multiple (solver, assessor) pairs and look at correlation between solver accuracy and assessor accuracy.
- You are not primarily interested in “within-model transfer,” but in “are solving and assessing skills correlated across models?”

**Limitation:** You lose the item-level “on problems this model solved correctly, does *this same model* assess better?” analysis, because the solver and assessor are different.

---

## Recommendation

- **For your stated topic (“Does mathematical problem-solving expertise in LLMs translate into assessment performance?”):**  
  Use **the same agent** as both solver and assessor.  
  - Run each model in both conditions (solver + assessor).  
  - Compare assessment performance on items the model solved correctly vs incorrectly (item-level).  
  - If you have multiple models, also correlate solving accuracy with assessment accuracy across models (model-level).

- **Optional addition:** You can still run a **different-agent** analysis as a secondary analysis (e.g. “when we use a strong solver and a weak assessor, how does assessment accuracy look?”) if that helps the discussion.

---

## How the codebase implements same-agent design

**One agent, shared persona, two task prompts.**

- **Agent identity (persona):** Defined once in **`prompts.py`** as **`AGENT_PERSONA`**. Default: *"You are an expert mathematical tutor. You are skilled at solving grade-school math word problems and at evaluating step-by-step solutions for errors."* So the agent is the **tutor**; the same identity is used in both conditions.
- **Task prompts:** Different instructions for each condition:
  - **Solving:** `get_problem_solving_system()` = persona + **`SOLVING_TASK`** (solve the problem, give Final answer).
  - **Assessment:** `get_assessment_system()` = persona + **`ASSESSMENT_TASK`** (evaluate given steps, return JSON with llm_label, rationale, error_type (compare llm_label to gold_label)).
- The **same LLM** with the **same persona** (tutor) receives either a solving task or an assessment task; only the task instructions and the user message (problem only vs problem + steps) differ.

To change the agent (e.g. different role), edit **`AGENT_PERSONA`** in `prompts.py`. To override persona for one condition only, use `get_problem_solving_system(persona="...")` or `get_assessment_system(persona="...")`.

---

## How the codebase supports same vs different agents

| Design | Solver | Assessor | What you do in code |
|--------|--------|----------|----------------------|
| **Same agent** | Model M | Model M | Use same `--model` for both solving and assessment. One model, shared persona, two task prompts. |
| **Different agents** | Model A | Model B | Run solver with `--model A`, assessor with `--model B`. |

So: **same agent = same `--model`** for both conditions; **different agents = different `--model`**. For your main question, **same agent** is the right design.
