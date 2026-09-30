"""Tests that the frozen split files say what they are supposed to say.

Splits are data now, not code, which means nothing re-derives them and nothing would notice
if one were edited, truncated, or regenerated with a different rule. These tests are the
guard. They check the properties each regime exists to guarantee, rather than checking that
the files merely parse.

    python curation/test_splits.py
"""

from __future__ import annotations

import csv
import itertools
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

SPLITS_A = REPO_ROOT / "tasks/taskA_crossfamily/splits"
SPLITS_B = REPO_ROOT / "tasks/taskB_mmlv_dms/splits"
INHERITED_A = REPO_ROOT / "data/rt_sequences.csv"

STRETCHES = {"1": (60, 84), "2": (95, 124)}
AA20 = "ACDEFGHIKLMNPQRSTVWY"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def folds_of(rows: list[dict[str, str]]) -> dict[str, dict[str, set[str]]]:
    out: dict[str, dict[str, set[str]]] = defaultdict(lambda: {"train": set(), "test": set()})
    for row in rows:
        out[row["fold"]][row["role"]].add(row["id"])
    return out


def test_task_a_is_leave_one_family_out() -> None:
    rows = read(SPLITS_A / "leave_one_family_out.csv")
    source = read(INHERITED_A)
    family = {"A_" + r["rt_name"]: r["rt_family"] for r in source}
    all_ids = set(family)
    folds = folds_of(rows)

    assert len(folds) == len(set(family.values())), "one fold per family expected"
    for fold, parts in folds.items():
        assert not parts["train"] & parts["test"], fold + ": an id is both train and test"
        assert parts["train"] | parts["test"] == all_ids, fold + ": does not cover every id exactly once"
        assert parts["test"], fold + ": empty test set"
        # The defining property: the test set is exactly one family, and none of that family
        # is anywhere in training.
        assert {family[i] for i in parts["test"]} == {fold}, fold + ": test set is not exactly that family"
        assert fold not in {family[i] for i in parts["train"]}, fold + ": its family leaks into training"

    # Every id is tested exactly once across the folds, so nothing is evaluated twice or never.
    tested = [i for parts in folds.values() for i in parts["test"]]
    assert len(tested) == len(all_ids), "ids are not tested exactly once each"
    assert set(tested) == all_ids


def expected_task_b_ids() -> set[str]:
    reference = REPO_ROOT / "tasks/taskB_mmlv_dms/raw/reference_candidate_unconfirmed.fasta"
    sequence = "".join(
        line.strip() for line in reference.read_text(encoding="utf-8").splitlines()
        if not line.startswith(">")
    )
    ids = set()
    for first, last in STRETCHES.values():
        for position in range(first, last + 1):
            wild = sequence[position - 1]
            for mutant in AA20:
                if mutant != wild:
                    ids.add("B_" + wild + str(position) + mutant)
    return ids


def position_of(identifier: str) -> int:
    return int("".join(c for c in identifier[2:] if c.isdigit()))


def stretch_of(identifier: str) -> str:
    position = position_of(identifier)
    for stretch, (first, last) in STRETCHES.items():
        if first <= position <= last:
            return stretch
    raise AssertionError(identifier + " is at a position in neither stretch")


def test_task_b_ids_match_the_saturating_library() -> None:
    expected = expected_task_b_ids()
    assert len(expected) == 1045, "expected 1045 saturating variants, got " + str(len(expected))
    for name in ("position_held_out.csv", "stretch_held_out.csv", "random_variant_LEAKY_DO_NOT_REPORT.csv"):
        rows = read(SPLITS_B / name)
        ids = {r["id"] for r in rows} - {"B_wt"}
        assert ids == expected, name + ": id set does not match the saturating library"


def test_position_held_out_keeps_each_position_whole() -> None:
    rows = read(SPLITS_B / "position_held_out.csv")
    folds = folds_of(rows)
    assert len(folds) == 5, "expected 5 folds"
    test_fold_of_position: dict[int, str] = {}
    for fold, parts in folds.items():
        assert not parts["train"] & parts["test"], fold + ": an id is both train and test"
        assert "B_wt" in parts["train"], fold + ": wild type must be in training"
        assert "B_wt" not in parts["test"], fold + ": wild type must never be a test item"
        for identifier in parts["test"]:
            position = position_of(identifier)
            previous = test_fold_of_position.setdefault(position, fold)
            assert previous == fold, "position " + str(position) + " is tested in two folds"

    # The defining property: no substitution at a test position appears in training.
    for fold, parts in folds.items():
        test_positions = {position_of(i) for i in parts["test"]}
        train_positions = {position_of(i) for i in parts["train"] if i != "B_wt"}
        assert not test_positions & train_positions, (
            fold + ": positions " + str(sorted(test_positions & train_positions)[:5]) + " leak into training"
        )

    assert len(test_fold_of_position) == 55, "expected all 55 positions to be tested"
    # Every fold should draw from both libraries, which is why positions are assigned round
    # robin within each stretch rather than globally.
    for fold, parts in folds.items():
        assert {stretch_of(i) for i in parts["test"]} == {"1", "2"}, fold + ": does not span both stretches"


def test_stretch_held_out_tests_exactly_one_library() -> None:
    rows = read(SPLITS_B / "stretch_held_out.csv")
    folds = folds_of(rows)
    assert set(folds) == {"test_stretch_1", "test_stretch_2"}
    sizes = {}
    for fold, parts in folds.items():
        wanted = fold.rsplit("_", 1)[1]
        assert not parts["train"] & parts["test"], fold + ": an id is both train and test"
        assert "B_wt" in parts["train"] and "B_wt" not in parts["test"]
        assert {stretch_of(i) for i in parts["test"]} == {wanted}, fold + ": test set is not one stretch"
        assert wanted not in {stretch_of(i) for i in parts["train"] if i != "B_wt"}, (
            fold + ": the held-out stretch leaks into training"
        )
        sizes[wanted] = len(parts["test"])
    assert sizes == {"1": 475, "2": 570}, "stretch test sizes are " + str(sizes)


def test_the_leaky_split_is_labelled_as_leaky_in_the_file() -> None:
    path = SPLITS_B / "random_variant_LEAKY_DO_NOT_REPORT.csv"
    assert "LEAKY" in path.name, "the filename must say it is leaky"
    rows = read(path)
    assert rows, "file is empty"
    assert "leaky" in rows[0], "a leaky column is required"
    assert "never_report" in rows[0], "a never_report column is required"
    for row in rows:
        assert row["leaky"] == "yes", "every row must be marked leaky"
        assert row["never_report"].strip(), "every row must carry the reason"


def test_the_leaky_split_really_does_leak() -> None:
    """A positive control. If this split did not leak, labelling it leaky would be wrong.

    With 19 substitutions per position scattered at random across 5 folds, almost every test
    variant should have same-position siblings in training. This asserts the leak exists, so
    the file's own warning is justified rather than decorative.
    """
    rows = read(SPLITS_B / "random_variant_LEAKY_DO_NOT_REPORT.csv")
    folds = folds_of(rows)
    for fold, parts in folds.items():
        train_positions = {position_of(i) for i in parts["train"] if i != "B_wt"}
        leaked = [i for i in parts["test"] if position_of(i) in train_positions]
        fraction = len(leaked) / len(parts["test"])
        assert fraction > 0.9, (
            fold + ": only " + format(fraction, ".3f") + " of test variants share a position with "
            "training, so this split is not as leaky as the file claims"
        )


def test_no_split_file_disagrees_with_the_clusters_on_ids() -> None:
    for threshold in (90, 70, 50):
        path = SPLITS_A / ("clusters_" + str(threshold) + ".tsv")
        with path.open(encoding="utf-8") as handle:
            cluster_ids = {r["id"] for r in csv.DictReader(handle, delimiter="\t")}
        split_ids = {r["id"] for r in read(SPLITS_A / "leave_one_family_out.csv")}
        assert cluster_ids == split_ids, (
            "clusters_" + str(threshold) + ".tsv and the split file disagree on the id set"
        )


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failures += 1
            print("FAIL " + test.__name__ + ": " + str(error))
        except Exception as error:  # noqa: BLE001
            failures += 1
            print("ERROR " + test.__name__ + ": " + type(error).__name__ + ": " + str(error))
        else:
            print("pass " + test.__name__)
    print("tests: " + str(len(tests)) + ", failures: " + str(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
