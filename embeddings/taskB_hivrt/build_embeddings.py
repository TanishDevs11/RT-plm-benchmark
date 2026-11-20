"""ESM-2 representations and zero-shot scores for the HIV-1 RT phenotype task.

Two products, from the same model load.

**Representations**, three per model, all from the final transformer block:

  `mean_full`        mean pooled over the whole sequence
  `resistance_pool`  mean pooled over the published HIVDB major resistance positions only
  `mutated_pool`     mean pooled over the positions where this isolate differs from
                     consensus B, falling back to the full mean when it differs nowhere

The layer index is fixed a priori per model and recorded. No layer sweep: a sweep is a
selection decision and belongs in the inner loop of the modelling phase.

**Zero-shot scores**, which need no training and may beat every trained model:

  `masked_marginal`  mask each position of the consensus B reference in turn, read
                     log P(mutant) minus log P(wild type) at that position, and sum over
                     the isolate's mutations
  `wt_marginal`      the same differences read from a single unmasked forward pass of the
                     reference

The masked-marginal is computed over the reference rather than per variant, which is the
standard construction and is what makes it affordable: 560 forward passes per model, one
per position, after which every isolate's score is a sum of precomputed terms. Computing
it per variant would be 4139 times more expensive for a score that is defined on the
wild-type context anyway.

    python embeddings/taskB_hivrt/build_embeddings.py --sizes 8M 35M
    python embeddings/taskB_hivrt/build_embeddings.py --sizes 650M

Outputs:
    embeddings/taskB_hivrt/esm2_<size>_<strategy>.npz
    embeddings/taskB_hivrt/esm2_<size>_zeroshot.csv
    embeddings/taskB_hivrt/MANIFEST.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import threading
import time
from datetime import date
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import library_versions, print_run_header, sha256_of  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_hivrt"
ISOLATES = TASK_DIR / "curated_isolates.csv"
REFERENCE = TASK_DIR / "reference.fasta"
OUT_DIR = REPO_ROOT / "embeddings" / "taskB_hivrt"
MANIFEST = OUT_DIR / "MANIFEST.json"

PRIMARY_DATASET = "filtered"
AA20 = "ACDEFGHIKLMNPQRSTVWY"

MODELS: dict[str, tuple[str, int, int]] = {
    "8M": ("esm2_t6_8M_UR50D", 6, 320),
    "35M": ("esm2_t12_35M_UR50D", 12, 480),
    "150M": ("esm2_t30_150M_UR50D", 30, 640),
    "650M": ("esm2_t33_650M_UR50D", 33, 1280),
}

# The published HIVDB major resistance positions, for the restricted pooling.
RESISTANCE_POSITIONS = sorted(
    {41, 65, 70, 74, 75, 151, 184, 210, 215} | {100, 101, 103, 106, 181, 188, 190, 230}
)

STRATEGIES = ("mean_full", "resistance_pool", "mutated_pool")


class PeakMemory:
    def __init__(self, interval: float = 0.1) -> None:
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
                except Exception:  # noqa: BLE001
                    return
                self._stop.wait(self.interval)

        self._thread = threading.Thread(target=sample, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *_exc) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def load_reference() -> str:
    return "".join(
        line.strip()
        for line in REFERENCE.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith(">")
    ).upper()


def load_isolates() -> list[dict]:
    with ISOLATES.open(encoding="utf-8") as handle:
        return [r for r in csv.DictReader(handle) if r["dataset"] == PRIMARY_DATASET]


def parse_mutations(field: str) -> list[tuple[int, str, str]]:
    out = []
    for token in (field or "").split(";"):
        token = token.strip()
        if len(token) < 3:
            continue
        position_text, wild, mutant = token[1:-1], token[0], token[-1]
        if position_text.isdigit() and mutant in AA20 and wild in AA20:
            out.append((int(position_text), wild, mutant))
    return out


def checkpoint_path(model_name: str):
    import torch

    candidate = Path(torch.hub.get_dir()) / "checkpoints" / (model_name + ".pt")
    return candidate if candidate.is_file() else None


def build(size: str, rows: list[dict], reference: str, force: bool) -> dict:
    import esm
    import torch

    model_name, final_layer, width = MODELS[size]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ids = [r["drug_class"] + ":" + r["isolate_id"] for r in rows]
    sequences = [r["sequence"] for r in rows]
    mutations = [parse_mutations(r["mutations"]) for r in rows]

    existing = OUT_DIR / ("esm2_" + size + "_mean_full.npz")
    if existing.is_file() and not force:
        print("  already present, skipping; pass --force to recompute")
        return {}

    print("  loading " + model_name)
    started = time.time()
    with PeakMemory() as peak:
        model, alphabet = getattr(esm.pretrained, model_name)()
        model.eval()
        converter = alphabet.get_batch_converter()
        if model.num_layers != final_layer:
            raise SystemExit(
                model_name + " reports " + str(model.num_layers) + " layers, expected "
                + str(final_layer)
            )
        load_seconds = time.time() - started
        print("  loaded in " + format(load_seconds, ".1f") + "s")

        # Zero-shot, over the reference only. One masked pass per position, plus one
        # unmasked pass. Every isolate's score is then a sum of precomputed terms.
        print("  zero-shot: " + str(len(reference)) + " masked passes over the reference")
        log_softmax = torch.nn.functional.log_softmax
        masked_table = np.zeros((len(reference), len(AA20)), dtype=np.float32)
        wt_table = np.zeros((len(reference), len(AA20)), dtype=np.float32)
        aa_index = {a: alphabet.get_idx(a) for a in AA20}
        zero_started = time.time()
        with torch.no_grad():
            _, _, tokens = converter([("ref", reference)])
            out = model(tokens, repr_layers=[], return_contacts=False)
            logits = log_softmax(out["logits"][0], dim=-1)
            for position in range(len(reference)):
                for column, residue in enumerate(AA20):
                    wt_table[position, column] = float(logits[position + 1, aa_index[residue]])
            for position in range(len(reference)):
                masked = tokens.clone()
                masked[0, position + 1] = alphabet.mask_idx
                out = model(masked, repr_layers=[], return_contacts=False)
                row = log_softmax(out["logits"][0, position + 1], dim=-1)
                for column, residue in enumerate(AA20):
                    masked_table[position, column] = float(row[aa_index[residue]])
                if (position + 1) % 100 == 0:
                    print("    masked " + str(position + 1) + " of " + str(len(reference)))
                    sys.stdout.flush()
        zero_seconds = time.time() - zero_started

        column_of = {residue: index for index, residue in enumerate(AA20)}
        zero_rows = []
        for identifier, muts in zip(ids, mutations):
            masked_score = 0.0
            wt_score = 0.0
            for position, wild, mutant in muts:
                if not (1 <= position <= len(reference)):
                    continue
                index = position - 1
                masked_score += float(
                    masked_table[index, column_of[mutant]] - masked_table[index, column_of[wild]]
                )
                wt_score += float(
                    wt_table[index, column_of[mutant]] - wt_table[index, column_of[wild]]
                )
            zero_rows.append(
                {
                    "unit": identifier,
                    "n_mutations_scored": len(muts),
                    "masked_marginal": format(masked_score, ".6f"),
                    "wt_marginal": format(wt_score, ".6f"),
                }
            )

        # Representations.
        print("  representations: " + str(len(sequences)) + " sequences")
        pooled: dict[str, list[np.ndarray]] = {s: [] for s in STRATEGIES}
        inference_started = time.time()
        with torch.no_grad():
            for index, (sequence, muts) in enumerate(zip(sequences, mutations), start=1):
                _, _, tokens = converter([("x", sequence)])
                out = model(tokens, repr_layers=[final_layer], return_contacts=False)
                representation = out["representations"][final_layer][0]
                residues = representation[1 : len(sequence) + 1]
                pooled["mean_full"].append(residues.mean(0).cpu().numpy().astype(np.float32))
                resistance = [p - 1 for p in RESISTANCE_POSITIONS if p <= len(sequence)]
                pooled["resistance_pool"].append(
                    residues[resistance].mean(0).cpu().numpy().astype(np.float32)
                )
                positions = [p - 1 for p, _, _ in muts if 1 <= p <= len(sequence)]
                if positions:
                    pooled["mutated_pool"].append(
                        residues[positions].mean(0).cpu().numpy().astype(np.float32)
                    )
                else:
                    pooled["mutated_pool"].append(
                        residues.mean(0).cpu().numpy().astype(np.float32)
                    )
                if index % 250 == 0:
                    print("    " + str(index) + " of " + str(len(sequences)))
                    sys.stdout.flush()
        inference_seconds = time.time() - inference_started
        del model
    total_seconds = time.time() - started

    entry: dict = {
        "model_name": model_name,
        "model_size": size,
        "layer": final_layer,
        "layer_is_final": True,
        "dtype": "float16",
        "n_rows": len(ids),
        "dataset": PRIMARY_DATASET,
        "generated": date.today().isoformat(),
        "load_seconds": round(load_seconds, 2),
        "zero_shot_seconds": round(zero_seconds, 2),
        "representation_seconds": round(inference_seconds, 2),
        "wall_clock_seconds": round(total_seconds, 2),
        "peak_rss_gib_sampled": round(peak.peak / (1 << 30), 3) if peak.peak > 0 else None,
        "resistance_positions": RESISTANCE_POSITIONS,
        "files": {},
    }
    checkpoint = checkpoint_path(model_name)
    if checkpoint:
        entry["checkpoint_file"] = checkpoint.name
        entry["checkpoint_sha256"] = sha256_of(checkpoint)

    for strategy in STRATEGIES:
        matrix = np.vstack(pooled[strategy]).astype(np.float16)
        if matrix.shape != (len(ids), width):
            raise SystemExit("unexpected shape " + str(matrix.shape) + " for " + strategy)
        path = OUT_DIR / ("esm2_" + size + "_" + strategy + ".npz")
        np.savez_compressed(
            path, features=matrix, ids=np.array(ids, dtype=object)
        )
        entry["files"][strategy] = {
            "file": path.relative_to(REPO_ROOT).as_posix(),
            "shape": list(matrix.shape),
            "sha256": sha256_of(path),
        }
        print("  wrote " + path.name + " " + str(matrix.shape))

    zero_path = OUT_DIR / ("esm2_" + size + "_zeroshot.csv")
    with zero_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["unit", "n_mutations_scored", "masked_marginal", "wt_marginal"]
        )
        writer.writeheader()
        writer.writerows(zero_rows)
    entry["files"]["zeroshot"] = {
        "file": zero_path.relative_to(REPO_ROOT).as_posix(),
        "rows": len(zero_rows),
        "sha256": sha256_of(zero_path),
    }
    print("  wrote " + zero_path.name + ", " + str(len(zero_rows)) + " rows")
    print(
        "  timing: zero-shot "
        + format(zero_seconds, ".0f")
        + "s, representations "
        + format(inference_seconds, ".0f")
        + "s, peak RSS "
        + (format(peak.peak / (1 << 30), ".2f") + " GiB" if peak.peak > 0 else "unmeasured")
    )
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", nargs="*", default=["8M"], choices=list(MODELS))
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    print_run_header("embeddings/taskB_hivrt/build_embeddings.py", [ISOLATES, REFERENCE])
    reference = load_reference()
    rows = load_isolates()
    print("reference: " + str(len(reference)) + " residues")
    print("isolates: " + str(len(rows)) + " (" + PRIMARY_DATASET + ")")
    print("strategies: " + ", ".join(STRATEGIES))
    print("no layer sweep: the final block only, recorded per model")

    manifest: dict = {"task": "B_hivrt", "runs": {}}
    if MANIFEST.is_file():
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest.setdefault("runs", {})
    manifest["library_versions"] = library_versions()
    manifest["isolates_sha256"] = sha256_of(ISOLATES)

    for size in args.sizes:
        print("")
        print("=== ESM-2 " + size + " ===")
        entry = build(size, rows, reference, args.force)
        if entry:
            manifest["runs"][size] = entry
            MANIFEST.write_text(
                json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            print("  manifest updated")

    print("")
    print("wrote " + MANIFEST.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
