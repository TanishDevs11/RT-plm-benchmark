"""Write the frozen split definition files.

Splits are files, not code that runs at model time. The point is that the partition is fixed
before any model exists, so it cannot be adjusted, reseeded, or quietly re-derived once
results start appearing.

Task A: leave-one-family-out, 7 folds, preserving the inherited family definition so the new
work stays comparable to the existing audit.

Task B: three regimes, all defined now. The Task B id set is fully determined without the
activity data, because both libraries are exactly saturating: stretch 1 covers residues 60 to
84 and stretch 2 covers 95 to 124, and every one of the 19 non-wild-type substitutions is
present at every position, giving 25 times 19 plus 30 times 19, so 1045 variants. The
wild-type residue at each of those 55 positions comes from the resolved reference frame, and
none of the four unresolved PE2 substitution positions (200, 306, 313, 330) falls inside
either stretch, so the identities of the variants are certain even though the parent
construct's substitution content is not.

That makes these split files a reconciliation check as well as a partition: when the parser
eventually reads Tables S6 and S7, any variant it produces that is not in these files, or any
id here that the parser does not produce, is a discrepancy to be logged rather than absorbed.

    python curation/define_splits.py
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import GLOBAL_SEED, print_run_header, sha256_of  # noqa: E402

AA20 = "ACDEFGHIKLMNPQRSTVWY"

CURATED_A = REPO_ROOT / "tasks/taskA_crossfamily/curated.csv"
INHERITED_A = REPO_ROOT / "data/rt_sequences.csv"
SPLITS_A = REPO_ROOT / "tasks/taskA_crossfamily/splits"

# The identity threshold the secondary split holds out, as the brief specifies.
CLUSTER_SPLIT_THRESHOLD = 70

REFERENCE_B = REPO_ROOT / "tasks/taskB_mmlv_dms/raw/reference_candidate_unconfirmed.fasta"
SPLITS_B = REPO_ROOT / "tasks/taskB_mmlv_dms/splits"

# Library boundaries, verbatim from the source: "Stretch 1 spanning residues S60-Q84" and
# "Stretch 2 spanning residues N95-D124".
STRETCHES: dict[str, tuple[int, int]] = {"1": (60, 84), "2": (95, 124)}

WILD_TYPE_ID = "B_wt"
POSITION_FOLDS = 5


def write_split(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    counts = Counter((str(r["fold"]), str(r["role"])) for r in rows)
    print("  wrote " + path.relative_to(REPO_ROOT).as_posix())
    print("    sha256=" + sha256_of(path) + ", " + str(len(rows)) + " assignment rows")
    for (fold, role), count in sorted(counts.items()):
        print("      fold " + fold + " " + role + ": " + str(count))


def load_task_a_rows() -> tuple[list[dict[str, str]], str]:
    """Task A rows, from curated.csv when it exists and the inherited file otherwise.

    curated.csv is the authority once the parse has run: it is the table built from the
    primary source and endorsed at Gate G2. The inherited file stays as a fallback only
    so that this script can still run before the parse, and the source actually used is
    printed on every run rather than left to be inferred.
    """
    if CURATED_A.is_file():
        rows = list(csv.DictReader(CURATED_A.open(encoding="utf-8")))
        # Normalise to the column names the rest of this function uses, so that the two
        # sources are interchangeable here and the difference stays in one place.
        return (
            [{"rt_name": r["rt_name"], "rt_family": r["family"], "active": r["active"]} for r in rows],
            "curated.csv",
        )
    rows = list(csv.DictReader(INHERITED_A.open(encoding="utf-8")))
    return (
        [{"rt_name": r["rt_name"], "rt_family": r["rt_family"], "active": r["active"]} for r in rows],
        "FALLBACK " + INHERITED_A.relative_to(REPO_ROOT).as_posix(),
    )


def load_clusters(threshold: int) -> dict[str, str]:
    """{id: cluster representative} at one identity threshold."""
    path = SPLITS_A / ("clusters_" + str(threshold) + ".tsv")
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        return {
            row["id"]: row["cluster_representative"]
            for row in csv.DictReader(handle, delimiter="\t")
        }


def task_a_splits() -> int:
    if not CURATED_A.is_file() and not INHERITED_A.is_file():
        print("Task A source absent: " + CURATED_A.as_posix())
        return 1
    rows, source = load_task_a_rows()
    families = sorted({r["rt_family"] for r in rows})
    print("")
    print("=== Task A: leave-one-family-out ===")
    print("  source: " + source)
    print("  " + str(len(rows)) + " sequences, " + str(len(families)) + " folds: " + ", ".join(families))

    assignments: list[dict[str, object]] = []
    for family in families:
        for row in rows:
            assignments.append(
                {
                    "rt_name": row["rt_name"],
                    "id": "A_" + row["rt_name"],
                    "fold": family,
                    "role": "test" if row["rt_family"] == family else "train",
                }
            )
    write_split(
        SPLITS_A / "leave_one_family_out.csv",
        assignments,
        ["rt_name", "id", "fold", "role"],
    )

    # Secondary split: leave-one-cluster-out at 70 percent identity.
    #
    # It exists because family labels may under-describe the redundancy. The primary
    # split holds out a family, and the Phase 2 clustering showed that this holds out an
    # identity cluster down to 50 percent but not at 30, where four clusters cross a
    # family boundary. Holding out an identity cluster instead makes the redundancy
    # control explicit rather than a consequence of the labelling.
    #
    # 70 percent is the threshold named in the brief. It is a stricter control than the
    # family split in the sense that it is defined on measured sequence identity rather
    # than on a label, and a weaker one in the sense that its folds are much smaller, so
    # it is reported alongside the primary split rather than instead of it.
    clusters = load_clusters(CLUSTER_SPLIT_THRESHOLD)
    if not clusters:
        print("")
        print("  clusters_" + str(CLUSTER_SPLIT_THRESHOLD) + ".tsv absent, so the")
        print("  leave-one-cluster-out split cannot be written. Run")
        print("  curation/cluster_redundancy.py first.")
    else:
        print("")
        print("=== Task A: leave-one-cluster-out at " + str(CLUSTER_SPLIT_THRESHOLD) + " percent ===")
        missing = [r["rt_name"] for r in rows if "A_" + r["rt_name"] not in clusters]
        if missing:
            raise SystemExit(
                "no cluster assignment for " + str(missing) + "; the cluster file and the "
                "curated table disagree, which must be fixed rather than worked around"
            )
        # Folds are named by their representative, so a fold name is traceable to the
        # cluster file rather than being an opaque integer.
        representatives = sorted({clusters["A_" + r["rt_name"]] for r in rows})
        print("  " + str(len(rows)) + " sequences, " + str(len(representatives)) + " folds")
        cluster_assignments: list[dict[str, object]] = []
        for representative in representatives:
            for row in rows:
                in_test = clusters["A_" + row["rt_name"]] == representative
                cluster_assignments.append(
                    {
                        "rt_name": row["rt_name"],
                        "id": "A_" + row["rt_name"],
                        "fold": representative.replace("A_", "cluster_"),
                        "role": "test" if in_test else "train",
                    }
                )
        write_split(
            SPLITS_A / ("leave_one_cluster_out_" + str(CLUSTER_SPLIT_THRESHOLD) + ".csv"),
            cluster_assignments,
            ["rt_name", "id", "fold", "role"],
        )

    # A fold that holds no positive cannot contribute to a ranking or a precision-recall
    # measurement, and three of the seven do not. Stated here because it is a property of the
    # split, not of any model, and it bounds what the task can ever show.
    positives = Counter()
    totals = Counter()
    for row in rows:
        totals[row["rt_family"]] += 1
        positives[row["rt_family"]] += int(row["active"])
    print("  fold composition, n and positives:")
    for family in families:
        note = "  <-- no positive, contributes no ranking signal when held out" if positives[family] == 0 else ""
        print("    " + family.ljust(22) + " n=" + str(totals[family]).rjust(2) + " positives=" + str(positives[family]) + note)
    return 0


def task_b_expected_ids(reference: str) -> list[dict[str, object]]:
    """Every variant the saturating libraries must contain, from the reference frame."""
    variants: list[dict[str, object]] = []
    for stretch, (first, last) in STRETCHES.items():
        for position in range(first, last + 1):
            wild = reference[position - 1]
            for mutant in AA20:
                if mutant == wild:
                    continue
                variants.append(
                    {
                        "id": "B_" + wild + str(position) + mutant,
                        "position": position,
                        "stretch": stretch,
                        "wt_aa": wild,
                        "mut_aa": mutant,
                    }
                )
    return variants


def task_b_splits() -> int:
    print("")
    print("=== Task B: four regimes ===")
    if not REFERENCE_B.is_file():
        print("  reference frame absent: " + REFERENCE_B.as_posix())
        print("  run data_acquisition/resolve_mmlv_reference.py first")
        return 1
    reference = "".join(
        line.strip() for line in REFERENCE_B.read_text(encoding="utf-8").splitlines()
        if not line.startswith(">")
    )
    print("  reference frame: " + str(len(reference)) + " residues, from " + REFERENCE_B.name)

    variants = task_b_expected_ids(reference)
    per_stretch = Counter(str(v["stretch"]) for v in variants)
    print("  expected variants: " + str(len(variants)) + " total, stretch 1: " + str(per_stretch["1"]) + ", stretch 2: " + str(per_stretch["2"]))
    if per_stretch["1"] != 475 or per_stretch["2"] != 570 or len(variants) != 1045:
        print("  MISMATCH against the source's stated 475, 570, and 1045.")
        print("  The reference frame or the stretch boundaries are wrong. Halting.")
        return 1
    print("  matches the source's stated 475, 570, and 1045 exactly.")

    positions = sorted({int(v["position"]) for v in variants})
    duplicate_ids = [item for item, count in Counter(str(v["id"]) for v in variants).items() if count > 1]
    if duplicate_ids:
        print("  duplicate ids generated, which should be impossible: " + str(duplicate_ids[:5]))
        return 1

    # Regime 1: position held out. Positions are assigned round robin within each stretch, so
    # every fold contains positions from both libraries and the folds stay balanced. A
    # stricter variant would use contiguous blocks of positions, which would also withhold
    # the immediate structural neighbours; that is a harder regime and is noted in
    # reports/split_design.md rather than used here, because the brief asks for one
    # position-held-out regime and this is the standard grouped form of it.
    fold_of_position: dict[int, int] = {}
    for stretch in STRETCHES:
        stretch_positions = sorted({int(v["position"]) for v in variants if v["stretch"] == stretch})
        for index, position in enumerate(stretch_positions):
            fold_of_position[position] = index % POSITION_FOLDS

    assignments: list[dict[str, object]] = []
    for fold in range(POSITION_FOLDS):
        for variant in variants:
            assignments.append(
                {
                    "id": variant["id"],
                    "fold": "pos_fold_" + str(fold),
                    "role": "test" if fold_of_position[int(variant["position"])] == fold else "train",
                    "group": "position_" + str(variant["position"]),
                }
            )
        # The wild type is the reference the labels are defined against, not a test item.
        assignments.append(
            {"id": WILD_TYPE_ID, "fold": "pos_fold_" + str(fold), "role": "train", "group": "wild_type"}
        )
    write_split(
        SPLITS_B / "position_held_out.csv",
        assignments,
        ["id", "fold", "role", "group"],
    )
    print("    " + str(len(positions)) + " positions across " + str(POSITION_FOLDS) + " folds; no position is split across folds")

    # Regime 2: stretch held out. The headline Task B result.
    assignments = []
    for test_stretch in sorted(STRETCHES):
        fold = "test_stretch_" + test_stretch
        for variant in variants:
            assignments.append(
                {
                    "id": variant["id"],
                    "fold": fold,
                    "role": "test" if variant["stretch"] == test_stretch else "train",
                    "group": "stretch_" + str(variant["stretch"]),
                }
            )
        assignments.append({"id": WILD_TYPE_ID, "fold": fold, "role": "train", "group": "wild_type"})
    write_split(
        SPLITS_B / "stretch_held_out.csv",
        assignments,
        ["id", "fold", "role", "group"],
    )

    # Regime 3: the deliberately leaky reference. Labelled in the filename and in a column on
    # every row, so it cannot be mistaken for a reportable result by anyone reading either.
    import random

    generator = random.Random(GLOBAL_SEED)
    shuffled = [str(v["id"]) for v in variants]
    generator.shuffle(shuffled)
    fold_of_id = {identifier: index % POSITION_FOLDS for index, identifier in enumerate(shuffled)}
    assignments = []
    for fold in range(POSITION_FOLDS):
        for variant in variants:
            assignments.append(
                {
                    "id": variant["id"],
                    "fold": "random_fold_" + str(fold),
                    "role": "test" if fold_of_id[str(variant["id"])] == fold else "train",
                    "leaky": "yes",
                    "never_report": "this split leaks position identity between train and test",
                }
            )
        assignments.append(
            {
                "id": WILD_TYPE_ID,
                "fold": "random_fold_" + str(fold),
                "role": "train",
                "leaky": "yes",
                "never_report": "this split leaks position identity between train and test",
            }
        )
    write_split(
        SPLITS_B / "random_variant_LEAKY_DO_NOT_REPORT.csv",
        assignments,
        ["id", "fold", "role", "leaky", "never_report"],
    )
    print("    seeded with GLOBAL_SEED=" + str(GLOBAL_SEED))
    print("    labelled leaky in the filename and on every row; it quantifies optimism only")

    # Regime 4: target amino acid held out. All substitutions TO a given residue are held
    # out together, so the model cannot have seen any example of that substitution
    # chemistry during training. It tests whether a representation has learned what it
    # means to put a tryptophan somewhere, as opposed to having learned which positions
    # in this protein tolerate change at all.
    #
    # One fold per target residue, 20 folds. Every fold's test set spans both stretches
    # and many positions, so unlike the position regime it does not also hold out a
    # region; that is deliberate, because the point is to isolate substitution chemistry
    # from position identity rather than to confound the two.
    assignments = []
    targets = sorted({str(v["mut_aa"]) for v in variants})
    for target in targets:
        fold = "test_to_" + target
        for variant in variants:
            assignments.append(
                {
                    "id": variant["id"],
                    "fold": fold,
                    "role": "test" if str(variant["mut_aa"]) == target else "train",
                    "group": "to_" + str(variant["mut_aa"]),
                }
            )
        assignments.append(
            {"id": WILD_TYPE_ID, "fold": fold, "role": "train", "group": "wild_type"}
        )
    write_split(
        SPLITS_B / "aa_held_out.csv",
        assignments,
        ["id", "fold", "role", "group"],
    )
    sizes = Counter(str(v["mut_aa"]) for v in variants)
    print(
        "    "
        + str(len(targets))
        + " folds, one per target residue; test sizes "
        + str(min(sizes.values()))
        + " to "
        + str(max(sizes.values()))
        + " variants"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write frozen split definition files.")
    parser.parse_args(argv)
    print_run_header("curation/define_splits.py", [INHERITED_A, REFERENCE_B])
    failures = task_a_splits() + task_b_splits()
    print("")
    if failures:
        print("some splits could not be written; see above")
    else:
        print("All splits written. These files are frozen: nothing regenerates them at model time.")
    print("")
    print("Task A2 splits are not written. That cohort is evaluation only, so it has no folds:")
    print("it is scored whole, by a model trained on Task A alone.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
