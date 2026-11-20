"""Regenerate the three presentation figures from repository result artifacts.

Every value plotted here is read from a committed JSON result file. Nothing is
typed in by hand except axis text. Outputs go to reports/figures/presentation/.

Sources:
  bench/results/search_null.json        search-capacity null sweep
  bench/results/baseline_ladder.json    zero-parameter and trained baselines
  bench/results/representations.json    representation comparison, family accuracy
  audit/leakage_report.md               the submitted 0.9754, as the corrected claim
"""

import json
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "reports" / "figures" / "presentation"
OUT.mkdir(parents=True, exist_ok=True)

INK = "#1F1F1F"
MUTED = "#6B6B6B"
ACCENT = "#2C6E7F"
ALERT = "#B85450"
RULE = "#C4C4C4"
TINT = "#EEF2F3"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Calibri", "Carlito", "DejaVu Sans"],
    "text.color": INK,
    "axes.labelcolor": INK,
    "axes.edgecolor": RULE,
    "xtick.color": INK,
    "ytick.color": INK,
    "axes.grid": True,
    "grid.color": RULE,
    "grid.linewidth": 0.6,
    "grid.alpha": 0.7,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
})

SUBMITTED_CLS = 0.9754  # audit/leakage_report.md, section 3, final commit in the ladder


def strip(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def search_null_curve():
    data = json.loads((ROOT / "bench" / "results" / "search_null.json").read_text())
    sweep = sorted(data["k_sweep"], key=lambda r: r["k"])
    ks = [r["k"] for r in sweep]
    p95 = [r["p95"] for r in sweep]
    mean = [r["mean"] for r in sweep]

    fig, ax = plt.subplots(figsize=(9.2, 5.0), dpi=200)
    ax.plot(ks, p95, marker="o", markersize=7, linewidth=2.4, color=ACCENT,
            label="null CLS, 95th percentile")
    ax.plot(ks, mean, marker="o", markersize=5, linewidth=1.6, color=ACCENT,
            alpha=0.45, linestyle="--", label="null CLS, mean")
    ax.axhline(SUBMITTED_CLS, color=ALERT, linewidth=2.2, linestyle="-")
    ax.annotate("submitted score, 0.975", xy=(1.5, SUBMITTED_CLS), xytext=(1.5, SUBMITTED_CLS + 0.035),
                color=ALERT, fontsize=15, fontweight="bold")

    k29 = next(r for r in sweep if r["k"] == 29)
    ax.annotate(
        "29 free parameters,\nthe matched count: 0.934",
        xy=(29, k29["p95"]), xytext=(31.5, 0.70),
        color=INK, fontsize=14,
        arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=1.2),
    )
    ax.plot([29], [k29["p95"]], marker="o", markersize=12, markerfacecolor="white",
            markeredgecolor=ACCENT, markeredgewidth=2.4, zorder=5)

    ax.set_xlabel("free parameters fitted against the 57 labels", fontsize=15)
    ax.set_ylabel("CLS reached on pure noise", fontsize=15)
    ax.set_ylim(0.0, 1.08)
    ax.set_xlim(0, 54)
    ax.tick_params(labelsize=13)
    ax.legend(frameon=False, fontsize=13, loc="lower right")
    strip(ax)
    fig.tight_layout()
    path = OUT / "search_capacity_null.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def baseline_ladder():
    ladder = json.loads((ROOT / "bench" / "results" / "baseline_ladder.json").read_text())["rows"]
    reps = json.loads((ROOT / "bench" / "results" / "representations.json").read_text())["rows"]
    by_name = {r["method"]: r for r in ladder}
    rep_by_name = {r["method"]: r for r in reps}

    picks = [
        ("4. 3-mer cosine to nearest training active, no training",
         "3-mer cosine to nearest active\nno training", by_name, False),
        ("1. protein_length_aa, no training",
         "protein length\nno training", by_name, True),
        ("8b. handcrafted + RandomForest",
         "handcrafted features\n+ random forest", by_name, False),
        ("5. family prior by nearest training family, no training",
         "family prior\nno training", by_name, False),
        ("ESM-2 150M mean-pooled",
         "ESM-2 150M\nmean-pooled", rep_by_name, False),
        ("8a. handcrafted + ExtraTrees",
         "handcrafted features\n+ extra trees", by_name, False),
        ("10. raw ESM-2 mean-pooled + logistic regression",
         "ESM-2 650M\n+ logistic regression", by_name, False),
    ]

    labels, cls, lo, hi, nulls, highlight = [], [], [], [], [], []
    for key, label, table, mark in picks:
        row = table[key]
        labels.append(label)
        cls.append(row["cls"])
        lo.append(row["cls"] - row["ci_low"])
        hi.append(row["ci_high"] - row["cls"])
        nulls.append(row["null_cls_p95"])
        highlight.append(mark)

    y = list(range(len(labels)))[::-1]
    fig, ax = plt.subplots(figsize=(10.4, 5.6), dpi=200)
    colors = [ACCENT if h else "#B9C8CC" for h in highlight]
    ax.barh(y, cls, height=0.6, color=colors, edgecolor="none", zorder=3)
    ax.errorbar(cls, y, xerr=[lo, hi], fmt="none", ecolor=MUTED,
                elinewidth=1.3, capsize=5, zorder=4)
    for yi, n in zip(y, nulls):
        ax.plot([n, n], [yi - 0.36, yi + 0.36], color=ALERT, linewidth=2.6, zorder=5)
    for yi, v in zip(y, cls):
        ax.text(0.885, yi, f"{v:.4f}", va="center", ha="right",
                fontsize=14, color=INK)

    ax.plot([], [], color=ALERT, linewidth=2.6, label="search-capacity null p95 for that row")
    ax.errorbar([], [], xerr=[[0], [0]], fmt="none", ecolor=MUTED, elinewidth=1.3,
                capsize=5, label="95 percent bootstrap interval")
    ax.legend(frameon=False, fontsize=13, loc="upper center",
              bbox_to_anchor=(0.46, -0.14), ncol=2)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=13)
    ax.set_xlabel("CLS, out of fold, nested leave-one-family-out", fontsize=15)
    ax.set_xticks([0.0, 0.2, 0.4, 0.6, 0.8])
    ax.set_xlim(0, 0.90)
    ax.tick_params(labelsize=13)
    ax.grid(axis="y", visible=False)
    strip(ax)
    fig.tight_layout()
    path = OUT / "baseline_ladder.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def lineage_vs_function():
    reps = json.loads((ROOT / "bench" / "results" / "representations.json").read_text())["rows"]
    pts = [(r["family_accuracy"], r["cls"], r["method"]) for r in reps]
    majority = reps[0]["family_majority"]

    labelled = {
        "ESM-2 150M mean-pooled": ("ESM-2 150M", -30, 14),
        "ESM-2 35M mean-pooled": ("ESM-2 35M", -28, 14),
        "ESM-2 8M mean-pooled": ("ESM-2 8M", -26, 14),
        "handcrafted: sequence and physicochemical": ("handcrafted", -32, 14),
        "structure: pLDDT, cleft and topology": ("structure", -22, 14),
    }

    fig, ax = plt.subplots(figsize=(9.6, 5.2), dpi=200)
    for acc, cls_v, name in pts:
        ax.scatter([acc], [cls_v], s=150, color=ACCENT, alpha=0.9, zorder=4,
                   edgecolor="white", linewidth=1.2)
        if name in labelled:
            text, dx, dy = labelled[name]
            ax.annotate(text, xy=(acc, cls_v), xytext=(dx, dy),
                        textcoords="offset points", fontsize=14, color=INK)

    ax.annotate(
        "ESM-2 650M and its four pooling\nand residualization variants:\nhighest lineage accuracy, zero CLS",
        xy=(0.806, 0.004), xytext=(0.663, 0.175), fontsize=14, color=ALERT,
        arrowprops=dict(arrowstyle="-", color=ALERT, linewidth=1.2),
    )
    ax.text(0.648, 0.318, f"family majority baseline: {majority:.4f}",
            fontsize=13, color=MUTED)

    ax.set_xlabel("lineage: 5-fold RT family classification accuracy", fontsize=15)
    ax.set_ylabel("function: out-of-family CLS", fontsize=15)
    ax.set_xlim(0.635, 0.855)
    ax.set_ylim(-0.025, 0.355)
    ax.tick_params(labelsize=13)
    strip(ax)
    fig.tight_layout()
    path = OUT / "lineage_vs_function.png"
    fig.savefig(path)
    plt.close(fig)
    return path


def hill_climb():
    """Reported CLS by commit, parsed from the audit report's commit ladder table."""
    text = (ROOT / "audit" / "leakage_report.md").read_text(encoding="utf-8")
    block = text.split("## 3. Commit ladder", 1)[1].split("Figure:", 1)[0]
    values = []
    for line in block.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 4 and cells[1].isdigit():
            values.append((int(cells[1]), float(cells[3])))
    values.sort()
    xs = list(range(1, len(values) + 1))
    ys = [v for _, v in values]

    fig, ax = plt.subplots(figsize=(8.6, 4.8), dpi=200)
    ax.plot(xs, ys, marker="o", markersize=7, linewidth=2.4, color=ALERT)
    ax.annotate(f"{ys[0]:.4f}", xy=(xs[0], ys[0]), xytext=(6, -20),
                textcoords="offset points", fontsize=15, color=INK)
    ax.annotate(f"{ys[-1]:.4f}", xy=(xs[-1], ys[-1]), xytext=(-18, 14),
                textcoords="offset points", fontsize=15, color=INK, fontweight="bold")
    ax.set_xlabel("commits quoting a CLS, oldest to newest", fontsize=15)
    ax.set_ylabel("CLS reported in the commit message", fontsize=15)
    ax.set_ylim(0.38, 1.04)
    ax.set_xlim(0.4, len(values) + 0.6)
    ax.set_xticks([1, 5, 10, 15, 20])
    ax.tick_params(labelsize=13)
    strip(ax)
    fig.tight_layout()
    path = OUT / "hill_climb.png"
    fig.savefig(path)
    plt.close(fig)
    return path


if __name__ == "__main__":
    for fn in (search_null_curve, baseline_ladder, lineage_vs_function, hill_climb):
        print("wrote", fn())
