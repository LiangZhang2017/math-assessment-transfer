# One example per task (solving vs assessment)

Same agent (tutor), same persona; two different tasks. Below is **one full example for Task 1** and **one full example for Task 2**, using item **gsm8k-0** from the dataset.

---

## Task 1: Problem-solving (solve the problem yourself)

The model sees **only the problem**. It must produce a step-by-step solution and end with `Final answer: <number>`.

### System message (persona + solving task)

```
You are an expert mathematical tutor. You are skilled at solving grade-school math word problems and at evaluating step-by-step solutions for errors. You read carefully, reason clearly, and give precise answers.

Your task now: solve the given math problem step by step and give one final answer.

Instructions:
1. Read the problem carefully and identify what is being asked.
2. Work through the solution step by step. Show your reasoning and calculations clearly.
3. At the end, you must give exactly one final answer on its own line in this format:
   Final answer: <number>
   Use only the numeric answer (e.g. 42 or 2800), no units or extra text in the final line. If the answer is a dollar amount, give the number only (e.g. 37 not $37).
4. Do not add explanation after the final answer line.
```

### User message (problem only)

```
Solve the following problem. Show your work step by step, then end with a single line: Final answer: <number>

Problem:
Sue lives in a fun neighborhood.  One weekend, the neighbors decided to play a prank on Sue.  On Friday morning, the neighbors placed 18 pink plastic flamingos out on Sue's front yard.  On Saturday morning, the neighbors took back one third of the flamingos, painted them white, and put these newly painted white flamingos back out on Sue's front yard.  Then, on Sunday morning, they added another 18 pink plastic flamingos to the collection. At noon on Sunday, how many more pink plastic flamingos were out than white plastic flamingos?
```

### Example LLM response (Task 1)

```
On Friday: 18 pink flamingos are placed. No white ones yet.

On Saturday: The neighbors take back 1/3 of 18 = 6 flamingos, paint them white, and put those 6 back. So on the yard we have 18 - 6 = 12 pink and 6 white.

On Sunday: They add 18 more pink. So 12 + 18 = 30 pink and still 6 white.

Difference: 30 - 6 = 24 more pink than white.

Final answer: 24
```

Correctness is decided by comparing the extracted final answer (e.g. 24) to **gold_answer** (24 for this item in the dataset).

---

## Task 2: Assessment (evaluate a given solution)

The model sees the **same problem** plus **benchmark solution steps** (from ProcessBench). It must output a JSON with the earliest erroneous step index (or -1 if all correct).

### System message (persona + assessment task)

```
You are an expert mathematical tutor. You are skilled at solving grade-school math word problems and at evaluating step-by-step solutions for errors. You read carefully, reason clearly, and give precise answers.

Your task now: evaluate the given step-by-step solution and identify the earliest step that contains an error.

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
  "rationale": "...",
  "error_type": "<mathematical | logical | conceptual | completeness | none>"
}
(llm_label: 1-based index of earliest erroneous step, or -1 if all correct.)
```

### User message (problem + steps to evaluate)

```
Now evaluate the following example.

Problem:
Sue lives in a fun neighborhood.  One weekend, the neighbors decided to play a prank on Sue.  On Friday morning, the neighbors placed 18 pink plastic flamingos out on Sue's front yard.  On Saturday morning, the neighbors took back one third of the flamingos, painted them white, and put these newly painted white flamingos back out on Sue's front yard.  Then, on Sunday morning, they added another 18 pink plastic flamingos to the collection. At noon on Sunday, how many more pink plastic flamingos were out than white plastic flamingos?

Steps:
Step 1: To find out how many more pink plastic flamingos were out than white plastic flamingos at noon on Sunday, we can break down the problem into steps. First, on Friday, the neighbors start with 18 pink plastic flamingos.

Step 2: On Saturday, they take back one third of the flamingos. Since there were 18 flamingos, \(1/3 \times 18 = 6\) flamingos are taken back. So, they have \(18 - 6 = 12\) flamingos left in their possession. Then, they paint these 6 flamingos white and put them back out on Sue's front yard. Now, Sue has the original 12 pink flamingos plus the 6 new white ones. Thus, by the end of Saturday, Sue has \(12 + 6 = 18\) pink flamingos and 6 white flamingos.

Step 3: On Sunday, the neighbors add another 18 pink plastic flamingos to Sue's front yard. By the end of Sunday morning, Sue has \(18 + 18 = 36\) pink flamingos and still 6 white flamingos.

Step 4: To find the difference, subtract the number of white flamingos from the number of pink flamingos: \(36 - 6 = 30\). Therefore, at noon on Sunday, there were 30 more pink plastic flamingos out than white plastic flamingos. The answer is \(\boxed{30}\).
```

### Example LLM response (Task 2)

```json
{
  "llm_label": 2,
  "rationale": "In Step 2, the solution correctly finds 6 flamingos taken and painted white and 12 pink remaining. But it then states 'Sue has (12 + 6 = 18) pink flamingos and 6 white flamingos.' The 18 here is the total on the yard (12 pink + 6 white), not the number of pink flamingos. So the count of pink is wrong in that sentence; the first actual mathematical error that affects the rest of the solution is in Step 2.",
  "error_type": "logical"
}
```

Assessment correctness is decided by comparing the model’s **llm_label** (e.g. 2) to **gold_label** (human annotation; 1-based index of earliest error; dataset field `label`; for gsm8k-0 gold_label is 1).

---

## Summary

| Task   | User sees              | Model returns                    | Compared to        |
|--------|------------------------|-----------------------------------|--------------------|
| **1 – Solving**   | Problem only           | Full solution + `Final answer: N` | **gold_answer**    |
| **2 – Assessment** | Problem + solution steps | JSON: **llm_label**, rationale, error_type | **gold_label** (human; dataset field `label`)  |

Same **persona** (tutor) in both; only the **task** and the **user message** differ.
