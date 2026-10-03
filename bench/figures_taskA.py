"""The two headline figures: representation comparison with error bars, and the nulls.

Every other figure in this benchmark describes the dataset or the representation space.
These two describe the result, and they are built to make the result's shape legible at a
glance: that the ordering of the representations is mostly inside its own uncertainty,
and that almost everything sits under one null or another.

    python bench/figures_taskA.py

Outputs:
    reports/figures/taskA_representation_comparison.png
    reports/figures/taskA_null_comparison.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header  # noqa: E402

RESULTS = REPO_ROOT / "bench" / "results"
MAIN = RESULTS / "taskA_representations.json"
VALIDATION = RESULTS / "taskA_validation.json"
FIGURES = REPO_ROOT / "reports" / "figures"

# Palette slots 1 to 3 from the project's reference palette. Three slots are the most
# that validate on the all-pairs pairlist, which is what a grouped chart needs, so the
# null comparison uses exactly three series and no more.
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
SERIES_3 = "#1baf7a"
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8980"
GRID = "#e5e4e0"

HEAD = "classification"


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(colors=INK_SECONDARY, labelsize=8.5, length=0)
    ax.xaxis.label.set_color(INK_SECONDARY)
    ax.yaxis.label.set_color(INK_SECONDARY)


def load() -> tuple[dict, dict]:
    return (
        json.loads(MAIN.read_text(encoding="utf-8")),
        json.loads(VALIDATION.read_text(encoding="utf-8")),
    )


def figure_comparison(main: dict, validation: dict, prevalence: float, path: Path) -> None:
    """PR-AUC per representation with its bootstrap interval, against chance."""
    import matplotlib.pyplot as plt

    rows = []
    for label, entry in main["results"].items():
        if HEAD not in entry:
            continue
        score = entry[HEAD]["pr_auc"]
        interval = validation["intervals"].get(label, {}).get(HEAD, {}).get("pr_auc", {})
        rows.append(
            (
                score,
                label,
                interval.get("ci_low", score),
                interval.get("ci_high", score),
            )
        )
    rows.sort()

    fig, ax = plt.subplots(figsize=(7.6, 4.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    positions = np.arange(len(rows))
    scores = np.array([r[0] for r in rows])
    low = np.array([r[2] for r in rows])
    high = np.array([r[3] for r in rows])

    ax.hlines(
        positions, low, high, color=SERIES_1, linewidth=2.0, alpha=0.45, zorder=2
    )
    ax.scatter(scores, positions, s=52, color=SERIES_1, zorder=3, edgecolors=SURFACE, linewidths=0.8)
    ax.axvline(prevalence, color=INK_MUTED, linewidth=1.4, linestyle="--", zorder=1)
    # Anchored at the bottom of the plot, where there is space, rather than at the top
    # where it would collide with the subtitle.
    ax.text(
        prevalence,
        -0.75,
        "  chance = prevalence " + format(prevalence, ".3f"),
        fontsize=8.5,
        color=INK_SECONDARY,
        va="center",
    )
    ax.set_yticks(positions)
    ax.set_yticklabels([r[1] for r in rows], fontsize=9)
    ax.set_xlabel("classification PR-AUC, with 95 percent bootstrap interval")
    ax.set_xlim(0, 1.0)
    ax.set_ylim(-1.4, len(rows) - 0.3)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(
        "Representation comparison: the intervals overlap almost everywhere",
        loc="left",
        fontsize=11,
        color=INK_PRIMARY,
        pad=22,
    )
    # The subtitle states a fact, so it is computed rather than asserted.
    excludes_chance = [r[1] for r in rows if r[2] > prevalence]
    if excludes_chance:
        claim = (
            "only "
            + ", ".join(excludes_chance)
            + " has an interval entirely above chance; the rest of the ordering is not resolvable"
        )
    else:
        claim = "every interval spans chance; the ordering is not resolvable"
    ax.text(
        0.0,
        1.012,
        claim,
        transform=ax.transAxes,
        fontsize=8.5,
        color=INK_MUTED,
    )
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def figure_nulls(main: dict, validation: dict, prevalence: float, path: Path) -> None:
    """Observed against the two measured nulls, per representation."""
    import matplotlib.pyplot as plt

    noise = validation.get("noise", {})
    permutation = validation.get("permutation", {})
    rows = []
    for label, entry in main["results"].items():
        if HEAD not in entry:
            continue
        rows.append(
            (
                entry[HEAD]["pr_auc"],
                label,
                noise.get(label, {}).get(HEAD, {}).get("pr_auc"),
                permutation.get(label, {}).get(HEAD, {}).get("pr_auc_p95"),
            )
        )
    rows.sort()

    fig, ax = plt.subplots(figsize=(7.8, 4.8), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    positions = np.arange(len(rows))
    offset = 0.26

    ax.scatter(
        [r[0] for r in rows],
        positions + offset,
        s=56,
        marker="o",
        color=SERIES_1,
        edgecolors=SURFACE,
        linewidths=0.8,
        label="observed",
        zorder=3,
    )
    noise_positions = [i for i, r in enumerate(rows) if r[2] is not None]
    ax.scatter(
        [rows[i][2] for i in noise_positions],
        np.array(noise_positions),
        s=56,
        marker="s",
        color=SERIES_2,
        edgecolors=SURFACE,
        linewidths=0.8,
        label="Gaussian noise control",
        zorder=3,
    )
    perm_positions = [i for i, r in enumerate(rows) if r[3] is not None]
    ax.scatter(
        [rows[i][3] for i in perm_positions],
        np.array(perm_positions) - offset,
        s=58,
        marker="^",
        color=SERIES_3,
        edgecolors=SURFACE,
        linewidths=0.8,
        label="permuted-label p95",
        zorder=3,
    )
    for index, row in enumerate(rows):
        values = [v for v in (row[0], row[2], row[3]) if v is not None]
        ax.hlines(index, min(values), max(values), color=GRID, linewidth=1.2, zorder=1)

    ax.axvline(prevalence, color=INK_MUTED, linewidth=1.4, linestyle="--", zorder=1)
    ax.set_yticks(positions)
    ax.set_yticklabels([r[1] for r in rows], fontsize=9)
    ax.set_xlabel("classification PR-AUC")
    ax.set_xlim(0, 0.8)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    legend = ax.legend(frameon=False, fontsize=8.5, loc="lower right")
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)
    ax.set_title(
        "Against the nulls: only kmer4 sits right of both its controls",
        loc="left",
        fontsize=11,
        color=INK_PRIMARY,
        pad=22,
    )
    ax.text(
        0.0,
        1.012,
        "ESM-2 650M and 8M clear the noise control and then lose to their own shuffled labels",
        transform=ax.transAxes,
        fontsize=8.5,
        color=INK_MUTED,
    )
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    print_run_header("bench/figures_taskA.py", [MAIN, VALIDATION])
    main_results, validation = load()
    import csv

    with (REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv").open(
        encoding="utf-8"
    ) as handle:
        rows = list(csv.DictReader(handle))
    prevalence = sum(1 for r in rows if r["active"] == "1") / len(rows)

    FIGURES.mkdir(parents=True, exist_ok=True)
    figure_comparison(
        main_results, validation, prevalence, FIGURES / "taskA_representation_comparison.png"
    )
    figure_nulls(main_results, validation, prevalence, FIGURES / "taskA_null_comparison.png")
    print("wrote reports/figures/taskA_representation_comparison.png")
    print("wrote reports/figures/taskA_null_comparison.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
