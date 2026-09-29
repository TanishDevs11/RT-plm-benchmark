"""Search-capacity null: how much CLS a search can manufacture from noise.

Given a selection procedure with K free parameters and a search budget B, the
search-capacity null runs that procedure unchanged on K vectors of pure Gaussian
noise and records the CLS it reaches. Nothing in those vectors carries information
about activity, so whatever the search attains is what the procedure can
manufacture from nothing on this dataset with this metric.

This is the instrument the whole project turns on. A headline score printed
without its null has reported nothing, because the reader cannot tell the signal
from the search.

Reference configuration mirrors the inherited `fast_opt.py` exactly: 29 vectors,
weight bounds [-1.5, 1.5], power in [0.2, 1.5], maxiter 260, popsize 10, seed 42,
polish disabled, deferred updating. One deviation is deliberate and noted in the
report: `fast_opt.py` seeds its starting point from previously fitted constants,
which cannot be done for noise. The null therefore searches from scratch, which
can only understate it.

Outputs bench/results/search_null.json and bench/figures/search_null_capacity.png.
"""

from __future__ import annotations

import json
import platform
import sys
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import scipy
from scipy.optimize import differential_evolution
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evaluation"))
from evaluate import compute_cls  # noqa: E402

SEED = 42
REFERENCE_K = 29
REFERENCE_MAXITER = 260
REFERENCE_POPSIZE = 10
REFERENCE_EXPECTED = 0.848
REFERENCE_TOLERANCE = 0.05
WEIGHT_BOUND = 1.5
POWER_LOW = 0.2
POWER_HIGH = 1.5

K_SWEEP = [1, 2, 5, 10, 20, 29, 50]
BUDGET_SWEEP = [10, 30, 60, 130, 260]


def _rank_percentile(values, n):
    v = np.nan_to_num(np.asarray(values, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
    return rankdata(v, method="average") / (n + 1.0)


def de_blend_null(
    y_true,
    pe,
    k,
    maxiter=REFERENCE_MAXITER,
    popsize=REFERENCE_POPSIZE,
    seed=SEED,
    noise_seed=None,
):
    """Run the inherited blend search on k pure-noise vectors.

    Returns the best CLS the optimizer reached. The optimizer is given exactly the
    freedom the inherited one had: one weight per vector plus a shared power
    exponent.
    """
    n = len(y_true)
    rng = np.random.default_rng(SEED if noise_seed is None else noise_seed)
    noise = rng.standard_normal((k, n))
    ranks = np.vstack([_rank_percentile(noise[i], n) for i in range(k)])

    def objective(params):
        w = params[:-1]
        power = params[-1]
        score = (w[:, None] * np.power(ranks, power)).sum(axis=0)
        return -compute_cls(y_true, score, pe)["cls"]

    bounds = [(-WEIGHT_BOUND, WEIGHT_BOUND)] * k + [(POWER_LOW, POWER_HIGH)]
    res = differential_evolution(
        objective,
        bounds,
        maxiter=maxiter,
        popsize=popsize,
        tol=1e-4,
        seed=seed,
        polish=False,
        updating="deferred",
        workers=1,
    )
    return float(-res.fun)


def search_null(y_true, pe, k, budget=REFERENCE_MAXITER, n_repeats=20, seed=SEED):
    """Distribution of null CLS, not a single number.

    A single null run is one draw from a distribution with real spread. Reporting
    the p95 rather than the mean is what makes the comparison conservative: a
    method must clear what the search reaches on noise most of the time, not on
    average.
    """
    vals = []
    for r in range(n_repeats):
        vals.append(
            de_blend_null(
                y_true, pe, k, maxiter=budget, seed=seed + r, noise_seed=seed + 1000 + r
            )
        )
    arr = np.asarray(vals, dtype=float)
    return {
        "k": k,
        "budget": budget,
        "n_repeats": n_repeats,
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        "min": float(arr.min()),
        "median": float(np.median(arr)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(arr.max()),
        "values": [float(v) for v in arr],
    }


def selection_null(y_true, pe, n_candidates, n_repeats=200, seed=SEED):
    """Null for picking the best of a discrete candidate set.

    The differential evolution null above models the inherited 29-weight blend. A
    method whose inner loop simply picks one of C candidate configurations has a
    different and much smaller search capacity, and using the blend null for it
    would overstate the bar unfairly. This models that procedure directly: draw C
    noise vectors, keep the best CLS among them, repeat.

    n_candidates of 1 is the no-search case, which is the right null for a
    zero-parameter baseline: it is simply the CLS of one random score vector.
    """
    rng = np.random.default_rng(seed)
    n = len(y_true)
    best_vals = []
    for _ in range(n_repeats):
        best = -np.inf
        for _ in range(max(1, int(n_candidates))):
            score = rng.standard_normal(n)
            best = max(best, compute_cls(y_true, score, pe)["cls"])
        best_vals.append(best)
    arr = np.asarray(best_vals, dtype=float)
    return {
        "n_candidates": int(n_candidates),
        "n_repeats": n_repeats,
        "mean": float(arr.mean()),
        "std": float(arr.std(ddof=1)) if len(arr) > 1 else 0.0,
        "median": float(np.median(arr)),
        "p95": float(np.percentile(arr, 95)),
        "max": float(arr.max()),
    }


def signal_margin(cls_value, null_p95):
    """How far a score clears the search it came from. Negative means it did not."""
    return float(cls_value - null_p95)


def load_labels():
    gt = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    return (
        gt["active"].to_numpy(),
        gt["pe_efficiency_pct"].to_numpy(dtype=float),
    )


def main(n_repeats=20, sweep_repeats=10):
    out_dir = ROOT / "bench" / "results"
    fig_dir = ROOT / "bench" / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)
    fig_dir.mkdir(parents=True, exist_ok=True)

    y, pe = load_labels()
    print(f"seed={SEED}")
    print(
        f"python={sys.version.split()[0]} numpy={np.__version__} "
        f"scipy={scipy.__version__} platform={platform.platform()}"
    )
    print()

    t0 = time.time()
    print(f"Reference run: K={REFERENCE_K}, maxiter={REFERENCE_MAXITER}, single draw at seed {SEED}")
    reference_single = de_blend_null(y, pe, REFERENCE_K, seed=SEED, noise_seed=SEED)
    print(f"  observed reference CLS: {reference_single:.4f}")
    print(f"  expected approximately: {REFERENCE_EXPECTED} (tolerance {REFERENCE_TOLERANCE})")
    deviation = abs(reference_single - REFERENCE_EXPECTED)
    self_check_passed = deviation <= REFERENCE_TOLERANCE
    print(f"  deviation: {deviation:.4f}  self-check: {'PASS' if self_check_passed else 'FAIL'}")
    print(f"  [{time.time() - t0:.1f}s]")
    print()

    print(f"Reference distribution: {n_repeats} repeats")
    reference_dist = search_null(y, pe, REFERENCE_K, n_repeats=n_repeats)
    print(
        f"  mean {reference_dist['mean']:.4f}  median {reference_dist['median']:.4f}  "
        f"p95 {reference_dist['p95']:.4f}  max {reference_dist['max']:.4f}"
    )
    print()

    print(f"K sweep at budget {REFERENCE_MAXITER}, {sweep_repeats} repeats each")
    k_rows = []
    for k in K_SWEEP:
        t = time.time()
        row = search_null(y, pe, k, n_repeats=sweep_repeats)
        k_rows.append(row)
        print(
            f"  K={k:3d}  mean {row['mean']:.4f}  p95 {row['p95']:.4f}  "
            f"max {row['max']:.4f}  [{time.time() - t:.1f}s]"
        )
    print()

    print(f"Budget sweep at K={REFERENCE_K}, {sweep_repeats} repeats each")
    b_rows = []
    for b in BUDGET_SWEEP:
        t = time.time()
        row = search_null(y, pe, REFERENCE_K, budget=b, n_repeats=sweep_repeats)
        b_rows.append(row)
        print(
            f"  budget={b:4d}  mean {row['mean']:.4f}  p95 {row['p95']:.4f}  "
            f"[{time.time() - t:.1f}s]"
        )
    print()

    payload = {
        "seed": SEED,
        "versions": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "pandas": pd.__version__,
        },
        "platform": platform.platform(),
        "reference": {
            "k": REFERENCE_K,
            "maxiter": REFERENCE_MAXITER,
            "popsize": REFERENCE_POPSIZE,
            "observed_single_draw": reference_single,
            "expected": REFERENCE_EXPECTED,
            "tolerance": REFERENCE_TOLERANCE,
            "deviation": deviation,
            "self_check_passed": bool(self_check_passed),
            "distribution": reference_dist,
        },
        "k_sweep": k_rows,
        "budget_sweep": b_rows,
        "seconds": time.time() - t0,
    }
    (out_dir / "search_null.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    plot_capacity(k_rows, b_rows, fig_dir / "search_null_capacity.png")
    print(f"wrote {out_dir / 'search_null.json'}")
    print(f"wrote {fig_dir / 'search_null_capacity.png'}")
    return 0 if self_check_passed else 1


def plot_capacity(k_rows, b_rows, path):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    ks = [r["k"] for r in k_rows]
    ax = axes[0]
    ax.plot(ks, [r["mean"] for r in k_rows], marker="o", label="mean null CLS")
    ax.plot(ks, [r["p95"] for r in k_rows], marker="s", linestyle="--", label="95th percentile")
    ax.fill_between(
        ks, [r["min"] for r in k_rows], [r["max"] for r in k_rows], alpha=0.15, label="min to max"
    )
    ax.set_xlabel("K, free parameters in the search")
    ax.set_ylabel("CLS achieved on pure noise")
    ax.set_title("Search capacity against free parameters")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)

    bs = [r["budget"] for r in b_rows]
    ax = axes[1]
    ax.plot(bs, [r["mean"] for r in b_rows], marker="o", label="mean null CLS")
    ax.plot(bs, [r["p95"] for r in b_rows], marker="s", linestyle="--", label="95th percentile")
    ax.set_xlabel("Search budget, differential evolution iterations")
    ax.set_ylabel("CLS achieved on pure noise")
    ax.set_title(f"Search capacity against budget, K = {REFERENCE_K}")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right", fontsize=9)

    fig.suptitle(
        "What this 57-row benchmark can manufacture from noise, effective sample size 11.3",
        fontsize=11,
    )
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def quick_self_check():
    """Fast instrument check for continuous integration.

    Verifies the three properties that make the null trustworthy as an
    instrument: it is deterministic at a fixed seed, it produces a score well
    above zero from pure noise (so it is actually searching), and its capacity
    grows with the number of free parameters. It deliberately does not assert a
    specific published value, for the reason recorded in the results report.
    """
    y, pe = load_labels()
    budget = 20

    a = de_blend_null(y, pe, 5, maxiter=budget, seed=SEED, noise_seed=SEED)
    b = de_blend_null(y, pe, 5, maxiter=budget, seed=SEED, noise_seed=SEED)
    assert a == b, f"null is not deterministic at a fixed seed: {a} vs {b}"
    print(f"PASS  deterministic at seed {SEED}: {a:.4f}")

    assert a > 0.2, f"null of {a:.4f} is implausibly low; the optimizer may not be running"
    print(f"PASS  noise search reaches {a:.4f}, well above zero")

    small = de_blend_null(y, pe, 2, maxiter=budget, seed=SEED, noise_seed=SEED)
    large = de_blend_null(y, pe, 20, maxiter=budget, seed=SEED, noise_seed=SEED)
    assert large >= small, (
        f"capacity did not grow with free parameters: K=2 gave {small:.4f}, "
        f"K=20 gave {large:.4f}"
    )
    print(f"PASS  capacity grows with K: K=2 {small:.4f} <= K=20 {large:.4f}")
    print("search-null self-check passed")
    return 0


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        raise SystemExit(quick_self_check())
    raise SystemExit(main())
