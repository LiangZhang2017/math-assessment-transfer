"""
Paper-oriented analysis: assessment on solved vs unsolved, ProcessBench metrics (F1),
solve-assess gap, 2x2 statistical test, error-present vs no-error, exact/near-miss, qualitative cases.
Writes to results/paper_metrics/ (tables + example IDs).
Usage: python scripts/analyze_paper_metrics.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "output"
RESULTS_DIR = ROOT / "results"
PAPER_METRICS_DIR = RESULTS_DIR / "paper_metrics"

RUNS = ["run_1", "run_2", "run_3"]
SPLITS = ["gsm8k", "math"]
MODELS = ["gpt-4", "gpt-5-tp"]


def load_solving_by_id(out_dir: Path) -> dict[str, bool]:
    """Return dict id -> correctness (bool)."""
    out = {}
    for path in out_dir.glob("*.json"):
        if path.name == "responses.json":
            continue
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            out[data["id"]] = data.get("correctness") is True
        except (json.JSONDecodeError, KeyError):
            pass
    return out


def load_assessment_by_id(out_dir: Path) -> dict[str, dict]:
    """Return dict id -> {label (human), llm_label, correctness_llm_label, ...}."""
    out = {}
    for path in out_dir.glob("*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            out[data["id"]] = {
                "label": data.get("label"),
                "llm_label": data.get("llm_label"),
                "correctness_llm_label": data.get("correctness_llm_label") is True,
            }
        except (json.JSONDecodeError, KeyError):
            pass
    return out


def aligned_pairs(model: str, split: str, run: str) -> list[dict]:
    """Load solving and assessment for this run; return list of {id, solve_correct, assess_correct, human_label, llm_label}."""
    solve_dir = OUTPUT_DIR / model / "solving" / split / run
    assess_dir = OUTPUT_DIR / model / "assessment" / split / run
    solving = load_solving_by_id(solve_dir)
    assessment = load_assessment_by_id(assess_dir)
    rows = []
    for id_ in solving:
        if id_ not in assessment:
            continue
        s = solving[id_]
        a = assessment[id_]
        rows.append({
            "id": id_,
            "solve_correct": s,
            "assess_correct": a["correctness_llm_label"],
            "human_label": a["label"],
            "llm_label": a["llm_label"],
        })
    return rows


def processbench_accuracy_on_groups(rows: list[dict]) -> tuple[float, float, float]:
    """Error-present (human label != -1), no-error (human label == -1), and F1 (harmonic mean of accuracies)."""
    err_rows = [r for r in rows if r["human_label"] is not None and r["human_label"] != -1]
    correct_rows = [r for r in rows if r["human_label"] == -1]
    acc_err = (sum(1 for r in err_rows if r["assess_correct"]) / len(err_rows) * 100) if err_rows else 0.0
    acc_correct = (sum(1 for r in correct_rows if r["assess_correct"]) / len(correct_rows) * 100) if correct_rows else 0.0
    if acc_err + acc_correct > 0:
        f1 = 2 * acc_err * acc_correct / (acc_err + acc_correct)
    else:
        f1 = 0.0
    return acc_err, acc_correct, f1


def exact_near_miss(rows: list[dict]) -> tuple[int, int, int]:
    """Count exact match, off-by-1, off-by-2+ (for earliest-error step)."""
    exact = off1 = off2 = 0
    for r in rows:
        h, p = r["human_label"], r["llm_label"]
        if h is None or p is None:
            continue
        if h == p:
            exact += 1
        elif h == -1 or p == -1:
            off2 += 1  # one says error one says no error
        else:
            d = abs(p - h)
            if d == 1:
                off1 += 1
            else:
                off2 += 1
    return exact, off1, off2


def run_chi2(solve_correct: list[bool], assess_correct: list[bool]) -> tuple[float, float]:
    """2x2 chi-square and Fisher exact (approximate). Returns (chi2_stat, p_value)."""
    try:
        from scipy.stats import chi2_contingency, fisher_exact
    except ImportError:
        return (float("nan"), float("nan"))
    a = sum(1 for s, a in zip(solve_correct, assess_correct) if s and a)
    b = sum(1 for s, a in zip(solve_correct, assess_correct) if s and not a)
    c = sum(1 for s, a in zip(solve_correct, assess_correct) if not s and a)
    d = sum(1 for s, a in zip(solve_correct, assess_correct) if not s and not a)
    table = [[a, b], [c, d]]
    chi2, p_chi, _, _ = chi2_contingency(table)
    _, p_fisher = fisher_exact(table)
    return (chi2, p_fisher)


def difference_of_proportions_ci(
    solve_correct: list[bool], assess_correct: list[bool]
) -> tuple[float, float, float, float]:
    """Difference (solved - unsolved) in assessment accuracy (%), 95% CI, and two-proportion z-test p.
    Returns (diff_pct, ci_lower, ci_upper, p_value). Uses normal approximation."""
    try:
        from scipy.stats import norm
    except ImportError:
        return (float("nan"), float("nan"), float("nan"), float("nan"))
    solved = [(s, a) for s, a in zip(solve_correct, assess_correct) if s]
    unsolved = [(s, a) for s, a in zip(solve_correct, assess_correct) if not s]
    n1, n2 = len(solved), len(unsolved)
    if n1 == 0 or n2 == 0:
        return (float("nan"), float("nan"), float("nan"), float("nan"))
    p1 = sum(1 for _, a in solved if a) / n1
    p2 = sum(1 for _, a in unsolved if a) / n2
    diff = (p1 - p2) * 100  # in percentage points
    se = (p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2) ** 0.5
    if se <= 0:
        return (diff, diff, diff, 0.0)
    z = (p1 - p2) / se
    p_value = 2 * (1 - norm.cdf(abs(z)))
    margin = 1.96 * se * 100  # CI in percentage points
    return (diff, diff - margin, diff + margin, p_value)


def main() -> int:
    PAPER_METRICS_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: dict[tuple[str, str], list[dict]] = {}  # (model, split) -> pooled rows (all runs)
    for model in MODELS:
        for split in SPLITS:
            rows = []
            for run in RUNS:
                rows.extend(aligned_pairs(model, split, run))
            all_rows[(model, split)] = rows

    # 1) Assessment on solved vs unsolved
    lines = ["# 1. Assessment accuracy on Solved vs Unsolved items (mean over runs, then pooled)\n"]
    lines.append("model,split,solved_correct_n,assess_acc_on_solved,unsolved_n,assess_acc_on_unsolved\n")
    for model in MODELS:
        for split in SPLITS:
            rows = all_rows[(model, split)]
            solved = [r for r in rows if r["solve_correct"]]
            unsolved = [r for r in rows if not r["solve_correct"]]
            acc_s = (sum(1 for r in solved if r["assess_correct"]) / len(solved) * 100) if solved else 0.0
            acc_u = (sum(1 for r in unsolved if r["assess_correct"]) / len(unsolved) * 100) if unsolved else 0.0
            lines.append(f"{model},{split},{len(solved)},{acc_s:.2f},{len(unsolved)},{acc_u:.2f}\n")
    (PAPER_METRICS_DIR / "assessment_on_solved_vs_unsolved.csv").write_text("".join(lines), encoding="utf-8")

    # 2) ProcessBench-style: acc on error-present, acc on no-error, F1
    lines = ["# 2. ProcessBench-style metrics: accuracy on erroneous samples, on correct samples, F1 (harmonic mean)\n"]
    lines.append("model,split,acc_err_present_pct,acc_no_error_pct,f1_pct,n_err_present,n_no_error\n")
    for model in MODELS:
        for split in SPLITS:
            rows = all_rows[(model, split)]
            acc_err, acc_correct, f1 = processbench_accuracy_on_groups(rows)
            n_err = sum(1 for r in rows if r["human_label"] is not None and r["human_label"] != -1)
            n_ok = sum(1 for r in rows if r["human_label"] == -1)
            lines.append(f"{model},{split},{acc_err:.2f},{acc_correct:.2f},{f1:.2f},{n_err},{n_ok}\n")
    (PAPER_METRICS_DIR / "processbench_metrics.csv").write_text("".join(lines), encoding="utf-8")

    # 3) Solve–assess gap (overall acc and F1)
    with open(PAPER_METRICS_DIR / "solve_assess_gap.csv", "w", encoding="utf-8") as f:
        f.write("# 3. Solve–assess gap (solving accuracy - assessment metric)\n")
        f.write("model,split,solve_acc_pct,assess_overall_acc_pct,assess_f1_pct,gap_overall,gap_f1\n")
        for model in MODELS:
            for split in SPLITS:
                rows = all_rows[(model, split)]
                solve_acc = sum(1 for r in rows if r["solve_correct"]) / len(rows) * 100 if rows else 0.0
                assess_acc = sum(1 for r in rows if r["assess_correct"]) / len(rows) * 100 if rows else 0.0
                _, _, f1 = processbench_accuracy_on_groups(rows)
                gap_a = solve_acc - assess_acc
                gap_f = solve_acc - f1
                f.write(f"{model},{split},{solve_acc:.2f},{assess_acc:.2f},{f1:.2f},{gap_a:.2f},{gap_f:.2f}\n")

    # 4) Statistical test: P(assess correct | solve correct) vs P(assess correct | solve incorrect)
    lines = ["# 4. 2x2 test: solve_correct x assess_correct. Chi2 stat, p (Fisher exact)\n"]
    lines.append("model,split,chi2,p_fisher\n")
    for model in MODELS:
        for split in SPLITS:
            rows = all_rows[(model, split)]
            solve_correct = [r["solve_correct"] for r in rows]
            assess_correct = [r["assess_correct"] for r in rows]
            chi2, p = run_chi2(solve_correct, assess_correct)
            lines.append(f"{model},{split},{chi2:.4f},{p:.4e}\n")
    (PAPER_METRICS_DIR / "statistical_test_2x2.csv").write_text("".join(lines), encoding="utf-8")

    # 4b) Difference in assessment accuracy (solved - unsolved) with 95% CI and two-proportion z-test
    lines = [
        "# 4b. Transfer effect: difference in assessment acc (solved_correct - solved_incorrect), 95% CI, p-values\n"
    ]
    lines.append("model,split,diff_pct,ci_lower,ci_upper,p_two_proportion,p_fisher\n")
    for model in MODELS:
        for split in SPLITS:
            rows = all_rows[(model, split)]
            solve_correct = [r["solve_correct"] for r in rows]
            assess_correct = [r["assess_correct"] for r in rows]
            diff, ci_lo, ci_hi, p_z = difference_of_proportions_ci(solve_correct, assess_correct)
            _, p_fisher = run_chi2(solve_correct, assess_correct)
            lines.append(f"{model},{split},{diff:.2f},{ci_lo:.2f},{ci_hi:.2f},{p_z:.4e},{p_fisher:.4e}\n")
    (PAPER_METRICS_DIR / "significance_transfer.csv").write_text("".join(lines), encoding="utf-8")

    # 5) Error-present vs no-error (already in processbench_metrics; add explicit breakdown)
    # Done in #2.

    # 6) Exact / off-by-1 / off-by-2+
    lines = ["# 6. Assessment: exact match, off-by-1 step, off-by-2+\n"]
    lines.append("model,split,exact,off_by_1,off_by_2plus,total,exact_pct,off1_pct,off2_pct\n")
    for model in MODELS:
        for split in SPLITS:
            rows = all_rows[(model, split)]
            exact, off1, off2 = exact_near_miss(rows)
            n = exact + off1 + off2
            if n:
                lines.append(f"{model},{split},{exact},{off1},{off2},{n},{exact/n*100:.2f},{off1/n*100:.2f},{off2/n*100:.2f}\n")
            else:
                lines.append(f"{model},{split},0,0,0,0,0,0,0\n")
    (PAPER_METRICS_DIR / "exact_near_miss.csv").write_text("".join(lines), encoding="utf-8")

    # 7) Qualitative: example IDs for (solve✓, assess✓), (solve✓, assess✗), (solve✗, assess✓), (solve✗, assess✗)
    lines = ["# 7. Example item IDs for qualitative cases (run_1)\n"]
    for model in MODELS:
        for split in SPLITS:
            rows_run1 = aligned_pairs(model, split, "run_1")
            cases = {"solve_ok_assess_ok": [], "solve_ok_assess_bad": [], "solve_bad_assess_ok": [], "solve_bad_assess_bad": []}
            for r in rows_run1:
                if r["solve_correct"] and r["assess_correct"]:
                    cases["solve_ok_assess_ok"].append(r["id"])
                elif r["solve_correct"] and not r["assess_correct"]:
                    cases["solve_ok_assess_bad"].append(r["id"])
                elif not r["solve_correct"] and r["assess_correct"]:
                    cases["solve_bad_assess_ok"].append(r["id"])
                else:
                    cases["solve_bad_assess_bad"].append(r["id"])
            lines.append(f"\n[{model}, {split}]\n")
            for name, ids in cases.items():
                lines.append(f"  {name}: {ids[:5]}\n")  # first 5 examples
    (PAPER_METRICS_DIR / "qualitative_case_examples.txt").write_text("".join(lines), encoding="utf-8")

    # Summary report
    report = [
        "Paper metrics summary\n",
        "====================\n",
        "1. assessment_on_solved_vs_unsolved.csv — Assessment accuracy on items the model solved correctly vs incorrectly.\n",
        "2. processbench_metrics.csv — Acc on error-present samples, on no-error samples, F1 (harmonic mean).\n",
        "3. solve_assess_gap.csv — Solving accuracy minus assessment (overall and F1).\n",
        "4. statistical_test_2x2.csv — Chi2 and Fisher p for (solve correct x assess correct).\n",
        "5. exact_near_miss.csv — Exact step match, off-by-1, off-by-2+.\n",
        "6. qualitative_case_examples.txt — Example IDs for the four (solve, assess) outcome cells.\n",
    ]
    (PAPER_METRICS_DIR / "README.txt").write_text("".join(report), encoding="utf-8")

    # Optional: figure for assessment on solved vs unsolved (dual: GSM8K and MATH)
    try:
        import numpy as np
        import matplotlib.pyplot as plt
        fig, axes = plt.subplots(1, 2, figsize=(8, 4), layout="constrained")
        for ax, split in zip(axes, SPLITS):
            x = np.arange(2)  # Solved correctly | Solved incorrectly
            width = 0.35
            g4_vals = [0.0, 0.0]
            g5_vals = [0.0, 0.0]
            for i, model in enumerate(MODELS):
                rows = all_rows[(model, split)]
                solved = [r for r in rows if r["solve_correct"]]
                unsolved = [r for r in rows if not r["solve_correct"]]
                acc_s = (sum(1 for r in solved if r["assess_correct"]) / len(solved) * 100) if solved else 0.0
                acc_u = (sum(1 for r in unsolved if r["assess_correct"]) / len(unsolved) * 100) if unsolved else 0.0
                v = (g4_vals if model == MODELS[0] else g5_vals)
                v[0], v[1] = acc_s, acc_u
            bars1 = ax.bar(x - width / 2, g4_vals, width, label="GPT-4")
            bars2 = ax.bar(x + width / 2, g5_vals, width, label="GPT-5")
            ax.bar_label(bars1, fmt="%.1f%%", label_type="edge")
            ax.bar_label(bars2, fmt="%.1f%%", label_type="edge")
            ax.set_xticks(x)
            ax.set_xticklabels(["Solved correctly", "Solved incorrectly"])
            ax.set_ylabel("Assessment accuracy (%)")
            ax.set_ylim(0, 105)
            ax.set_yticks(np.arange(0, 101, 10))
            ax.legend()
            ax.grid(axis="y", alpha=0.3)
            ax.set_title(split.upper())
        fig.savefig(PAPER_METRICS_DIR / "assessment_on_solved_vs_unsolved.png", dpi=150, bbox_inches="tight")
        plt.close()
        print("Figure: assessment_on_solved_vs_unsolved.png")
    except Exception:
        pass

    print(f"Paper metrics written to {PAPER_METRICS_DIR}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
