"""Build the Task A ESM-2 representations: final layer, mean pooled, four model sizes.

Deliberately narrow. One pooling strategy, one layer per model, and no sweep of either.
A sweep over layers or pooling strategies is a selection decision, and a selection
decision made here would be made with the whole panel in view, including the rows a model
will later be tested on. It belongs in the inner loop of the modelling phase or nowhere.
`embeddings/build_embeddings.py` does extract mid-depth and catalytic-core variants for
the earlier single-task benchmark; those are not inputs to this one.

What "final layer, mean pooled over the full sequence" means exactly, since both halves
can be got wrong quietly:

  * the layer index is the model's last transformer block, 6 for 8M, 12 for 35M, 30 for
    150M and 33 for 650M, and it is recorded per file rather than inferred by a reader
  * the mean is over residue positions only. ESM-2 prepends a beginning-of-sequence token
    and appends an end-of-sequence token, so residue i of the sequence is token i + 1, and
    including those two tokens in the mean would mix two learned constants into every
    representation, with the largest effect on the shortest sequences

Row order is asserted against `curated.csv`, not assumed. An embedding matrix silently
permuted against its labels produces a plausible-looking result with no error anywhere.

    python embeddings/build_embeddings_taskA.py
    python embeddings/build_embeddings_taskA.py --sizes 8M 35M
    python embeddings/build_embeddings_taskA.py --force      # recompute existing files

Outputs:
    embeddings/esm2_<size>/taskA_v2_mean_full_final.npz
    embeddings/esm2_<size>/taskA_v2_mean_full_final_ids.txt
    embeddings/MANIFEST_TASKA.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import threading
import time
from datetime import date
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import library_versions, print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
EMBEDDINGS = REPO_ROOT / "embeddings"
MANIFEST = EMBEDDINGS / "MANIFEST_TASKA.json"

# Model name, the esm.pretrained loader, and the final transformer block index. The index
# is hardcoded rather than read from the model so that a mismatch is a loud failure here
# instead of a silently different layer in a file whose name claims otherwise.
MODELS: dict[str, tuple[str, int, int]] = {
    "8M": ("esm2_t6_8M_UR50D", 6, 320),
    "35M": ("esm2_t12_35M_UR50D", 12, 480),
    "150M": ("esm2_t30_150M_UR50D", 30, 640),
    "650M": ("esm2_t33_650M_UR50D", 33, 1280),
}

POOLING = "mean over residue positions, excluding the BOS and EOS tokens"
DTYPE = "float16"


class PeakMemory:
    """Sample this process's resident set size on a thread, and keep the maximum.

    torch does not track peak CPU allocation, so the honest measurement is the operating
    system's view of the process. Sampling can miss a spike shorter than the interval,
    which is why the manifest field is named `peak_rss_bytes_sampled`.
    """

    def __init__(self, interval: float = 0.05) -> None:
        self.interval = interval
        self.peak = 0
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "PeakMemory":
        try:
            import psutil
        except ImportError:
            self.peak = -1
            return self
        process = psutil.Process()

        def sample() -> None:
            while not self._stop.is_set():
                try:
                    self.peak = max(self.peak, process.memory_info().rss)
                except Exception:  # noqa: BLE001 - a dead process ends sampling
                    return
                self._stop.wait(self.interval)

        self._thread = threading.Thread(target=sample, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def load_curated() -> tuple[list[str], list[str]]:
    with CURATED.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [r["rt_name"] for r in rows], [r["sequence"] for r in rows]


def checkpoint_path(model_name: str) -> Path | None:
    import torch

    candidate = Path(torch.hub.get_dir()) / "checkpoints" / (model_name + ".pt")
    return candidate if candidate.is_file() else None


def embed_one(size: str, names: list[str], sequences: list[str], force: bool) -> dict:
    import esm
    import torch

    model_name, final_layer, expected_width = MODELS[size]
    out_dir = EMBEDDINGS / ("esm2_" + size)
    out_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = out_dir / "taskA_v2_mean_full_final.npz"
    ids_path = out_dir / "taskA_v2_mean_full_final_ids.txt"

    if matrix_path.is_file() and not force:
        print("  already present, skipping: " + matrix_path.name)
        print("  pass --force to recompute")
        return describe_existing(size, matrix_path, ids_path, final_layer, model_name)

    print("  loading " + model_name)
    started = time.time()
    with PeakMemory() as peak:
        model, alphabet = getattr(esm.pretrained, model_name)()
        model.eval()
        converter = alphabet.get_batch_converter()
        load_seconds = time.time() - started
        print("  loaded in " + format(load_seconds, ".1f") + "s")

        if model.num_layers != final_layer:
            raise SystemExit(
                model_name
                + " reports "
                + str(model.num_layers)
                + " layers but this script expects a final layer of "
                + str(final_layer)
                + "; refusing to write a file whose name would claim the wrong layer"
            )

        vectors: list[np.ndarray] = []
        inference_started = time.time()
        with torch.no_grad():
            for position, (name, sequence) in enumerate(zip(names, sequences), start=1):
                _, _, tokens = converter([(name, sequence)])
                out = model(tokens, repr_layers=[final_layer], return_contacts=False)
                representation = out["representations"][final_layer][0]
                # Residue i of the sequence is token i + 1: token 0 is BOS and the last
                # token is EOS. Both are excluded from the mean.
                residues = representation[1 : len(sequence) + 1]
                if residues.shape[0] != len(sequence):
                    raise SystemExit(
                        name
                        + ": sliced "
                        + str(residues.shape[0])
                        + " residue positions from a sequence of "
                        + str(len(sequence))
                    )
                vectors.append(residues.mean(0).cpu().numpy().astype(np.float32))
                if position % 10 == 0 or position == len(names):
                    print("    " + str(position) + " of " + str(len(names)))
                    sys.stdout.flush()
        inference_seconds = time.time() - inference_started
        del model
    total_seconds = time.time() - started

    matrix = np.vstack(vectors).astype(np.float16)
    if matrix.shape != (len(names), expected_width):
        raise SystemExit(
            "expected shape "
            + str((len(names), expected_width))
            + ", produced "
            + str(matrix.shape)
        )

    np.savez_compressed(matrix_path, embeddings=matrix)
    ids_path.write_text("\n".join(names) + "\n", encoding="utf-8")

    # The assertion the brief asks for, made against what was actually written rather
    # than against the in-memory list.
    written = ids_path.read_text(encoding="utf-8").split()
    if written != names:
        raise SystemExit("the ids file does not reproduce curated.csv row order")

    checkpoint = checkpoint_path(model_name)
    entry = {
        "model_name": model_name,
        "model_size": size,
        "checkpoint_file": checkpoint.name if checkpoint else "downloaded, not cached",
        "checkpoint_sha256": sha256_of(checkpoint) if checkpoint else None,
        "pooling": POOLING,
        "layer": final_layer,
        "layer_is_final": True,
        "n_layers": final_layer,
        "dtype": DTYPE,
        "shape": list(matrix.shape),
        "file": matrix_path.relative_to(REPO_ROOT).as_posix(),
        "file_sha256": sha256_of(matrix_path),
        "ids_file": ids_path.relative_to(REPO_ROOT).as_posix(),
        "ids_sha256": sha256_of(ids_path),
        "row_order": "exactly tasks/taskA_crossfamily/curated.csv, asserted after writing",
        "generated": date.today().isoformat(),
        "load_seconds": round(load_seconds, 2),
        "inference_seconds": round(inference_seconds, 2),
        "wall_clock_seconds": round(total_seconds, 2),
        "peak_rss_bytes_sampled": peak.peak,
        "peak_rss_gib_sampled": (
            round(peak.peak / (1 << 30), 3) if peak.peak > 0 else None
        ),
    }
    print(
        "  wrote "
        + matrix_path.relative_to(REPO_ROOT).as_posix()
        + " shape="
        + str(matrix.shape)
        + " in "
        + format(total_seconds, ".1f")
        + "s, peak RSS "
        + (format(peak.peak / (1 << 30), ".2f") + " GiB" if peak.peak > 0 else "unmeasured")
    )
    return entry


def describe_existing(
    size: str, matrix_path: Path, ids_path: Path, final_layer: int, model_name: str
) -> dict:
    payload = np.load(matrix_path)
    matrix = payload[list(payload.keys())[0]]
    return {
        "model_name": model_name,
        "model_size": size,
        "pooling": POOLING,
        "layer": final_layer,
        "dtype": str(matrix.dtype),
        "shape": list(matrix.shape),
        "file": matrix_path.relative_to(REPO_ROOT).as_posix(),
        "file_sha256": sha256_of(matrix_path),
        "ids_file": ids_path.relative_to(REPO_ROOT).as_posix(),
        "ids_sha256": sha256_of(ids_path),
        "note": "file already present; timings and peak memory belong to the run that "
        "produced it and are not reported here, because this run did not measure them",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes", nargs="*", default=list(MODELS), choices=list(MODELS)
    )
    parser.add_argument("--force", action="store_true", help="recompute existing files")
    args = parser.parse_args()

    print_run_header("embeddings/build_embeddings_taskA.py", [CURATED])
    names, sequences = load_curated()
    print("rows: " + str(len(names)))
    print("pooling: " + POOLING)
    print("no layer sweep and no pooling sweep: both are selection decisions")

    existing = {}
    if MANIFEST.is_file():
        existing = json.loads(MANIFEST.read_text(encoding="utf-8"))
    runs = {entry["model_size"]: entry for entry in existing.get("runs", [])}

    for size in args.sizes:
        print("")
        print("=== ESM-2 " + size + " ===")
        runs[size] = embed_one(size, names, sequences, args.force)
        MANIFEST.write_text(
            json.dumps(
                {
                    "task": "A",
                    "curated_csv": CURATED.relative_to(REPO_ROOT).as_posix(),
                    "curated_sha256": sha256_of(CURATED),
                    "library_versions": library_versions(),
                    "pooling": POOLING,
                    "layer_policy": "the model's final transformer block, no sweep",
                    "runs": [runs[k] for k in MODELS if k in runs],
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print("  manifest updated: " + MANIFEST.relative_to(REPO_ROOT).as_posix())

    print("")
    print("wrote " + MANIFEST.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
