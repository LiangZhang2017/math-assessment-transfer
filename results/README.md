# Results (averaged over 3 runs)

- **`figures/solving.png`** — Problem-solving accuracy: mean over run_1, run_2, run_3 by dataset (GSM8K, MATH) and model (GPT-4, GPT-5-tp). Error bars = std across 3 runs.
- **`figures/assessment.png`** — Assessment accuracy (llm_label vs human label): same layout.
- **`accuracy_mean_3runs.csv`** — Table of mean_pct, std_pct, n_runs per task, model, split.

Regenerate figures from `output/` with:
```bash
python scripts/plot_results.py
```
