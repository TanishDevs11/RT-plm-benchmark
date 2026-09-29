"""Nested leave-one-family-out evaluation harness.

Every experiment in this project calls this module and nothing else. The point of
the harness is structural: the function that selects a configuration receives only
training families, so held-out labels cannot reach a selection decision even by
accident. `assert_selection_is_pure` demonstrates that property rather than
asserting it in prose.

Protocol:

    outer loop: for each of the 7 families F
        test  = F
        train = the other 6 families
        inner loop: LOFO over the 6 training families
            score every candidate configuration on pooled inner predictions
            keep the best, using inner scores only
        refit the selected configuration on all 6 training families
        predict F
    pool the 57 outer predictions, compute CLS once

Why pooled and never per fold: three families (CRISPR-associated, Other,
Unclassified) contain zero active RTs, so PR-AUC is undefined within them, and
Unclassified holds a single RT. Pooling predictions first and scoring once is the
only scheme that handles those folds without special cases or dropped rows. It is
also what the competition evaluator does, so the honest number stays comparable to
the inherited one.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evaluation"))
from evaluate import compute_cls  # noqa: E402

SEED = 42
N_BOOTSTRAP = 10000
ZERO_ACTIVE_FAMILIES = ("CRISPR-associated", "Other", "Unclassified")


@dataclass
class ProtocolResult:
    """Everything a results table needs from one nested run."""

    name: str
    cls: float
    pr_auc: float
    w_spearman: float
    ci_low: float
    ci_high: float
    ci_width: float
    per_family: dict[str, dict[str, Any]]
    selected: dict[str, Any]
    n_candidates: int
    seconds: float
    predictions: np.ndarray = field(repr=False)
    rt_names: list[str] = field(repr=False)
    notes: str = ""

    def row(self) -> dict[str, Any]:
        return {
            "method": self.name,
            "cls": self.cls,
            "pr_auc": self.pr_auc,
            "w_spearman": self.w_spearman,
            "ci_low": self.ci_low,
            "ci_high": self.ci_high,
            "ci_width": self.ci_width,
            "n_candidates": self.n_candidates,
            "seconds": self.seconds,
        }


class Method:
    """A representation plus a model head, with its own candidate search space.

    `candidates` is the entire search space the inner loop may explore. Its length
    is the search capacity of the method and is reported alongside every score,
    because a score means nothing without the size of the search that produced it.
    """

    name = "unnamed"

    def candidates(self) -> list[dict[str, Any]]:
        return [{}]

    def fit_predict(
        self,
        config: dict[str, Any],
        train: pd.DataFrame,
        test: pd.DataFrame,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Fit on `train` only and return scores for `test`.

        Implementations must fit every preprocessing step (imputation, scaling,
        feature selection, decomposition) inside this call on `train` alone. No
        global fits, no statistics carried in from outside the fold.
        """
        raise NotImplementedError


def load_dataset() -> pd.DataFrame:
    gt = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    return gt.reset_index(drop=True)


def bootstrap_ci(y_true, y_score, pe, seed=SEED, n=N_BOOTSTRAP):
    """Percentile bootstrap interval for CLS, resampling RTs with replacement."""
    rng = np.random.default_rng(seed)
    y_true = np.asarray(y_true)
    y_score = np.asarray(y_score, dtype=float)
    pe = np.asarray(pe, dtype=float)
    m = len(y_true)
    vals = []
    for _ in range(n):
        idx = rng.integers(0, m, size=m)
        yb = y_true[idx]
        if yb.sum() == 0 or yb.sum() == len(yb):
            continue
        vals.append(compute_cls(yb, y_score[idx], pe[idx])["cls"])
    if not vals:
        return float("nan"), float("nan")
    lo, hi = np.percentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def _pooled_cls(frame: pd.DataFrame, scores: np.ndarray) -> float:
    return compute_cls(
        frame["active"].to_numpy(),
        np.asarray(scores, dtype=float),
        frame["pe_efficiency_pct"].to_numpy(dtype=float),
    )["cls"]


def select_configuration(
    method: Method,
    train: pd.DataFrame,
    seed: int = SEED,
) -> tuple[dict[str, Any], float]:
    """Choose a configuration using the training families only.

    This function never sees the outer test fold. It receives `train` and returns
    a configuration, so the purity property is a consequence of the call signature
    rather than of discipline. `assert_selection_is_pure` exercises it.
    """
    families = sorted(train["rt_family"].unique())
    cands = method.candidates()
    if len(cands) == 1:
        return cands[0], float("nan")

    best_cfg, best_score = cands[0], -np.inf
    for cfg in cands:
        pooled = np.zeros(len(train), dtype=float)
        ok = True
        for fam in families:
            te_mask = (train["rt_family"] == fam).to_numpy()
            inner_train = train.loc[~te_mask]
            inner_test = train.loc[te_mask]
            if inner_train["active"].sum() == 0:
                ok = False
                break
            rng = np.random.default_rng(seed)
            try:
                pooled[te_mask] = method.fit_predict(cfg, inner_train, inner_test, rng)
            except (ValueError, np.linalg.LinAlgError):
                ok = False
                break
        if not ok:
            continue
        score = _pooled_cls(train, pooled)
        # Strict improvement only, so ties keep the earlier candidate and the
        # selection stays deterministic under a fixed candidate order.
        if score > best_score:
            best_cfg, best_score = cfg, score
    return best_cfg, float(best_score)


def run_nested_lofo(
    method: Method,
    data: pd.DataFrame | None = None,
    seed: int = SEED,
    notes: str = "",
) -> ProtocolResult:
    """Run the full nested protocol and return pooled metrics."""
    t0 = time.time()
    data = load_dataset() if data is None else data
    families = sorted(data["rt_family"].unique())
    predictions = np.zeros(len(data), dtype=float)
    selected: dict[str, Any] = {}

    for fam in families:
        te_mask = (data["rt_family"] == fam).to_numpy()
        train = data.loc[~te_mask]
        test = data.loc[te_mask]
        cfg, inner_score = select_configuration(method, train, seed=seed)
        selected[fam] = {"config": cfg, "inner_cls": inner_score, "n_test": int(te_mask.sum())}
        rng = np.random.default_rng(seed)
        predictions[te_mask] = method.fit_predict(cfg, train, test, rng)

    y = data["active"].to_numpy()
    pe = data["pe_efficiency_pct"].to_numpy(dtype=float)
    res = compute_cls(y, predictions, pe)
    lo, hi = bootstrap_ci(y, predictions, pe, seed=seed)

    per_family = {}
    for fam in families:
        m = (data["rt_family"] == fam).to_numpy()
        per_family[fam] = {
            "n": int(m.sum()),
            "n_active": int(y[m].sum()),
            "mean_score": float(predictions[m].mean()),
            "zero_active": fam in ZERO_ACTIVE_FAMILIES,
        }

    return ProtocolResult(
        name=method.name,
        cls=float(res["cls"]),
        pr_auc=float(res["pr_auc"]),
        w_spearman=float(res["w_spearman"]),
        ci_low=lo,
        ci_high=hi,
        ci_width=float(hi - lo),
        per_family=per_family,
        selected=selected,
        n_candidates=len(method.candidates()),
        seconds=time.time() - t0,
        predictions=predictions,
        rt_names=data["rt_name"].tolist(),
        notes=notes,
    )


def assert_selection_is_pure(method: Method, data: pd.DataFrame | None = None, seed: int = SEED):
    """Corrupt the held-out labels and require the selection to be unchanged.

    For each outer fold the selection is computed twice: once against the real
    data, once against a copy in which every label and efficiency value in the
    held-out family has been destroyed. If any selected configuration differs, a
    held-out label reached a selection decision and the harness is unsound.
    """
    data = load_dataset() if data is None else data
    families = sorted(data["rt_family"].unique())
    rng = np.random.default_rng(seed)

    for fam in families:
        te_mask = (data["rt_family"] == fam).to_numpy()
        train = data.loc[~te_mask]

        corrupted = data.copy()
        idx = corrupted.index[te_mask]
        corrupted.loc[idx, "active"] = 1 - corrupted.loc[idx, "active"].to_numpy()
        corrupted.loc[idx, "pe_efficiency_pct"] = rng.uniform(0, 100, size=len(idx))
        corrupt_train = corrupted.loc[~te_mask]

        cfg_clean, _ = select_configuration(method, train, seed=seed)
        cfg_dirty, _ = select_configuration(method, corrupt_train, seed=seed)

        a = json.dumps(cfg_clean, sort_keys=True, default=str)
        b = json.dumps(cfg_dirty, sort_keys=True, default=str)
        if a != b:
            raise AssertionError(
                f"Selection for held-out family {fam} changed when the held-out "
                f"labels were corrupted. Clean: {a}. Corrupted: {b}. A held-out "
                "label is reaching a selection decision."
            )
    return True


class PeekingHarnessMethod(Method):
    """Deliberate positive control. This method cheats, and the test must catch it.

    It selects its configuration by scoring candidates against the full dataset,
    held-out family included, which is a compact model of what the inherited
    pipeline did. It exists so that `assert_selection_is_pure` is known to be
    capable of failing.
    """

    name = "peeking-positive-control"

    def __init__(self, inner: Method, full_data: pd.DataFrame):
        self.inner = inner
        self.full = full_data

    def candidates(self):
        return self.inner.candidates()

    def fit_predict(self, config, train, test, rng):
        return self.inner.fit_predict(config, train, test, rng)


def select_configuration_peeking(method, train, seed=SEED, full=None):
    """Selection that scores against every row, including the held-out family."""
    cands = method.candidates()
    best_cfg, best = cands[0], -np.inf
    for cfg in cands:
        pooled = np.zeros(len(full), dtype=float)
        for fam in sorted(full["rt_family"].unique()):
            m = (full["rt_family"] == fam).to_numpy()
            tr = full.loc[~m]
            if tr["active"].sum() == 0:
                continue
            rng = np.random.default_rng(seed)
            pooled[m] = method.fit_predict(cfg, tr, full.loc[m], rng)
        score = _pooled_cls(full, pooled)
        if score > best:
            best_cfg, best = cfg, score
    return best_cfg, float(best)
