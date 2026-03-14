"""Prompt templates for ProcessBench. One agent (e.g. tutor) with a shared persona; two task-specific prompts for solving vs assessment."""

# ---- Shared agent persona (same identity for both conditions) ----
# The same LLM plays both solver and assessor; only the task instructions differ.
AGENT_PERSONA = """You are an expert mathematical tutor. You are skilled at solving grade-school math word problems and at evaluating step-by-step solutions for errors. You read carefully, reason clearly, and give precise answers."""


# ---- Condition 1: Problem-solving (task-specific prompt) ----
SOLVING_TASK = """Your task now: solve the given math problem step by step and give one final answer.

Instructions:
1. Read the problem carefully and identify what is being asked.
2. Work through the solution step by step. Show your reasoning and calculations clearly.
3. At the end, you must give exactly one final answer on its own line in this format:
   Final answer: <number>
   Use only the numeric answer (e.g. 42 or 2800), no units or extra text in the final line. If the answer is a dollar amount, give the number only (e.g. 37 not $37).
4. Do not add explanation after the final answer line."""


def get_problem_solving_system(persona: str | None = None) -> str:
    """System prompt for the solving condition: shared persona + solving task."""
    p = (persona or AGENT_PERSONA).strip()
    return p + "\n\n" + SOLVING_TASK


def problem_solving_user_prompt(problem: str) -> str:
    """User message for solving: the problem only."""
    return f"""Solve the following problem. Show your work step by step, then end with a single line: Final answer: <number>

Problem:
{problem}"""


# ---- Condition 2: Assessment (task-specific prompt) ----
ASSESSMENT_TASK = """Your task now: evaluate the given step-by-step solution and identify the earliest step that contains an error.

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
3. For each step, judge whether it is valid based on the problem statement and the previously verified steps.
4. Stop at the first erroneous step. Do not continue evaluating later steps once the first error is found.
5. If all steps are correct, return -1.
6. Be concise and precise. Do not rewrite the full solution.

Output format:
Return a JSON object with exactly these fields:
{
  "llm_label": <integer>,
  "rationale": "<brief explanation of why this is the earliest error, or why all steps are correct>",
  "error_type": "<mathematical | logical | conceptual | completeness | none>"
}
(llm_label: 1-based index of the earliest erroneous step, or -1 if all steps are correct.)"""


def get_assessment_system(persona: str | None = None) -> str:
    """System prompt for the assessment condition: shared persona + assessment task."""
    p = (persona or AGENT_PERSONA).strip()
    return p + "\n\n" + ASSESSMENT_TASK


# Backward compatibility: ASSESSMENT_SYSTEM as full prompt (with default persona)
ASSESSMENT_SYSTEM = get_assessment_system()


def assessment_user_prompt(problem: str, steps: list[str]) -> str:
    """User message for assessment: problem + solution steps to evaluate."""
    steps_text = "\n".join(f"Step {i}: {s}" for i, s in enumerate(steps, start=1))
    return f"""Now evaluate the following example.

Problem:
{problem}

Steps:
{steps_text}
"""
