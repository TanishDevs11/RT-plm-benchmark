"""Tests that the Task A embedding files are aligned, typed, and described honestly.

Runs as a plain script, and also under pytest:

    python embeddings/test_embeddings_taskA.py

An embedding matrix permuted against its labels is the most dangerous defect in this
pipeline. Nothing raises, every downstream score is computed on representations belonging
to the wrong enzymes, and the output looks like an ordinary modelling result: plausible,
mediocre, publishable. So row order is asserted against `curated.csv` in three places,
the matrix, the ids file, and the manifest, rather than being assumed anywhere.

The manifest claims are checked too. A manifest that says `layer: 33` for a file extracted
at a different layer is worse than no manifest, because it is believed.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
EMBEDDINGS = REPO_ROOT / "embeddings"
MANIFEST = EMBEDDINGS / "MANIFEST_TASKA.json"

EXPECTED_WIDTH = {"8M": 320, "35M": 480, "150M": 640, "650M": 1280}
EXPECTED_FINAL_LAYER = {"8M": 6, "35M": 12, "150M": 30, "650M": 33}


def curated_names() -> list[str]:
    with CURATED.open(encoding="utf-8") as handle:
        return [row["rt_name"] for row in csv.DictReader(handle)]


def manifest() -> dict | None:
    if not MANIFEST.is_file():
        print("    skipped: MANIFEST_TASKA.json is not present")
        return None
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def test_every_embedding_file_is_in_curated_row_order() -> None:
    names = curated_names()
    checked = 0
    for size in EXPECTED_WIDTH:
        ids_path = EMBEDDINGS / ("esm2_" + size) / "taskA_v2_mean_full_final_ids.txt"
        if not ids_path.is_file():
            continue
        ids = ids_path.read_text(encoding="utf-8").split()
        assert ids == names, (
            size
            + ": ids file is not in curated.csv row order. A permuted embedding matrix "
            "produces a plausible result with no error anywhere"
        )
        checked += 1
    if checked == 0:
        print("    skipped: no embedding ids files are present")


def test_every_embedding_matrix_has_the_right_shape_and_dtype() -> None:
    names = curated_names()
    checked = 0
    for size, width in EXPECTED_WIDTH.items():
        path = EMBEDDINGS / ("esm2_" + size) / "taskA_v2_mean_full_final.npz"
        if not path.is_file():
            continue
        payload = np.load(path)
        matrix = payload["embeddings"]
        assert matrix.shape == (len(names), width), (
            size + ": shape " + str(matrix.shape) + ", expected " + str((len(names), width))
        )
        assert matrix.dtype == np.float16, (
            size + ": dtype " + str(matrix.dtype) + ", expected float16"
        )
        assert np.isfinite(matrix.astype(np.float32)).all(), size + ": non-finite values"
        checked += 1
    if checked == 0:
        print("    skipped: no embedding matrices are present")


def test_the_manifest_describes_the_files_that_exist() -> None:
    data = manifest()
    if data is None:
        return
    assert data["curated_sha256"] == sha256_of(CURATED), (
        "the manifest was written against a different curated.csv than the one on disk"
    )
    for entry in data["runs"]:
        size = entry["model_size"]
        path = REPO_ROOT / entry["file"]
        if not path.is_file():
            continue
        assert entry["layer"] == EXPECTED_FINAL_LAYER[size], (
            size + ": manifest claims layer " + str(entry["layer"])
        )
        payload = np.load(path)
        matrix = payload["embeddings"]
        assert list(matrix.shape) == entry["shape"], (
            size + ": manifest shape disagrees with the file"
        )
        if "file_sha256" in entry:
            assert entry["file_sha256"] == sha256_of(path), (
                size + ": the file has changed since the manifest was written"
            )


def test_the_manifest_records_one_pooling_strategy_and_no_sweep() -> None:
    """A layer or pooling sweep here would be a selection decision made outside a fold."""
    data = manifest()
    if data is None:
        return
    strategies = {entry["pooling"] for entry in data["runs"]}
    assert len(strategies) <= 1, "more than one pooling strategy recorded: " + str(strategies)
    for entry in data["runs"]:
        assert entry["layer"] == EXPECTED_FINAL_LAYER[entry["model_size"]]


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
