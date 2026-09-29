"""Extract protein language model representations for the 57 reverse transcriptases.

Produces, per model, a mean-pooled embedding matrix. For one designated model it
also stores per-residue representations and a per-residue attention weight vector,
which the corrected-pooling variants in `bench/representations.py` need.

Everything is cached under bench/cache so the benchmark can be rerun without
repeating the forward passes. Extraction is model inference only: it involves no
labels at all, so caching it does not move any selection decision outside a fold.

Run directly to build the cache:

    python bench/embeddings.py
"""

from __future__ import annotations

import gc
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "bench" / "cache"

# name -> (fair-esm loader attribute, final layer index)
MODELS = {
    "esm2_8M": ("esm2_t6_8M_UR50D", 6),
    "esm2_35M": ("esm2_t12_35M_UR50D", 12),
    "esm2_150M": ("esm2_t30_150M_UR50D", 30),
    "esm2_650M": ("esm2_t33_650M_UR50D", 33),
    "esm1v": ("esm1v_t33_650M_UR90S_1", 33),
}

PER_RESIDUE_MODEL = "esm2_650M"
ATTENTION_MODEL = "esm2_150M"

# The RT catalytic core is anchored by the YXDD motif in the palm subdomain.
YXDD = re.compile(r"Y.DD")


def load_sequences():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    return seq["rt_name"].tolist(), [str(s).upper() for s in seq["sequence"]]


def catalytic_windows(names, seqs, flank=150):
    """Locate the YXDD motif and return a window around it per sequence.

    Every RT where the motif is absent is recorded explicitly rather than being
    silently given a default window, because a silent fallback would quietly turn
    a structural claim into a full-length pooling for an unknown subset.
    """
    windows, missing, multiple = {}, [], []
    for name, s in zip(names, seqs):
        hits = list(YXDD.finditer(s))
        if not hits:
            missing.append(name)
            windows[name] = (0, len(s))
            continue
        if len(hits) > 1:
            multiple.append(name)
        # The palm YXDD is the catalytic one; where several match, take the last,
        # which sits in the palm rather than in an N-terminal fingers repeat.
        m = hits[-1]
        lo = max(0, m.start() - flank)
        hi = min(len(s), m.end() + flank)
        windows[name] = (lo, hi)
    return windows, missing, multiple


def extract(model_key, names, seqs, want_per_residue=False, want_attention=False):
    import esm
    import torch

    loader_name, layer = MODELS[model_key]
    loader = getattr(esm.pretrained, loader_name)
    model, alphabet = loader()
    model.eval()
    converter = alphabet.get_batch_converter()

    pooled = np.zeros((len(names), model.embed_dim), dtype=np.float32)
    per_residue: dict[str, np.ndarray] = {}
    attention: dict[str, np.ndarray] = {}

    with torch.no_grad():
        for i, (name, s) in enumerate(zip(names, seqs)):
            _, _, toks = converter([(name, s)])
            out = model(
                toks,
                repr_layers=[layer],
                return_contacts=False,
                need_head_weights=bool(want_attention),
            )
            rep = out["representations"][layer][0, 1 : len(s) + 1]
            pooled[i] = rep.mean(0).numpy()
            if want_per_residue:
                per_residue[name] = rep.numpy().astype(np.float32)
            if want_attention:
                # Last layer, mean over heads, mean over query positions: how much
                # each residue is attended to by the rest of the sequence.
                att = out["attentions"][0, -1]
                w = att.mean(0).mean(0)[1 : len(s) + 1]
                attention[name] = w.numpy().astype(np.float32)
            del out
            if i % 10 == 0:
                print(f"    {model_key}: {i + 1}/{len(names)}", flush=True)

    del model
    gc.collect()
    return pooled, per_residue, attention


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    names, seqs = load_sequences()
    print(f"{len(names)} sequences, lengths {min(map(len, seqs))} to {max(map(len, seqs))}")

    windows, missing, multiple = catalytic_windows(names, seqs)
    (CACHE / "catalytic_windows.json").write_text(
        json.dumps(
            {
                "windows": {k: list(v) for k, v in windows.items()},
                "motif": "Y.DD",
                "flank": 150,
                "missing_motif": missing,
                "multiple_hits": multiple,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"YXDD motif: found in {len(names) - len(missing)}/{len(names)}")
    if missing:
        print(f"  motif NOT found in {len(missing)}: {', '.join(missing)}")
    if multiple:
        print(f"  multiple hits in {len(multiple)}: {', '.join(multiple)}")

    status = {}
    for key in MODELS:
        out_path = CACHE / f"pooled_{key}.npz"
        if out_path.exists():
            print(f"{key}: cached, skipping")
            status[key] = "cached"
            continue
        print(f"{key}: extracting")
        t = time.time()
        try:
            pooled, per_res, att = extract(
                key,
                names,
                seqs,
                want_per_residue=(key == PER_RESIDUE_MODEL),
                want_attention=(key == ATTENTION_MODEL),
            )
        except (RuntimeError, MemoryError, OSError) as exc:
            print(f"  FAILED: {type(exc).__name__}: {exc}")
            status[key] = f"FAILED: {type(exc).__name__}: {exc}"
            continue
        np.savez_compressed(out_path, names=np.array(names, dtype=object), embeddings=pooled)
        if per_res:
            np.savez_compressed(CACHE / f"per_residue_{key}.npz", **per_res)
        if att:
            np.savez_compressed(CACHE / f"attention_{key}.npz", **att)
        status[key] = f"ok in {time.time() - t:.1f}s"
        print(f"  {key}: {pooled.shape} in {time.time() - t:.1f}s")

    (CACHE / "extraction_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    print()
    for k, v in status.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
