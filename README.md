# math-assessment-transfer
Studying whether mathematical problem-solving ability in LLMs transfers to step-level assessment on ProcessBench.

## Setup

1. **Environment**
   - Copy `.env.example` to `.env` and fill in your Azure OpenAI values (or use the defaults already in `.env`).
   - `pip install -r requirements.txt` (or use the project venv: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`).

2. **ProcessBench dataset (GSM8K only)**
   - Grade-school subset only. Download to JSON:  
     `python scripts/download_processbench.py`  
   - The repo’s **`dataset/gsm8k.json`** has **400 examples** with `id`, `generator`, `problem`, `steps`, `final_answer_correct`, `label`, and **`gold_answer`** (for problem-solving evaluation).

3. **Azure OpenAI**
   - Set in `.env`: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_VERSION`, `AZURE_OPENAI_MODEL`.
   - **`AZURE_OPENAI_MODEL` must be the deployment name** in your Azure resource (e.g. `gpt-4`, `gpt-4o`), not the model family name—see Azure Portal → your resource → Deployments. If you get `404 DeploymentNotFound`, the value does not match any deployment name.
   - To override for a single run, use `--model <deployment-name>` with the script (e.g. `--model gpt-4`).

## Usage

- **Problem-solving condition**: `main.run_problem_solving(problem)` — model sees only the problem.
- **Assessment condition**: `main.run_assessment(problem, steps)` — model sees problem + benchmark solution and returns JSON with `label`, `rationale`, `error_type`.
- Load data: `main.load_processbench("gsm8k")` → returns a list of dicts. Only the GSM8K split is supported.
- Sanity check: `python main.py` runs a short API check with the active model.

## Run the two tasks

**Task 1 — Problem-solving** (model solves from the problem only; we compare final answer to `gold_answer`):

```bash
python scripts/run_problem_solving_eval.py --model gpt-4o
```

Output: `output/<model>/solving/<id>.json` and `output/<model>/solving/summary.txt`. Optional: `--limit N`, **`--run <name>`** (saves to `.../solving/<name>/` so multiple runs use different folders, e.g. `--run run_1`).

**Task 2 — Assessment** (model evaluates benchmark steps; we compare `llm_label` to human `label`):

```bash
python scripts/run_assessment_eval.py --model gpt-4o
```

Output: `output/<model>/assessment/<id>.json` and `output/<model>/assessment/summary.txt`. Optional: `--limit N`, **`--run <name>`** (e.g. `--run run_1` → `.../assessment/run_1/`), `--out-dir <path>`.

Use the same `--model` (e.g. `gpt-4`, `gpt-4o`) for both if you want one model for solving and assessment.

**Multiple runs** — To keep separate runs in separate folders, pass **`--run <name>`** for both tasks. Each run writes to `output/<model>/solving/<name>/` and `output/<model>/assessment/<name>/`. Reruns with the same `--run` resume (skip existing files).

```bash
# First run
python scripts/run_problem_solving_eval.py --model gpt-4 --run run_1
python scripts/run_assessment_eval.py --model gpt-4 --run run_1

# Second run (different folder; can resume within each run by rerunning the same command)
python scripts/run_problem_solving_eval.py --model gpt-4 --run run_2
python scripts/run_assessment_eval.py --model gpt-4 --run run_2
```

See docs/OUTPUT_AND_MODELS.md and docs/EXAMPLE_OUTPUTS.md.

## Evaluating outcomes

- **Problem-solving**: Correctness is computed by comparing the model’s extracted final answer to **`gold_answer`** (see `evaluate_problem_solving.py`).
- **Assessment**: Ground truth is each row’s **`label`**. We compare the model’s **`llm_label`** to it and store **`correctness_llm_label`** in each assessment output JSON.
