"""Write the frozen split definition files for the HIV-1 RT phenotype task.

Four regimes, all of them grouped at isolate level, which is not optional here. Each
isolate carries up to 7.6 phenotype results, so a row-level split would place an
isolate's 3TC measurement in training and its AZT measurement in test, sharing a sequence
across the boundary. That is leakage with no redeeming interpretation.

The regimes:

  `random`             a leaky reference only, labelled as such inside the file
  `identity_cluster`   primary; whole identity clusters assigned to folds
  `drm_pattern`        isolates carrying a named resistance package held out
  `subtype`            isolates of a named subtype held out, where subtype is recorded

Identity clustering needs care here and the brief says so. These are variants of one gene
in one virus, so pairwise identity is high throughout and the thresholds that work for a
cross-family panel are useless. The threshold is therefore swept at 99, 98, 95 and 90
percent, the cluster size distribution is reported at each, and the one that produces a
usable number of clusters of usable size is selected and documented.

    python curation/splits_hivrt.py --mmseqs <path to mmseqs>

Outputs:
    tasks/taskB_hivrt/splits/clusters_<threshold>.tsv
    tasks/taskB_hivrt/splits/random_LEAKY_DO_NOT_REPORT.csv
    tasks/taskB_hivrt/splits/identity_cluster.csv
    tasks/taskB_hivrt/splits/drm_pattern_held_out.csv
    tasks/taskB_hivrt/splits/subtype_held_out.csv
    reports/taskB_hivrt/split_design.md
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import GLOBAL_SEED, print_run_header, sha256_of  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_hivrt"
ISOLATES = TASK_DIR / "curated_isolates.csv"
CURATED = TASK_DIR / "curated.csv"
SPLITS = TASK_DIR / "splits"
DESIGN = REPO_ROOT / "reports" / "taskB_hivrt" / "split_design.md"

# The primary analysis is the filtered, PhenoSense-only sets.
PRIMARY_DATASET = "filtered"

# Thresholds swept, as the brief specifies. Standard cross-family thresholds are useless
# on variants of one gene in one virus.
IDENTITY_THRESHOLDS = (99, 98, 95, 90)
COVERAGE = "0.8"
COVERAGE_MODE = "0"
SENSITIVITY = "7.5"

K_FOLDS = 5

# The TAM1 thymidine analogue mutation package. These travel together under
# treatment selection, so a model can learn the package without learning any causal
# contribution; holding it out asks whether the model generalises to a resistance
# mechanism it has not seen.
DRM_PATTERNS = {
    "TAM1": ("M41L", "L210W", "T215Y"),
    "TAM2": ("D67N", "K70R", "T215F", "K219Q"),
    "M184V": ("M184V",),
    "K65R": ("K65R",),
}


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_split(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    counts = Counter((r["fold"], r["role"]) for r in rows)
    print("  wrote " + path.relative_to(REPO_ROOT).as_posix())
    print("    sha256=" + sha256_of(path) + ", " + str(len(rows)) + " assignment rows")
    folds = sorted({f for f, _ in counts})
    print("    folds: " + str(len(folds)))


def run_mmseqs(binary: str, fasta: Path, threshold: int, workdir: Path) -> dict[str, str]:
    workdir.mkdir(parents=True, exist_ok=True)
    prefix = workdir / ("clu" + str(threshold))
    tmp = workdir / ("tmp" + str(threshold))
    tmp.mkdir(parents=True, exist_ok=True)
    command = [
        binary, "easy-cluster", str(fasta), str(prefix), str(tmp),
        "--min-seq-id", str(threshold / 100),
        "-c", COVERAGE, "--cov-mode", COVERAGE_MODE, "-s", SENSITIVITY,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    table = Path(str(prefix) + "_cluster.tsv")
    if result.returncode != 0 or not table.is_file():
        print(result.stdout[-1500:])
        print(result.stderr[-1500:])
        raise RuntimeError("mmseqs easy-cluster failed at threshold " + str(threshold))
    assignment: dict[str, str] = {}
    for line in table.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        representative, member = line.split("\t")[:2]
        assignment[member] = representative
    return assignment


def describe_clusters(assignment: dict[str, str]) -> dict:
    sizes = Counter(assignment.values())
    distribution = Counter(sizes.values())
    counts = np.asarray(list(sizes.values()), dtype=float)
    return {
        "sequences": len(assignment),
        "clusters": len(sizes),
        "largest": int(counts.max()) if counts.size else 0,
        "median_size": float(np.median(counts)) if counts.size else 0.0,
        "singletons": int(distribution.get(1, 0)),
        "share_in_largest": float(counts.max() / counts.sum()) if counts.size else 0.0,
        "size_distribution": {str(k): v for k, v in sorted(distribution.items())},
    }


def assign_groups_to_folds(group_sizes: dict[str, int], k: int, seed: int) -> dict[str, int]:
    """Greedy balanced assignment: largest group first into the lightest fold.

    Random assignment of groups to folds leaves very uneven folds when group sizes are
    skewed, which they are here. Greedy largest-first keeps the folds comparable in size,
    and the result is deterministic given the seed used to break ties.
    """
    generator = random.Random(seed)
    order = sorted(group_sizes.items(), key=lambda kv: (-kv[1], kv[0]))
    loads = [0] * k
    out: dict[str, int] = {}
    for group, size in order:
        lightest = min(range(k), key=lambda index: (loads[index], generator.random()))
        out[group] = lightest
        loads[lightest] += size
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mmseqs", default=os.environ.get("MMSEQS_BIN", "mmseqs"))
    args = parser.parse_args(argv)

    print_run_header("curation/splits_hivrt.py", [ISOLATES, CURATED])
    isolates = [r for r in read(ISOLATES) if r["dataset"] == PRIMARY_DATASET]
    labels = [r for r in read(CURATED) if r["dataset"] == PRIMARY_DATASET]
    print("primary dataset: " + PRIMARY_DATASET)
    print("isolate rows: " + str(len(isolates)) + ", label rows: " + str(len(labels)))

    # An isolate id can appear once per drug class, with a class-specific sequence, so the
    # unit is the class-qualified isolate. Keyed that way throughout.
    unit_of: dict[str, str] = {}
    sequence_of: dict[str, str] = {}
    for row in isolates:
        unit = row["drug_class"] + ":" + row["isolate_id"]
        unit_of[unit] = row["drug_class"]
        sequence_of[unit] = row["sequence"]
    units = sorted(sequence_of)
    print("class-qualified isolates: " + str(len(units)))

    rows_per_unit = Counter(r["drug_class"] + ":" + r["isolate_id"] for r in labels)
    print(
        "label rows per isolate: median "
        + str(int(np.median(list(rows_per_unit.values()))))
        + ", max "
        + str(max(rows_per_unit.values()))
    )

    binary = shutil.which(args.mmseqs) or args.mmseqs
    if not Path(binary).is_file() and shutil.which(binary) is None:
        print("")
        print("mmseqs not found at " + str(args.mmseqs) + "; pass --mmseqs or set MMSEQS_BIN")
        return 1
    version = subprocess.run([binary, "version"], capture_output=True, text=True)
    print("mmseqs version: " + version.stdout.strip())

    summary: dict = {
        "primary_dataset": PRIMARY_DATASET,
        "n_units": len(units),
        "thresholds": {},
        "mmseqs_version": version.stdout.strip(),
        "mmseqs_parameters": {
            "coverage": COVERAGE,
            "cov_mode": COVERAGE_MODE,
            "sensitivity": SENSITIVITY,
        },
    }

    clusters: dict[int, dict[str, str]] = {}
    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)
        fasta = workdir / "isolates.fasta"
        lines = []
        for unit in units:
            lines.append(">" + unit)
            sequence = sequence_of[unit]
            lines += [sequence[i : i + 60] for i in range(0, len(sequence), 60)]
        fasta.write_text("\n".join(lines) + "\n", encoding="utf-8")

        print("")
        print("=== identity clustering sweep ===")
        for threshold in IDENTITY_THRESHOLDS:
            assignment = run_mmseqs(binary, fasta, threshold, workdir / ("t" + str(threshold)))
            clusters[threshold] = assignment
            stats = describe_clusters(assignment)
            summary["thresholds"][str(threshold)] = stats
            print(
                "  "
                + str(threshold)
                + "%: "
                + str(stats["clusters"])
                + " clusters, largest "
                + str(stats["largest"])
                + " ("
                + format(100 * stats["share_in_largest"], ".1f")
                + " percent of all isolates), "
                + str(stats["singletons"])
                + " singletons"
            )
            out = SPLITS / ("clusters_" + str(threshold) + ".tsv")
            out.parent.mkdir(parents=True, exist_ok=True)
            with out.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle, delimiter="\t")
                writer.writerow(["unit", "drug_class", "isolate_id", "cluster_representative"])
                for unit in units:
                    cls, isolate = unit.split(":", 1)
                    writer.writerow([unit, cls, isolate, assignment.get(unit, unit)])

    # Threshold selection, by a stated rule rather than by eye.
    #
    # A usable threshold needs enough clusters to form K folds and no cluster so large
    # that it dominates a fold. The rule: the tightest threshold whose largest cluster
    # holds less than half of one fold's worth of isolates, which is 1/(2K) of the panel.
    budget = 1.0 / (2 * K_FOLDS)
    usable = [
        t for t in IDENTITY_THRESHOLDS
        if summary["thresholds"][str(t)]["share_in_largest"] < budget
        and summary["thresholds"][str(t)]["clusters"] >= K_FOLDS * 2
    ]
    chosen = max(usable) if usable else None
    summary["selection_rule"] = (
        "the tightest threshold whose largest cluster holds less than "
        + format(100 * budget, ".0f")
        + " percent of all isolates, which is half of one fold, and which yields at least "
        + str(K_FOLDS * 2)
        + " clusters"
    )
    summary["chosen_threshold"] = chosen
    print("")
    if chosen is None:
        print("NO USABLE THRESHOLD: every threshold leaves one cluster dominating a fold.")
        print("That is a reportable property of the data, not a failure of the sweep.")
        chosen = min(IDENTITY_THRESHOLDS)
        summary["chosen_threshold"] = chosen
        summary["selection_note"] = (
            "no threshold satisfied the rule; the loosest was taken so a split exists, and "
            "the dominance is reported as a limitation"
        )
        print("Falling back to " + str(chosen) + " percent and reporting the dominance.")
    else:
        print("chosen threshold: " + str(chosen) + " percent, by the stated rule")

    print("")
    print("=== split regimes ===")
    chosen_assignment = clusters[chosen]

    # 1. identity_cluster, primary.
    group_sizes: dict[str, int] = Counter()
    for unit in units:
        group_sizes[chosen_assignment.get(unit, unit)] += rows_per_unit.get(unit, 0)
    fold_of_group = assign_groups_to_folds(dict(group_sizes), K_FOLDS, GLOBAL_SEED)
    rows = []
    for fold in range(K_FOLDS):
        for unit in units:
            group = chosen_assignment.get(unit, unit)
            cls, isolate = unit.split(":", 1)
            rows.append(
                {
                    "isolate_id": isolate,
                    "drug_class": cls,
                    "unit": unit,
                    "fold": "cluster_fold_" + str(fold),
                    "role": "test" if fold_of_group[group] == fold else "train",
                    "group": group,
                }
            )
    write_split(
        SPLITS / "identity_cluster.csv", rows,
        ["isolate_id", "drug_class", "unit", "fold", "role", "group"],
    )

    # 2. random, the leaky reference.
    generator = random.Random(GLOBAL_SEED)
    shuffled = list(units)
    generator.shuffle(shuffled)
    fold_of_unit = {unit: index % K_FOLDS for index, unit in enumerate(shuffled)}
    rows = []
    for fold in range(K_FOLDS):
        for unit in units:
            cls, isolate = unit.split(":", 1)
            rows.append(
                {
                    "isolate_id": isolate,
                    "drug_class": cls,
                    "unit": unit,
                    "fold": "random_fold_" + str(fold),
                    "role": "test" if fold_of_unit[unit] == fold else "train",
                    "leaky": "yes",
                    "never_report": (
                        "this split separates identity clusters, so near-identical "
                        "sequences appear in both train and test"
                    ),
                }
            )
    write_split(
        SPLITS / "random_LEAKY_DO_NOT_REPORT.csv", rows,
        ["isolate_id", "drug_class", "unit", "fold", "role", "leaky", "never_report"],
    )

    # 3. drm_pattern_held_out.
    mutations_of = {
        r["drug_class"] + ":" + r["isolate_id"]: set((r["mutations"] or "").split(";"))
        for r in isolates
    }
    rows = []
    pattern_counts: dict[str, int] = {}
    for name, pattern in DRM_PATTERNS.items():
        held = [u for u in units if set(pattern).issubset(mutations_of.get(u, set()))]
        pattern_counts[name] = len(held)
        if not held:
            continue
        held_set = set(held)
        for unit in units:
            cls, isolate = unit.split(":", 1)
            rows.append(
                {
                    "isolate_id": isolate,
                    "drug_class": cls,
                    "unit": unit,
                    "fold": "held_out_" + name,
                    "role": "test" if unit in held_set else "train",
                    "group": name,
                }
            )
    summary["drm_pattern_counts"] = pattern_counts
    print("  DRM pattern isolate counts: " + str(pattern_counts))
    if rows:
        write_split(
            SPLITS / "drm_pattern_held_out.csv", rows,
            ["isolate_id", "drug_class", "unit", "fold", "role", "group"],
        )

    # 4. subtype_held_out, from the unfiltered metadata joined by isolate id.
    subtype_of: dict[str, str] = {}
    for row in read(ISOLATES):
        if row["dataset"] != "unfiltered" or not row["subtype"]:
            continue
        subtype_of[row["drug_class"] + ":" + row["isolate_id"]] = row["subtype"]
    annotated = [u for u in units if u in subtype_of]
    subtype_counts = Counter(subtype_of[u] for u in annotated)
    summary["subtype_coverage"] = {
        "units_with_subtype": len(annotated),
        "units_total": len(units),
        "counts": dict(subtype_counts.most_common()),
    }
    print(
        "  subtype annotated: "
        + str(len(annotated))
        + " of "
        + str(len(units))
        + " isolates; "
        + str(dict(subtype_counts.most_common(6)))
    )
    # Only subtypes with enough isolates to form a test set are held out.
    holdable = [s for s, n in subtype_counts.items() if n >= 20 and s]
    rows = []
    for subtype in sorted(holdable):
        for unit in units:
            cls, isolate = unit.split(":", 1)
            is_test = subtype_of.get(unit) == subtype
            rows.append(
                {
                    "isolate_id": isolate,
                    "drug_class": cls,
                    "unit": unit,
                    "fold": "held_out_subtype_" + subtype,
                    "role": "test" if is_test else "train",
                    "group": subtype_of.get(unit, "unannotated"),
                }
            )
    summary["subtypes_held_out"] = sorted(holdable)
    if rows:
        write_split(
            SPLITS / "subtype_held_out.csv", rows,
            ["isolate_id", "drug_class", "unit", "fold", "role", "group"],
        )

    (SPLITS / "split_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("")
    print("wrote " + (SPLITS / "split_summary.json").relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
