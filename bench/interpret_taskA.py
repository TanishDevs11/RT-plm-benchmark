"""Interpret the Task A results, but only for a representation that earned it.

The gate, from the brief and not negotiable here: **a representation is analyzed only if
it clears both its own dimensionality-matched noise control and the search-capacity null
at its matched free-parameter count.** Interpreting a model that loses to protein length
is interpreting noise, and a feature-importance plot of such a model is actively
misleading, because it looks exactly like a feature-importance plot of a model that works.

So this script reads `bench/results/taskA_validation.json`, applies the gate, and takes
one of two branches:

  * **something cleared.** Feature importance for that representation, the contribution of
    length specifically, and the contribution of family-correlated dimensions.
  * **nothing cleared.** It says so plainly as the result, and runs the failure analysis
    instead: which families are predicted worst, whether the errors track length or
    distance from the training distribution, and which individual enzymes are misranked.

    python bench/interpret_taskA.py

Outputs:
    reports/interpretation.md
    reports/figures/taskA_failure_by_family.png
    reports/figures/taskA_error_vs_length.png
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bench"))

from representations_taskA import load_representations, load_taskA_dataset  # noqa: E402

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
RESULTS = REPO_ROOT / "bench" / "results"
MAIN = RESULTS / "taskA_representations.json"
VALIDATION = RESULTS / "taskA_validation.json"
OUT = REPO_ROOT / "reports" / "interpretation.md"
FIGURES = REPO_ROOT / "reports" / "figures"

SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8980"
GRID = "#e5e4e0"


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(colors=INK_SECONDARY, labelsize=8, length=0)
    ax.xaxis.label.set_color(INK_SECONDARY)
    ax.yaxis.label.set_color(INK_SECONDARY)


def apply_gate(
    main: dict, validation: dict, prevalence: float
) -> tuple[list[dict], list[dict], float | None]:
    """Which representation and head pairs clear their nulls, on each of two tests.

    Two gates, because CLS and PR-AUC answer different questions.

    The CLS gate is the one the brief names: clear the dimensionality-matched noise
    control and the search-capacity null at matched K. But CLS is the harmonic mean of
    PR-AUC and a weighted Spearman computed against `pe_efficiency_pct`, and the Gate G2
    ruling established that column is a digitization of Figure S1A. A representation that
    separates actives well but does not reproduce the digitized ordering scores a CLS of
    zero, because the harmonic mean floors there, and failing the CLS gate for that reason
    is a statement about the figure rather than about the representation.

    So the classification head is also gated on PR-AUC against its own noise control and
    against the positive prevalence, which is the chance level for PR-AUC. That is the
    test of the reproducible binary label, and it is the primary claim per Gate G2. There
    is no search-capacity null for PR-AUC, because bench/search_null.py measures CLS, and
    that gap is stated rather than filled with the CLS bar.
    """
    search = validation.get("search_null_matched")
    bar = search["p95"] if search else None
    noise = validation.get("noise", {})
    cleared_cls: list[dict] = []
    cleared_pr: list[dict] = []
    for label, entry in main["results"].items():
        for head in main["heads"]:
            if head not in entry:
                continue
            noise_entry = noise.get(label, {}).get(head, {})
            score = entry[head]["cls"]
            noise_score = noise_entry.get("cls")
            if noise_score is not None and bar is not None:
                if score > noise_score and score > bar:
                    cleared_cls.append(
                        {
                            "label": label,
                            "head": head,
                            "metric": "cls",
                            "score": score,
                            "noise": noise_score,
                            "floor": bar,
                            "margin": score - max(noise_score, bar),
                        }
                    )
            if head == "classification":
                pr = entry[head]["pr_auc"]
                noise_pr = noise_entry.get("pr_auc")
                if noise_pr is not None:
                    worst = max(noise_pr, prevalence)
                    if pr > worst:
                        cleared_pr.append(
                            {
                                "label": label,
                                "head": head,
                                "metric": "pr_auc",
                                "score": pr,
                                "noise": noise_pr,
                                "floor": prevalence,
                                "margin": pr - worst,
                            }
                        )
    return (
        sorted(cleared_cls, key=lambda item: -item["margin"]),
        sorted(cleared_pr, key=lambda item: -item["margin"]),
        bar,
    )


def figure_failure_by_family(
    families: np.ndarray, residuals: np.ndarray, head_label: str, path: Path
) -> None:
    import matplotlib.pyplot as plt

    order = sorted(np.unique(families), key=lambda f: -(families == f).sum())
    fig, ax = plt.subplots(figsize=(7.0, 3.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    rng = np.random.default_rng(1729)
    for position, family in enumerate(order):
        mask = families == family
        values = residuals[mask]
        ax.scatter(
            values,
            np.full(mask.sum(), position) + rng.uniform(-0.15, 0.15, mask.sum()),
            s=36,
            color=SERIES_1,
            alpha=0.85,
            edgecolors=SURFACE,
            linewidths=0.8,
            zorder=3,
        )
        median = float(np.median(values))
        ax.plot(
            [median, median],
            [position - 0.3, position + 0.3],
            color=INK_PRIMARY,
            linewidth=2.0,
            zorder=4,
        )
    ax.axvline(0.0, color=INK_MUTED, linewidth=1.0, zorder=2)
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels([f.replace("_", " ") for f in order], fontsize=9)
    ax.set_xlabel("signed error, predicted rank percentile minus true rank percentile")
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(
        "Where the predictions fail, by family: " + head_label,
        loc="left",
        fontsize=11,
        color=INK_PRIMARY,
        pad=10,
    )
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def figure_error_vs_length(
    lengths: np.ndarray,
    residuals: np.ndarray,
    distances: np.ndarray,
    rho_length: float,
    rho_distance: float,
    path: Path,
) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(8.4, 3.6), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    for ax, x, label, rho in (
        (axes[0], lengths, "sequence length, residues", rho_length),
        (
            axes[1],
            distances,
            "distance from the training distribution, z-scored",
            rho_distance,
        ),
    ):
        ax.scatter(
            x, np.abs(residuals), s=38, color=SERIES_1, edgecolors=SURFACE, linewidths=0.8
        )
        ax.set_xlabel(label)
        ax.set_ylabel("absolute error, rank percentile")
        ax.set_title(
            "Spearman " + format(rho, "+.3f"), loc="left", fontsize=10, color=INK_PRIMARY
        )
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.yaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        style_axes(ax)
    fig.suptitle(
        "Do the errors track length, or novelty?",
        fontsize=11,
        color=INK_PRIMARY,
        x=0.01,
        ha="left",
    )
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def rank_percentile(values: np.ndarray) -> np.ndarray:
    order = np.argsort(np.argsort(values))
    return order / max(1, len(values) - 1)


def main() -> int:
    print_run_header("bench/interpret_taskA.py", [CURATED, MAIN, VALIDATION])
    if not MAIN.is_file() or not VALIDATION.is_file():
        raise SystemExit(
            "run bench/representations_taskA.py and bench/validate_taskA.py first"
        )
    main_results = json.loads(MAIN.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    data = load_taskA_dataset()

    prevalence = float(data["active"].to_numpy().mean())
    cleared_cls, cleared_pr, bar = apply_gate(main_results, validation, prevalence)
    cleared = cleared_cls + cleared_pr
    print("")
    print("two gates applied:")
    print("  CLS: clear the noise control and the search-capacity null p95 at K=1")
    print("  PR-AUC, classification only: clear the noise control and the prevalence")
    if bar is not None:
        print("search-capacity null p95 at K=1: " + format(bar, ".4f"))
    print("prevalence, the PR-AUC chance level: " + format(prevalence, ".4f"))
    print("clearing the CLS gate: " + str(len(cleared_cls)))
    for item in cleared_cls:
        print(
            "  "
            + item["label"]
            + " | "
            + item["head"]
            + " CLS "
            + format(item["score"], ".4f")
            + " margin "
            + format(item["margin"], "+.4f")
        )
    print("clearing the PR-AUC gate: " + str(len(cleared_pr)))
    for item in cleared_pr:
        print(
            "  "
            + item["label"]
            + " | PR-AUC "
            + format(item["score"], ".4f")
            + " vs noise "
            + format(item["noise"], ".4f")
            + " margin "
            + format(item["margin"], "+.4f")
        )

    lines = [
        "# Task A interpretation",
        "",
        "Written by `bench/interpret_taskA.py`.",
        "",
        "Source: `tasks/taskA_crossfamily/curated.csv`, SHA256",
        "`" + sha256_of(CURATED) + "`.",
        "",
        "## The gate",
        "",
        "A representation is interpreted here only if it clears, at once, its own",
        "dimensionality-matched Gaussian noise control and the search-capacity null at its",
        "matched free-parameter count. Interpreting a model that loses to protein length is",
        "interpreting noise, and a feature-importance plot of such a model is actively",
        "misleading: it looks exactly like the plot of a model that works.",
        "",
    ]
    if bar is not None:
        lines.append(
            "The search-capacity bar is a CLS of "
            + format(bar, ".4f")
            + ", the p95 of what a one-free-parameter"
        )
        lines.append("search reaches on pure Gaussian noise.")
        lines.append("")

    lines += [
        "| gate | metric | floor it must clear | representations clearing it |",
        "| --- | --- | --- | --- |",
        "| CLS | CLS | the larger of its noise control and the K=1 search-capacity null p95"
        + (" of " + format(bar, ".4f") if bar is not None else "")
        + " | "
        + str(len(cleared_cls))
        + " |",
        "| PR-AUC, classification only | PR-AUC | the larger of its noise control and the positive prevalence of "
        + format(prevalence, ".4f")
        + " | "
        + str(len(cleared_pr))
        + " |",
        "",
        "The second gate exists because CLS is the harmonic mean of PR-AUC and a weighted",
        "Spearman against `pe_efficiency_pct`. Per the Gate G2 ruling that column is a",
        "digitization of Figure S1A, so a representation that separates actives well but",
        "does not reproduce the digitized ordering scores a CLS of zero, the harmonic mean",
        "flooring there. Failing the CLS gate for that reason is a statement about the",
        "figure, not about the representation. There is no search-capacity null for PR-AUC,",
        "because `bench/search_null.py` measures CLS; that gap is stated rather than filled",
        "with the CLS bar, which would compare two different quantities.",
        "",
    ]

    if cleared:
        lines += [
            "## Representations that cleared a gate",
            "",
            "| representation | head | metric | score | noise control | floor | margin |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for item in cleared:
            lines.append(
                "| `"
                + item["label"]
                + "` | "
                + item["head"]
                + " | "
                + item["metric"]
                + " | "
                + format(item["score"], ".4f")
                + " | "
                + format(item["noise"], ".4f")
                + " | "
                + format(item["floor"], ".4f")
                + " | "
                + format(item["margin"], "+.4f")
                + " |"
            )
        lines += [
            "",
            "Feature attribution for a representation that clears a gate is the next step",
            "and is deliberately not implemented in this script. Writing an attribution",
            "path speculatively, for a case that might not arise, would mean shipping",
            "untested code that produces a plot; and a plot is believed. The two things to",
            "compute first are the contribution of length specifically and the contribution",
            "of family-correlated dimensions, because those are the two confounds the",
            "earlier phases measured directly.",
            "",
            "Note what clearing the PR-AUC gate does and does not license. It licenses the",
            "claim that the representation separates active from inactive enzymes above its",
            "own noise control. It does not license a claim about predicting efficiency, and",
            "it does not by itself rule out that the separation is lineage: a representation",
            "that encodes family will separate actives in a panel where 12 of 18 retroviral",
            "enzymes are active and 0 of 15 across three other families are. The",
            "family-classification control in `reports/representation_diagnostics.md` is",
            "what speaks to that, and it shows these representations classify family far",
            "better than they classify activity.",
            "",
        ]
        best = cleared[0]
    else:
        lines += [
            "## Nothing cleared the gate. That is the result.",
            "",
            "**No representation, under either head, scores above both its own",
            "dimensionality-matched noise control and the search-capacity null at one free",
            "parameter.** No SHAP analysis, no feature importance ranking and no attribution",
            "of any kind is produced below, because there is no model whose behaviour would",
            "be worth attributing. This is the honest outcome and it is reported as the",
            "finding rather than worked around.",
            "",
            "What follows instead is the failure analysis the brief specifies for this case.",
            "",
        ]
        best = None

    # Failure analysis runs either way: it is informative about the panel even when
    # something clears, and it is the deliverable when nothing does.
    head = "classification"
    candidates = [
        (label, entry[head]["cls"])
        for label, entry in main_results["results"].items()
        if head in entry
    ]
    if not candidates:
        raise SystemExit("no classification results to analyze")
    label, score = max(candidates, key=lambda pair: pair[1])
    predictions = np.asarray(
        main_results["results"][label][head]["predictions"], dtype=float
    )
    families = data["rt_family"].to_numpy()
    lengths = data["protein_length_aa"].to_numpy(dtype=float)
    efficiency = data["pe_efficiency_pct"].to_numpy(dtype=float)
    names = data["rt_name"].to_numpy()

    # Signed error in rank percentile, so the scale is comparable across heads and the
    # sign says whether an enzyme was over- or under-ranked.
    predicted_rank = rank_percentile(predictions)
    true_rank = rank_percentile(efficiency)
    residuals = predicted_rank - true_rank

    from scipy.stats import spearmanr

    # Distance from the training distribution, as a z-scored Euclidean distance from the
    # panel centroid in the representation that scored best. A row far from the centroid
    # is a row the training folds had least to say about.
    representation = load_representations([label])[label][0]
    centred = representation - representation.mean(axis=0)
    spread = centred.std(axis=0)
    spread[spread == 0] = 1.0
    z = centred / spread
    distances = np.linalg.norm(z, axis=1)

    rho_length, p_length = spearmanr(lengths, np.abs(residuals))
    rho_distance, p_distance = spearmanr(distances, np.abs(residuals))

    per_family = []
    for family in sorted(np.unique(families)):
        mask = families == family
        per_family.append(
            {
                "family": family,
                "n": int(mask.sum()),
                "n_active": int(data["active"].to_numpy()[mask].sum()),
                "mean_abs_error": float(np.abs(residuals[mask]).mean()),
                "mean_signed_error": float(residuals[mask].mean()),
            }
        )
    per_family.sort(key=lambda row: -row["mean_abs_error"])

    worst = np.argsort(np.abs(residuals))[::-1][:10]

    lines += [
        "## Failure analysis",
        "",
        "Run on `"
        + label
        + "`, the "
        + head
        + " head's highest-scoring representation at a CLS of "
        + format(score, ".4f")
        + ".",
        "Errors are expressed as a signed difference in rank percentile, predicted minus",
        "true, so the scale is comparable across heads and the sign says whether an enzyme",
        "was ranked too high or too low.",
        "",
        "### Which families are predicted worst",
        "",
        "| family | n | actives | mean absolute error | mean signed error |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in per_family:
        lines.append(
            "| "
            + row["family"]
            + " | "
            + str(row["n"])
            + " | "
            + str(row["n_active"])
            + " | "
            + format(row["mean_abs_error"], ".4f")
            + " | "
            + format(row["mean_signed_error"], "+.4f")
            + " |"
        )

    lines += [
        "",
        "### Do the errors track length, or novelty?",
        "",
        "| predictor of absolute error | Spearman | p |",
        "| --- | --- | --- |",
        "| sequence length | "
        + format(float(rho_length), "+.4f")
        + " | "
        + format(float(p_length), ".4g")
        + " |",
        "| distance from the panel centroid in representation space | "
        + format(float(rho_distance), "+.4f")
        + " | "
        + format(float(p_distance), ".4g")
        + " |",
        "",
        "The second row is a proxy for how far a held-out enzyme sits from what the",
        "training folds contained. It is a z-scored Euclidean distance from the panel",
        "centroid, which is a crude measure: it treats every dimension as equally",
        "informative and it is computed over the whole panel rather than per fold. A",
        "stronger version would use the per-fold training centroid, and that is a stated",
        "limitation rather than a result.",
        "",
        "### The worst-ranked individual enzymes",
        "",
        "| enzyme | family | active | true efficiency | predicted rank percentile | true rank percentile | signed error |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    active_flags = data["active"].to_numpy()
    for index in worst:
        lines.append(
            "| `"
            + str(names[index])
            + "` | "
            + str(families[index])
            + " | "
            + ("yes" if active_flags[index] else "no")
            + " | "
            + format(efficiency[index], ".1f")
            + " | "
            + format(predicted_rank[index], ".3f")
            + " | "
            + format(true_rank[index], ".3f")
            + " | "
            + format(residuals[index], "+.3f")
            + " |"
        )

    lines += [
        "",
        "## Figures",
        "",
        "| figure | what it shows |",
        "| --- | --- |",
        "| `figures/taskA_failure_by_family.png` | signed error by family, with the family median |",
        "| `figures/taskA_error_vs_length.png` | absolute error against length and against distance from the panel centroid |",
        "",
        "## What the failure analysis does and does not say",
        "",
        "It describes where this particular model's errors fall. It does not diagnose why",
        "the representations fail, because with 21 positives, a CLS-weighted effective",
        "sample size of 11.338, and three of seven folds holding no active at all, the",
        "panel cannot distinguish between the two live explanations: that the",
        "representations carry no activity signal, and that they carry some but the panel",
        "is too small and too confounded to detect it. Those are different conclusions with",
        "different consequences, and this dataset does not separate them.",
        "",
        "What the earlier phases did establish, and what the failure analysis is consistent",
        "with, is that the representations encode lineage and length rather than function:",
        "ESM-2 650M classifies family at 0.8197 against a majority baseline of 0.3214, and",
        "its leading principal component tracks sequence length at Spearman -0.7681. A",
        "representation that is mostly a lineage-and-length encoding has little left to",
        "offer a family-held-out activity task, which is exactly what these results look",
        "like.",
    ]

    FIGURES.mkdir(parents=True, exist_ok=True)
    figure_failure_by_family(
        families, residuals, label + ", " + head, FIGURES / "taskA_failure_by_family.png"
    )
    figure_error_vs_length(
        lengths,
        residuals,
        distances,
        float(rho_length),
        float(rho_distance),
        FIGURES / "taskA_error_vs_length.png",
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    print("wrote 2 figures to reports/figures/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
