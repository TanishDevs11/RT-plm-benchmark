"""The baseline ladder: what this task looks like with little or no learning.

Every row runs through `bench.protocol.run_nested_lofo` and nothing else. The
zero-parameter baselines are not tuned at all, so their inner loop has a single
candidate and their search capacity is one. They exist to give every trained model
something honest to clear: a model that cannot beat `protein_length_aa` has not
learned anything about function, whatever its absolute score.

Outputs bench/results/baseline_ladder.md and bench/results/baseline_ladder.json.
"""

from __future__ import annotations

import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bench"))

from protocol import SEED, Method, load_dataset, run_nested_lofo  # noqa: E402
from search_null import selection_null, signal_margin  # noqa: E402

AMINO_ACIDS = "ACDEFGHIKLMNPQRSTVWY"


# ---------------------------------------------------------------- feature tables


def handcrafted_table():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")[["rt_name", "protein_length_aa"]]
    hand = pd.read_csv(ROOT / "data" / "handcrafted_features.csv")
    struct = pd.read_csv(ROOT / "data" / "structure_features.csv")
    topo = pd.read_csv(ROOT / "data" / "topology_features.csv").drop(
        columns=["pdb_filename"], errors="ignore"
    )
    out = seq.merge(hand, on="rt_name", how="left")
    out = out.merge(struct, on="rt_name", how="left")
    out = out.merge(topo, on="rt_name", how="left")
    return out.set_index("rt_name").select_dtypes(include=[np.number])


def embedding_table():
    z = np.load(ROOT / "data" / "esm2_embeddings.npz", allow_pickle=True)
    names = [str(n) for n in z["names"]]
    return pd.DataFrame(z["embeddings"], index=names)


def aa_composition_table():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    rows = {}
    for name, s in zip(seq["rt_name"], seq["sequence"]):
        s = str(s).upper()
        total = max(len(s), 1)
        rows[name] = [s.count(a) / total for a in AMINO_ACIDS]
    return pd.DataFrame.from_dict(rows, orient="index", columns=list(AMINO_ACIDS))


def kmer_table(k=3):
    """3-mer composition as a sparse-ish dense frame, L2 normalized."""
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    vocab: dict[str, int] = {}
    counts = []
    for s in seq["sequence"]:
        s = str(s).upper()
        c: dict[int, float] = {}
        for i in range(len(s) - k + 1):
            kmer = s[i : i + k]
            if any(ch not in AMINO_ACIDS for ch in kmer):
                continue
            j = vocab.setdefault(kmer, len(vocab))
            c[j] = c.get(j, 0.0) + 1.0
        counts.append(c)
    mat = np.zeros((len(counts), len(vocab)), dtype=np.float32)
    for i, c in enumerate(counts):
        for j, v in c.items():
            mat[i, j] = v
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return pd.DataFrame(mat / norms, index=seq["rt_name"].tolist())


# ------------------------------------------------------- zero-parameter baselines


class LengthBaseline(Method):
    name = "1. protein_length_aa, no training"

    def __init__(self, sign=1):
        self.sign = sign
        self.table = load_dataset().set_index("rt_name")["protein_length_aa"]

    def fit_predict(self, config, train, test, rng):
        return self.sign * self.table.loc[test["rt_name"]].to_numpy(dtype=float)


class NegativeLengthBaseline(LengthBaseline):
    name = "2. negative protein_length_aa, no training"

    def __init__(self):
        super().__init__(sign=-1)


class CompositionPC1Baseline(Method):
    """First principal component of amino acid composition, PCA fit in-fold.

    The sign of a principal component is arbitrary, so it is fixed
    deterministically by forcing the largest-magnitude loading to be positive.
    Choosing the sign by which direction scores better would be a one-bit label
    leak, which is exactly the class of decision this project exists to refuse.
    """

    name = "3. amino acid composition PC1, no training"

    def __init__(self):
        self.table = aa_composition_table()

    def fit_predict(self, config, train, test, rng):
        xtr = self.table.loc[train["rt_name"]].to_numpy(dtype=float)
        xte = self.table.loc[test["rt_name"]].to_numpy(dtype=float)
        scaler = StandardScaler().fit(xtr)
        pca = PCA(n_components=1, random_state=SEED).fit(scaler.transform(xtr))
        loading = pca.components_[0]
        sign = 1.0 if loading[np.argmax(np.abs(loading))] >= 0 else -1.0
        return sign * pca.transform(scaler.transform(xte))[:, 0]


class KmerNearestActiveBaseline(Method):
    """Maximum 3-mer cosine similarity to any active RT in the training fold."""

    name = "4. 3-mer cosine to nearest training active, no training"

    def __init__(self):
        self.table = kmer_table(3)

    def fit_predict(self, config, train, test, rng):
        actives = train.loc[train["active"] == 1, "rt_name"]
        if len(actives) == 0:
            return np.zeros(len(test), dtype=float)
        a = self.table.loc[actives].to_numpy(dtype=np.float32)
        t = self.table.loc[test["rt_name"]].to_numpy(dtype=np.float32)
        return (t @ a.T).max(axis=1).astype(float)


class FamilyPriorBaseline(Method):
    """Active fraction of the nearest training family by mean embedding distance."""

    name = "5. family prior by nearest training family, no training"

    def __init__(self):
        self.emb = embedding_table()

    def fit_predict(self, config, train, test, rng):
        fams = sorted(train["rt_family"].unique())
        centroids, priors = [], []
        for f in fams:
            names = train.loc[train["rt_family"] == f, "rt_name"]
            centroids.append(self.emb.loc[names].to_numpy(dtype=float).mean(axis=0))
            priors.append(float(train.loc[train["rt_family"] == f, "active"].mean()))
        centroids = np.vstack(centroids)
        priors = np.asarray(priors, dtype=float)
        x = self.emb.loc[test["rt_name"]].to_numpy(dtype=float)
        d = np.linalg.norm(x[:, None, :] - centroids[None, :, :], axis=2)
        return priors[d.argmin(axis=1)]


# ------------------------------------------------------------- trained baselines


class TabularModelMethod(Method):
    """Shared inner-selected pipeline over a fixed feature table."""

    def __init__(self, name, table, grid, model_factory):
        self.name = name
        self.table = table
        self.grid = grid
        self.model_factory = model_factory

    def candidates(self):
        keys = sorted(self.grid)
        return [dict(zip(keys, vals)) for vals in product(*(self.grid[k] for k in keys))]

    def fit_predict(self, config, train, test, rng):
        xtr = self.table.loc[train["rt_name"]].to_numpy(dtype=float)
        xte = self.table.loc[test["rt_name"]].to_numpy(dtype=float)
        ytr = train["active"].to_numpy()
        pipe = Pipeline(
            [
                ("impute", SimpleImputer(strategy="median")),
                ("scale", StandardScaler()),
                ("model", self.model_factory(config)),
            ]
        )
        pipe.fit(xtr, ytr)
        return pipe.predict_proba(xte)[:, 1]


def make_extratrees(cfg):
    return ExtraTreesClassifier(
        n_estimators=cfg["n_estimators"],
        max_depth=cfg["max_depth"],
        random_state=SEED,
        n_jobs=1,
    )


def make_randomforest(cfg):
    return RandomForestClassifier(
        n_estimators=cfg["n_estimators"],
        max_depth=cfg["max_depth"],
        random_state=SEED,
        n_jobs=1,
    )


def make_logreg(cfg):
    return LogisticRegression(C=cfg["C"], max_iter=5000, random_state=SEED)


TREE_GRID = {"n_estimators": [200, 500], "max_depth": [3, 6, None]}
LOGREG_GRID = {"C": [0.01, 0.1, 1.0, 10.0]}


def build_methods():
    hand = handcrafted_table()
    emb = embedding_table()
    return [
        (LengthBaseline(), "zero-parameter"),
        (NegativeLengthBaseline(), "zero-parameter"),
        (CompositionPC1Baseline(), "zero-parameter"),
        (KmerNearestActiveBaseline(), "zero-parameter"),
        (FamilyPriorBaseline(), "zero-parameter"),
        (
            TabularModelMethod("8a. handcrafted + ExtraTrees", hand, TREE_GRID, make_extratrees),
            "trained",
        ),
        (
            TabularModelMethod("8b. handcrafted + RandomForest", hand, TREE_GRID, make_randomforest),
            "trained",
        ),
        (
            TabularModelMethod("9. handcrafted + logistic regression", hand, LOGREG_GRID, make_logreg),
            "trained",
        ),
        (
            TabularModelMethod(
                "10. raw ESM-2 mean-pooled + logistic regression", emb, LOGREG_GRID, make_logreg
            ),
            "trained",
        ),
    ]


NOT_RUN = [
    (
        "6. zero-shot ESM-1v masked-marginal pseudo-likelihood",
        "NOT RUN",
        "Masked marginals need one forward pass per residue per sequence. At 57 RTs "
        "of median length 523 that is roughly 30000 forward passes of a 650M "
        "parameter model, and the probe found torch 2.11.0+cpu with zero CUDA "
        "devices. This is a wall-clock blocker, not a missing dependency.",
    ),
    (
        "7. inverse-folding log-likelihood, ESM-IF or ProteinMPNN",
        "NOT RUN",
        "Neither package is installed. ESM-IF additionally requires a geometric deep "
        "learning stack (torch-geometric, torch-sparse) with no prebuilt wheels for "
        "Python 3.14 on this platform.",
    ),
]


def main():
    data = load_dataset()
    y = data["active"].to_numpy()
    pe = data["pe_efficiency_pct"].to_numpy(dtype=float)

    print(f"seed={SEED}")
    print(f"numpy={np.__version__} pandas={pd.__version__}")
    print()

    rows = []
    for method, kind in build_methods():
        res = run_nested_lofo(method, data=data, seed=SEED)
        null = selection_null(y, pe, res.n_candidates, seed=SEED)
        row = res.row()
        row["kind"] = kind
        row["null_cls_mean"] = null["mean"]
        row["null_cls_p95"] = null["p95"]
        row["signal_margin"] = signal_margin(res.cls, null["p95"])
        row["selected"] = {k: v["config"] for k, v in res.selected.items()}
        rows.append(row)
        print(
            f"{res.name:52s} CLS {res.cls:.4f}  CI [{res.ci_low:.3f}, {res.ci_high:.3f}]  "
            f"null_p95 {null['p95']:.4f}  margin {row['signal_margin']:+.4f}  "
            f"[{res.seconds:.1f}s]"
        )

    length_cls = next(r["cls"] for r in rows if r["method"].startswith("1."))
    for r in rows:
        r["beats_length_baseline"] = bool(r["cls"] > length_cls)

    out_dir = ROOT / "bench" / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "baseline_ladder.json").write_text(
        json.dumps({"seed": SEED, "length_baseline_cls": length_cls, "rows": rows}, indent=2, default=str),
        encoding="utf-8",
    )
    write_markdown(rows, length_cls, out_dir / "baseline_ladder.md")
    print()
    print(f"wrote {out_dir / 'baseline_ladder.md'}")
    return 0


def write_markdown(rows, length_cls, path):
    L = []
    L.append("# Baseline ladder")
    L.append("")
    L.append(f"Seed: {SEED}. Every row runs through the nested protocol in `bench/protocol.py`.")
    L.append("")
    L.append(
        "`null p95` is the 95th percentile of the CLS reached by the same selection "
        "procedure applied to pure noise, and `margin` is the score minus that null. "
        "A row whose margin is not clearly positive has not demonstrated signal, "
        "however high its raw CLS looks."
    )
    L.append("")
    L.append(
        "| Method | Kind | CLS | PR-AUC | wSpearman | 95% CI | Cands | null p95 | Margin | Beats length |"
    )
    L.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        beats = "yes" if r["beats_length_baseline"] else "NO"
        if r["method"].startswith("1."):
            beats = "reference"
        L.append(
            f"| {r['method']} | {r['kind']} | {r['cls']:.4f} | {r['pr_auc']:.4f} | "
            f"{r['w_spearman']:.4f} | [{r['ci_low']:.3f}, {r['ci_high']:.3f}] | "
            f"{r['n_candidates']} | {r['null_cls_p95']:.4f} | {r['signal_margin']:+.4f} | {beats} |"
        )
    L.append("")
    L.append("## Not run")
    L.append("")
    L.append("| Baseline | Status | Blocker |")
    L.append("| --- | --- | --- |")
    for name, status, why in NOT_RUN:
        L.append(f"| {name} | {status} | {why} |")
    L.append("")
    L.append("## Reading this table")
    L.append("")
    L.append(
        f"The reference line is baseline 1, `protein_length_aa` used directly as the "
        f"score with no training whatsoever, at CLS {length_cls:.4f}. Any trained "
        "model below that line is not learning function; it is learning something "
        "weaker than a single number that was already in the input file."
    )
    L.append("")
    L.append(
        "The bootstrap intervals are wide because the dataset is small and the "
        "weighted Spearman term has a Kish effective sample size of 11.3. Two rows "
        "whose intervals overlap heavily have not been separated by this benchmark, "
        "and the paired comparison in the representation phase is the only place "
        "where a difference is claimed."
    )
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
