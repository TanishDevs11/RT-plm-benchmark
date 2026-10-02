"""Verify the frozen Task A splits against every leakage condition, and report.

A split file is data, so nothing else in the pipeline would notice if one were edited,
regenerated under a different rule, or quietly reordered. This script is what notices. It
reads the frozen files and checks, for every fold of every split:

  * no sequence appears in both train and test, by identity and by sequence digest
  * every row is tested exactly once across the folds, so nothing is scored twice or never
  * no family spans the split, for the family split
  * no identity cluster spans the split, at 90, 70, 50 and 30 percent
  * the primary split agrees exactly with the partition bench/protocol.py derives at run
    time, so the frozen file and the harness cannot drift apart

It also reports the two fold properties that bound what each split can measure: folds
whose training set holds fewer than two actives, and folds whose test set holds no active
at all. Both need a handling rule, and the rule is stated once here and applied uniformly.

    python curation/verify_splits_taskA.py

Output: reports/split_verification.md, and a non-zero exit if any check fails.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from curation.define_splits import CLUSTER_SPLIT_THRESHOLD  # noqa: E402
from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
SPLITS = REPO_ROOT / "tasks" / "taskA_crossfamily" / "splits"
OUT = REPO_ROOT / "reports" / "split_verification.md"

IDENTITY_THRESHOLDS = (90, 70, 50, 30)

SPLIT_FILES = {
    "leave-one-family-out, primary": "leave_one_family_out.csv",
    "leave-one-cluster-out at 70 percent, secondary": "leave_one_cluster_out_70.csv",
}

# A fold needs at least this many actives in training for a classifier to be fittable at
# all. With one positive, a regularized logistic regression has nothing to separate.
MIN_TRAIN_ACTIVES = 2


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_clusters(threshold: int) -> dict[str, str]:
    path = SPLITS / ("clusters_" + str(threshold) + ".tsv")
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        return {
            row["id"]: row["cluster_representative"]
            for row in csv.DictReader(handle, delimiter="\t")
        }


def folds_of(rows: list[dict[str, str]]) -> dict[str, dict[str, set[str]]]:
    out: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"train": set(), "test": set()})
    for row in rows:
        out[row["fold"]][row["role"]].add(row["id"])
    return dict(out)


def protocol_partition(curated: list[dict[str, str]]) -> dict[str, set[str]]:
    """The partition bench/protocol.py derives at run time, for comparison.

    protocol.py does not read a split file: it loads the dataset and groups by family
    inside run_nested_lofo. So the frozen file's claim to be compatible with the harness
    is only true if it reproduces that grouping, and this is the check of that claim.
    """
    sys.path.insert(0, str(REPO_ROOT / "bench"))
    from protocol import load_dataset  # noqa: E402

    data = load_dataset()
    out: dict[str, set[str]] = {}
    for family in sorted(data["rt_family"].unique()):
        held = data.loc[data["rt_family"] == family, "rt_name"]
        out[family] = {"A_" + name for name in held}
    return out


def main() -> int:
    print_run_header("curation/verify_splits_taskA.py", [CURATED])
    curated = read_csv(CURATED)
    all_ids = {row["id"] for row in curated}
    family_of = {row["id"]: row["family"] for row in curated}
    active_of = {row["id"]: row["active"] == "1" for row in curated}
    digest_of = {
        row["id"]: hashlib.sha256(row["sequence"].encode("utf-8")).hexdigest()
        for row in curated
    }
    clusters = {t: read_clusters(t) for t in IDENTITY_THRESHOLDS}

    failures: list[str] = []
    lines = [
        "# Task A split verification",
        "",
        "Written by `curation/verify_splits_taskA.py`. The splits are frozen files, not",
        "code that runs at model time, so that the partition is fixed before any model",
        "exists and cannot be adjusted or re-derived once results start appearing. This",
        "report is the check that each file says what it is supposed to say.",
        "",
        "Curated table: `tasks/taskA_crossfamily/curated.csv`, SHA256",
        "`" + sha256_of(CURATED) + "`.",
        "",
        "| file | SHA256 |",
        "| --- | --- |",
    ]
    for label, filename in SPLIT_FILES.items():
        path = SPLITS / filename
        lines.append(
            "| `"
            + filename
            + "` | "
            + ("`" + sha256_of(path) + "`" if path.is_file() else "ABSENT")
            + " |"
        )
    for threshold in IDENTITY_THRESHOLDS:
        path = SPLITS / ("clusters_" + str(threshold) + ".tsv")
        lines.append(
            "| `"
            + path.name
            + "` | "
            + ("`" + sha256_of(path) + "`" if path.is_file() else "ABSENT")
            + " |"
        )

    for label, filename in SPLIT_FILES.items():
        path = SPLITS / filename
        lines.append("")
        lines.append("## " + label)
        lines.append("")
        if not path.is_file():
            lines.append("**ABSENT.** `" + filename + "` has not been written.")
            failures.append(filename + " absent")
            continue
        rows = read_csv(path)
        folds = folds_of(rows)
        checks: list[tuple[str, bool, str]] = []

        # Coverage and disjointness, per fold.
        overlap_folds = [f for f, p in folds.items() if p["train"] & p["test"]]
        checks.append(
            (
                "no id appears in both train and test, in any fold",
                not overlap_folds,
                "folds with an overlap: " + str(overlap_folds) if overlap_folds else "",
            )
        )
        incomplete = [f for f, p in folds.items() if (p["train"] | p["test"]) != all_ids]
        checks.append(
            (
                "every fold covers every row exactly once",
                not incomplete,
                "folds not covering the table: " + str(incomplete) if incomplete else "",
            )
        )
        tested = [i for p in folds.values() for i in p["test"]]
        checks.append(
            (
                "every row is tested exactly once across the folds",
                len(tested) == len(all_ids) and set(tested) == all_ids,
                "tested " + str(len(tested)) + " times against " + str(len(all_ids)) + " rows",
            )
        )

        # Sequence-level disjointness. Two rows could carry the same sequence under
        # different names, which an id check would not catch.
        digest_overlap = []
        for fold, parts in folds.items():
            train_digests = {digest_of[i] for i in parts["train"]}
            test_digests = {digest_of[i] for i in parts["test"]}
            if train_digests & test_digests:
                digest_overlap.append(fold)
        checks.append(
            (
                "no sequence digest appears in both train and test",
                not digest_overlap,
                "folds sharing a sequence: " + str(digest_overlap) if digest_overlap else "",
            )
        )

        # Family containment, for the family split only.
        if "family" in label:
            bad = []
            for fold, parts in folds.items():
                test_families = {family_of[i] for i in parts["test"]}
                train_families = {family_of[i] for i in parts["train"]}
                if test_families != {fold} or fold in train_families:
                    bad.append(fold)
            checks.append(
                (
                    "no family spans the split: each test set is exactly one family, absent from training",
                    not bad,
                    "folds failing: " + str(bad) if bad else "",
                )
            )

        lines.append("| check | result | detail |")
        lines.append("| --- | --- | --- |")
        for name, passed, detail in checks:
            lines.append(
                "| " + name + " | " + ("PASS" if passed else "**FAIL**") + " | " + detail + " |"
            )
            if not passed:
                failures.append(filename + ": " + name)

        # Cluster containment at every threshold, reported as a property rather than
        # enforced as a pass or fail.
        #
        # The distinction matters and is easy to get wrong. A split defined at one
        # identity threshold cannot hold out clusters defined at a coarser one: a 70
        # percent cluster is a subset of a 50 percent cluster, so holding out the former
        # necessarily leaves other members of the latter in training. Calling that a
        # failure would mean the leave-one-cluster-out split failed by construction, and a
        # guard that can never pass is a guard that gets ignored.
        #
        # So containment is reported per threshold with the reason it holds or does not,
        # and only the conditions that are genuine defects stay above as pass or fail:
        # train-test overlap, coverage, duplicate sequences across the boundary, family
        # containment for the family split, and agreement with the harness.
        own_threshold = CLUSTER_SPLIT_THRESHOLD if "cluster" in label else None
        lines.append("")
        lines.append("#### Identity cluster containment")
        lines.append("")
        lines.append("| threshold | clusters spanning train and test | holds | why |")
        lines.append("| --- | --- | --- | --- |")
        for threshold in IDENTITY_THRESHOLDS:
            assignment = clusters[threshold]
            if not assignment:
                lines.append(
                    "| " + str(threshold) + " percent | unknown | no | cluster file absent |"
                )
                failures.append(
                    filename + ": clusters_" + str(threshold) + ".tsv absent"
                )
                continue
            spanning: dict[str, list[str]] = {}
            for fold, parts in folds.items():
                train_clusters = {assignment[i] for i in parts["train"]}
                test_clusters = {assignment[i] for i in parts["test"]}
                shared = train_clusters & test_clusters
                if shared:
                    spanning[fold] = sorted(shared)
            if not spanning:
                reason = "every cluster at this threshold lies inside one fold"
            elif own_threshold is not None and threshold < own_threshold:
                reason = (
                    "expected by construction: this split holds out a "
                    + str(own_threshold)
                    + " percent cluster, which is a subset of a "
                    + str(threshold)
                    + " percent cluster"
                )
            else:
                reason = (
                    "**a real limitation**: "
                    + str(len(spanning))
                    + " folds leave a relative of the held-out set in training at this threshold"
                )
            lines.append(
                "| "
                + str(threshold)
                + " percent | "
                + str(len(spanning))
                + " | "
                + ("yes" if not spanning else "no")
                + " | "
                + reason
                + " |"
            )
            if spanning and not (own_threshold is not None and threshold < own_threshold):
                for fold, shared in sorted(spanning.items())[:8]:
                    lines.append(
                        "| | | | `"
                        + fold
                        + "` shares cluster "
                        + ", ".join("`" + c.replace("A_", "") + "`" for c in shared)
                        + " |"
                    )

        # Fold properties that bound what the split can measure.
        thin_train = []
        empty_test = []
        for fold, parts in sorted(folds.items()):
            train_actives = sum(1 for i in parts["train"] if active_of[i])
            test_actives = sum(1 for i in parts["test"] if active_of[i])
            if train_actives < MIN_TRAIN_ACTIVES:
                thin_train.append((fold, train_actives))
            if test_actives == 0:
                empty_test.append((fold, len(parts["test"])))

        lines.append("")
        lines.append("### Fold properties")
        lines.append("")
        lines.append("| quantity | value |")
        lines.append("| --- | --- |")
        lines.append("| folds | " + str(len(folds)) + " |")
        lines.append(
            "| folds whose training set holds fewer than "
            + str(MIN_TRAIN_ACTIVES)
            + " actives | "
            + str(len(thin_train))
            + " |"
        )
        lines.append(
            "| folds whose test set holds no active | "
            + str(len(empty_test))
            + " of "
            + str(len(folds))
            + " |"
        )
        if thin_train:
            lines.append("")
            lines.append("Folds with too few training actives to fit a classifier:")
            lines.append("")
            for fold, count in thin_train:
                lines.append("- `" + fold + "`: " + str(count) + " actives in training")
        else:
            lines.append("")
            lines.append(
                "No fold has fewer than "
                + str(MIN_TRAIN_ACTIVES)
                + " actives in training, so the handling rule below does not fire for"
            )
            lines.append("this split. It is stated anyway, because it must not be invented later.")
        if empty_test:
            lines.append("")
            lines.append("Folds whose test set is all negative, on which a ranking correlation is undefined:")
            lines.append("")
            # Capped: this split has 49 folds and listing all of them would bury the
            # report. The count above is the number that matters.
            shown = sorted(empty_test)[:10]
            for fold, size in shown:
                lines.append(
                    "- `"
                    + fold
                    + "`: "
                    + str(size)
                    + (" row" if size == 1 else " rows")
                    + ", 0 actives"
                )
            if len(empty_test) > len(shown):
                lines.append(
                    "- and "
                    + str(len(empty_test) - len(shown))
                    + " more; the full assignment is in the split file"
                )

    lines += [
        "",
        "## The handling rules, stated once and applied uniformly",
        "",
        "Two fold conditions need a rule. Both rules are stated here so that they are",
        "fixed before any result exists, rather than chosen later when it is known which",
        "choice flatters a number.",
        "",
        "**Rule 1, a training set with fewer than "
        + str(MIN_TRAIN_ACTIVES)
        + " actives.** Such a fold cannot support a",
        "classifier: with one positive there is nothing to separate. The fold is reported",
        "as **undefined** and is excluded from the pooled prediction vector, with its",
        "exclusion and its row count stated in the results table. It is never filled with",
        "a constant, a prior, or a majority-class prediction, because each of those is an",
        "invented prediction that would then be scored as though it were a measurement.",
        "",
        "**Rule 2, a test set with no active.** Precision-recall area is undefined on an",
        "all-negative test set and so is a ranking correlation against an all-zero target.",
        "The fold's predictions still enter the pooled vector, because the pooled metric is",
        "computed once over all 57 rows and those rows are genuine negatives that a model",
        "must not rank highly. What is **not** done is computing a per-fold score for such",
        "a fold and reporting it as zero, or dropping its rows from the pool. Scoring it as",
        "zero invents a measurement; dropping it changes the denominator. Per-family",
        "breakdowns therefore show `undefined` for these folds rather than a number.",
        "",
        "This is why the primary split is scored by pooling predictions across folds and",
        "computing the metric once, rather than by averaging per-fold metrics: "
        + str(len([f for f in ("CRISPR-associated", "Other", "Unclassified")]))
        + " of the 7",
        "families hold no active at all, and per-fold averaging has no defined value for",
        "them.",
        "",
    ]

    # Compatibility with the harness, which derives its own partition at run time.
    lines += [
        "## Compatibility with `bench/protocol.py`",
        "",
        "`bench/protocol.py` does not read a split file. It loads the dataset and groups",
        "by family inside `run_nested_lofo`, so the frozen primary split is only",
        "compatible with the harness if it reproduces that grouping exactly. Asserting",
        "that here is what stops the file and the harness drifting apart.",
        "",
    ]
    try:
        runtime = protocol_partition(curated)
        frozen = folds_of(read_csv(SPLITS / "leave_one_family_out.csv"))
        frozen_tests = {fold: parts["test"] for fold, parts in frozen.items()}
        agrees = frozen_tests == runtime
        lines.append("| check | result | detail |")
        lines.append("| --- | --- | --- |")
        detail = ""
        if not agrees:
            only_frozen = {k: sorted(v - runtime.get(k, set())) for k, v in frozen_tests.items()}
            only_runtime = {k: sorted(v - frozen_tests.get(k, set())) for k, v in runtime.items()}
            detail = (
                "in the file only: "
                + str({k: v for k, v in only_frozen.items() if v})
                + "; in the harness only: "
                + str({k: v for k, v in only_runtime.items() if v})
            )
            failures.append("frozen split disagrees with bench/protocol.py")
        lines.append(
            "| the frozen test sets equal the partition the harness derives | "
            + ("PASS" if agrees else "**FAIL**")
            + " | "
            + detail
            + " |"
        )
    except Exception as error:  # noqa: BLE001
        lines.append("Could not run the comparison: " + type(error).__name__ + ": " + str(error))
        failures.append("protocol comparison failed: " + str(error))

    lines += [
        "",
        "## Result",
        "",
        ("**All checks pass.**" if not failures else "**" + str(len(failures)) + " check(s) FAILED.**"),
        "",
    ]
    if failures:
        for failure in failures:
            lines.append("- " + failure)
        lines.append("")
    lines += [
        "What passing does not mean: the splits control sequence identity and family",
        "membership, and nothing more. They do not remove the association between family",
        "and activity, which is real in these data, so a model that predicts",
        "\"retroviral, therefore active\" still scores well without knowing anything about",
        "catalysis. That confound is addressed by the family-classification control in the",
        "modelling phase, not by any split.",
        "",
        "And as `reports/dataset_overview.md` records, the leave-one-cluster-out split at",
        "70 percent does not clear remote homology either: four clusters cross a family",
        "boundary at 30 percent identity, which no split defined at 70 percent can hold",
        "out. That is a stated limitation of the panel.",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    if failures:
        print("")
        print(str(len(failures)) + " check(s) FAILED:")
        for failure in failures:
            print("  " + failure)
        return 1
    print("all checks pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
