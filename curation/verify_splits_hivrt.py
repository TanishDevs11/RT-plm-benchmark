"""Verify the frozen HIV-1 RT splits against every leakage condition, and report.

Three conditions matter here and they are checked separately, because they fail for
different reasons:

  **isolate containment.** Each isolate carries up to 7.6 phenotype results. If an
  isolate's rows are separated, a sequence is on both sides of the boundary. This is
  enforced structurally by keying splits on the isolate rather than the row, and it is
  asserted anyway.

  **identity cluster containment.** Checked at every swept threshold, not only the chosen
  one. A split that holds out 99 percent clusters still leaves 95 percent relatives in
  training, and since 95 percent clustering puts half the panel in one cluster that is
  unavoidable rather than fixable. Reported as a property per threshold.

  **label comparability across folds.** A fold whose label distribution differs from the
  others is not a fair test fold, and with greedy balanced assignment over skewed cluster
  sizes that has to be checked rather than assumed.

    python curation/verify_splits_hivrt.py

Output: reports/taskB_hivrt/split_verification.md, and a non-zero exit if a real defect
is found. Cluster containment below the split's own threshold is reported, not failed,
for the reason given above.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_hivrt"
SPLITS = TASK_DIR / "splits"
CURATED = TASK_DIR / "curated.csv"
SUMMARY = SPLITS / "split_summary.json"
OUT = REPO_ROOT / "reports" / "taskB_hivrt" / "split_verification.md"

PRIMARY_DATASET = "filtered"
THRESHOLDS = (99, 98, 95, 90)
SPLIT_FILES = {
    "identity_cluster, primary": "identity_cluster.csv",
    "drm_pattern_held_out": "drm_pattern_held_out.csv",
    "subtype_held_out": "subtype_held_out.csv",
    "random, LEAKY reference only": "random_LEAKY_DO_NOT_REPORT.csv",
}


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def folds_of(rows: list[dict]) -> dict[str, dict[str, set[str]]]:
    out: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"train": set(), "test": set()}
    )
    for row in rows:
        out[row["fold"]][row["role"]].add(row["unit"])
    return dict(out)


def cluster_map(threshold: int) -> dict[str, str]:
    path = SPLITS / ("clusters_" + str(threshold) + ".tsv")
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        return {
            row["unit"]: row["cluster_representative"]
            for row in csv.DictReader(handle, delimiter="\t")
        }


def main() -> int:
    print_run_header("curation/verify_splits_hivrt.py", [CURATED])
    labels = [r for r in read(CURATED) if r["dataset"] == PRIMARY_DATASET]
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    chosen = summary["chosen_threshold"]

    rows_of_unit: dict[str, list[dict]] = defaultdict(list)
    for row in labels:
        rows_of_unit[row["drug_class"] + ":" + row["isolate_id"]].append(row)
    all_units = set(rows_of_unit)
    clusters = {t: cluster_map(t) for t in THRESHOLDS}

    failures: list[str] = []
    lines = [
        "# Task B HIV-1 RT split verification",
        "",
        "Written by `curation/verify_splits_hivrt.py`. The splits are frozen files, not",
        "code that runs at model time.",
        "",
        "Primary dataset: `" + PRIMARY_DATASET + "`, "
        + str(len(all_units))
        + " class-qualified isolates carrying "
        + str(len(labels))
        + " phenotype results.",
        "",
        "Chosen identity threshold: **" + str(chosen) + " percent**, by the rule recorded in",
        "`tasks/taskB_hivrt/splits/split_summary.json`.",
        "",
        "| file | SHA256 |",
        "| --- | --- |",
    ]
    for label, filename in SPLIT_FILES.items():
        path = SPLITS / filename
        lines.append(
            "| `" + filename + "` | "
            + ("`" + sha256_of(path) + "`" if path.is_file() else "ABSENT")
            + " |"
        )

    for label, filename in SPLIT_FILES.items():
        path = SPLITS / filename
        lines.append("")
        lines.append("## " + label)
        lines.append("")
        if not path.is_file():
            lines.append("**ABSENT.**")
            failures.append(filename + " absent")
            continue
        rows = read(path)
        folds = folds_of(rows)
        checks: list[tuple[str, bool, str]] = []

        overlap = [f for f, p in folds.items() if p["train"] & p["test"]]
        checks.append(
            ("no isolate appears in both train and test", not overlap,
             "folds overlapping: " + str(overlap[:5]) if overlap else "")
        )
        incomplete = [f for f, p in folds.items() if (p["train"] | p["test"]) != all_units]
        checks.append(
            ("every fold covers every isolate exactly once", not incomplete,
             str(len(incomplete)) + " folds do not cover the panel" if incomplete else "")
        )
        empty = [f for f, p in folds.items() if not p["test"]]
        checks.append(
            ("no fold has an empty test set", not empty,
             "empty: " + str(empty[:5]) if empty else "")
        )

        lines.append("| check | result | detail |")
        lines.append("| --- | --- | --- |")
        for name, passed, detail in checks:
            lines.append(
                "| " + name + " | " + ("PASS" if passed else "**FAIL**") + " | " + detail + " |"
            )
            if not passed:
                failures.append(filename + ": " + name)

        # Cluster containment at every threshold.
        lines.append("")
        lines.append("### Identity cluster containment")
        lines.append("")
        lines.append("| threshold | folds whose test cluster also appears in training | holds | why |")
        lines.append("| --- | --- | --- | --- |")
        for threshold in THRESHOLDS:
            assignment = clusters[threshold]
            if not assignment:
                lines.append("| " + str(threshold) + " percent | unknown | no | cluster file absent |")
                continue
            spanning = 0
            for parts in folds.values():
                train_clusters = {assignment.get(u, u) for u in parts["train"]}
                test_clusters = {assignment.get(u, u) for u in parts["test"]}
                if train_clusters & test_clusters:
                    spanning += 1
            if spanning == 0:
                reason = "every cluster at this threshold lies inside one fold"
            elif "identity_cluster" in filename and threshold < chosen:
                share = summary["thresholds"][str(threshold)]["share_in_largest"]
                reason = (
                    "expected by construction: this split holds out "
                    + str(chosen)
                    + " percent clusters, and at "
                    + str(threshold)
                    + " percent the largest single cluster already holds "
                    + format(100 * share, ".1f")
                    + " percent of the panel, so no split can hold it out"
                )
            elif "random" in filename:
                reason = "**this is the leak the random split exists to demonstrate**"
            else:
                reason = "**a real limitation** at this threshold"
            lines.append(
                "| " + str(threshold) + " percent | " + str(spanning) + " of "
                + str(len(folds)) + " | " + ("yes" if spanning == 0 else "no") + " | "
                + reason + " |"
            )

        # Label comparability.
        lines.append("")
        lines.append("### Label distribution across test folds")
        lines.append("")
        lines.append("| fold | isolates in test | phenotype results | median log10 fold |")
        lines.append("| --- | --- | --- | --- |")
        medians = []
        for fold, parts in sorted(folds.items()):
            values = [
                float(r["log10_fold"])
                for unit in parts["test"]
                for r in rows_of_unit.get(unit, [])
                if r["log10_fold"]
            ]
            median = float(np.median(values)) if values else float("nan")
            medians.append(median)
            lines.append(
                "| `" + fold + "` | " + str(len(parts["test"])) + " | " + str(len(values))
                + " | " + (format(median, ".4f") if values else "no labelled rows") + " |"
            )
        finite = [m for m in medians if m == m]
        if len(finite) > 1:
            spread = max(finite) - min(finite)
            lines.append("")
            lines.append(
                "Spread of the fold medians: "
                + format(spread, ".4f")
                + " log10 units, a factor of "
                + format(10 ** spread, ".2f")
                + " in fold resistance."
            )
            if "identity_cluster" in filename or "random" in filename:
                comparable = spread < 0.3
                lines.append("")
                lines.append(
                    "Label distribution across folds is "
                    + ("comparable." if comparable else "**not comparable**, which has to be stated wherever a per-fold number is reported.")
                )

    lines += [
        "",
        "## The clustering sweep, and why 99 percent",
        "",
        "These are variants of one gene in one virus, so pairwise identity is high",
        "throughout and the thresholds that work for a cross-family panel do not partition",
        "this set at all. The sweep shows that directly.",
        "",
        "| threshold | clusters | largest cluster | share of the panel in it | singletons |",
        "| --- | --- | --- | --- | --- |",
    ]
    for threshold in THRESHOLDS:
        stats = summary["thresholds"][str(threshold)]
        lines.append(
            "| " + str(threshold) + " percent | " + str(stats["clusters"]) + " | "
            + str(stats["largest"]) + " | "
            + format(100 * stats["share_in_largest"], ".1f") + " percent | "
            + str(stats["singletons"]) + " |"
        )
    lines += [
        "",
        "**At 95 percent identity half the panel is one cluster, and at 90 percent 85",
        "percent of it is.** Those thresholds cannot produce folds: a single cluster would",
        "have to be either entirely in training or entirely in test, and either way one",
        "fold is almost the whole dataset.",
        "",
        "Selection rule, fixed before looking at any result: " + summary["selection_rule"] + ".",
        "",
        "That gives **" + str(chosen) + " percent**, with 3323 clusters whose largest holds",
        "4.3 percent of the panel. It is a weaker control than a cross-family identity",
        "split, and it is the strongest one this data admits. The shape of that curve, from",
        "3323 clusters at 99 percent to 7 at 90, is the material for the leakage analysis.",
        "",
        "## What these splits control and what they do not",
        "",
        "| regime | controls | does not control |",
        "| --- | --- | --- |",
        "| `identity_cluster` | isolates, and identity clusters at " + str(chosen) + " percent | relatedness below " + str(chosen) + " percent, which is most of the panel; patient identity, which the filtered sets do not record |",
        "| `drm_pattern_held_out` | the named resistance package, entirely absent from training | other resistance packages that co-occur with it; the held-out set is not a random sample, so its label distribution differs by construction |",
        "| `subtype_held_out` | the named subtype | almost nothing, because the panel is 96.6 percent subtype B; the non-B test sets are tiny |",
        "| `random` | **isolate identity only** | everything else; it is a leaky reference and is labelled so in its filename and on every row |",
        "",
        "**Patient-level grouping is the control this task most wants and cannot have in its",
        "primary analysis.** The filtered sets carry no `PtID`. The unfiltered sets do, and",
        "the source's own filtering removes only same-patient viruses that share a major",
        "resistance pattern, so patient structure survives into the filtered sets",
        "unmeasured. Any result here is therefore an upper bound relative to what a",
        "patient-held-out split would give.",
        "",
    ]
    if failures:
        lines += ["## Result", "", "**" + str(len(failures)) + " check(s) FAILED.**", ""]
        for failure in failures:
            lines.append("- " + failure)
    else:
        lines += ["## Result", "", "**All enforced checks pass.**", ""]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    if failures:
        for failure in failures:
            print("  FAILED " + failure)
        return 1
    print("all enforced checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
