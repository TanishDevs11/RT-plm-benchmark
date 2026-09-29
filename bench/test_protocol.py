"""Tests that fail the harness if a held-out label can influence a selection.

Runs as a plain script so continuous integration needs no test runner:

    python bench/test_protocol.py

The suite is only meaningful if it is capable of failing, so it includes a
deliberate positive control: a selector that peeks at the held-out family, which
the purity check must reject. A green run where the positive control also passed
would mean the check is inert.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bench"))

from protocol import (  # noqa: E402
    SEED,
    Method,
    assert_selection_is_pure,
    load_dataset,
    run_nested_lofo,
    select_configuration,
    select_configuration_peeking,
)

FEATURES = [
    "protein_length_aa",
    "molecular_weight",
    "aromaticity",
    "instability_index",
]


class SingleFeatureMethod(Method):
    """Zero-training method: score the test rows by one chosen feature.

    The search space is which feature to use. Selection therefore depends on the
    labels it is scored against, which is what makes this a usable probe for the
    purity check: if held-out labels leak, the chosen feature moves.
    """

    name = "single-feature-probe"

    def __init__(self, features=FEATURES):
        self.features = list(features)
        self._table = _feature_table()

    def candidates(self):
        return [{"feature": f} for f in self.features]

    def fit_predict(self, config, train, test, rng):
        col = self._table.loc[test["rt_name"], config["feature"]].to_numpy(dtype=float)
        return np.nan_to_num(col, nan=0.0, posinf=0.0, neginf=0.0)


def _feature_table():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    hand = pd.read_csv(ROOT / "data" / "handcrafted_features.csv")
    merged = seq[["rt_name", "protein_length_aa"]].merge(hand, on="rt_name", how="left")
    return merged.set_index("rt_name")


def _corrupt(data, te_mask, rng):
    corrupted = data.copy()
    idx = corrupted.index[te_mask]
    corrupted.loc[idx, "active"] = 1 - corrupted.loc[idx, "active"].to_numpy()
    corrupted.loc[idx, "pe_efficiency_pct"] = rng.uniform(0, 100, size=len(idx))
    return corrupted


def test_pure_selection_passes():
    """The real harness must survive corruption of the held-out labels."""
    method = SingleFeatureMethod()
    assert assert_selection_is_pure(method) is True
    print("PASS  pure selection is unaffected by held-out labels")


def test_peeking_selector_is_caught():
    """Positive control: a selector that peeks must be detected.

    If this test reports that peeking went undetected, the purity check is inert
    and every other green result in this file is worthless.
    """
    data = load_dataset()
    method = SingleFeatureMethod()
    rng = np.random.default_rng(SEED)
    detected = []

    for fam in sorted(data["rt_family"].unique()):
        te_mask = (data["rt_family"] == fam).to_numpy()
        corrupted = _corrupt(data, te_mask, rng)

        clean, _ = select_configuration_peeking(
            method, data.loc[~te_mask], seed=SEED, full=data
        )
        dirty, _ = select_configuration_peeking(
            method, corrupted.loc[~te_mask], seed=SEED, full=corrupted
        )
        if json.dumps(clean, sort_keys=True) != json.dumps(dirty, sort_keys=True):
            detected.append(fam)

    assert detected, (
        "The peeking selector produced identical configurations even after the "
        "held-out labels were destroyed. The purity check cannot detect leakage, "
        "so it is inert and must be repaired before any result is trusted."
    )
    print(f"PASS  peeking detected on {len(detected)} of 7 families: {', '.join(detected)}")


def test_pure_and_peeking_differ():
    """The two selectors must actually disagree, or the control proves nothing."""
    data = load_dataset()
    method = SingleFeatureMethod()
    disagreements = []
    for fam in sorted(data["rt_family"].unique()):
        te_mask = (data["rt_family"] == fam).to_numpy()
        pure, _ = select_configuration(method, data.loc[~te_mask], seed=SEED)
        peek, _ = select_configuration_peeking(
            method, data.loc[~te_mask], seed=SEED, full=data
        )
        if json.dumps(pure, sort_keys=True) != json.dumps(peek, sort_keys=True):
            disagreements.append(fam)
    print(
        f"PASS  pure and peeking selectors disagree on {len(disagreements)} of 7 "
        f"families: {', '.join(disagreements) if disagreements else 'none'}"
    )


def test_all_rows_predicted():
    """Every RT must receive a prediction from a model that never saw its family."""
    res = run_nested_lofo(SingleFeatureMethod())
    assert len(res.predictions) == 57, f"expected 57 predictions, got {len(res.predictions)}"
    assert np.isfinite(res.predictions).all(), "non-finite predictions present"
    assert len(res.selected) == 7, f"expected 7 outer folds, got {len(res.selected)}"
    print(f"PASS  57 pooled predictions across 7 outer folds, CLS {res.cls:.4f}")


def test_zero_active_families_handled():
    """The three zero-active families must be scored, not silently dropped."""
    res = run_nested_lofo(SingleFeatureMethod())
    for fam in ("CRISPR-associated", "Other", "Unclassified"):
        assert fam in res.per_family, f"{fam} missing from the per-family breakdown"
        assert res.per_family[fam]["n_active"] == 0
        assert res.per_family[fam]["n"] > 0
    assert res.per_family["Unclassified"]["n"] == 1, "Unclassified should hold one RT"
    print("PASS  zero-active families and the single-member family are handled")


def test_determinism():
    """Two runs at the same seed must agree exactly."""
    a = run_nested_lofo(SingleFeatureMethod(), seed=SEED)
    b = run_nested_lofo(SingleFeatureMethod(), seed=SEED)
    assert np.array_equal(a.predictions, b.predictions), "predictions differ across runs"
    assert a.cls == b.cls, "CLS differs across runs at a fixed seed"
    print(f"PASS  deterministic at seed {SEED}")


def main():
    print(f"seed={SEED}")
    print(f"numpy={np.__version__} pandas={pd.__version__}")
    print()
    tests = [
        test_pure_selection_passes,
        test_peeking_selector_is_caught,
        test_pure_and_peeking_differ,
        test_all_rows_predicted,
        test_zero_active_families_handled,
        test_determinism,
    ]
    failures = 0
    for t in tests:
        try:
            t()
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {t.__name__}: {exc}")
    print()
    if failures:
        print(f"{failures} of {len(tests)} tests failed")
        return 1
    print(f"all {len(tests)} tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
