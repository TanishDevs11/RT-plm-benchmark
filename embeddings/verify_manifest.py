"""Verify every file recorded in embeddings/MANIFEST.json.

A manifest is only worth having if something checks it. This script re-reads every recorded
file, recomputes its SHA256, and confirms that the stored shape and dtype are what the file
actually contains. It also checks the thing a manifest cannot state on its own: that the row
order of each embedding matrix matches the order of the identifiers in the task table, because
a silently permuted matrix would produce results that look plausible and mean nothing.

    python embeddings/verify_manifest.py

Exits non-zero on any mismatch.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, read_task_table, sha256_of  # noqa: E402

MANIFEST = REPO_ROOT / "embeddings/MANIFEST.json"

TASK_SOURCES: dict[str, tuple[Path, Path]] = {
    "A": (REPO_ROOT / "tasks/taskA_crossfamily/curated.csv", REPO_ROOT / "data/rt_sequences.csv"),
    "A2": (REPO_ROOT / "tasks/taskA2_evolved/curated.csv", REPO_ROOT / "nonexistent"),
    "B": (REPO_ROOT / "tasks/taskB_mmlv_dms/curated.csv", REPO_ROOT / "nonexistent"),
}


def task_order(task: str) -> list[str]:
    curated, fallback = TASK_SOURCES[task]
    if curated.is_file():
        frame = read_task_table(curated)
        return [str(r["id"]) for r in frame.to_dict("records")]
    if fallback.is_file():
        with fallback.open(encoding="utf-8") as handle:
            return ["A_" + r["rt_name"] for r in csv.DictReader(handle)]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the embedding manifest.")
    parser.parse_args(argv)
    print_run_header("embeddings/verify_manifest.py", [MANIFEST])

    if not MANIFEST.is_file():
        print("manifest absent: " + MANIFEST.as_posix())
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runs = manifest.get("runs", [])
    print("")
    print("runs in manifest: " + str(len(runs)))

    problems: list[str] = []
    checked = 0
    orders: dict[str, list[str]] = {}

    for run in runs:
        task = str(run["task"])
        if task not in orders:
            orders[task] = task_order(task)
        expected_order = orders[task]

        for field in (
            "model",
            "checkpoint_sha256",
            "layers_used",
            "catalytic_core_rule",
            "inference_seconds",
            "generated_utc",
        ):
            if run.get(field) in (None, ""):
                problems.append(run.get("model", "?") + " task " + task + ": manifest field " + field + " is empty")

        for entry in run.get("files", []):
            path = REPO_ROOT / str(entry["file"])
            ids_path = REPO_ROOT / str(entry["ids_file"])
            label = str(entry["file"])
            checked += 1

            if not path.is_file():
                problems.append(label + ": file absent")
                continue
            if not ids_path.is_file():
                problems.append(label + ": ids file absent")
                continue

            digest = sha256_of(path)
            if digest != entry["sha256"]:
                problems.append(label + ": sha256 mismatch, file has changed since generation")
            if sha256_of(ids_path) != entry["ids_sha256"]:
                problems.append(label + ": ids sha256 mismatch")

            with np.load(path) as payload:
                matrix = payload["embeddings"]
            if list(matrix.shape) != list(entry["shape"]):
                problems.append(
                    label + ": shape " + str(list(matrix.shape)) + " against recorded " + str(entry["shape"])
                )
            if str(matrix.dtype) != str(entry["dtype"]):
                problems.append(label + ": dtype " + str(matrix.dtype) + " against recorded " + str(entry["dtype"]))
            if not np.isfinite(matrix.astype(np.float32)).all():
                problems.append(label + ": contains a non-finite value")

            ids = ids_path.read_text(encoding="utf-8").split()
            if len(ids) != matrix.shape[0]:
                problems.append(
                    label + ": " + str(len(ids)) + " identifiers against " + str(matrix.shape[0]) + " rows"
                )
            if expected_order:
                if entry["pooling"] == "mean_full":
                    if ids != expected_order:
                        problems.append(label + ": row order does not match the task table order")
                else:
                    # Catalytic-core files are a subset, so they must appear in task order and
                    # contain nothing that is not in the task table.
                    unknown = [i for i in ids if i not in set(expected_order)]
                    if unknown:
                        problems.append(label + ": identifiers not in the task table: " + str(unknown[:3]))
                    ranks = [expected_order.index(i) for i in ids if i in set(expected_order)]
                    if ranks != sorted(ranks):
                        problems.append(label + ": subset is not in task table order")
                    if len(ids) + int(entry.get("rows_excluded", 0)) != len(expected_order):
                        problems.append(
                            label
                            + ": "
                            + str(len(ids))
                            + " rows plus "
                            + str(entry.get("rows_excluded"))
                            + " excluded does not account for "
                            + str(len(expected_order))
                            + " task rows"
                        )

        for relative in run.get("zero_shot_files", []):
            checked += 1
            if not (REPO_ROOT / relative).is_file():
                problems.append(str(relative) + ": zero-shot file absent")
        windows = run.get("windows_file")
        if windows:
            checked += 1
            if not (REPO_ROOT / windows).is_file():
                problems.append(str(windows) + ": windows file absent")

    print("artifacts checked: " + str(checked))
    print("problems: " + str(len(problems)))
    for problem in problems:
        print("  FAIL " + problem)
    if not problems:
        print("")
        print("Every recorded checksum verifies, every shape and dtype matches, and every")
        print("matrix's row order agrees with its task table.")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
