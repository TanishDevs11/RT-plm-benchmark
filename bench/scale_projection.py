"""Quantify what collecting more labelled RTs would actually buy.

Two quantities decide whether this benchmark can resolve anything: the width of
the bootstrap interval, and how much CLS a search can manufacture from noise.
Both are functions of sample size. Projecting them to n = 100 and n = 200 turns
"we need more data" from an assertion into a number.

Method: resample the observed 57 RTs with replacement up to the target n, then
recompute both quantities on the enlarged set. This assumes new RTs would be drawn
from the same distribution of families and efficiencies as the current ones, which
is optimistic: a genuinely broader panel would likely be more heterogeneous. The
projection is therefore a best case, and it is labelled as one.

Outputs bench/results/scale_projection.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bench"))
sys.path.insert(0, str(ROOT / "evaluation"))

from evaluate import compute_cls  # noqa: E402
from search_null import de_blend_null, REFERENCE_K  # noqa: E402

SEED = 42
SIZES = [57, 100, 200]
N_NULL_REPEATS = 8
N_BOOTSTRAP = 4000


def grown_dataset(y, pe, n, rng):
    """Resample up to size n, keeping the observed rows when n exceeds them."""
    if n <= len(y):
        idx = rng.choice(len(y), size=n, replace=False)
    else:
        extra = rng.integers(0, len(y), size=n - len(y))
        idx = np.concatenate([np.arange(len(y)), extra])
    return y[idx], pe[idx]


def ci_width_at(y, pe, n, seed=SEED, draws=N_BOOTSTRAP):
    """Bootstrap interval width for a fixed informative score vector at size n."""
    rng = np.random.default_rng(seed)
    yg, peg = grown_dataset(y, pe, n, rng)
    # A fixed, moderately informative score: the true efficiency plus noise. The
    # absolute level does not matter here, only how tightly n pins it down.
    score = peg + rng.normal(0, 5, size=len(peg))
    vals = []
    for _ in range(draws):
        idx = rng.integers(0, len(yg), size=len(yg))
        yb = yg[idx]
        if yb.sum() == 0 or yb.sum() == len(yb):
            continue
        vals.append(compute_cls(yb, score[idx], peg[idx])["cls"])
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(hi - lo), float(np.median(vals))


def kish_ess(pe):
    w = np.asarray(pe, dtype=float) + 0.01
    return float(w.sum() ** 2 / np.square(w).sum())


def main():
    gt = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    y = gt["active"].to_numpy()
    pe = gt["pe_efficiency_pct"].to_numpy(dtype=float)

    print(f"seed={SEED}")
    rows = []
    for n in SIZES:
        rng = np.random.default_rng(SEED)
        yg, peg = grown_dataset(y, pe, n, rng)
        width, median = ci_width_at(y, pe, n)
        nulls = [
            de_blend_null(yg, peg, REFERENCE_K, seed=SEED + r, noise_seed=SEED + 500 + r)
            for r in range(N_NULL_REPEATS)
        ]
        nulls = np.asarray(nulls)
        row = {
            "n": n,
            "kish_ess": kish_ess(peg),
            "ci_width": width,
            "median_cls": median,
            "null_mean": float(nulls.mean()),
            "null_p95": float(np.percentile(nulls, 95)),
            "null_repeats": N_NULL_REPEATS,
        }
        rows.append(row)
        print(
            f"  n={n:4d}  ESS {row['kish_ess']:6.2f}  CI width {width:.4f}  "
            f"null mean {row['null_mean']:.4f}  null p95 {row['null_p95']:.4f}"
        )

    out = ROOT / "bench" / "results" / "scale_projection.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "seed": SEED,
                "note": (
                    "Projections resample the observed 57 RTs with replacement, so they "
                    "assume new data is drawn from the same family and efficiency "
                    "distribution. A genuinely broader panel would be more "
                    "heterogeneous, so these are best-case figures."
                ),
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
