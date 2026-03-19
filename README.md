# math-assessment-transfer
Studying whether mathematical problem-solving ability in LLMs transfers to step-level assessment on ProcessBench.

## Setup

1. **Environment**
   - Copy `.env.example` to `.env` and fill in your Azure OpenAI values (or use the defaults already in `.env`).
   - `pip install -r requirements.txt` (or use the project venv: `python -m venv .venv && .venv/bin/pip install -r requirements.txt`).

2. **ProcessBench dataset**
   - One `.json` per split in **`dataset/`**: `gsm8k.json`, `math.json`, `olympiadbench.json`, `omnimath.json`.
   - **GSM8K** (400 items): use repo’s `dataset/gsm8k.json` or  
     `python scripts/download_processbench.py --split gsm8k`
   - **Math, OlympiadBench, Omnimath** (400 random each from HF):  
     `python scripts/download_processbench.py --split math olympiadbench omnimath`  
     Saves `dataset/math.json`, `dataset/olympiadbench.json`, `dataset/omnimath.json` with 400 randomly sampled questions each (seed 42). Optional: `--sample-size 400`, `--seed 42`.
   - Each item has `id`, `generator`, `problem`, `steps`, `final_answer_correct`, `label`, and `gold_answer` (from `\boxed{}` in steps when possible).

3. **Azure OpenAI**
   - Set in `.env`: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_VERSION`, `AZURE_OPENAI_MODEL`.
   - **`AZURE_OPENAI_MODEL` must be the deployment name** in your Azure resource (e.g. `gpt-4`, `gpt-4o`), not the model family name—see Azure Portal → your resource → Deployments. If you get `404 DeploymentNotFound`, the value does not match any deployment name. For **GPT-5–level models** and example deployment names, see **docs/OUTPUT_AND_MODELS.md** (section “GPT-5–level models”).
   - To override for a single run, use `--model <deployment-name>` with the script (e.g. `--model gpt-4`).
   - **Reasoning models (e.g. gpt-5-tp):** Set `AZURE_OPENAI_REASONING_MODELS=gpt-5-tp` (or comma-separated names) in `.env`. For these, the client sends only `max_completion_tokens`; no temperature, no `max_tokens`, no fallback to another model.

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

Output: `output/<model>/solving/<split>/<run?>/<id>.json` and `summary.txt`. Optional: **`--split gsm8k|math|olympiadbench|omnimath`** (default: gsm8k), `--limit N`, **`--run <name>`**.

**Task 2 — Assessment** (model evaluates benchmark steps; we compare `llm_label` to human `label`):

```bash
python scripts/run_assessment_eval.py --model gpt-4o
```

Output: `output/<model>/assessment/<split>/<run?>/<id>.json` and `summary.txt`. Optional: **`--split gsm8k|math|olympiadbench|omnimath`**, `--limit N`, **`--run <name>`**, `--out-dir <path>`.

Use the same `--model` (e.g. `gpt-4`, `gpt-4o`) for both if you want one model for solving and assessment.

**Multiple runs** — To keep separate runs in separate folders, pass **`--run <name>`** for both tasks. Each run writes to `output/<model>/solving/<name>/` and `output/<model>/assessment/<name>/`. Reruns with the same `--run` resume (skip existing files).

Run **one task** for run_1, run_2, run_3 (tasks run separately):

```bash
# Solving only for run_1, run_2, run_3
python scripts/run_multiple_runs.py --runs run_1 run_2 run_3 --task solving --model gpt-4

# Assessment only for run_1, run_2, run_3
python scripts/run_multiple_runs.py --runs run_1 run_2 run_3 --task assessment --model gpt-4
```

Run **both tasks** for the same runs (solving then assessment for each run):

```bash
python scripts/run_multiple_runs.py --runs run_1 run_2 run_3 --task both --model gpt-4
```

Use **`--split math`** (or olympiadbench, omnimath) to run on other datasets. Optional: `--limit N`. Or run tasks per run individually:

```bash
# Single run
python scripts/run_problem_solving_eval.py --model gpt-4 --run run_1
python scripts/run_assessment_eval.py --model gpt-4 --run run_1

# Another run (resume by rerunning the same command)
python scripts/run_problem_solving_eval.py --model gpt-4 --run run_2
python scripts/run_assessment_eval.py --model gpt-4 --run run_2
```

**Correctness across runs** — To get per-run correctness and mean percentage:

```bash
python scripts/aggregate_run_correctness.py --runs run_1 run_2 run_3 --model gpt-4 --split gsm8k
```

Use **`--split math`** (or olympiadbench, omnimath) when aggregating other datasets. Use `--task solving` or `--task assessment` to aggregate one task only.

Results are organized under **`output/<model>/<task>/<split>/[<run>/]`** (e.g. `output/gpt-4/solving/math/run_1/`). See docs/OUTPUT_EXAMPLE.md for the full layout; docs/OUTPUT_AND_MODELS.md and docs/EXAMPLE_OUTPUTS.md for details.

## Evaluating outcomes

- **Problem-solving**: Correctness is computed by comparing the model’s extracted final answer to **`gold_answer`** (see `evaluate_problem_solving.py`).
- **Assessment**: Ground truth is each row’s **`label`**. We compare the model’s **`llm_label`** to it and store **`correctness_llm_label`** in each assessment output JSON.

## Results and figures

- Aggregated 3-run summary figures are written to `results/figures/`:
  - `solving.png`
  - `assessment.png`
  - `solving_and_assessment.png` (dual-panel figure)
- Aggregated tables are written to `results/`, including `accuracy_mean_3runs.csv`.
- Paper-oriented metrics and plots are written to `results/paper_metrics/`, including:
  - `assessment_on_solved_vs_unsolved.csv`
  - `assessment_on_solved_vs_unsolved.png`
  - `processbench_metrics.csv`
  - `solve_assess_gap.csv`
  - `statistical_test_2x2.csv`
  - `significance_transfer.csv`
  - `exact_near_miss.csv`
  - `qualitative_case_examples.txt`

Regenerate these artifacts from current `output/`:

```bash
python scripts/plot_results.py
python scripts/analyze_paper_metrics.py
```
