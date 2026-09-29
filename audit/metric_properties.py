"""Properties of the CLS metric on this 57-row dataset.

Establishes what the metric can resolve before any model is compared under it:
the effective sample size of the weighted Spearman term, how concentrated the
weight is, how much the score moves under arbitrary tie-breaking, and how wide a
bootstrap interval on a fixed prediction vector is. That interval width is the
resolution limit of the whole benchmark.

Outputs audit/metric_report.md.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import scipy
import sklearn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "evaluation"))
from evaluate import compute_cls, EPSILON  # noqa: E402

SEED = 42
N_PERMUTATIONS = 2000
N_BOOTSTRAP = 10000
AUDIT_DIR = ROOT / "audit"


def library_versions():
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit-learn": sklearn.__version__,
    }


def kish_ess(weights):
    """Kish effective sample size: (sum w)^2 / sum(w^2)."""
    w = np.asarray(weights, dtype=float)
    return float(w.sum() ** 2 / np.square(w).sum())


def load_ground_truth():
    gt = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    return gt[["rt_name", "active", "pe_efficiency_pct", "rt_family"]]


def load_submission():
    """Load the inherited submission vector, the object of study."""
    for rel in ("submission.csv", "legacy_submission/submission.csv"):
        path = ROOT / rel
        if path.exists():
            return pd.read_csv(path), rel
    return None, None


def weight_analysis(gt):
    w = gt["pe_efficiency_pct"].to_numpy(dtype=float) + EPSILON
    total = w.sum()
    order = np.argsort(-w)
    shares = {}

    mm = gt["rt_name"].astype(str).str.upper().str.replace("-", "", regex=False)
    mmlv_mask = mm.str.contains("MMLV").to_numpy()
    shares["mmlv"] = float(w[mmlv_mask].sum() / total) if mmlv_mask.any() else None
    shares["mmlv_names"] = gt.loc[mmlv_mask, "rt_name"].tolist()

    shares["top5"] = float(w[order[:5]].sum() / total)
    shares["top5_names"] = gt.iloc[order[:5]]["rt_name"].tolist()

    inactive_mask = gt["active"].to_numpy() == 0
    shares["inactive"] = float(w[inactive_mask].sum() / total)
    shares["n_inactive"] = int(inactive_mask.sum())
    shares["n_active"] = int((~inactive_mask).sum())
    shares["ess"] = kish_ess(w)
    shares["n"] = int(len(w))
    return shares


def row_order_sensitivity(gt, pred, rng):
    """CLS under random row permutations of the merged frame.

    weighted_spearman ranks with argsort(argsort(...)), which assigns distinct
    integer ranks to tied values. Every zero-efficiency RT is tied, so the ranks
    handed to those rows depend on their position in the array, which is an
    artifact of merge order rather than of any prediction.
    """
    merged = gt.merge(pred[["rt_name", "predicted_score"]], on="rt_name", how="left")
    merged["predicted_score"] = merged["predicted_score"].fillna(0.0)
    n = len(merged)
    vals = np.empty(N_PERMUTATIONS, dtype=float)
    for i in range(N_PERMUTATIONS):
        idx = rng.permutation(n)
        sub = merged.iloc[idx]
        res = compute_cls(
            sub["active"].to_numpy(),
            sub["predicted_score"].to_numpy(dtype=float),
            sub["pe_efficiency_pct"].to_numpy(dtype=float),
        )
        vals[i] = res["cls"]
    return vals


def bootstrap_cls(gt, pred, rng):
    """Bootstrap CLS by resampling the 57 RTs with replacement."""
    merged = gt.merge(pred[["rt_name", "predicted_score"]], on="rt_name", how="left")
    merged["predicted_score"] = merged["predicted_score"].fillna(0.0)
    y = merged["active"].to_numpy()
    s = merged["predicted_score"].to_numpy(dtype=float)
    e = merged["pe_efficiency_pct"].to_numpy(dtype=float)
    n = len(merged)

    vals = []
    skipped = 0
    for _ in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, size=n)
        yb = y[idx]
        # PR-AUC is undefined when a resample contains a single class.
        if yb.sum() == 0 or yb.sum() == len(yb):
            skipped += 1
            continue
        vals.append(compute_cls(yb, s[idx], e[idx])["cls"])
    return np.asarray(vals), skipped


def fmt(v, places=4):
    return "n/a" if v is None else f"{v:.{places}f}"


def main():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    versions = library_versions()
    gt = load_ground_truth()
    pred, pred_src = load_submission()

    shares = weight_analysis(gt)

    lines = []
    lines.append("# Metric properties of CLS at n = 57")
    lines.append("")
    lines.append(f"Seed: {SEED}")
    lines.append("")
    lines.append("Library versions: " + ", ".join(f"{k} {v}" for k, v in versions.items()))
    lines.append("")
    lines.append(
        "Everything below is a property of the metric and the label distribution. "
        "None of it depends on any model, and none of it is a result."
    )
    lines.append("")

    lines.append("## 1. Effective sample size")
    lines.append("")
    lines.append(
        f"The weighted Spearman term weights each RT by `pe_efficiency_pct + {EPSILON}`."
    )
    lines.append("")
    lines.append("| Quantity | Value |")
    lines.append("| --- | --- |")
    lines.append(f"| Rows | {shares['n']} |")
    lines.append(f"| Active | {shares['n_active']} |")
    lines.append(f"| Inactive | {shares['n_inactive']} |")
    lines.append(f"| Kish effective sample size | {fmt(shares['ess'], 2)} |")
    lines.append("")
    lines.append(
        "The nominal sample size is 57. The weighted Spearman term behaves like a "
        f"sample of about {shares['ess']:.1f} independent points. Any procedure "
        "that fits more free parameters than that is fitting noise, and the "
        "search-capacity null in Phase 3 measures exactly how much."
    )
    lines.append("")

    lines.append("## 2. Weight concentration")
    lines.append("")
    lines.append("| Group | Share of total weight |")
    lines.append("| --- | --- |")
    if shares["mmlv"] is not None:
        lines.append(
            f"| MMLV-RT ({', '.join(shares['mmlv_names'])}) | {shares['mmlv'] * 100:.2f} percent |"
        )
    lines.append(f"| Top 5 RTs by weight | {shares['top5'] * 100:.2f} percent |")
    lines.append(
        f"| All {shares['n_inactive']} inactives combined | {shares['inactive'] * 100:.3f} percent |"
    )
    lines.append("")
    lines.append("Top 5 by weight: " + ", ".join(shares["top5_names"]) + ".")
    lines.append("")
    lines.append(
        "The inactives carry a fraction of a percent of the weighted Spearman term "
        "between them. Ordering them correctly is close to free, and ordering them "
        "incorrectly is close to costless, so that half of the metric is decided by "
        "a handful of high-efficiency enzymes."
    )
    lines.append("")

    lines.append("## 3. Row-order sensitivity")
    lines.append("")
    if pred is None:
        lines.append("No submission vector found, so this section could not be computed.")
    else:
        vals = row_order_sensitivity(gt, pred, rng)
        lines.append(f"Prediction vector: `{pred_src}`, {N_PERMUTATIONS} random row permutations.")
        lines.append("")
        lines.append("| Statistic | CLS |")
        lines.append("| --- | --- |")
        lines.append(f"| Minimum | {fmt(float(vals.min()))} |")
        lines.append(f"| Median | {fmt(float(np.median(vals)))} |")
        lines.append(f"| Maximum | {fmt(float(vals.max()))} |")
        lines.append(f"| Standard deviation | {fmt(float(vals.std(ddof=1)))} |")
        lines.append(f"| Range | {fmt(float(vals.max() - vals.min()))} |")
        lines.append("")
        lines.append(
            "`weighted_spearman` ranks with `argsort(argsort(...))`, which hands "
            "distinct integer ranks to tied values. Every zero-efficiency RT is "
            f"tied, so the ranks assigned to those {shares['n_inactive']} rows "
            "depend on their position in the merged array rather than on anything "
            "predicted. The effect is real, and it is small, because those rows "
            "carry almost none of the weight. It is reported because a metric whose "
            "value depends on row order at all should be stated plainly, not "
            "discovered later."
        )
    lines.append("")

    lines.append("## 4. Bootstrap confidence interval")
    lines.append("")
    if pred is None:
        lines.append("No submission vector found, so this section could not be computed.")
    else:
        boots, skipped = bootstrap_cls(gt, pred, rng)
        lo, hi = np.percentile(boots, [2.5, 97.5])
        lines.append(
            f"Resampling the {shares['n']} RTs with replacement, {N_BOOTSTRAP} draws, "
            f"on the fixed prediction vector `{pred_src}`."
        )
        lines.append("")
        lines.append("| Statistic | CLS |")
        lines.append("| --- | --- |")
        lines.append(f"| Point estimate on the observed rows | {fmt(compute_cls(*_arrays(gt, pred))['cls'])} |")
        lines.append(f"| Bootstrap mean | {fmt(float(boots.mean()))} |")
        lines.append(f"| 2.5th percentile | {fmt(float(lo))} |")
        lines.append(f"| 97.5th percentile | {fmt(float(hi))} |")
        lines.append(f"| Interval width | {fmt(float(hi - lo))} |")
        lines.append(f"| Draws discarded as single class | {skipped} |")
        lines.append("")
        lines.append(
            f"The 95 percent interval spans {hi - lo:.3f} CLS. That width is the "
            "resolution limit of this benchmark: two methods whose scores differ by "
            "less than it have not been distinguished by this dataset, however "
            "many decimal places are quoted for either. Phase 5 converts this into "
            "an explicit minimum resolvable difference and refuses to call anything "
            "below it a win."
        )
    lines.append("")

    out = AUDIT_DIR / "metric_report.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"seed={SEED}")
    print("versions: " + ", ".join(f"{k}={v}" for k, v in versions.items()))
    print(f"kish_ess={shares['ess']:.3f} n={shares['n']} active={shares['n_active']}")
    print(f"weight share inactive={shares['inactive']:.5f} top5={shares['top5']:.4f}")
    print(f"wrote {out}")


def _arrays(gt, pred):
    merged = gt.merge(pred[["rt_name", "predicted_score"]], on="rt_name", how="left")
    merged["predicted_score"] = merged["predicted_score"].fillna(0.0)
    return (
        merged["active"].to_numpy(),
        merged["predicted_score"].to_numpy(dtype=float),
        merged["pe_efficiency_pct"].to_numpy(dtype=float),
    )


if __name__ == "__main__":
    main()
