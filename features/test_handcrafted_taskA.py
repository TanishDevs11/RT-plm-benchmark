"""Tests that the Task A feature matrices are aligned, raw, and honest about absence.

Runs as a plain script, and also under pytest:

    python features/test_handcrafted_taskA.py

A feature matrix is the join between the curated table and every model in the benchmark,
and a silent misalignment there is the worst defect available: nothing fails, every
downstream number is computed on labels belonging to the wrong rows, and the result looks
like a modelling finding. This repository has already been bitten by exactly that, when a
join on `rt_name` matched zero rows because one file carried a `-RT` suffix and the other
did not, and nine entirely missing columns were fed to a model that trained on nothing.

So row order is asserted against `curated.csv` rather than assumed, and the three
no-fitting rules are asserted too: nothing scaled, nothing imputed, nothing selected.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
OUT_DIR = REPO_ROOT / "features" / "handcrafted"
FEATURES = OUT_DIR / "taskA_features_v2.csv"
MASK = OUT_DIR / "taskA_missing_mask_v2.csv"


def read(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def present() -> bool:
    if not FEATURES.is_file():
        print("    skipped: " + FEATURES.name + " is not present")
        return False
    return True


def curated_names() -> list[str]:
    return [row["rt_name"] for row in read(CURATED)]


def block(rows: list[dict[str, str]], prefix: str) -> np.ndarray:
    columns = [c for c in rows[0] if c.startswith(prefix)]
    return np.array(
        [[float(row[c]) for c in columns] for row in rows], dtype=float
    )


def test_row_order_matches_the_curated_table() -> None:
    if not present():
        return
    rows = read(FEATURES)
    assert [r["rt_name"] for r in rows] == curated_names(), (
        "the feature matrix is not in curated.csv row order; every downstream label "
        "join would be wrong and nothing would fail"
    )


def test_mask_has_the_same_shape_and_columns() -> None:
    if not present():
        return
    features = read(FEATURES)
    mask = read(MASK)
    assert len(features) == len(mask)
    assert list(features[0].keys()) == list(mask[0].keys()), (
        "mask and feature column order differ, so the mask cannot be applied positionally"
    )
    assert [r["rt_name"] for r in mask] == [r["rt_name"] for r in features]


def test_length_agrees_with_the_curated_sequence_length() -> None:
    if not present():
        return
    declared = {r["rt_name"]: int(r["sequence_len"]) for r in read(CURATED)}
    for row in read(FEATURES):
        assert int(row["length"]) == declared[row["rt_name"]], row["rt_name"]


def test_nothing_is_scaled_the_compositions_still_sum_to_one() -> None:
    """A scaled or centred composition block would no longer sum to one per row."""
    if not present():
        return
    rows = read(FEATURES)
    for prefix in ("aac_", "dpc_", "rk3_"):
        totals = block(rows, prefix).sum(axis=1)
        assert np.allclose(totals, 1.0, atol=1e-6), (
            prefix + " rows do not sum to 1, so the block has been transformed"
        )


def test_nothing_is_imputed_absence_is_blank_and_masked() -> None:
    """A missing structural value must be an empty cell with a 1 in the mask, not a 0."""
    if not present():
        return
    features = read(FEATURES)
    mask = read(MASK)
    masked = 0
    for feature_row, mask_row in zip(features, mask):
        for column, value in feature_row.items():
            if column == "rt_name":
                continue
            flag = mask_row[column]
            if flag == "1":
                masked += 1
                assert value == "", (
                    feature_row["rt_name"]
                    + " "
                    + column
                    + " is masked as missing but carries the value "
                    + repr(value)
                    + "; an imputed zero is indistinguishable from a measured zero"
                )
            else:
                assert value != "", (
                    feature_row["rt_name"] + " " + column + " is blank but not masked"
                )
    assert masked > 0, "no cell is masked, which would mean the mask is not being written"


def test_kmer_blocks_are_aligned_and_match_their_frozen_vocabulary() -> None:
    if not present():
        return
    names = curated_names()
    for k in (3, 4):
        path = OUT_DIR / ("taskA_kmer" + str(k) + ".npz")
        vocabulary_path = OUT_DIR / ("taskA_kmer" + str(k) + "_vocabulary.txt")
        if not path.is_file():
            print("    skipped: " + path.name + " is not present")
            continue
        payload = np.load(path, allow_pickle=True)
        matrix = payload["features"]
        ids = [str(i) for i in payload["ids"]]
        vocabulary = vocabulary_path.read_text(encoding="utf-8").split()
        assert ids == names, path.name + " row order does not match curated.csv"
        assert matrix.shape[0] == len(names)
        assert matrix.shape[1] == len(vocabulary), (
            path.name
            + " has "
            + str(matrix.shape[1])
            + " columns against a frozen vocabulary of "
            + str(len(vocabulary))
        )
        assert vocabulary == sorted(vocabulary), "vocabulary is not in sorted order"
        assert all(len(kmer) == k for kmer in vocabulary), "a vocabulary entry is not a k-mer"
        assert np.allclose(matrix.sum(axis=1), 1.0, atol=1e-4), (
            path.name + " rows are not frequencies"
        )
        assert matrix.min() >= 0.0


def test_the_kmer_vocabulary_drops_only_never_observed_columns() -> None:
    """The documented rule: keep every k-mer seen at least once, drop only the rest."""
    if not present():
        return
    sequences = [row["sequence"] for row in read(CURATED)]
    for k in (3, 4):
        vocabulary_path = OUT_DIR / ("taskA_kmer" + str(k) + "_vocabulary.txt")
        if not vocabulary_path.is_file():
            continue
        observed = set()
        for sequence in sequences:
            for position in range(len(sequence) - k + 1):
                observed.add(sequence[position : position + k])
        frozen = set(vocabulary_path.read_text(encoding="utf-8").split())
        assert frozen == observed, (
            "k="
            + str(k)
            + ": the frozen vocabulary is not exactly the observed k-mers. Missing "
            + str(len(observed - frozen))
            + ", extra "
            + str(len(frozen - observed))
            + ". Any difference means a selection rule was applied beyond dropping "
            "never-observed columns"
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
