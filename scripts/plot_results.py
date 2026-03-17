"""
Aggregate correctness over three runs and plot Solving vs Assessment as dual figures.
Creates results/figures/solving.png and results/figures/assessment.png:
  - X: dataset (GSM8K, MATH)
  - Y: mean accuracy over run_1, run_2, run_3 (%)
  - Grouped bars: gpt-4 vs gpt-5-tp
Usage: python scripts/plot_results.py
"""
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"

RUNS = ["run_1", "run_2", "run_3"]
SPLITS = ["gsm8k", "math"]
MODELS = ["gpt-4", "gpt-5-tp"]
SPLIT_LABELS = {"gsm8k": "GSM8K", "math": "MATH"}


def collect_solving_pct(out_dir: Path) -> float | None:
    """Return accuracy in [0, 100] or None if no data."""
    correct, total = 0, 0
    for path in out_dir.glob("*.json"):
        if path.name == "responses.json":
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            total += 1
            if data.get("correctness") is True:
                correct += 1
        except (json.JSONDecodeError, KeyError):
            pass
    return (correct / total * 100) if total else None


def collect_assessment_pct(out_dir: Path) -> float | None:
    """Return accuracy in [0, 100] or None if no data."""
    correct, total = 0, 0
    for path in out_dir.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            total += 1
            if data.get("correctness_llm_label") is True:
                correct += 1
        except (json.JSONDecodeError, KeyError):
            pass
    return (correct / total * 100) if total else None


def load_task_data(task: str) -> dict[tuple[str, str], list[float]]:
    """Load per (model, split) list of accuracies over RUNS. task in ('solving', 'assessment')."""
    collector = collect_solving_pct if task == "solving" else collect_assessment_pct
    data: dict[tuple[str, str], list[float]] = {}
    for model in MODELS:
        for split in SPLITS:
            pcts = []
            for run in RUNS:
                out_dir = OUTPUT_DIR / model / task / split / run
                if out_dir.is_dir():
                    p = collector(out_dir)
                    if p is not None:
                        pcts.append(p)
            if pcts:
                data[(model, split)] = pcts
    return data


def _compute_means_stds(
    data: dict[tuple[str, str], list[float]],
) -> tuple[dict[str, list[float]], dict[str, list[float]]]:
    """Return (means, stds) per model with one value per split in SPLITS order."""
    import numpy as np
    means = {}
    stds = {}
    for model in MODELS:
        means[model] = []
        stds[model] = []
        for split in SPLITS:
            vals = data.get((model, split), [])
            if vals:
                means[model].append(np.mean(vals))
                stds[model].append(np.std(vals) if len(vals) > 1 else 0.0)
            else:
                means[model].append(0.0)
                stds[model].append(0.0)
    return means, stds


def plot_bar_figure(
    data: dict[tuple[str, str], list[float]],
    out_path: Path,
    ylabel: str = "Accuracy (%)",
) -> None:
    """Grouped bar chart: x = dataset (GSM8K, MATH), groups = GPT-4, GPT-5; y = mean accuracy."""
    import numpy as np
    import matplotlib.pyplot as plt

    x_labels = [SPLIT_LABELS[s] for s in SPLITS]
    x = np.arange(len(x_labels))
    width = 0.35
    means, stds = _compute_means_stds(data)

    fig, ax = plt.subplots(layout="constrained", figsize=(5, 4))
    bars1 = ax.bar(x - width / 2, means["gpt-4"], width, label="GPT-4")
    bars2 = ax.bar(x + width / 2, means["gpt-5-tp"], width, label="GPT-5")

    ax.bar_label(bars1, fmt="%.1f%%", label_type="edge")
    ax.bar_label(bars2, fmt="%.1f%%", label_type="edge")

    ax.set_ylabel(ylabel)
    ax.set_xticks(x)
    ax.set_xticklabels(x_labels)
    ax.legend()
    ax.set_ylim(0, 105)
    ax.set_yticks(np.arange(0, 101, 10))
    ax.grid(axis="y", alpha=0.3)

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def plot_solving_and_assessment_dual(
    solving_data: dict[tuple[str, str], list[float]],
    assessment_data: dict[tuple[str, str], list[float]],
    out_path: Path,
) -> None:
    """Single figure with two panels: Solving (left), Assessment (right). Same style as single plots."""
    import numpy as np
    import matplotlib.pyplot as plt

    x_labels = [SPLIT_LABELS[s] for s in SPLITS]
    x = np.arange(len(x_labels))
    width = 0.35
    means_solve, _ = _compute_means_stds(solving_data)
    means_assess, _ = _compute_means_stds(assessment_data)

    fig, axes = plt.subplots(1, 2, figsize=(8, 4), layout="constrained")
    for ax, means, title in zip(
        axes,
        [means_solve, means_assess],
        ["Solving", "Assessment"],
    ):
        bars1 = ax.bar(x - width / 2, means["gpt-4"], width, label="GPT-4")
        bars2 = ax.bar(x + width / 2, means["gpt-5-tp"], width, label="GPT-5")
        ax.bar_label(bars1, fmt="%.1f%%", label_type="edge")
        ax.bar_label(bars2, fmt="%.1f%%", label_type="edge")
        ax.set_ylabel("Accuracy (%)")
        ax.set_xticks(x)
        ax.set_xticklabels(x_labels)
        ax.legend()
        ax.set_ylim(0, 105)
        ax.set_yticks(np.arange(0, 101, 10))
        ax.grid(axis="y", alpha=0.3)
        ax.set_title(title)

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close()


def main() -> int:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    solving_data = load_task_data("solving")
    assessment_data = load_task_data("assessment")

    try:
        plot_bar_figure(solving_data, FIGURES_DIR / "solving.png", ylabel="Accuracy (%)")
        plot_bar_figure(assessment_data, FIGURES_DIR / "assessment.png", ylabel="Accuracy (%)")
        plot_solving_and_assessment_dual(
            solving_data, assessment_data, FIGURES_DIR / "solving_and_assessment.png"
        )
    except ImportError:
        print("matplotlib not installed; run: pip install matplotlib", file=sys.stderr)
        return 1

    # Write summary table to results/
    table_path = RESULTS_DIR / "accuracy_mean_3runs.csv"
    with open(table_path, "w", encoding="utf-8") as f:
        f.write("task,model,split,mean_pct,std_pct,n_runs\n")
        for task, data in [("solving", solving_data), ("assessment", assessment_data)]:
            for model in MODELS:
                for split in SPLITS:
                    vals = data.get((model, split), [])
                    if vals:
                        mean_pct = statistics.mean(vals)
                        std_pct = statistics.stdev(vals) if len(vals) > 1 else 0.0
                        f.write(f"{task},{model},{split},{mean_pct:.2f},{std_pct:.2f},{len(vals)}\n")

    print(f"Figures saved to {FIGURES_DIR}/")
    print(f"  solving.png, assessment.png, solving_and_assessment.png (dual)")
    print(f"Summary table: {table_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
