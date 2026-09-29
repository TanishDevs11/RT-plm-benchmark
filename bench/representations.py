"""Representation benchmark: do protein language model embeddings beat handcrafted
features for out-of-family reverse transcriptase function prediction?

Every representation is evaluated under one identical nested protocol with one
identical pair of model heads, both inner-selected. The only thing that varies
across rows is the representation itself, which is what makes the comparison a
comparison.

Alongside each score the table reports a lineage-confound score: how accurately
that representation predicts RT family. A representation that predicts family well
and function poorly is encoding evolutionary lineage, not catalysis, which is the
central question this benchmark exists to answer.

Outputs bench/results/representations.md, representations.json, and
bench/figures/function_vs_lineage.png.
"""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bench"))

from names import (  # noqa: E402
    DUPLICATE_PDB_STEMS,
    NO_STRUCTURE,
    align_to_reference,
    assert_full_coverage,
)
from protocol import SEED, Method, load_dataset, run_nested_lofo  # noqa: E402
from search_null import selection_null, signal_margin  # noqa: E402
from baselines import handcrafted_table  # noqa: E402

CACHE = ROOT / "bench" / "cache"
N_PAIRED_BOOTSTRAP = 10000


# ----------------------------------------------------------------- in-fold transforms


def residualize_on_length(xtr, xte, train, test, data):
    """Remove the component of every dimension that is linear in sequence length.

    PC1 of the mean-pooled embedding tracks sequence length at Spearman -0.77, so
    the dominant axis of the representation is measuring size rather than
    catalysis. The regression is fit on training rows only and applied outward.
    """
    ltr = data.set_index("rt_name").loc[train["rt_name"], "protein_length_aa"].to_numpy(dtype=float)
    lte = data.set_index("rt_name").loc[test["rt_name"], "protein_length_aa"].to_numpy(dtype=float)
    reg = LinearRegression().fit(ltr.reshape(-1, 1), xtr)
    return xtr - reg.predict(ltr.reshape(-1, 1)), xte - reg.predict(lte.reshape(-1, 1))


def residualize_on_family(xtr, xte, train, test, data, n_remove=None):
    """Remove the leading principal components that carry family identity.

    The PCA and the family association are both fit on the training fold. The
    number of removed components is either fixed by the caller or chosen as the
    components whose one-way ANOVA against family is significant within the
    training rows.
    """
    pca = PCA(n_components=min(len(xtr) - 1, xtr.shape[1]), random_state=SEED).fit(xtr)
    ztr, zte = pca.transform(xtr), pca.transform(xte)
    fam = train["rt_family"].to_numpy()

    if n_remove is None:
        drop = []
        for j in range(min(10, ztr.shape[1])):
            groups = [ztr[fam == f, j] for f in np.unique(fam) if (fam == f).sum() > 1]
            if len(groups) > 1:
                f_stat, p = stats.f_oneway(*groups)
                if p < 0.05:
                    drop.append(j)
    else:
        drop = list(range(n_remove))

    keep = [j for j in range(ztr.shape[1]) if j not in drop]
    var_removed = float(pca.explained_variance_ratio_[drop].sum()) if drop else 0.0
    return ztr[:, keep], zte[:, keep], len(drop), var_removed


# ----------------------------------------------------------------- representation tables


def pooled_table(key):
    path = CACHE / f"pooled_{key}.npz"
    if not path.exists():
        return None
    z = np.load(path, allow_pickle=True)
    return pd.DataFrame(z["embeddings"], index=[str(n) for n in z["names"]])


def inherited_embedding_table():
    z = np.load(ROOT / "data" / "esm2_embeddings.npz", allow_pickle=True)
    return pd.DataFrame(z["embeddings"], index=[str(n) for n in z["names"]])


def catalytic_core_table(key):
    """Mean-pool per-residue embeddings over the catalytic core window only."""
    pr_path = CACHE / f"per_residue_{key}.npz"
    win_path = CACHE / "catalytic_windows.json"
    if not pr_path.exists() or not win_path.exists():
        return None, None
    windows = json.loads(win_path.read_text(encoding="utf-8"))
    z = np.load(pr_path, allow_pickle=True)
    rows, names = [], []
    for name in z.files:
        lo, hi = windows["windows"][name]
        rep = z[name][lo:hi]
        if len(rep) == 0:
            rep = z[name]
        rows.append(rep.mean(0))
        names.append(name)
    return pd.DataFrame(np.vstack(rows), index=names), windows["missing_motif"]


def attention_pooled_table(key):
    """Attention-weighted pooling over the catalytic core window."""
    att_path = CACHE / f"attention_{key}.npz"
    pr_key = "esm2_650M"
    pr_path = CACHE / f"per_residue_{pr_key}.npz"
    win_path = CACHE / "catalytic_windows.json"
    if not att_path.exists() or not pr_path.exists() or not win_path.exists():
        return None
    windows = json.loads(win_path.read_text(encoding="utf-8"))["windows"]
    att = np.load(att_path, allow_pickle=True)
    pr = np.load(pr_path, allow_pickle=True)
    rows, names = [], []
    for name in pr.files:
        if name not in att.files:
            continue
        lo, hi = windows[name]
        rep = pr[name][lo:hi]
        w = att[name][lo:hi]
        if len(rep) == 0 or len(w) != len(rep):
            rep, w = pr[name], att[name][: len(pr[name])]
        if w.sum() <= 0:
            w = np.ones(len(rep), dtype=float)
        rows.append((rep * (w / w.sum())[:, None]).sum(0))
        names.append(name)
    if not rows:
        return None
    return pd.DataFrame(np.vstack(rows), index=names)


def structure_table():
    """AlphaFold pLDDT summaries plus the cleft and topology descriptors.

    Aligned through `bench.names`. Line1-RT has no predicted structure in the
    inherited data, so its structure features stay missing and are imputed inside
    each training fold rather than globally.
    """
    ref = load_dataset()["rt_name"].tolist()
    parts = [
        pd.read_csv(ROOT / "data" / "structure_features.csv"),
        pd.read_csv(ROOT / "data" / "topology_features.csv").drop(
            columns=["pdb_filename"], errors="ignore"
        ),
    ]
    plddt = plddt_summaries()
    if plddt is not None:
        parts.append(plddt)
    frames = [align_to_reference(p, ref).select_dtypes(include=[np.number]) for p in parts]
    out = pd.concat(frames, axis=1)
    out = out.loc[:, ~out.columns.duplicated()]
    assert_full_coverage(out, ref, "structure_table", allow_missing=NO_STRUCTURE)
    return out


def plddt_summaries():
    """Per-structure pLDDT statistics, read from PDB B-factor columns.

    Skips the duplicate PDB stems recorded in `bench.names`, so an RT that has two
    structure files contributes one row rather than two.
    """
    sdir = ROOT / "data" / "structures"
    if not sdir.exists():
        return None
    rows = []
    for pdb in sorted(sdir.glob("*.pdb")):
        if pdb.stem in DUPLICATE_PDB_STEMS:
            continue
        vals = []
        for line in pdb.read_text(errors="replace").splitlines():
            if line.startswith("ATOM") and line[12:16].strip() == "CA":
                try:
                    vals.append(float(line[60:66]))
                except ValueError:
                    continue
        if not vals:
            continue
        v = np.asarray(vals, dtype=float)
        rows.append(
            {
                "rt_name": pdb.stem,
                "plddt_mean": v.mean(),
                "plddt_median": float(np.median(v)),
                "plddt_min": v.min(),
                "plddt_frac_confident": float((v > 70).mean()),
                "plddt_frac_very_low": float((v < 50).mean()),
            }
        )
    return pd.DataFrame(rows) if rows else None


# ----------------------------------------------------------------- the method


class RepresentationMethod(Method):
    """One representation, two inner-selected heads, all preprocessing in-fold."""

    def __init__(self, name, table, transform=None, data=None):
        self.name = name
        self.table = table
        self.transform = transform
        self.data = load_dataset() if data is None else data
        self.transform_info = {}

    def candidates(self):
        logreg = [{"head": "logreg", "C": c} for c in (0.01, 0.1, 1.0, 10.0)]
        hgb = [
            {"head": "hgb", "max_depth": d, "learning_rate": lr}
            for d, lr in product((2, 3), (0.05, 0.1))
        ]
        return logreg + hgb

    def _head(self, config):
        if config["head"] == "logreg":
            return LogisticRegression(C=config["C"], max_iter=5000, random_state=SEED)
        return HistGradientBoostingClassifier(
            max_depth=config["max_depth"],
            learning_rate=config["learning_rate"],
            max_iter=200,
            random_state=SEED,
        )

    def fit_predict(self, config, train, test, rng):
        xtr = self.table.loc[train["rt_name"]].to_numpy(dtype=float)
        xte = self.table.loc[test["rt_name"]].to_numpy(dtype=float)

        imp = SimpleImputer(strategy="median", keep_empty_features=True).fit(xtr)
        xtr, xte = imp.transform(xtr), imp.transform(xte)
        scaler = StandardScaler().fit(xtr)
        xtr, xte = scaler.transform(xtr), scaler.transform(xte)

        if self.transform == "length":
            xtr, xte = residualize_on_length(xtr, xte, train, test, self.data)
        elif self.transform == "family":
            xtr, xte, n_drop, var = residualize_on_family(xtr, xte, train, test, self.data)
            self.transform_info = {"components_removed": n_drop, "variance_removed": var}

        model = self._head(config)
        model.fit(xtr, train["active"].to_numpy())
        return model.predict_proba(xte)[:, 1]


# ----------------------------------------------------------------- lineage confound


def lineage_confound(table, data, seed=SEED):
    """5-fold accuracy of predicting RT family from the representation.

    This is a descriptive property of the representation. It is computed once on
    all rows and is never used to select anything, so it cannot leak into a score.
    Families with a single member are dropped, since they cannot be stratified.
    """
    idx = data["rt_name"]
    x = table.loc[idx].to_numpy(dtype=float)
    x = SimpleImputer(strategy="median", keep_empty_features=True).fit_transform(x)
    x = StandardScaler().fit_transform(x)
    y = data["rt_family"].to_numpy()
    counts = pd.Series(y).value_counts()
    keep = np.isin(y, counts[counts >= 5].index)
    if keep.sum() < 10:
        return float("nan"), float("nan")
    x, y = x[keep], y[keep]
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    acc = cross_val_score(
        LogisticRegression(max_iter=5000, random_state=seed), x, y, cv=cv, scoring="accuracy"
    )
    majority = float(pd.Series(y).value_counts(normalize=True).max())
    return float(acc.mean()), majority


# ----------------------------------------------------------------- paired comparison


def paired_bootstrap(pred_a, pred_b, data, seed=SEED, n=N_PAIRED_BOOTSTRAP):
    """Probability that A beats B, resampling the same RTs for both.

    A bare difference of point estimates is not a result at this sample size. The
    paired resample holds the RTs common between the two methods, so the
    comparison is not inflated by the shared difficulty of the same 57 enzymes.
    """
    from evaluate import compute_cls

    rng = np.random.default_rng(seed)
    y = data["active"].to_numpy()
    pe = data["pe_efficiency_pct"].to_numpy(dtype=float)
    m = len(y)
    wins, diffs = 0, []
    used = 0
    for _ in range(n):
        idx = rng.integers(0, m, size=m)
        yb = y[idx]
        if yb.sum() == 0 or yb.sum() == len(yb):
            continue
        ca = compute_cls(yb, pred_a[idx], pe[idx])["cls"]
        cb = compute_cls(yb, pred_b[idx], pe[idx])["cls"]
        diffs.append(ca - cb)
        wins += ca > cb
        used += 1
    diffs = np.asarray(diffs)
    return {
        "p_a_beats_b": wins / used if used else float("nan"),
        "mean_diff": float(diffs.mean()),
        "sd_diff": float(diffs.std(ddof=1)),
        "n_used": used,
    }


def minimum_resolvable_difference(sd_diff, power=0.8, alpha=0.05):
    """Smallest CLS difference detectable at the given power.

    Uses the bootstrap standard deviation of the paired difference as the
    standard error. Any observed gap below this value is noise at this sample
    size and must be reported as unresolvable rather than as a win.
    """
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_power = stats.norm.ppf(power)
    return float((z_alpha + z_power) * sd_diff)


# ----------------------------------------------------------------- assembly


def build_representations(data):
    reps, blocked = [], []

    hand = handcrafted_table()
    reps.append(("handcrafted: sequence and physicochemical", hand, None))

    struct = structure_table()
    if struct is not None and struct.shape[1] > 0:
        reps.append(("structure: pLDDT, cleft and topology", struct, None))
    else:
        blocked.append(("structure: pLDDT, cleft and topology", "no structure descriptors available"))

    for key, label in [
        ("esm2_8M", "ESM-2 8M mean-pooled"),
        ("esm2_35M", "ESM-2 35M mean-pooled"),
        ("esm2_150M", "ESM-2 150M mean-pooled"),
        ("esm2_650M", "ESM-2 650M mean-pooled"),
        ("esm1v", "ESM-1v mean-pooled"),
    ]:
        t = pooled_table(key)
        if t is None:
            blocked.append((label, f"embedding cache bench/cache/pooled_{key}.npz not produced"))
        else:
            reps.append((label, t, None))

    big = pooled_table("esm2_650M")
    if big is None:
        big = inherited_embedding_table()
        reps.append(("ESM-2 650M mean-pooled, inherited cache", big, None))
    reps.append(("ESM-2 650M, length-residualized", big, "length"))
    reps.append(("ESM-2 650M, family-residualized", big, "family"))

    core, missing = catalytic_core_table("esm2_650M")
    if core is not None:
        reps.append(("ESM-2 650M, catalytic-core pooled", core, None))
    else:
        blocked.append(
            ("ESM-2 650M, catalytic-core pooled", "per-residue cache not produced")
        )
        missing = None

    att = attention_pooled_table("esm2_150M")
    if att is not None:
        reps.append(("ESM-2, attention-weighted core pooling", att, None))
    else:
        blocked.append(
            ("ESM-2, attention-weighted core pooling", "attention cache not produced")
        )

    blocked.append(
        (
            "ProtT5-XL-U50 mean-pooled",
            "transformers and sentencepiece are not installed and could not be "
            "installed in this environment",
        )
    )
    blocked.append(
        (
            "inverse-folding likelihood, ESM-IF or ProteinMPNN",
            "neither package is installed; ESM-IF needs a geometric deep learning "
            "stack with no Python 3.14 wheels on this platform",
        )
    )
    return reps, blocked, missing


def main():
    data = load_dataset()
    y = data["active"].to_numpy()
    pe = data["pe_efficiency_pct"].to_numpy(dtype=float)
    reps, blocked, motif_missing = build_representations(data)

    print(f"seed={SEED}")
    print(f"{len(reps)} representations to evaluate, {len(blocked)} blocked")
    print()

    rows, preds = [], {}
    for label, table, transform in reps:
        method = RepresentationMethod(label, table, transform=transform, data=data)
        res = run_nested_lofo(method, data=data, seed=SEED)
        null = selection_null(y, pe, res.n_candidates, seed=SEED)
        acc, majority = lineage_confound(table, data)
        row = res.row()
        row["null_cls_p95"] = null["p95"]
        row["signal_margin"] = signal_margin(res.cls, null["p95"])
        row["family_accuracy"] = acc
        row["family_majority"] = majority
        row["n_features"] = int(table.shape[1])
        row["transform_info"] = method.transform_info
        rows.append(row)
        preds[label] = res.predictions
        print(
            f"{label:46s} CLS {res.cls:.4f}  margin {row['signal_margin']:+.4f}  "
            f"family acc {acc:.3f}  [{res.seconds:.1f}s]"
        )

    print()
    print("Paired comparisons against the length baseline and between top rows")
    comparisons, sds = [], []
    order = sorted(rows, key=lambda r: -r["cls"])
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            a, b = order[i]["method"], order[j]["method"]
            cmp = paired_bootstrap(preds[a], preds[b], data)
            comparisons.append({"a": a, "b": b, **cmp})
            sds.append(cmp["sd_diff"])
    mrd = minimum_resolvable_difference(float(np.median(sds))) if sds else float("nan")
    print(f"  {len(comparisons)} pairwise comparisons, median sd of paired difference "
          f"{np.median(sds):.4f}")
    print(f"  minimum resolvable CLS difference at 80 percent power: {mrd:.4f}")

    out_dir = ROOT / "bench" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "representations.json").write_text(
        json.dumps(
            {
                "seed": SEED,
                "rows": rows,
                "blocked": [{"representation": a, "blocker": b} for a, b in blocked],
                "comparisons": comparisons,
                "minimum_resolvable_difference": mrd,
                "motif_missing": motif_missing,
            },
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    plot_function_vs_lineage(rows, ROOT / "bench" / "figures" / "function_vs_lineage.png")
    write_markdown(rows, blocked, comparisons, mrd, motif_missing, out_dir / "representations.md")
    print(f"wrote {out_dir / 'representations.md'}")
    return 0


def plot_function_vs_lineage(rows, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pts = [(r["family_accuracy"], r["cls"], r["method"]) for r in rows if np.isfinite(r["family_accuracy"])]
    if not pts:
        return
    fig, ax = plt.subplots(figsize=(9, 6))
    xs, ys, labels = zip(*pts)
    ax.scatter(xs, ys, s=70)
    for x, y, lab in pts:
        ax.annotate(lab, (x, y), fontsize=7, xytext=(4, 4), textcoords="offset points")
    ax.set_xlabel("Lineage confound: 5-fold family classification accuracy")
    ax.set_ylabel("Function: nested out-of-family CLS")
    ax.set_title("Does the representation encode function, or lineage?")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def write_markdown(rows, blocked, comparisons, mrd, motif_missing, path):
    L = []
    L.append("# Representation benchmark")
    L.append("")
    L.append(f"Seed: {SEED}. One nested protocol, one pair of inner-selected heads, "
             "only the representation varies.")
    L.append("")
    L.append("## Power statement")
    L.append("")
    L.append(
        f"With 21 positives and a weighted-Spearman effective sample size of 11.3, the "
        f"minimum CLS difference this benchmark can resolve at 80 percent power is "
        f"**{mrd:.3f}**. Any gap smaller than that is reported below as not resolvable "
        "at this sample size, and is not a win for either side. This threshold is "
        "computed from the bootstrap standard deviation of the paired difference, not "
        "assumed."
    )
    L.append("")
    L.append("## Results")
    L.append("")
    L.append(
        "| Representation | Dims | CLS | PR-AUC | wSpearman | 95% CI | null p95 | Margin | Family acc |"
    )
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in sorted(rows, key=lambda r: -r["cls"]):
        L.append(
            f"| {r['method']} | {r['n_features']} | {r['cls']:.4f} | {r['pr_auc']:.4f} | "
            f"{r['w_spearman']:.4f} | [{r['ci_low']:.3f}, {r['ci_high']:.3f}] | "
            f"{r['null_cls_p95']:.4f} | {r['signal_margin']:+.4f} | {r['family_accuracy']:.3f} |"
        )
    L.append("")
    if motif_missing:
        L.append(
            f"YXDD motif not found in {len(motif_missing)} RTs, handled explicitly by "
            f"falling back to full-length pooling for those rows: {', '.join(motif_missing)}."
        )
        L.append("")
    L.append("## Pairwise comparisons")
    L.append("")
    L.append(
        "Paired bootstrap over the same 57 RTs. `P(A beats B)` is the fraction of "
        "resamples in which A scored higher, not a point difference."
    )
    L.append("")
    L.append("| A | B | P(A beats B) | Mean diff | Resolvable |")
    L.append("| --- | --- | --- | --- | --- |")
    for c in comparisons:
        resolvable = "yes" if abs(c["mean_diff"]) >= mrd else "NOT RESOLVABLE"
        L.append(
            f"| {c['a']} | {c['b']} | {c['p_a_beats_b']:.3f} | {c['mean_diff']:+.4f} | {resolvable} |"
        )
    L.append("")
    L.append("## Blocked")
    L.append("")
    L.append("| Representation | Status | Blocker |")
    L.append("| --- | --- | --- |")
    for name, why in blocked:
        L.append(f"| {name} | NOT RUN | {why} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
