"""Generate protein language model representations, one set of matrices per task.

Scope of this run
-----------------
ESM-2 at 8M, 35M, 150M, and 650M parameters. ESM-1v and ProtT5-XL-U50 are not included: the
ESM-1v checkpoint in the local cache is a partial download and ProtT5 needs the `transformers`
package, which is absent. Their main purpose in the brief is the Task B zero-shot variant
effect baseline, and Task B has no labels, so nothing is lost by deferring them. The gap is
recorded in `embeddings/MANIFEST.json` and in the pipeline report rather than papered over.

Layers, fixed a priori
----------------------
Two per model: the final layer, and a mid-depth layer at floor(n_layers / 2). Both indices are
recorded per file. There is no layer sweep here, deliberately: choosing a layer by how it
scores is a selection decision and belongs in the inner loop of the modelling phase.

| model | layers | final | mid-depth |
| --- | --- | --- | --- |
| esm2_t6_8M_UR50D | 6 | 6 | 3 |
| esm2_t12_35M_UR50D | 12 | 12 | 6 |
| esm2_t30_150M_UR50D | 30 | 30 | 15 |
| esm2_t33_650M_UR50D | 33 | 33 | 16 |

Pooling, stored separately and never averaged together
------------------------------------------------------
1. `mean_full`: mean over every residue position, excluding the beginning-of-sequence and
   end-of-sequence tokens.

2. `catalytic_core`: mean over a window anchored on the YXDD catalytic motif. The window is
   `[y - 200, y + 140)` in one-based residue coordinates, clipped to the sequence, where `y` is
   the position of the Y in the first YXDD match.

   The offsets are derived from M-MLV RT rather than chosen freely. In the 677-residue M-MLV RT
   frame the YXDD motif begins at residue 222, which puts the catalytic aspartates at 224 and
   225, and the polymerase domain carrying fingers, palm, and thumb runs to roughly residue
   360. So 221 residues precede the motif and about 138 follow it, and `[y - 200, y + 140)`
   approximates that span while anchoring on a motif that can actually be located in an
   arbitrary RT. For M-MLV this gives residues 22 to 361.

   The motif is absent in 7 of the 57 Task A sequences. Those rows are excluded from the
   catalytic-core files rather than pooled over a guessed window, every one of them is logged
   by name, and the window or the reason for its absence is recorded per sequence in
   `catalytic_core_windows.json`. Abi-RT has more than one YXDD match and the first is used,
   which is also recorded.

Zero-shot scores
----------------
Sequence log-likelihood from a single forward pass: at each position, the log probability the
model assigns to the residue actually present, summed over the sequence and also divided by
length. This is the single-pass, unmasked quantity, and it is named that way in every file and
column. It is **not** the masked-marginal pseudo-log-likelihood, which needs one forward pass
per position: for 57 sequences averaging 450 residues that is about 25,000 forward passes per
model, which is not viable for the 650M model on this CPU. `--masked-pll` computes the true
masked-marginal quantity for a named model, and is run for the 8M model so the two can be
compared and the approximation quantified rather than assumed.

The ESM-1v masked-marginal variant effect scores the brief requires exist only for Task B
variants, so they are deferred with Task B.

    python embeddings/build_embeddings.py
    python embeddings/build_embeddings.py --models 8M --masked-pll
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import (  # noqa: E402
    GLOBAL_SEED,
    library_versions,
    print_run_header,
    read_task_table,
    sha256_of,
)

OUT_ROOT = REPO_ROOT / "embeddings"
MANIFEST = OUT_ROOT / "MANIFEST.json"

MODELS: dict[str, tuple[str, int]] = {
    "8M": ("esm2_t6_8M_UR50D", 6),
    "35M": ("esm2_t12_35M_UR50D", 12),
    "150M": ("esm2_t30_150M_UR50D", 30),
    "650M": ("esm2_t33_650M_UR50D", 33),
}

# Catalytic-core window offsets, in residues, relative to the Y of the YXDD motif. Derived
# from M-MLV RT as set out in the module docstring; fixed a priori.
CORE_BEFORE = 200
CORE_AFTER = 140
YXDD = re.compile("Y.DD")

TASK_SOURCES: dict[str, tuple[Path, Path]] = {
    "A": (REPO_ROOT / "tasks/taskA_crossfamily/curated.csv", REPO_ROOT / "data/rt_sequences.csv"),
    "A2": (REPO_ROOT / "tasks/taskA2_evolved/curated.csv", REPO_ROOT / "nonexistent"),
    "B": (REPO_ROOT / "tasks/taskB_mmlv_dms/curated.csv", REPO_ROOT / "nonexistent"),
}


def load_task(task: str) -> tuple[list[tuple[str, str]], str]:
    curated, fallback = TASK_SOURCES[task]
    if curated.is_file():
        frame = read_task_table(curated)
        return (
            [(str(r["id"]), str(r["sequence"]).strip().upper()) for r in frame.to_dict("records")],
            "curated.csv",
        )
    if fallback.is_file():
        with fallback.open(encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
        return (
            [("A_" + r["rt_name"], r["sequence"].strip().upper()) for r in records],
            "PROVISIONAL, from " + fallback.relative_to(REPO_ROOT).as_posix(),
        )
    return [], "absent"


def core_window(sequence: str) -> tuple[int, int, str] | None:
    """Return (start, end, note) as zero-based half-open residue indices, or None."""
    matches = list(YXDD.finditer(sequence))
    if not matches:
        return None
    y = matches[0].start()  # zero based index of the Y
    start = max(0, y - CORE_BEFORE)
    end = min(len(sequence), y + CORE_AFTER)
    note = "YXDD at residue " + str(y + 1)
    if len(matches) > 1:
        note += "; " + str(len(matches)) + " matches, first used"
    return start, end, note


def peak_memory_mib() -> float | None:
    try:
        import psutil

        return float(psutil.Process(os.getpid()).memory_info().rss) / (1024 * 1024)
    except Exception:  # noqa: BLE001
        return None


def checkpoint_path(model_name: str) -> Path | None:
    candidate = Path(torch.hub.get_dir()) / "checkpoints" / (model_name + ".pt")
    return candidate if candidate.is_file() else None


def write_npz(path: Path, ids: list[str], matrix: np.ndarray) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    half = matrix.astype(np.float16)
    np.savez_compressed(path, embeddings=half)
    ids_path = path.with_name(path.stem + "_ids.txt")
    ids_path.write_text("\n".join(ids) + "\n", encoding="utf-8")
    return {
        "file": path.relative_to(REPO_ROOT).as_posix(),
        "ids_file": ids_path.relative_to(REPO_ROOT).as_posix(),
        "dtype": "float16",
        "shape": list(half.shape),
        "sha256": sha256_of(path),
        "ids_sha256": sha256_of(ids_path),
    }


def run_model(
    size: str, task: str, rows: list[tuple[str, str]], manifest: dict[str, object], masked_pll: bool
) -> None:
    import esm

    model_name, n_layers = MODELS[size]
    final_layer = n_layers
    mid_layer = n_layers // 2
    out_dir = OUT_ROOT / ("esm2_" + size)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("")
    print("=== esm2 " + size + ", task " + task + " ===")
    print("  layers: final " + str(final_layer) + ", mid-depth " + str(mid_layer))

    started = time.time()
    model, alphabet = getattr(esm.pretrained, model_name)()
    model.eval()
    converter = alphabet.get_batch_converter()
    load_seconds = time.time() - started
    checkpoint = checkpoint_path(model_name)
    print("  loaded in " + format(load_seconds, ".1f") + "s from " + (checkpoint.name if checkpoint else "download"))

    ids = [identifier for identifier, _ in rows]
    windows: dict[str, object] = {}
    pooled: dict[tuple[int, str], list[np.ndarray]] = {
        (layer, strategy): []
        for layer in (final_layer, mid_layer)
        for strategy in ("mean_full", "catalytic_core")
    }
    core_ids: list[str] = []
    no_motif: list[str] = []
    pll_rows: list[dict[str, object]] = []

    inference_started = time.time()
    with torch.no_grad():
        for position, (identifier, sequence) in enumerate(rows, start=1):
            _, _, tokens = converter([(identifier, sequence)])
            out = model(tokens, repr_layers=[final_layer, mid_layer], return_contacts=False)

            # Token 0 is the beginning-of-sequence token and the final token is
            # end-of-sequence, so residue i of the sequence is token i + 1.
            residue_slice = slice(1, len(sequence) + 1)

            window = core_window(sequence)
            if window is None:
                no_motif.append(identifier)
                windows[identifier] = {"found": False, "reason": "no YXDD match"}
            else:
                start, end, note = window
                core_ids.append(identifier)
                windows[identifier] = {
                    "found": True,
                    "start_1based": start + 1,
                    "end_1based": end,
                    "length": end - start,
                    "note": note,
                }

            for layer in (final_layer, mid_layer):
                representation = out["representations"][layer][0]
                pooled[(layer, "mean_full")].append(
                    representation[residue_slice].mean(0).cpu().numpy()
                )
                if window is not None:
                    start, end, _ = window
                    pooled[(layer, "catalytic_core")].append(
                        representation[1 + start : 1 + end].mean(0).cpu().numpy()
                    )

            logits = out["logits"][0]
            log_probs = torch.log_softmax(logits, dim=-1)
            observed = tokens[0][residue_slice]
            per_position = log_probs[residue_slice].gather(1, observed.unsqueeze(1)).squeeze(1)
            total = float(per_position.sum())
            pll_rows.append(
                {
                    "id": identifier,
                    "sequence_len": len(sequence),
                    "singlepass_loglik_sum": total,
                    "singlepass_loglik_per_residue": total / len(sequence),
                }
            )

            if position % 10 == 0 or position == len(rows):
                print("    " + str(position) + "/" + str(len(rows)) + " sequences")

    inference_seconds = time.time() - inference_started
    peak = peak_memory_mib()

    entries: list[dict[str, object]] = []
    for (layer, strategy), vectors in pooled.items():
        if not vectors:
            continue
        row_ids = ids if strategy == "mean_full" else core_ids
        matrix = np.vstack(vectors)
        if matrix.shape[0] != len(row_ids):
            raise RuntimeError(
                "row count " + str(matrix.shape[0]) + " does not match id count " + str(len(row_ids))
            )
        path = out_dir / ("task" + task + "_" + strategy + "_layer" + str(layer) + ".npz")
        entry = write_npz(path, row_ids, matrix)
        entry.update(
            {
                "model": model_name,
                "model_size": size,
                "task": task,
                "pooling": strategy,
                "layer": layer,
                "layer_role": "final" if layer == final_layer else "mid_depth",
                "n_layers": n_layers,
                "rows_excluded": len(ids) - len(row_ids),
            }
        )
        entries.append(entry)
        print("  wrote " + entry["file"] + " shape " + str(entry["shape"]))

    pll_path = out_dir / ("task" + task + "_zeroshot_singlepass_loglik.csv")
    with pll_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["id", "sequence_len", "singlepass_loglik_sum", "singlepass_loglik_per_residue"],
        )
        writer.writeheader()
        writer.writerows(pll_rows)
    print("  wrote " + pll_path.relative_to(REPO_ROOT).as_posix())

    if masked_pll:
        print("  computing true masked-marginal pseudo-log-likelihood, one pass per position")
        masked_path = out_dir / ("task" + task + "_zeroshot_masked_marginal_pll.csv")
        masked_rows: list[dict[str, object]] = []
        masked_started = time.time()
        with torch.no_grad():
            for position, (identifier, sequence) in enumerate(rows, start=1):
                _, _, tokens = converter([(identifier, sequence)])
                total = 0.0
                for index in range(len(sequence)):
                    masked = tokens.clone()
                    masked[0, index + 1] = alphabet.mask_idx
                    out = model(masked, repr_layers=[], return_contacts=False)
                    log_probs = torch.log_softmax(out["logits"][0, index + 1], dim=-1)
                    total += float(log_probs[tokens[0, index + 1]])
                masked_rows.append(
                    {
                        "id": identifier,
                        "sequence_len": len(sequence),
                        "masked_marginal_pll_sum": total,
                        "masked_marginal_pll_per_residue": total / len(sequence),
                    }
                )
                print("    " + str(position) + "/" + str(len(rows)) + " " + identifier)
        with masked_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=[
                    "id",
                    "sequence_len",
                    "masked_marginal_pll_sum",
                    "masked_marginal_pll_per_residue",
                ],
            )
            writer.writeheader()
            writer.writerows(masked_rows)
        print("  wrote " + masked_path.relative_to(REPO_ROOT).as_posix())
        print("  masked-marginal wall clock " + format(time.time() - masked_started, ".1f") + "s")

    windows_path = out_dir / ("task" + task + "_catalytic_core_windows.json")
    windows_path.write_text(json.dumps(windows, indent=2, sort_keys=True), encoding="utf-8")
    print("  wrote " + windows_path.relative_to(REPO_ROOT).as_posix())
    if no_motif:
        print("  YXDD motif NOT found in " + str(len(no_motif)) + " sequences, excluded from")
        print("  the catalytic-core files rather than pooled over a guessed window:")
        for identifier in no_motif:
            print("    " + identifier)

    # Replace any earlier entry for this model and task rather than appending, so a rerun
    # updates the manifest instead of leaving two contradictory records of the same files.
    runs = manifest.setdefault("runs", [])
    runs[:] = [r for r in runs if not (r.get("model") == model_name and r.get("task") == task)]
    runs.append(
        {
            "model": model_name,
            "model_size": size,
            "task": task,
            "checkpoint_file": checkpoint.name if checkpoint else None,
            "checkpoint_sha256": sha256_of(checkpoint) if checkpoint else None,
            "n_layers": n_layers,
            "layers_used": {"final": final_layer, "mid_depth": mid_layer},
            "catalytic_core_rule": {
                "motif": "Y.DD",
                "residues_before_motif": CORE_BEFORE,
                "residues_after_motif": CORE_AFTER,
                "sequences_without_motif": no_motif,
            },
            "n_sequences": len(rows),
            "n_sequences_with_motif": len(core_ids),
            "load_seconds": round(load_seconds, 2),
            "inference_seconds": round(inference_seconds, 2),
            "seconds_per_sequence": round(inference_seconds / max(1, len(rows)), 3),
            "peak_rss_mib": round(peak, 1) if peak else None,
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "files": entries,
            "zero_shot_files": (
                [pll_path.relative_to(REPO_ROOT).as_posix()]
                + ([masked_path.relative_to(REPO_ROOT).as_posix()] if masked_pll else [])
            ),
            "windows_file": windows_path.relative_to(REPO_ROOT).as_posix(),
        }
    )

    del model
    print("  inference wall clock " + format(inference_seconds, ".1f") + "s, "
          + format(inference_seconds / max(1, len(rows)), ".2f") + "s per sequence"
          + (", peak RSS " + format(peak, ".0f") + " MiB" if peak else ""))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build protein language model embeddings.")
    parser.add_argument("--models", default="all", help="comma separated: 8M,35M,150M,650M or all")
    parser.add_argument("--tasks", default="all", help="comma separated task ids, or all")
    parser.add_argument(
        "--masked-pll",
        action="store_true",
        help="also compute the true masked-marginal pseudo-log-likelihood; slow",
    )
    args = parser.parse_args(argv)

    torch.manual_seed(GLOBAL_SEED)
    torch.set_grad_enabled(False)
    print_run_header("embeddings/build_embeddings.py")
    print("torch threads: " + str(torch.get_num_threads()))

    sizes = list(MODELS) if args.models == "all" else [s.strip() for s in args.models.split(",")]
    tasks = list(TASK_SOURCES) if args.tasks == "all" else [t.strip() for t in args.tasks.split(",")]

    manifest: dict[str, object] = {}
    if MANIFEST.is_file():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["library_versions"] = library_versions()
    manifest["seed"] = GLOBAL_SEED
    manifest.setdefault("runs", [])
    manifest["not_generated"] = {
        "esm1v": (
            "the local checkpoint is a partial download; its purpose in the brief is the Task B "
            "masked-marginal variant effect baseline, and Task B has no labels yet"
        ),
        "prott5_xl_u50": "requires the transformers package, which is not installed",
        "inverse_folding": (
            "ESM-IF and ProteinMPNN not run; structures exist for 56 of 57 Task A rows but their "
            "modelling provenance is undocumented, so an inverse-folding likelihood over them "
            "would carry an unknown dependency"
        ),
    }

    for task in tasks:
        rows, note = load_task(task)
        print("")
        print("task " + task + ": " + str(len(rows)) + " sequences, source " + note)
        if not rows:
            continue
        if note.startswith("PROVISIONAL"):
            print("  identifiers are provisional; only sequences are used and they are final")
        for size in sizes:
            run_model(size, task, rows, manifest, args.masked_pll)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print("")
    print("wrote " + MANIFEST.relative_to(REPO_ROOT).as_posix())
    print("runs recorded: " + str(len(manifest["runs"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
