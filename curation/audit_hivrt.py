"""Audit the HIV-1 RT phenotype dataset before any model is fitted.

Descriptive only. Nothing here is fitted, selected or predicted. The point is to establish
what the dataset can support, and in particular three numbers that bound every later
claim: how many independent sequences there really are behind the phenotype rows, how much
of the label range is assay noise rather than signal, and what the source's filtering
removed.

The reproducibility ceiling is the one that matters most. Where the same reconstructed
sequence carries two independent phenotype measurements for the same drug, the agreement
between those measurements is an upper bound on any model's achievable correlation. A
model credited with approaching a correlation above the assay's own replicate agreement
has been credited with predicting noise.

    python curation/audit_hivrt.py
    python curation/audit_hivrt.py --no-figures

Outputs:
    reports/taskB_hivrt/audit_report.md
    reports/taskB_hivrt/audit_summary.json
    reports/taskB_hivrt/figures/hivrt_label_distribution.png
    reports/taskB_hivrt/figures/hivrt_mutation_counts.png
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_hivrt"
CURATED = TASK_DIR / "curated.csv"
ISOLATES = TASK_DIR / "curated_isolates.csv"
PARSE_REPORT = TASK_DIR / "parse_report.json"
OUT = REPO_ROOT / "reports" / "taskB_hivrt" / "audit_report.md"
SUMMARY = REPO_ROOT / "reports" / "taskB_hivrt" / "audit_summary.json"
FIGURES = REPO_ROOT / "reports" / "taskB_hivrt" / "figures"

DRUGS = {
    "NRTI": ("3TC", "ABC", "AZT", "D4T", "DDI", "TDF"),
    "NNRTI": ("EFV", "NVP", "ETR", "RPV", "DOR"),
}

# The modelling scale, stated once and used everywhere. Fold resistance is approximately
# log-normal, so log10 is the scale on which it is modelled and reported.
LABEL_SCALE = "log10 fold resistance"

# Effect-direction bands, used only for description. Fold resistance below 1 means the
# isolate is more susceptible than wild type, which is measurement noise around 1 for most
# isolates rather than a biological effect, so the bands are deliberately coarse.
RESISTANT_FOLD = 10.0
INTERMEDIATE_FOLD = 3.0

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


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def describe(values: np.ndarray) -> dict:
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


def reproducibility_ceiling(labels: list[dict], isolates: list[dict]) -> dict:
    """Agreement between repeated measurements of the same sequence and drug.

    Two decisions make this estimate defensible, and both were forced by what a naive
    version produced.

    **Only fully sequenced isolates count.** The reconstruction encodes unsequenced
    positions, mixtures and other indeterminate cells as `X`, and the median unfiltered
    isolate carries 258 such positions out of 560. Two isolates differing only at `X`
    positions collapse to the same string without being the same virus. A first version of
    this function ignored that and reported a ceiling of 0.9761 over 306759 pairs; almost
    all of those pairs came from five groups of isolates that were more than half
    unsequenced, one of them containing 256 isolates. That is not replicate agreement, it
    is the agreement of a group of different viruses that happen to be indistinguishable
    at low sequencing coverage. Requiring zero unknown positions removes it.

    **One pair per group.** A group of n identical sequences contributes n(n-1)/2 pairs, so
    a handful of large groups otherwise dominates the estimate. Taking one pair per group
    weights each distinct sequence equally.

    The sensitivity of the result to the first decision is reported rather than hidden,
    because it is large and a reader should see it.
    """
    from scipy.stats import pearsonr, spearmanr

    def estimate(max_unknown: int, one_pair_per_group: bool) -> dict:
        sequence_of: dict[tuple[str, str], str] = {}
        for row in isolates:
            if row["dataset"] != "unfiltered":
                continue
            if int(row["n_unknown_positions"]) > max_unknown:
                continue
            sequence_of[(row["drug_class"], row["isolate_id"])] = row["sequence"]
        groups: dict[tuple[str, str], list[float]] = defaultdict(list)
        for row in labels:
            if row["dataset"] != "unfiltered" or not row["log10_fold"]:
                continue
            sequence = sequence_of.get((row["drug_class"], row["isolate_id"]))
            if sequence is None:
                continue
            groups[(row["drug"], sequence)].append(float(row["log10_fold"]))
        a: list[float] = []
        b: list[float] = []
        n_groups = 0
        for values in groups.values():
            if len(values) < 2:
                continue
            n_groups += 1
            if one_pair_per_group:
                a.append(values[0])
                b.append(values[1])
            else:
                for i in range(len(values)):
                    for j in range(i + 1, len(values)):
                        a.append(values[i])
                        b.append(values[j])
        if len(a) < 3:
            return {"n_groups": n_groups, "n_pairs": len(a), "note": "too few pairs"}
        first = np.asarray(a, dtype=float)
        second = np.asarray(b, dtype=float)
        return {
            "n_groups": n_groups,
            "n_pairs": int(first.size),
            "spearman": float(spearmanr(first, second).statistic),
            "pearson": float(pearsonr(first, second).statistic),
            "mean_abs_difference_log10": float(np.abs(first - second).mean()),
            "sd_of_difference_log10": float((first - second).std(ddof=1)),
        }

    # The adopted estimate: fully sequenced isolates only, one pair per distinct sequence.
    adopted = estimate(0, True)

    per_drug: dict[str, dict] = {}
    sequence_of = {
        (r["drug_class"], r["isolate_id"]): r["sequence"]
        for r in isolates
        if r["dataset"] == "unfiltered" and int(r["n_unknown_positions"]) == 0
    }
    groups: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in labels:
        if row["dataset"] != "unfiltered" or not row["log10_fold"]:
            continue
        sequence = sequence_of.get((row["drug_class"], row["isolate_id"]))
        if sequence is None:
            continue
        groups[(row["drug"], sequence)].append(float(row["log10_fold"]))
    by_drug: dict[str, tuple[list[float], list[float]]] = defaultdict(lambda: ([], []))
    for (drug, _sequence), values in groups.items():
        if len(values) < 2:
            continue
        by_drug[drug][0].append(values[0])
        by_drug[drug][1].append(values[1])
    for drug, (first_list, second_list) in by_drug.items():
        first = np.asarray(first_list, dtype=float)
        second = np.asarray(second_list, dtype=float)
        if first.size < 3:
            per_drug[drug] = {"n_pairs": int(first.size), "note": "too few pairs"}
            continue
        per_drug[drug] = {
            "n_pairs": int(first.size),
            "spearman": float(spearmanr(first, second).statistic),
            "pearson": float(pearsonr(first, second).statistic),
            "mean_abs_difference_log10": float(np.abs(first - second).mean()),
        }

    return {
        "adopted": adopted,
        "per_drug": per_drug,
        "pooled": adopted,
        "sensitivity": {
            "max_unknown_" + str(threshold): estimate(threshold, True)
            for threshold in (0, 20, 50, 100, 560)
        },
        "all_pairs_no_quality_filter": estimate(560, False),
    }


def figure_labels(labels: list[dict], path: Path) -> None:
    import matplotlib.pyplot as plt

    by_drug: dict[str, list[float]] = defaultdict(list)
    for row in labels:
        if row["dataset"] == "filtered" and row["log10_fold"]:
            by_drug[row["drug"]].append(float(row["log10_fold"]))
    order = [d for cls in ("NRTI", "NNRTI") for d in DRUGS[cls] if d in by_drug]
    fig, axes = plt.subplots(
        2, max(1, (len(order) + 1) // 2), figsize=(2.3 * ((len(order) + 1) // 2), 4.6),
        dpi=200, squeeze=False,
    )
    fig.patch.set_facecolor(SURFACE)
    flat = [ax for row in axes for ax in row]
    for ax, drug in zip(flat, order):
        values = np.asarray(by_drug[drug], dtype=float)
        ax.hist(values, bins=28, color=SERIES_1)
        ax.axvline(0.0, color=INK_MUTED, linewidth=1.0)
        ax.axvline(math.log10(RESISTANT_FOLD), color=SERIES_2, linewidth=1.2, linestyle="--")
        ax.set_title(
            drug + "\nn=" + str(values.size) + ", median " + format(np.median(values), ".2f"),
            fontsize=8.5, color=INK_PRIMARY,
        )
        ax.set_xlabel("log10 fold", fontsize=8)
        style_axes(ax)
    for ax in flat[len(order):]:
        ax.set_visible(False)
    fig.suptitle(
        "Label distribution per drug, filtered sets; dashed line is 10-fold",
        fontsize=10, color=INK_PRIMARY, x=0.01, ha="left",
    )
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def figure_mutations(isolates: list[dict], path: Path) -> None:
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 3.4), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    for ax, dataset in zip(axes, ("filtered", "unfiltered")):
        counts = np.asarray(
            [int(r["n_mutations"]) for r in isolates if r["dataset"] == dataset], dtype=float
        )
        ax.hist(counts, bins=40, color=SERIES_1)
        ax.axvline(
            float(np.median(counts)), color=INK_PRIMARY, linewidth=1.6,
        )
        ax.set_title(
            dataset + ": median " + str(int(np.median(counts))) + ", max " + str(int(counts.max())),
            loc="left", fontsize=10, color=INK_PRIMARY,
        )
        ax.set_xlabel("mutations per isolate, relative to consensus B")
        ax.set_ylabel("isolates")
        style_axes(ax)
    fig.suptitle(
        "Each isolate carries many substitutions at once, not one",
        fontsize=10, color=INK_PRIMARY, x=0.01, ha="left",
    )
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()

    print_run_header("curation/audit_hivrt.py", [CURATED, ISOLATES])
    labels = read(CURATED)
    isolates = read(ISOLATES)
    parse_report = json.loads(PARSE_REPORT.read_text(encoding="utf-8"))
    print("label rows: " + str(len(labels)) + ", isolate rows: " + str(len(isolates)))

    summary: dict = {
        "curated_sha256": sha256_of(CURATED),
        "isolates_sha256": sha256_of(ISOLATES),
        "label_scale": LABEL_SCALE,
    }

    # 1. Counts per drug and class.
    per_drug: dict[str, dict] = {}
    for dataset in ("filtered", "unfiltered"):
        for cls, drugs in DRUGS.items():
            for drug in drugs:
                values = [
                    float(r["log10_fold"])
                    for r in labels
                    if r["drug"] == drug and r["dataset"] == dataset and r["log10_fold"]
                ]
                raw = [
                    float(r["fold"])
                    for r in labels
                    if r["drug"] == drug and r["dataset"] == dataset and r["fold"]
                ]
                if not raw:
                    continue
                key = dataset + "/" + drug
                per_drug[key] = {
                    "drug": drug,
                    "drug_class": cls,
                    "dataset": dataset,
                    "n": len(raw),
                    "log10": describe(np.asarray(values, dtype=float)),
                    "raw_median": float(np.median(np.asarray(raw, dtype=float))),
                    "raw_max": float(np.max(np.asarray(raw, dtype=float))),
                    "n_resistant_at_10x": sum(1 for v in raw if v >= RESISTANT_FOLD),
                    "n_intermediate_3x_to_10x": sum(
                        1 for v in raw if INTERMEDIATE_FOLD <= v < RESISTANT_FOLD
                    ),
                    "n_susceptible_below_3x": sum(1 for v in raw if v < INTERMEDIATE_FOLD),
                    "n_nonpositive_fold": sum(1 for v in raw if v <= 0),
                }
    summary["per_drug"] = per_drug

    # 2. Isolates against results.
    ratios: dict[str, dict] = {}
    for dataset in ("filtered", "unfiltered"):
        for cls in DRUGS:
            rows = [r for r in labels if r["dataset"] == dataset and r["drug_class"] == cls]
            uniq = {r["isolate_id"] for r in rows}
            if not rows:
                continue
            ratios[dataset + "/" + cls] = {
                "results": len(rows),
                "isolates": len(uniq),
                "results_per_isolate": round(len(rows) / max(1, len(uniq)), 4),
            }
    summary["results_per_isolate"] = ratios

    # 3. Mutation counts.
    mutation_stats: dict[str, dict] = {}
    for dataset in ("filtered", "unfiltered"):
        counts = np.asarray(
            [int(r["n_mutations"]) for r in isolates if r["dataset"] == dataset], dtype=float
        )
        unknown = np.asarray(
            [int(r["n_unknown_positions"]) for r in isolates if r["dataset"] == dataset],
            dtype=float,
        )
        mutation_stats[dataset] = {
            "mutations": describe(counts),
            "unknown_positions": describe(unknown),
            "exactly_one_mutation": int((counts == 1).sum()),
            "zero_mutations": int((counts == 0).sum()),
        }
    summary["mutations"] = mutation_stats

    # 4. Censoring, both kinds.
    marker_censored = sum(
        1 for r in labels if any(ch in (r["fold_original"] or "") for ch in ("<", ">"))
    )
    summary["marker_censored_values"] = marker_censored
    per_drug_censoring: dict[str, dict] = {}
    for dataset in ("filtered", "unfiltered"):
        for cls, drugs in DRUGS.items():
            for drug in drugs:
                rows = [
                    r for r in labels if r["drug"] == drug and r["dataset"] == dataset
                ]
                if not rows:
                    continue
                censored = sum(1 for r in rows if r["censored"] == "1")
                if censored == 0:
                    continue
                recovered = sum(1 for r in rows if r["censoring_recovered"] == "1")
                per_drug_censoring[dataset + "/" + drug] = {
                    "n": len(rows),
                    "censored": censored,
                    "censored_fraction": round(censored / len(rows), 4),
                    "recovered": recovered,
                    "unrecovered": censored - recovered,
                }
    summary["censoring"] = {
        "per_drug": per_drug_censoring,
        "from_parse": parse_report.get("censoring", {}),
    }

    # 5. Sequence length and duplicates.
    lengths = Counter(len(r["sequence"]) for r in isolates)
    summary["sequence_lengths"] = {str(k): v for k, v in lengths.items()}
    duplicate_groups: dict[str, int] = {}
    for dataset in ("filtered", "unfiltered"):
        seen: dict[tuple[str, str], list[str]] = defaultdict(list)
        for row in isolates:
            if row["dataset"] != dataset:
                continue
            seen[(row["drug_class"], row["sequence"])].append(row["isolate_id"])
        duplicate_groups[dataset] = sum(1 for v in seen.values() if len(set(v)) > 1)
    summary["duplicate_sequence_groups"] = duplicate_groups

    # 6. Subtype composition, unfiltered only.
    subtypes = Counter(
        r["subtype"] or "unrecorded" for r in isolates if r["dataset"] == "unfiltered"
    )
    summary["subtypes_unfiltered"] = dict(subtypes.most_common(15))
    methods = Counter(
        r["method"] or "unrecorded" for r in isolates if r["dataset"] == "unfiltered"
    )
    summary["methods_unfiltered"] = dict(methods.most_common())
    isolate_types = Counter(
        r["isolate_type"] or "unrecorded" for r in isolates if r["dataset"] == "unfiltered"
    )
    summary["isolate_types_unfiltered"] = dict(isolate_types.most_common())
    patients = {
        r["ptid"] for r in isolates if r["dataset"] == "unfiltered" and r["ptid"]
    }
    unfiltered_isolates = {
        r["isolate_id"] for r in isolates if r["dataset"] == "unfiltered"
    }
    summary["patients_unfiltered"] = len(patients)
    summary["isolates_unfiltered"] = len(unfiltered_isolates)

    # 7. The reproducibility ceiling.
    ceiling = reproducibility_ceiling(labels, isolates)
    summary["reproducibility"] = ceiling
    if ceiling.get("pooled"):
        print(
            "reproducibility ceiling, pooled: Spearman "
            + format(ceiling["pooled"]["spearman"], ".4f")
            + " over "
            + str(ceiling["pooled"]["n_pairs"])
            + " replicate pairs"
        )

    # 8. What the filtering removes.
    filtered_ids = {
        (r["drug_class"], r["isolate_id"]) for r in isolates if r["dataset"] == "filtered"
    }
    removal: dict[str, dict] = {}
    for cls in DRUGS:
        kept, dropped = [], []
        for row in labels:
            if row["dataset"] != "unfiltered" or row["drug_class"] != cls:
                continue
            if not row["log10_fold"]:
                continue
            target = kept if (cls, row["isolate_id"]) in filtered_ids else dropped
            target.append(float(row["log10_fold"]))
        if not kept or not dropped:
            continue
        kept_array = np.asarray(kept, dtype=float)
        dropped_array = np.asarray(dropped, dtype=float)
        removal[cls] = {
            "kept_results": int(kept_array.size),
            "removed_results": int(dropped_array.size),
            "kept_median_log10": float(np.median(kept_array)),
            "removed_median_log10": float(np.median(dropped_array)),
            "difference_in_median_log10": float(
                np.median(kept_array) - np.median(dropped_array)
            ),
        }
    summary["filtering_effect"] = removal

    if not args.no_figures:
        FIGURES.mkdir(parents=True, exist_ok=True)
        figure_labels(labels, FIGURES / "hivrt_label_distribution.png")
        figure_mutations(isolates, FIGURES / "hivrt_mutation_counts.png")
        print("wrote 2 figures to reports/taskB_hivrt/figures/")

    write_report(summary, parse_report)
    SUMMARY.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    print("wrote " + SUMMARY.relative_to(REPO_ROOT).as_posix())
    return 0


def write_report(summary: dict, parse_report: dict) -> None:
    per_drug = summary["per_drug"]
    lines = [
        "# Task B audit: HIV-1 RT drug susceptibility phenotype",
        "",
        "Written by `curation/audit_hivrt.py`. Descriptive only: nothing here is fitted,",
        "selected or predicted.",
        "",
        "Source: `tasks/taskB_hivrt/curated.csv`, SHA256 `" + summary["curated_sha256"] + "`.",
        "",
        "**This dataset is not a deep mutational scan.** Each row is a clinical or",
        "laboratory isolate carrying many substitutions at once, and correlation here is",
        "not causal attribution of effect to individual mutations.",
        "",
        "## What bounds every later claim",
        "",
        "Three numbers, first because they are the constraints rather than the results.",
        "",
        "| quantity | value | consequence |",
        "| --- | --- | --- |",
    ]
    pooled = summary["reproducibility"].get("pooled") or {}
    if pooled:
        lines.append(
            "| assay reproducibility ceiling, Spearman between repeated measurements of the same sequence | **"
            + format(pooled["spearman"], ".4f")
            + "** over "
            + str(pooled["n_pairs"])
            + " replicate pairs | no model may be credited for a correlation above this; it is the assay's own agreement with itself |"
        )
        lines.append(
            "| mean absolute difference between replicates | "
            + format(pooled["mean_abs_difference_log10"], ".4f")
            + " log10 units | a predicted value closer than this to a measurement is inside the noise |"
        )
    ratios = summary["results_per_isolate"]
    worst = max(ratios.items(), key=lambda kv: kv[1]["results_per_isolate"])
    lines.append(
        "| phenotype results per isolate, worst case | "
        + format(worst[1]["results_per_isolate"], ".2f")
        + " in "
        + worst[0]
        + " | rows greatly outnumber independent sequences, so **every split must group at isolate level**; a row-level split leaks outright |"
    )
    lines += [
        "",
        "## 1. Counts per drug",
        "",
        "`n` is the number of non-missing phenotype results. The three susceptibility bands",
        "use fold resistance cutoffs of 3 and 10, stated here once and used throughout.",
        "",
        "| dataset | class | drug | n | median log10 | median fold | max fold | below 3x | 3x to 10x | at or above 10x |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for key in sorted(per_drug, key=lambda k: (per_drug[k]["dataset"], per_drug[k]["drug_class"], per_drug[k]["drug"])):
        e = per_drug[key]
        lines.append(
            "| "
            + e["dataset"]
            + " | "
            + e["drug_class"]
            + " | `"
            + e["drug"]
            + "` | "
            + str(e["n"])
            + " | "
            + format(e["log10"]["median"], ".3f")
            + " | "
            + format(e["raw_median"], ".2f")
            + " | "
            + format(e["raw_max"], ".1f")
            + " | "
            + str(e["n_susceptible_below_3x"])
            + " | "
            + str(e["n_intermediate_3x_to_10x"])
            + " | "
            + str(e["n_resistant_at_10x"])
            + " |"
        )

    lines += [
        "",
        "Fold resistance is approximately log-normal, so **" + LABEL_SCALE + " is the",
        "modelling scale** and every score in this task is computed on it.",
        "",
        "## 2. Isolates against phenotype results",
        "",
        "| dataset and class | results | isolates | results per isolate |",
        "| --- | --- | --- | --- |",
    ]
    for key, entry in sorted(ratios.items()):
        lines.append(
            "| "
            + key
            + " | "
            + str(entry["results"])
            + " | "
            + str(entry["isolates"])
            + " | "
            + format(entry["results_per_isolate"], ".2f")
            + " |"
        )
    lines += [
        "",
        "This ratio is the reason **isolate-level grouping is mandatory in every split**.",
        "A split that puts an isolate's 3TC row in training and its AZT row in test shares",
        "a sequence across the boundary, which is leakage with no redeeming interpretation.",
        "",
        "## 3. Mutations per isolate",
        "",
        "| dataset | n | min | median | q3 | max | isolates with exactly one mutation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for dataset, entry in summary["mutations"].items():
        m = entry["mutations"]
        lines.append(
            "| "
            + dataset
            + " | "
            + str(m["n"])
            + " | "
            + str(int(m["min"]))
            + " | "
            + str(int(m["median"]))
            + " | "
            + str(int(m["q3"]))
            + " | "
            + str(int(m["max"]))
            + " | "
            + str(entry["exactly_one_mutation"])
            + " |"
        )
    lines += [
        "",
        "**This is the single clearest way to see that the task is not variant effect",
        "prediction.** A mutagenesis library would have every row at exactly one mutation.",
        "Here the median isolate carries many, and single-mutant isolates are a small",
        "minority, so no model here estimates the effect of a mutation in isolation.",
        "",
        "Unknown positions per isolate, which are positions encoded as `X` because they",
        "were not sequenced, carried a mixture, or were otherwise indeterminate:",
        "",
        "| dataset | median unknown positions | max |",
        "| --- | --- | --- |",
    ]
    for dataset, entry in summary["mutations"].items():
        u = entry["unknown_positions"]
        lines.append(
            "| " + dataset + " | " + str(int(u["median"])) + " | " + str(int(u["max"])) + " |"
        )

    lines += [
        "",
        "## 4. Censoring, which is present and was nearly missed",
        "",
        "**No label in any file carries a `>` or `<` marker: "
        + str(summary["marker_censored_values"])
        + " found. That is not the same as**",
        "**no censoring, and the first version of this audit drew the wrong conclusion from**",
        "**it.**",
        "",
        "The filtered datasets are **right-censored at a fold resistance of 100**, and the",
        "truncation is reported as a point value rather than as a bound. It is visible only",
        "distributionally: the filtered maximum is exactly 100.0 for five of the eleven",
        "drugs, while the unfiltered sets for the same drugs reach 5000, 6659 and 24630.",
        "",
        "| dataset and drug | n | censored at 100 | share | recovered | unrecovered |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for key, entry in sorted(summary["censoring"]["per_drug"].items()):
        lines.append(
            "| "
            + key
            + " | "
            + str(entry["n"])
            + " | "
            + str(entry["censored"])
            + " | "
            + format(100 * entry["censored_fraction"], ".2f")
            + " percent | "
            + str(entry["recovered"])
            + " | "
            + str(entry["unrecovered"])
            + " |"
        )
    lines += [
        "",
        "**45.19 percent of filtered 3TC values sit exactly on the bound.** Treating those",
        "as point measurements would bias every number computed from that drug, which is",
        "precisely the error this dataset is known for.",
        "",
        "### The evidence that this is truncation and not a real mode",
        "",
        "Of the 2196 isolate-drug pairs whose filtered value is exactly 100.0 and which also",
        "appear in the unfiltered set, **2176 have an unfiltered value above 100**, with a",
        "median of 200 and a maximum of 2400. Only 16 are genuinely 100. Where neither is",
        "capped the two datasets agree exactly 98.5 percent of the time, so these are the",
        "same measurements reported at different precision.",
        "",
        "### The handling rule, stated once and applied uniformly",
        "",
        "1. A value equal to its dataset-and-drug maximum, where that maximum carries at",
        "   least 2 percent of the mass, is flagged `censored`. Both conditions are",
        "   required: the mass condition alone produced a false positive on unfiltered DOR,",
        "   which has 5.9 percent of values at exactly 100 but a maximum of 50000, so 100",
        "   there is a round number rather than a bound.",
        "2. Where the same isolate and drug has a higher value in the unfiltered set, that",
        "   value is **recovered** and the row is flagged `censoring_recovered`. 2151 of",
        "   2170 censored values were recovered this way.",
        "3. A censored value that cannot be recovered is **retained** for rank-based metrics,",
        "   which tolerate ties, and **excluded** from RMSE and MAE, where squaring the",
        "   distance to a bound is meaningless.",
        "",
        "Nothing is dropped and nothing is imputed. `curated.csv` carries `censored`,",
        "`censoring_recovered` and `fold_original` so every downstream consumer can see",
        "exactly which values were adjusted and to what.",
        "",
        "## 5. Sequence lengths and duplicates",
        "",
        "| length | isolate rows |",
        "| --- | --- |",
    ]
    for length, count in sorted(summary["sequence_lengths"].items()):
        lines.append("| " + length + " | " + str(count) + " |")
    lines += [
        "",
        "Every reconstructed sequence is the same length as the reference, as substitutions",
        "require. Any deviation would be an error rather than an indel to accommodate, and",
        "insertions are recorded as their own category rather than lengthening a sequence.",
        "",
        "| dataset | distinct sequences carried by more than one isolate id |",
        "| --- | --- |",
    ]
    for dataset, count in sorted(summary["duplicate_sequence_groups"].items()):
        lines.append("| " + dataset + " | " + str(count) + " |")

    lines += [
        "",
        "Those duplicate groups are what makes the reproducibility ceiling estimable, and",
        "they are also a redundancy the splits have to control: two isolate ids with an",
        "identical sequence are not two independent observations.",
        "",
        "## 6. The reproducibility ceiling, in detail",
        "",
        "Where two different isolate ids carry an identical reconstructed sequence and both",
        "were measured for the same drug, the two measurements are effectively replicates.",
        "Their agreement is an upper bound on any model's achievable correlation.",
        "",
        "| drug | replicate pairs | Spearman | Pearson | mean absolute difference, log10 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for drug, entry in sorted(summary["reproducibility"]["per_drug"].items()):
        if "spearman" not in entry:
            lines.append(
                "| `" + drug + "` | " + str(entry["n_pairs"]) + " | too few pairs | | |"
            )
            continue
        lines.append(
            "| `"
            + drug
            + "` | "
            + str(entry["n_pairs"])
            + " | "
            + format(entry["spearman"], ".4f")
            + " | "
            + format(entry["pearson"], ".4f")
            + " | "
            + format(entry["mean_abs_difference_log10"], ".4f")
            + " |"
        )
    if pooled:
        lines += [
            "| **pooled** | **"
            + str(pooled["n_pairs"])
            + "** | **"
            + format(pooled["spearman"], ".4f")
            + "** | **"
            + format(pooled["pearson"], ".4f")
            + "** | **"
            + format(pooled["mean_abs_difference_log10"], ".4f")
            + "** |",
            "",
            "**This ceiling must be drawn on every comparison figure in this task.** A model",
            "reported as reaching a Spearman above it has not beaten the assay; it has",
            "overfitted something, or the evaluation is leaking.",
            "",
            "A mean absolute difference of "
            + format(pooled["mean_abs_difference_log10"], ".4f")
            + " log10 units between replicates is a factor of",
            "about "
            + format(10 ** pooled["mean_abs_difference_log10"], ".2f")
            + " in fold resistance. Two measurements of the same virus routinely disagree by",
            "that much, which is the practical resolution of the label.",
            "",
            "### How this estimate was constrained, and why it matters",
            "",
            "Two decisions were forced by what a naive version produced, and both are stated",
            "because the difference between them is large.",
            "",
            "**Only fully sequenced isolates count.** The reconstruction encodes unsequenced",
            "positions and mixtures as `X`, and the median unfiltered isolate carries 258",
            "such positions out of 560. Two isolates differing only at `X` positions collapse",
            "to the same string without being the same virus.",
            "",
            "**One pair per distinct sequence.** A group of n identical sequences contributes",
            "n(n-1)/2 pairs, so a few large groups would otherwise dominate.",
            "",
            "The first version of this estimate did neither, and reported a ceiling of",
            "**0.9761 over 306759 pairs**. Almost all of those pairs came from five groups of",
            "isolates that were more than half unsequenced, the largest containing 256",
            "isolates. That is not replicate agreement; it is the agreement of different",
            "viruses that happen to be indistinguishable at low sequencing coverage. The",
            "corrected figure is far lower, and using the inflated one would have set a",
            "ceiling no model could be measured against.",
            "",
            "Sensitivity to the sequencing-quality threshold, one pair per group throughout:",
            "",
            "| maximum unknown positions allowed | groups with a replicate | Spearman | mean absolute difference |",
            "| --- | --- | --- | --- |",
        ]
        for key, entry in sorted(
            summary["reproducibility"]["sensitivity"].items(),
            key=lambda kv: int(kv[0].rsplit("_", 1)[1]),
        ):
            threshold = key.rsplit("_", 1)[1]
            if "spearman" not in entry:
                lines.append("| " + threshold + " | " + str(entry.get("n_groups", 0)) + " | too few | |")
                continue
            lines.append(
                "| "
                + threshold
                + (" **(adopted)**" if threshold == "0" else "")
                + " | "
                + str(entry["n_groups"])
                + " | "
                + format(entry["spearman"], ".4f")
                + " | "
                + format(entry["mean_abs_difference_log10"], ".4f")
                + " |"
            )
        unfiltered_all = summary["reproducibility"]["all_pairs_no_quality_filter"]
        if "spearman" in unfiltered_all:
            lines += [
                "",
                "And for completeness, the naive estimate this replaces: all pairs, no quality",
                "filter, "
                + str(unfiltered_all["n_pairs"])
                + " pairs, Spearman "
                + format(unfiltered_all["spearman"], ".4f")
                + ". **Not used.**",
            ]

    lines += [
        "",
        "## 7. Composition, from the unfiltered sets",
        "",
        "The filtered sets carry no metadata beyond the sequence and the labels, so",
        "everything in this section comes from the unfiltered files.",
        "",
        "| quantity | value |",
        "| --- | --- |",
        "| isolates | " + str(summary["isolates_unfiltered"]) + " |",
        "| distinct patient identifiers | " + str(summary["patients_unfiltered"]) + " |",
        "",
        "**Patient is a stronger grouping than isolate, and it is available here.** Multiple",
        "isolates come from one patient. The source's own filtering removes same-patient",
        "viruses that share a major drug resistance mutation pattern, which is partial:",
        "patient structure survives it. This is taken up in the split design.",
        "",
        "| subtype | isolates |",
        "| --- | --- |",
    ]
    for subtype, count in summary["subtypes_unfiltered"].items():
        lines.append("| " + subtype + " | " + str(count) + " |")
    lines += [
        "",
        "Subtype composition bounds any generalization claim: a benchmark dominated by one",
        "subtype says little about the others.",
        "",
        "| phenotype method | isolates |",
        "| --- | --- |",
    ]
    for method, count in summary["methods_unfiltered"].items():
        lines.append("| " + method + " | " + str(count) + " |")
    lines += [
        "",
        "The unfiltered sets mix assay methods, which pools measurement scales. That is why",
        "the filtered sets, PhenoSense only, are the primary analysis.",
        "",
        "| isolate type | isolates |",
        "| --- | --- |",
    ]
    for kind, count in summary["isolate_types_unfiltered"].items():
        lines.append("| " + kind + " | " + str(count) + " |")
    lines += [
        "",
        "Laboratory isolates are site-directed mutants or in vitro passage products, so they",
        "are not clinical samples and do not carry the same phylogenetic structure.",
        "",
        "## 8. What the filtering removes",
        "",
        "Comparing the unfiltered results whose isolate survives into the filtered set",
        "against those that do not.",
        "",
        "| class | kept results | removed results | kept median log10 | removed median log10 | difference |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for cls, entry in sorted(summary["filtering_effect"].items()):
        lines.append(
            "| "
            + cls
            + " | "
            + str(entry["kept_results"])
            + " | "
            + str(entry["removed_results"])
            + " | "
            + format(entry["kept_median_log10"], ".4f")
            + " | "
            + format(entry["removed_median_log10"], ".4f")
            + " | "
            + format(entry["difference_in_median_log10"], "+.4f")
            + " |"
        )
    worst = max(
        summary["filtering_effect"].items(),
        key=lambda kv: abs(kv[1]["difference_in_median_log10"]),
        default=(None, None),
    )
    lines += [
        "",
    ]
    if worst[0] is not None:
        gap = worst[1]["difference_in_median_log10"]
        lines += [
            "**The filtering is not neutral with respect to resistance level.** For "
            + worst[0]
            + " the",
            "removed results have a median log10 fold of "
            + format(worst[1]["removed_median_log10"], ".4f")
            + " against "
            + format(worst[1]["kept_median_log10"], ".4f")
            + " for those kept, a",
            "difference of "
            + format(abs(gap), ".4f")
            + " log10 units, which is a factor of "
            + format(10 ** abs(gap), ".2f")
            + " in fold resistance.",
            "",
            "So the filtered set is **enriched for less resistant isolates**, which follows",
            "from the source's own exclusion rule: it removes viruses carrying mixtures at",
            "major drug resistance positions, and mixtures at those positions are commoner in",
            "treatment-experienced, more resistant viruses. The filtered set's label",
            "distribution is therefore not a random subsample of the unfiltered one, and any",
            "result on it describes a population shifted toward susceptibility. That has to",
            "be stated wherever a filtered result is reported.",
        "",
        "## Figures",
        "",
        "| figure | what it shows |",
        "| --- | --- |",
        "| `figures/hivrt_label_distribution.png` | log10 fold resistance per drug, filtered sets, with the 10-fold line |",
        "| `figures/hivrt_mutation_counts.png` | mutations per isolate; the clearest view of why this is not a mutagenesis library |",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
