"""Static and empirical leakage audit of the inherited RT-Activity-Predictor tree.

This script does not produce any benchmark result. It characterizes the inherited
work: which files let held-out labels reach a selection decision, how many free
parameters were fitted against the 57 labels, how the reported metric climbed
across the commit history, and what each blended component scores on its own.

Outputs audit/leakage_report.md and audit/figures/cls_ladder.png.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
import scipy

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evaluation"))
from evaluate import compute_cls, weighted_spearman  # noqa: E402

SEED = 42
AUDIT_DIR = ROOT / "audit"
FIG_DIR = AUDIT_DIR / "figures"

# Directories holding inherited code that the audit inspects.
SCAN_ROOTS = ["src", "experiments", "features", "evaluation", "legacy_leaky", "."]

# Markers that indicate an optimizer or search loop is present in a file.
SEARCH_MARKERS = [
    "differential_evolution",
    "minimize(",
    "optuna",
    "GridSearchCV",
    "RandomizedSearchCV",
    "best_cls",
    "best_score",
    "itertools.product",
    "np.linspace",
]

# Markers that indicate the CLS objective is being returned to an optimizer.
OBJECTIVE_MARKERS = [
    "return -",
    "-res[",
    "-result[",
    "-compute_cls",
    '-cls',
]

LABEL_MARKERS = ["rt_sequences.csv", '"active"', "'active'", "pe_efficiency_pct"]


def library_versions():
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit-learn": sklearn.__version__,
        "matplotlib": matplotlib.__version__,
    }


def iter_python_files():
    """Yield every inherited python file the audit should inspect."""
    seen = set()
    for rel in SCAN_ROOTS:
        base = ROOT / rel
        if not base.exists():
            continue
        pattern = "*.py" if rel == "." else "**/*.py"
        for path in sorted(base.glob(pattern)):
            if not path.is_file():
                continue
            if "audit" in path.parts or "bench" in path.parts:
                continue
            if path.resolve() in seen:
                continue
            seen.add(path.resolve())
            yield path


def classify_file(text):
    """Classify how a file uses the labels.

    SELECTION_LEAK: the file scores against the full label set and feeds that
    score back into a search or selection construct.
    EVAL_ONLY: the file scores against labels but selects nothing.
    UNCLEAR: labels are touched but the control flow is not decisive from a
    static read, so a human should look.
    """
    uses_metric = ("compute_cls" in text) or ("average_precision_score" in text)
    touches_labels = any(m in text for m in LABEL_MARKERS)
    if not (uses_metric and touches_labels):
        return None, [], []

    search_hits = [m for m in SEARCH_MARKERS if m in text]
    objective_hits = [m for m in OBJECTIVE_MARKERS if m in text]

    if search_hits and objective_hits:
        verdict = "SELECTION_LEAK"
    elif search_hits:
        verdict = "UNCLEAR"
    else:
        verdict = "EVAL_ONLY"
    return verdict, search_hits, objective_hits


def objective_lines(text):
    """Line numbers where a label array enters a scoring or objective call."""
    lines = []
    for i, line in enumerate(text.splitlines(), start=1):
        if "compute_cls(" in line or "average_generation" in line:
            lines.append(i)
        elif "average_precision_score(" in line:
            lines.append(i)
        elif re.search(r"return\s+-\s*\w*res", line) or "return -res" in line:
            lines.append(i)
    return lines


def static_scan():
    rows = []
    for path in iter_python_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        verdict, search_hits, objective_hits = classify_file(text)
        if verdict is None:
            continue
        rows.append(
            {
                "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                "verdict": verdict,
                "objective_lines": objective_lines(text),
                "search_markers": search_hits,
                "objective_markers": objective_hits,
            }
        )
    order = {"SELECTION_LEAK": 0, "UNCLEAR": 1, "EVAL_ONLY": 2}
    rows.sort(key=lambda r: (order[r["verdict"]], r["file"]))
    return rows


def _resolve(rel):
    """Find an inherited artifact at its original path or under quarantine."""
    for base in ("", "legacy_leaky/", "legacy_submission/"):
        path = ROOT / (base + rel)
        if path.exists():
            return path
    return None


def count_free_parameters():
    """Count free parameters fitted against the 57 labels, per artifact."""
    targets = [
        "fast_opt.py",
        "results/cls_search_log.json",
        "results/best_weights.json",
        "results/de_best_weights.json",
        "results/component_weight_search_best.json",
        "results/blend_search_best.json",
        "temp_artifacts/results_scratch/component_weight_search_best.json",
        "temp_artifacts/results_scratch/blend_search_best.json",
        "legacy_leaky/fast_opt.py",
    ]
    rows = []
    for rel in targets:
        path = _resolve(rel)
        if path is None:
            rows.append({"artifact": rel, "status": "absent", "n_params": None, "note": ""})
            continue
        if path.suffix == ".json":
            try:
                obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except (json.JSONDecodeError, OSError) as exc:
                rows.append(
                    {"artifact": rel, "status": "unreadable", "n_params": None, "note": type(exc).__name__}
                )
                continue
            n, note = count_json_params(obj)
            rows.append({"artifact": rel, "status": "present", "n_params": n, "note": note})
        else:
            text = path.read_text(encoding="utf-8", errors="replace")
            m = re.search(r"bounds\s*=\s*\[\(.*?\)\s*for .*?\]\s*\+\s*\[\(", text, re.S)
            note = "bounds vector: one weight per component plus one power exponent"
            n = None
            if "branch_names" in text and m:
                n = "n_components + 1"
            rows.append({"artifact": rel, "status": "present", "n_params": n, "note": note})
    return rows


def count_json_params(obj):
    """Count fitted scalars inside a stored search artifact."""
    if isinstance(obj, dict):
        if "weights" in obj and isinstance(obj["weights"], dict):
            n = len(obj["weights"])
            extra = [k for k in ("power", "threshold", "exponent") if k in obj]
            return n + len(extra), f"{n} weights plus {len(extra)} scalar(s): {', '.join(extra) or 'none'}"
        floats = [v for v in obj.values() if isinstance(v, (int, float))]
        return len(floats), "loose scalar fields"
    if isinstance(obj, list):
        return len(obj), "list entries"
    return 0, "no countable parameters"


def commit_ladder():
    """Extract every CLS value mentioned in the commit history, oldest first."""
    try:
        out = subprocess.run(
            ["git", "log", "--oneline", "--reverse"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (subprocess.CalledProcessError, OSError) as exc:
        return [], f"git log failed: {type(exc).__name__}"

    pattern = re.compile(r"CLS[\s_\-:=]*([01]?\.\d+)", re.IGNORECASE)
    rows = []
    for idx, line in enumerate(out.splitlines()):
        m = pattern.search(line)
        if m:
            rows.append({"index": idx, "sha": line.split()[0], "cls": float(m.group(1)), "subject": line})
    return rows, ""


def plot_ladder(rows):
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "cls_ladder.png"
    if not rows:
        return None
    x = list(range(len(rows)))
    y = [r["cls"] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(x, y, marker="o", linewidth=1.5)
    ax.set_xlabel("Commit index, oldest to newest")
    ax.set_ylabel("Reported CLS in commit message")
    ax.set_title("Metric hill-climbing trajectory")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)
    return out


def component_table():
    """Score each stored blend component on its own against the 57 labels.

    These are not honest generalization estimates either: the components were
    themselves produced by pipelines tuned on this dataset. They are reported to
    show the gap between any single component and the blended 0.975.
    """
    comp_path = _resolve("results/component_arrays.json")
    names_path = _resolve("results/component_rt_names.json")
    if comp_path is None:
        return [], "component_arrays.json not found"

    components = json.loads(comp_path.read_text(encoding="utf-8"))
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv").set_index("rt_name")
    if names_path is not None:
        names = json.loads(names_path.read_text(encoding="utf-8"))
        seq = seq.loc[names]

    y_true = seq["active"].to_numpy()
    pe = seq["pe_efficiency_pct"].to_numpy(dtype=float)

    rows = []
    for key, arr in components.items():
        vec = np.nan_to_num(np.asarray(arr, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
        if vec.shape[0] != y_true.shape[0]:
            rows.append({"component": key, "cls": None, "pr_auc": None, "w_spearman": None})
            continue
        res = compute_cls(y_true, vec, pe)
        rows.append(
            {
                "component": key,
                "cls": res["cls"],
                "pr_auc": res["pr_auc"],
                "w_spearman": res["w_spearman"],
            }
        )
    rows.sort(key=lambda r: (r["cls"] is None, -(r["cls"] or 0.0)))
    return rows, ""


def fmt(value, places=4):
    if value is None:
        return "n/a"
    return f"{value:.{places}f}"


def main():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    versions = library_versions()
    scan = static_scan()
    params = count_free_parameters()
    ladder, ladder_err = commit_ladder()
    fig_path = plot_ladder(ladder)
    comps, comp_err = component_table()

    lines = []
    lines.append("# Leakage audit of the inherited tree")
    lines.append("")
    lines.append(f"Seed: {SEED}")
    lines.append("")
    lines.append("Library versions: " + ", ".join(f"{k} {v}" for k, v in versions.items()))
    lines.append("")
    lines.append(
        "This report characterizes inherited work. Nothing in it is a benchmark "
        "result, and no number here may be carried into a results table."
    )
    lines.append("")

    lines.append("## 1. Static scan")
    lines.append("")
    lines.append(
        "Files that both use the competition metric and touch the label columns. "
        "SELECTION_LEAK means the metric value is fed back into a search or "
        "selection construct in the same file, so held-out labels inform a choice."
    )
    lines.append("")
    lines.append("| File | Verdict | Lines where labels enter scoring | Search markers |")
    lines.append("| --- | --- | --- | --- |")
    for r in scan:
        ol = ", ".join(str(i) for i in r["objective_lines"][:10]) or "none matched"
        sm = ", ".join(r["search_markers"][:4]) or "none"
        lines.append(f"| `{r['file']}` | {r['verdict']} | {ol} | {sm} |")
    lines.append("")
    counts = {}
    for r in scan:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
    lines.append("Totals: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    lines.append("")

    lines.append("## 2. Free parameters fitted against the 57 labels")
    lines.append("")
    lines.append("| Artifact | Status | Free parameters | Note |")
    lines.append("| --- | --- | --- | --- |")
    for r in params:
        lines.append(
            f"| `{r['artifact']}` | {r['status']} | {r['n_params'] if r['n_params'] is not None else 'n/a'} | {r['note']} |"
        )
    lines.append("")

    lines.append("## 3. Commit ladder")
    lines.append("")
    if ladder_err:
        lines.append(f"Could not parse the commit history: {ladder_err}")
    elif not ladder:
        lines.append("No commit message contained a parseable CLS value.")
    else:
        lines.append(
            f"{len(ladder)} commits carry a CLS value in the subject line. "
            f"First {fmt(ladder[0]['cls'])}, last {fmt(ladder[-1]['cls'])}."
        )
        lines.append("")
        lines.append("| Commit index | SHA | CLS | Subject |")
        lines.append("| --- | --- | --- | --- |")
        for r in ladder:
            subject = r["subject"].replace("|", "\\|")
            lines.append(f"| {r['index']} | `{r['sha']}` | {fmt(r['cls'])} | {subject} |")
        lines.append("")
        if fig_path:
            lines.append(f"Figure: `{fig_path.relative_to(ROOT)}`".replace("\\", "/"))
    lines.append("")

    lines.append("## 4. Per-component scores")
    lines.append("")
    if comp_err:
        lines.append(comp_err)
    else:
        vals = [r["cls"] for r in comps if r["cls"] is not None]
        lines.append(
            "Each of the stored blend components, scored on its own against the "
            "same 57 labels. These are not generalization estimates: the "
            "components were produced by pipelines already tuned on this dataset. "
            "They are shown to size the gap between any one component and the "
            "blended figure."
        )
        lines.append("")
        if vals:
            lines.append(
                f"Components scored: {len(vals)}. Best {fmt(max(vals))}, "
                f"mean {fmt(float(np.mean(vals)))}, worst {fmt(min(vals))}."
            )
            lines.append("")
        lines.append("| Component | CLS | PR-AUC | Weighted Spearman |")
        lines.append("| --- | --- | --- | --- |")
        for r in comps:
            lines.append(
                f"| `{r['component']}` | {fmt(r['cls'])} | {fmt(r['pr_auc'])} | {fmt(r['w_spearman'])} |"
            )
    lines.append("")

    out = AUDIT_DIR / "leakage_report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"seed={SEED}")
    print("versions: " + ", ".join(f"{k}={v}" for k, v in versions.items()))
    print(f"static scan rows: {len(scan)} ({counts})")
    print(f"commit ladder entries: {len(ladder)}")
    print(f"components scored: {sum(1 for r in comps if r['cls'] is not None)}")
    if comps:
        vals = [r["cls"] for r in comps if r["cls"] is not None]
        if vals:
            print(f"component best={max(vals):.4f} mean={float(np.mean(vals)):.4f}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
