"""Describe the Task A panel: composition, lengths, efficiencies, and redundancy.

Everything here is descriptive. Nothing is fitted, selected, or predicted, and no model
is trained. The point is to establish, before any result is reported, what this dataset
can and cannot resolve, so that a later number can be read against the size of the thing
that produced it.

Three quantities in particular decide the benchmark's ceiling and are reported first:
how many families hold no active enzyme at all, how many hold a single member, and the
Kish effective sample size of the CLS weighting. A leave-one-family-out evaluation over
a panel where three folds contain no positive is not a 7-fold evaluation, and a metric
whose weights concentrate on a handful of rows is not measuring 57 observations.

    python curation/dataset_overview_taskA.py
    python curation/dataset_overview_taskA.py --no-figures

Outputs:
    reports/dataset_overview.md
    reports/figures/taskA_family_composition.png
    reports/figures/taskA_activity_by_family.png
    reports/figures/taskA_length_by_family.png
    reports/figures/taskA_efficiency_among_actives.png
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
SPLITS = REPO_ROOT / "tasks" / "taskA_crossfamily" / "splits"
OUT = REPO_ROOT / "reports" / "dataset_overview.md"
FIGURES = REPO_ROOT / "reports" / "figures"

IDENTITY_THRESHOLDS = (90, 70, 50, 30)

# The CLS weighting, from evaluation/evaluate.py. Weights are the efficiency plus a small
# constant so that an inactive row still counts for something, but only barely: an
# inactive weighs 0.01 against M-MLV RT's 41.01.
CLS_EPSILON = 0.01

# Palette, from the data-visualization reference palette. Two categorical slots are all
# this report needs, and that pair passes every gate: adjacent CVD delta E 24.7, normal
# vision 33.6, both above the floors, and both slots clear 3:1 on the light surface.
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8980"
GRID = "#e5e4e0"


def kish_effective_sample_size(weights: np.ndarray) -> float:
    """Kish's effective sample size: the sum of weights squared over the sum of squares.

    For equal weights this returns n. The further the weights are from equal, the lower
    it goes, and it is the honest denominator for a weighted statistic.
    """
    weights = np.asarray(weights, dtype=float)
    return float(weights.sum() ** 2 / np.square(weights).sum())


def describe(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return {}
    return {
        "n": int(values.size),
        "min": float(values.min()),
        "q1": float(np.percentile(values, 25)),
        "median": float(np.median(values)),
        "q3": float(np.percentile(values, 75)),
        "max": float(values.max()),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=1)) if values.size > 1 else float("nan"),
    }


def load_clusters() -> dict[int, pd.DataFrame]:
    out: dict[int, pd.DataFrame] = {}
    for threshold in IDENTITY_THRESHOLDS:
        path = SPLITS / ("clusters_" + str(threshold) + ".tsv")
        if path.is_file():
            out[threshold] = pd.read_csv(path, sep="\t")
    return out


def style_axes(ax) -> None:
    """Recessive axes and grid, so the marks carry the chart."""
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(colors=INK_SECONDARY, labelsize=9, length=0)
    ax.xaxis.label.set_color(INK_SECONDARY)
    ax.yaxis.label.set_color(INK_SECONDARY)


def figure_family_composition(frame: pd.DataFrame, path: Path) -> None:
    """How many enzymes per family. One series, so no legend: the title names it."""
    import matplotlib.pyplot as plt

    counts = frame["family"].value_counts().sort_values()
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    positions = np.arange(len(counts))
    ax.barh(positions, counts.to_numpy(), height=0.6, color=SERIES_1)
    ax.set_yticks(positions)
    ax.set_yticklabels(counts.index, fontsize=9)
    ax.set_xlabel("enzymes")
    ax.set_xlim(0, counts.max() * 1.18)
    # Counts are integers, so the ticks are too. A tick at 2.5 enzymes is not a thing.
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    # Direct labels on every bar: there are seven of them, so every bar can carry its
    # value without the chart becoming a number soup.
    for position, value in zip(positions, counts.to_numpy()):
        ax.text(
            value + counts.max() * 0.02,
            position,
            str(value),
            va="center",
            fontsize=9,
            color=INK_PRIMARY,
        )
    ax.set_title(
        "Task A family composition, 57 enzymes",
        loc="left",
        fontsize=11,
        color=INK_PRIMARY,
        pad=10,
    )
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def figure_activity_by_family(frame: pd.DataFrame, path: Path) -> None:
    """Actives against inactives per family. Two series, so a legend plus direct labels."""
    import matplotlib.pyplot as plt

    order = frame["family"].value_counts().sort_values().index
    actives = [int((frame[frame["family"] == f]["active"] == "1").sum()) for f in order]
    inactives = [
        int((frame[frame["family"] == f]["active"] == "0").sum()) for f in order
    ]
    fig, ax = plt.subplots(figsize=(7.2, 3.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    positions = np.arange(len(order))
    ax.barh(positions, actives, height=0.6, color=SERIES_1, label="active")
    # A 2px surface gap between the two fills, so the boundary is not a colour seam.
    ax.barh(
        positions,
        inactives,
        height=0.6,
        left=[a + 0.12 for a in actives],
        color=SERIES_2,
        label="inactive",
    )
    ax.set_yticks(positions)
    ax.set_yticklabels(order, fontsize=9)
    ax.set_xlabel("enzymes")
    total = max(a + i for a, i in zip(actives, inactives))
    ax.set_xlim(0, total * 1.2)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for position, (a, i) in enumerate(zip(actives, inactives)):
        ax.text(
            a + i + total * 0.025,
            position,
            str(a) + " of " + str(a + i),
            va="center",
            fontsize=9,
            color=INK_PRIMARY,
        )
    legend = ax.legend(
        frameon=False, fontsize=9, loc="lower right", labelcolor=INK_SECONDARY
    )
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)
    ax.set_title(
        "Activity by family: three families hold no active enzyme",
        loc="left",
        fontsize=11,
        color=INK_PRIMARY,
        pad=10,
    )
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def figure_length_by_family(frame: pd.DataFrame, path: Path) -> None:
    """Length spread per family. A strip plot, because n per family is 1 to 18.

    A box plot would imply quartiles on a family of one. The points are the data.
    """
    import matplotlib.pyplot as plt

    order = list(frame["family"].value_counts().sort_values().index)
    fig, ax = plt.subplots(figsize=(7.2, 3.8), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    rng = np.random.default_rng(1729)
    for position, family in enumerate(order):
        lengths = frame.loc[frame["family"] == family, "sequence_len"].astype(int)
        jitter = rng.uniform(-0.16, 0.16, size=len(lengths))
        ax.scatter(
            lengths,
            np.full(len(lengths), position) + jitter,
            s=38,
            color=SERIES_1,
            alpha=0.85,
            linewidths=0.8,
            edgecolors=SURFACE,
            zorder=3,
        )
        median = float(np.median(lengths))
        ax.plot(
            [median, median],
            [position - 0.3, position + 0.3],
            color=INK_PRIMARY,
            linewidth=2.0,
            zorder=4,
        )
    ax.set_yticks(np.arange(len(order)))
    ax.set_yticklabels(order, fontsize=9)
    ax.set_xlabel("sequence length, residues")
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(
        "Length by family; the vertical tick is the family median",
        loc="left",
        fontsize=11,
        color=INK_PRIMARY,
        pad=10,
    )
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def figure_efficiency_among_actives(frame: pd.DataFrame, path: Path) -> None:
    """The 21 non-zero efficiencies, sorted. One series, direct labels on all of them."""
    import matplotlib.pyplot as plt

    actives = frame[frame["active"] == "1"].copy()
    actives["value"] = actives["pe_efficiency_pct"].astype(float)
    actives = actives.sort_values("value")
    fig, ax = plt.subplots(figsize=(7.2, 5.2), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    positions = np.arange(len(actives))
    ax.barh(positions, actives["value"].to_numpy(), height=0.62, color=SERIES_1)
    ax.set_yticks(positions)
    ax.set_yticklabels(actives["rt_name"], fontsize=8.5)
    ax.set_xlabel("prime editing efficiency, percent of precise edits")
    ax.set_xlim(0, actives["value"].max() * 1.16)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for position, value in zip(positions, actives["value"].to_numpy()):
        ax.text(
            value + actives["value"].max() * 0.015,
            position,
            ("%g" % value),
            va="center",
            fontsize=8,
            color=INK_PRIMARY,
        )
    ax.set_title(
        "Efficiency among the 21 actives, digitized from Figure S1A",
        loc="left",
        fontsize=11,
        color=INK_PRIMARY,
        pad=26,
    )
    ax.text(
        0.0,
        1.012,
        "every value is an exact multiple of 0.5, the signature of a plot read by eye",
        transform=ax.transAxes,
        fontsize=8.5,
        color=INK_MUTED,
    )
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def cluster_section(
    clusters: dict[int, pd.DataFrame], family_of: dict, active_of: dict
) -> list[str]:
    lines = [
        "## Identity clustering",
        "",
        "MMseqs2 `easy-cluster`, commit `8cc5ce36`, at four thresholds with parameters",
        "fixed a priori: `--cov-mode 1 -c 0.8 -s 7.5`. Coverage is measured over the",
        "target rather than bidirectionally, because these are excised domains with",
        "different boundaries and containment is what redundancy between them looks like.",
        "",
        "| threshold | clusters | size distribution | clusters spanning two families | clusters with mixed activity |",
        "| --- | --- | --- | --- | --- |",
    ]
    details: list[str] = []
    for threshold in IDENTITY_THRESHOLDS:
        if threshold not in clusters:
            lines.append("| " + str(threshold) + " percent | not computed | | | |")
            continue
        frame = clusters[threshold]
        groups = frame.groupby("cluster_representative")["id"].apply(list)
        sizes = Counter(len(v) for v in groups)
        spanning = {k: v for k, v in groups.items() if len({family_of[i] for i in v}) > 1}
        mixed = {
            k: v
            for k, v in groups.items()
            if len(v) > 1 and len({active_of[i] for i in v}) > 1
        }
        lines.append(
            "| "
            + str(threshold)
            + " percent | "
            + str(frame["cluster_id"].nunique())
            + " | "
            + ", ".join(
                str(count) + " of size " + str(size) for size, count in sorted(sizes.items())
            )
            + " | "
            + str(len(spanning))
            + " | "
            + str(len(mixed))
            + " |"
        )
        if spanning:
            details.append("")
            details.append("### Clusters crossing a family boundary at " + str(threshold) + " percent")
            details.append("")
            for members in spanning.values():
                labelled = sorted(
                    (i.replace("A_", ""), family_of[i]) for i in members
                )
                details.append(
                    "- "
                    + ", ".join(name + " (" + family + ")" for name, family in labelled)
                )
    return lines + details


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-figures", action="store_true", help="skip the figures")
    args = parser.parse_args()

    print_run_header("curation/dataset_overview_taskA.py", [CURATED])
    frame = pd.read_csv(CURATED, dtype=str, keep_default_na=False)
    frame["length"] = frame["sequence_len"].astype(int)
    frame["efficiency"] = frame["pe_efficiency_pct"].astype(float)
    frame["is_active"] = frame["active"] == "1"

    family_of = dict(zip(frame["id"], frame["family"]))
    active_of = dict(zip(frame["id"], frame["active"]))
    clusters = load_clusters()

    families = sorted(frame["family"].unique())
    per_family = (
        frame.groupby("family")
        .agg(
            n=("rt_name", "size"),
            actives=("is_active", "sum"),
            min_len=("length", "min"),
            median_len=("length", "median"),
            max_len=("length", "max"),
        )
        .sort_values("n", ascending=False)
    )
    zero_active = [f for f in families if per_family.loc[f, "actives"] == 0]
    single_member = [f for f in families if per_family.loc[f, "n"] == 1]

    weights = frame["efficiency"].to_numpy(dtype=float) + CLS_EPSILON
    ess = kish_effective_sample_size(weights)
    weight_share = weights / weights.sum()
    ranked = np.argsort(weight_share)[::-1]
    top_name = frame["rt_name"].to_numpy()[ranked[0]]
    top_share = weight_share[ranked[0]]
    top5_share = weight_share[ranked[:5]].sum()
    inactive_share = weight_share[~frame["is_active"].to_numpy()].sum()

    lengths = describe(frame["length"].to_numpy())
    active_efficiency = describe(
        frame.loc[frame["is_active"], "efficiency"].to_numpy()
    )

    print("families: " + str(len(families)))
    print("families with zero actives: " + str(len(zero_active)) + " " + str(zero_active))
    print("families with a single member: " + str(len(single_member)) + " " + str(single_member))
    print("Kish effective sample size: " + str(round(ess, 3)))

    lines = [
        "# Task A dataset overview",
        "",
        "Written by `curation/dataset_overview_taskA.py`. Descriptive only: nothing here",
        "is fitted, selected or predicted, and no model has been trained.",
        "",
        "Source: `tasks/taskA_crossfamily/curated.csv`, SHA256",
        "`" + sha256_of(CURATED) + "`.",
        "",
        "## What this dataset can resolve, before any result",
        "",
        "These three numbers bound every claim the benchmark can make, so they come first.",
        "",
        "| quantity | value | consequence |",
        "| --- | --- | --- |",
        "| families holding no active enzyme | "
        + str(len(zero_active))
        + " of "
        + str(len(families))
        + " ("
        + ", ".join(zero_active)
        + ") | when one of these is the held-out fold the test set is all negative, so a ranking correlation is undefined on it. Leave-one-family-out rests on "
        + str(len(families) - len(zero_active))
        + " informative folds, not "
        + str(len(families))
        + " |",
        "| families holding a single enzyme | "
        + str(len(single_member))
        + " ("
        + ", ".join(single_member)
        + ") | a fold of one. Nothing about variance within that family is estimable |",
        "| Kish effective sample size of the CLS weighting | "
        + str(round(ess, 3))
        + " | the weighted half of CLS is worth about "
        + str(round(ess, 1))
        + " independent observations, not 57 |",
        "",
        "The effective sample size is low because the CLS weights are the efficiency plus",
        "0.01, and the efficiencies span 0 to 41. `"
        + top_name
        + "` alone carries "
        + str(round(100 * top_share, 2))
        + " percent of the",
        "total weight, the top five carry "
        + str(round(100 * top5_share, 2))
        + " percent, and all "
        + str(int((~frame["is_active"]).sum()))
        + " inactive enzymes together",
        "carry "
        + str(round(100 * inactive_share, 3))
        + " percent. A weighted Spearman over this panel is close to a statement",
        "about the ordering of a handful of enzymes.",
        "",
        "## Composition",
        "",
        "| quantity | value |",
        "| --- | --- |",
        "| enzymes | " + str(len(frame)) + " |",
        "| families | " + str(len(families)) + " |",
        "| active | "
        + str(int(frame["is_active"].sum()))
        + " ("
        + str(round(100 * frame["is_active"].mean(), 1))
        + " percent) |",
        "| inactive | " + str(int((~frame["is_active"]).sum())) + " |",
        "",
        "| family | enzymes | active | inactive | shortest | median | longest |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for family in per_family.index:
        row = per_family.loc[family]
        lines.append(
            "| "
            + family
            + " | "
            + str(int(row["n"]))
            + " | "
            + str(int(row["actives"]))
            + " | "
            + str(int(row["n"] - row["actives"]))
            + " | "
            + str(int(row["min_len"]))
            + " | "
            + str(int(row["median_len"]))
            + " | "
            + str(int(row["max_len"]))
            + " |"
        )

    lines += [
        "",
        "The panel is dominated by two families. Retroviral holds "
        + str(int(per_family.loc["Retroviral", "n"]))
        + " of the 57 enzymes and",
        str(int(per_family.loc["Retroviral", "actives"]))
        + " of the "
        + str(int(frame["is_active"].sum()))
        + " actives; Retron holds "
        + str(int(per_family.loc["Retron", "n"]))
        + " and "
        + str(int(per_family.loc["Retron", "actives"]))
        + ". Between them they are "
        + str(int(per_family.loc["Retroviral", "n"] + per_family.loc["Retron", "n"]))
        + " rows",
        "and " + str(int(per_family.loc["Retroviral", "actives"] + per_family.loc["Retron", "actives"]))
        + " of the actives, so a model that learns only the retroviral family will score well",
        "on the pooled metric while having learned one clade.",
        "",
        "## Length",
        "",
        "| statistic | all enzymes |",
        "| --- | --- |",
    ]
    for key in ("n", "min", "q1", "median", "q3", "max", "mean", "sd"):
        lines.append("| " + key + " | " + ("%g" % round(lengths[key], 1)) + " |")

    lines += [
        "",
        "Length is not independent of family. The bacterial families sit near 300 to 500",
        "residues and the retroviral family near 570 to 700, so any model with access to",
        "length has partial access to lineage. That is the confound the earlier audit",
        "measured as embedding PC1 tracking length at Spearman -0.77, and it is why the",
        "length-only baseline is the one every representation has to beat.",
        "",
        "## Efficiency among the actives",
        "",
        "Only the 21 active enzymes have a non-zero efficiency; all 36 inactives are",
        "exactly 0.0.",
        "",
        "| statistic | value |",
        "| --- | --- |",
    ]
    for key in ("n", "min", "q1", "median", "q3", "max", "mean", "sd"):
        lines.append("| " + key + " | " + ("%g" % round(active_efficiency[key], 3)) + " |")

    lines += [
        "",
        "Every one of these values is an exact multiple of 0.5, which is the signature of",
        "a figure read by eye rather than a table transcribed. The provenance is set out in",
        "`reports/reconciliation.md` section 4. Per the Gate G2 ruling, classification on",
        "the binary label is the primary result and every number derived from this column",
        "carries that digitization as a stated limitation.",
        "",
    ]

    lines += cluster_section(clusters, family_of, active_of)

    lines += [
        "",
        "### What the 30 percent threshold changes",
        "",
        "At 90, 70 and 50 percent identity no cluster crosses a family boundary, which is",
        "what an earlier version of `reports/split_design.md` reported as holding at every",
        "threshold. Adding 30 percent shows that claim was threshold-limited: four clusters",
        "cross a family boundary there. The correction matters because it is the only",
        "threshold at which the claim fails, and 30 percent is the conventional line below",
        "which two proteins are not assumed homologous.",
        "",
        "So leave-one-family-out does **not** hold out an identity cluster at 30 percent.",
        "For the families involved, holding out the family still leaves relatives above 30",
        "percent identity in the training set. Three of the four crossing clusters join",
        "bacterial families to each other, which is consistent with CRISPR-associated RTs",
        "being derived from group II intron RTs rather than with a labelling error; the",
        "fourth joins `CaMV-RT`, labelled Other, to the two LTR retrotransposon RTs, which",
        "is consistent with caulimovirus being a pararetrovirus. In other words these look",
        "like genuine phylogenetic signal that the 7-way labelling coarsens away, not like",
        "mislabelled rows. Either way they are flagged, and the leave-one-cluster-out split",
        "at 70 percent exists as the stricter control.",
        "",
        "### Clusters holding both an active and an inactive enzyme",
        "",
        "These are the pairs no similarity-based method can get fully right, because the",
        "members are near-identical and carry opposite labels.",
        "",
    ]
    if 90 in clusters:
        groups = clusters[90].groupby("cluster_representative")["id"].apply(list)
        for members in groups:
            if len(members) > 1 and len({active_of[i] for i in members}) > 1:
                described = ", ".join(
                    i.replace("A_", "")
                    + " ("
                    + ("active" if active_of[i] == "1" else "inactive")
                    + ")"
                    for i in sorted(members)
                )
                lines.append("- at 90 percent identity: " + described)
    lines += [
        "",
        "Either activity turns on a few residues or one of the calls is noise. 21",
        "positives cannot separate those two readings, and that is a limit of the dataset",
        "rather than of any particular model.",
        "",
        "## Figures",
        "",
        "| figure | what it shows |",
        "| --- | --- |",
        "| `figures/taskA_family_composition.png` | enzymes per family |",
        "| `figures/taskA_activity_by_family.png` | actives against inactives per family |",
        "| `figures/taskA_length_by_family.png` | length spread per family, with the family median |",
        "| `figures/taskA_efficiency_among_actives.png` | the 21 non-zero efficiencies, sorted |",
        "",
        "Every figure's underlying numbers are in the tables above, so the report is",
        "readable without the images.",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())

    if not args.no_figures:
        FIGURES.mkdir(parents=True, exist_ok=True)
        figure_family_composition(frame, FIGURES / "taskA_family_composition.png")
        figure_activity_by_family(frame, FIGURES / "taskA_activity_by_family.png")
        figure_length_by_family(frame, FIGURES / "taskA_length_by_family.png")
        figure_efficiency_among_actives(
            frame, FIGURES / "taskA_efficiency_among_actives.png"
        )
        for name in (
            "taskA_family_composition.png",
            "taskA_activity_by_family.png",
            "taskA_length_by_family.png",
            "taskA_efficiency_among_actives.png",
        ):
            print("wrote reports/figures/" + name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
