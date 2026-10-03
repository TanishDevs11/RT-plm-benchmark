"""Benchmark twelve Task A representations through two model heads and nothing else.

Two heads, fixed:

  * **classification** of `active`, by regularized logistic regression
  * **regression** of `pe_efficiency_pct`, by ridge regression

No other model family. No RandomForest, no gradient boosting, no SVM, no ensembling, no
blending. That restriction is the point rather than a simplification. The capacity to
search over model families is exactly what produced the 0.9754 artifact this repository
exists to correct: `bench/search_null.py` shows that a search with fifty free parameters
reaches that score on pure Gaussian noise. And a representation comparison is only
interpretable if the head is held fixed across representations, because otherwise a
difference between two rows is a difference between two searches.

The only thing selected is the regularization strength, and it is selected in the inner
loop of the nested leave-one-family-out protocol in `bench/protocol.py`, which receives
training families only. The grids are fixed here, a priori, and their size is the search
capacity reported beside every score.

Scaling and imputation happen inside each fold, through a pipeline fitted on the training
rows alone. The handcrafted block has 12 missing cells, all of them `Line1-RT`'s
structural features because it has no structure file, and a median imputed from the
training fold is the only defensible way to carry that row.

    python bench/representations_taskA.py
    python bench/representations_taskA.py --representations length esm2_650M
    python bench/representations_taskA.py --heads classification

Outputs:
    bench/results/taskA_representations.json
    bench/results/taskA_representations.md
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bench"))

from protocol import SEED, Method, assert_selection_is_pure, load_dataset, run_nested_lofo  # noqa: E402

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
HANDCRAFTED = REPO_ROOT / "features" / "handcrafted"
EMBEDDINGS = REPO_ROOT / "embeddings"
RESULTS = REPO_ROOT / "bench" / "results"

# Fixed a priori. Six values each, so the search capacity of every row in the results
# table is 6, and that number is reported beside the score.
LOGISTIC_C_GRID = (0.001, 0.01, 0.1, 1.0, 10.0, 100.0)
RIDGE_ALPHA_GRID = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)

ESM_SIZES = ("8M", "35M", "150M", "650M")


def load_taskA_dataset() -> pd.DataFrame:
    """The curated table, under the column names bench/protocol.py expects.

    The harness is reused rather than replaced, so the frame it receives has to speak its
    vocabulary. It is also checked against what `load_dataset` returns, which reads the
    inherited file: the two must agree row for row, because `reports/reconciliation.md`
    established that the curated table reproduces the inherited one exactly. If they ever
    disagree, every comparison with the earlier audit is void and this is where that
    should surface.
    """
    with CURATED.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    frame = pd.DataFrame(
        {
            "rt_name": [r["rt_name"] for r in rows],
            "sequence": [r["sequence"] for r in rows],
            "rt_family": [r["family"] for r in rows],
            "active": [int(r["active"]) for r in rows],
            "pe_efficiency_pct": [float(r["pe_efficiency_pct"]) for r in rows],
            "protein_length_aa": [int(r["sequence_len"]) for r in rows],
        }
    )
    # The two files are compared per enzyme, not positionally. curated.csv is in Table S1
    # index order and the inherited file is sorted by family, so the row orders differ by
    # construction; what must agree is every label attached to every name.
    inherited = load_dataset()
    if set(frame["rt_name"]) != set(inherited["rt_name"]):
        raise SystemExit(
            "curated.csv and data/rt_sequences.csv hold different enzymes; every "
            "comparison with the earlier audit would be void"
        )
    theirs = inherited.set_index("rt_name")
    mine = frame.set_index("rt_name")
    for column, their_column in (
        ("active", "active"),
        ("pe_efficiency_pct", "pe_efficiency_pct"),
        ("rt_family", "rt_family"),
    ):
        disagree = [
            name
            for name in mine.index
            if str(mine.loc[name, column]) != str(theirs.loc[name, their_column])
        ]
        if disagree:
            raise SystemExit(
                "curated.csv and data/rt_sequences.csv disagree on "
                + column
                + " for "
                + str(disagree)
                + "; every comparison with the earlier audit would be void"
            )
    return frame.reset_index(drop=True)


def load_representations(names: list[str]) -> dict[str, tuple[np.ndarray, str]]:
    """Each representation as a dense matrix in curated.csv row order, plus a description."""
    with CURATED.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    order = [r["rt_name"] for r in rows]

    table = pd.read_csv(HANDCRAFTED / "taskA_features_v2.csv")
    if table["rt_name"].tolist() != order:
        raise SystemExit("taskA_features_v2.csv is not in curated.csv row order")

    def columns_with(prefix: str) -> np.ndarray:
        selected = [c for c in table.columns if c.startswith(prefix)]
        return table[selected].to_numpy(dtype=float)

    available: dict[str, tuple[np.ndarray, str]] = {}

    available["length"] = (
        table[["length"]].to_numpy(dtype=float),
        "sequence length alone, 1 feature. The baseline every other row has to clear",
    )
    available["aa_composition"] = (
        columns_with("aac_"),
        "amino acid composition, 20 features",
    )
    available["dipeptide"] = (
        columns_with("dpc_"),
        "dipeptide composition, 400 features",
    )
    available["physicochemical"] = (
        columns_with("bio_"),
        "Biopython physicochemical descriptors including net charge at pH 7.4",
    )
    handcrafted = np.hstack(
        [
            table[["length"]].to_numpy(dtype=float),
            columns_with("aac_"),
            columns_with("dpc_"),
            columns_with("rk3_"),
            columns_with("bio_"),
            columns_with("struct_"),
        ]
    )
    available["handcrafted"] = (
        handcrafted,
        "every handcrafted block concatenated: length, composition, dipeptide, "
        "reduced-alphabet 3-mer, physicochemical, structural",
    )

    for k in (3, 4):
        path = HANDCRAFTED / ("taskA_kmer" + str(k) + ".npz")
        if path.is_file():
            payload = np.load(path, allow_pickle=True)
            if [str(i) for i in payload["ids"]] != order:
                raise SystemExit(path.name + " is not in curated.csv row order")
            available["kmer" + str(k)] = (
                payload["features"].astype(float),
                "full " + str(k) + "-mer frequencies over the 20-letter alphabet",
            )

    esm: dict[str, np.ndarray] = {}
    for size in ESM_SIZES:
        matrix_path = EMBEDDINGS / ("esm2_" + size) / "taskA_v2_mean_full_final.npz"
        ids_path = EMBEDDINGS / ("esm2_" + size) / "taskA_v2_mean_full_final_ids.txt"
        if not matrix_path.is_file():
            continue
        if ids_path.read_text(encoding="utf-8").split() != order:
            raise SystemExit(matrix_path.name + " is not in curated.csv row order")
        matrix = np.load(matrix_path)["embeddings"].astype(float)
        esm[size] = matrix
        available["esm2_" + size] = (
            matrix,
            "ESM-2 " + size + ", final layer, mean pooled over residue positions",
        )

    if "650M" in esm:
        available["handcrafted_plus_esm2_650M"] = (
            np.hstack([handcrafted, esm["650M"]]),
            "the handcrafted block concatenated with ESM-2 650M",
        )

    if names:
        unknown = [n for n in names if n not in available]
        if unknown:
            raise SystemExit(
                "unknown representation(s) "
                + str(unknown)
                + "; available: "
                + str(sorted(available))
            )
        return {n: available[n] for n in names}
    return available


class RepresentationHead(Method):
    """One representation, one head, with the regularization strength as the only choice."""

    def __init__(self, label: str, matrix: np.ndarray, head: str) -> None:
        self.name = label + " | " + head
        self.matrix = matrix
        self.head = head
        self.label = label

    def candidates(self) -> list[dict]:
        if self.head == "classification":
            return [{"C": value} for value in LOGISTIC_C_GRID]
        return [{"alpha": value} for value in RIDGE_ALPHA_GRID]

    def _pipeline(self, config: dict):
        from sklearn.impute import SimpleImputer
        from sklearn.linear_model import LogisticRegression, Ridge
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler

        # Imputation and scaling are steps of the pipeline, so they are fitted on the
        # training rows of this fold and nothing else. The handcrafted block's 12 missing
        # cells are the reason the imputer is here at all.
        if self.head == "classification":
            estimator = LogisticRegression(
                C=config["C"], max_iter=5000, random_state=SEED
            )
        else:
            estimator = Ridge(alpha=config["alpha"], random_state=SEED)
        return make_pipeline(
            SimpleImputer(strategy="median"), StandardScaler(), estimator
        )

    def fit_predict(self, config, train, test, rng) -> np.ndarray:
        x_train = self.matrix[train.index.to_numpy()]
        x_test = self.matrix[test.index.to_numpy()]
        model = self._pipeline(config)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if self.head == "classification":
                model.fit(x_train, train["active"].to_numpy())
                return model.predict_proba(x_test)[:, 1]
            model.fit(x_train, train["pe_efficiency_pct"].to_numpy(dtype=float))
            return model.predict(x_test)


def harmonic_mean(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.0
    return float(2 * a * b / (a + b))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--representations", nargs="*", default=[])
    parser.add_argument(
        "--markdown-only",
        action="store_true",
        help="rewrite the markdown table from the stored JSON without refitting anything",
    )
    parser.add_argument(
        "--heads", nargs="*", default=["classification", "regression"],
        choices=["classification", "regression"],
    )
    args = parser.parse_args()

    print_run_header("bench/representations_taskA.py", [CURATED])
    if args.markdown_only:
        stored = json.loads(
            (RESULTS / "taskA_representations.json").read_text(encoding="utf-8")
        )
        write_markdown(stored["results"], stored["heads"])
        print("rewrote bench/results/taskA_representations.md from the stored JSON")
        return 0

    data = load_taskA_dataset()
    print("rows: " + str(len(data)) + ", actives: " + str(int(data["active"].sum())))
    print("curated.csv agrees with data/rt_sequences.csv on every label")
    print("")

    representations = load_representations(args.representations)
    print("representations: " + str(len(representations)))
    for label, (matrix, _) in representations.items():
        print("  " + label.ljust(28) + str(matrix.shape[1]) + " features")
    print("")
    print("heads: " + ", ".join(args.heads))
    print(
        "search capacity per row: "
        + str(len(LOGISTIC_C_GRID))
        + " regularization values, selected in the inner loop only"
    )

    results: dict[str, dict] = {}
    for label, (matrix, description) in representations.items():
        results[label] = {"description": description, "n_features": int(matrix.shape[1])}
        for head in args.heads:
            method = RepresentationHead(label, matrix, head)
            started = time.time()
            # The purity property is demonstrated per method, not assumed from the
            # harness's own test suite: this method is new code.
            assert_selection_is_pure(method, data)
            result = run_nested_lofo(method, data)
            results[label][head] = {
                "cls": result.cls,
                "pr_auc": result.pr_auc,
                "w_spearman": result.w_spearman,
                "ci_low": result.ci_low,
                "ci_high": result.ci_high,
                "ci_width": result.ci_width,
                "n_candidates": result.n_candidates,
                "seconds": round(result.seconds, 2),
                "selected": {
                    family: entry["config"] for family, entry in result.selected.items()
                },
                "per_family": result.per_family,
                "predictions": [float(v) for v in result.predictions],
            }
            print(
                "  "
                + label.ljust(28)
                + head.ljust(16)
                + "CLS "
                + format(result.cls, ".4f")
                + "  PR-AUC "
                + format(result.pr_auc, ".4f")
                + "  wSpearman "
                + format(result.w_spearman, ".4f")
                + "  ["
                + format(time.time() - started, ".0f")
                + "s]"
            )
            sys.stdout.flush()

        if "classification" in args.heads and "regression" in args.heads:
            # The two-head CLS: separation from the classifier, ranking from the
            # regressor, combined by the metric's own harmonic mean. This is what using
            # the brief's two heads actually implies, and it is reported alongside each
            # head's own single-vector CLS rather than instead of it.
            combined = harmonic_mean(
                results[label]["classification"]["pr_auc"],
                results[label]["regression"]["w_spearman"],
            )
            results[label]["two_head_cls"] = combined
            print("  " + label.ljust(28) + "two-head CLS".ljust(16) + format(combined, ".4f"))

    RESULTS.mkdir(parents=True, exist_ok=True)
    payload = {
        "curated_sha256": sha256_of(CURATED),
        "seed": SEED,
        "logistic_C_grid": list(LOGISTIC_C_GRID),
        "ridge_alpha_grid": list(RIDGE_ALPHA_GRID),
        "heads": args.heads,
        "selection_criterion": "pooled inner-loop CLS, as bench/protocol.py defines it",
        "results": results,
    }
    (RESULTS / "taskA_representations.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("")
    print("wrote bench/results/taskA_representations.json")
    write_markdown(results, args.heads)
    print("wrote bench/results/taskA_representations.md")
    return 0


def write_markdown(results: dict, heads: list[str]) -> None:
    lines = [
        "# Task A representation benchmark",
        "",
        "Written by `bench/representations_taskA.py`. Nested leave-one-family-out through",
        "`bench/protocol.py`, whose inner loop receives training families only and whose",
        "deliberate-peeking positive control passes.",
        "",
        "Two heads and nothing else: regularized logistic regression for `active`, ridge",
        "regression for `pe_efficiency_pct`. The only selected quantity is the",
        "regularization strength, from a grid of "
        + str(len(LOGISTIC_C_GRID))
        + " values fixed a priori, chosen in the",
        "inner loop. No other model family appears anywhere.",
        "",
        "Per the Gate G2 ruling, **classification is the primary result**: the binary label",
        "is read from Table S1's fill and is reproducible from the file, while",
        "`pe_efficiency_pct` is a digitization of Figure S1A at roughly half a percentage",
        "point of resolution. Every regression and weighted-Spearman number below inherits",
        "that limitation.",
        "",
    ]

    if "classification" in heads:
        lines += [
            "## Classification of `active`, the primary result",
            "",
            "| representation | features | CLS | PR-AUC | wSpearman | 95 percent CI | search capacity |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for label in sorted(
            results, key=lambda k: -results[k].get("classification", {}).get("pr_auc", -1)
        ):
            entry = results[label].get("classification")
            if entry is None:
                continue
            lines.append(
                "| `"
                + label
                + "` | "
                + str(results[label]["n_features"])
                + " | "
                + format(entry["cls"], ".4f")
                + " | "
                + format(entry["pr_auc"], ".4f")
                + " | "
                + format(entry["w_spearman"], ".4f")
                + " | "
                + format(entry["ci_low"], ".4f")
                + " to "
                + format(entry["ci_high"], ".4f")
                + " | "
                + str(entry["n_candidates"])
                + " |"
            )

    if "regression" in heads:
        lines += [
            "",
            "## Regression of `pe_efficiency_pct`",
            "",
            "Ordered by weighted Spearman, the component this head contributes.",
            "",
            "| representation | features | CLS | PR-AUC | wSpearman | 95 percent CI | search capacity |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for label in sorted(
            results, key=lambda k: -results[k].get("regression", {}).get("w_spearman", -1)
        ):
            entry = results[label].get("regression")
            if entry is None:
                continue
            lines.append(
                "| `"
                + label
                + "` | "
                + str(results[label]["n_features"])
                + " | "
                + format(entry["cls"], ".4f")
                + " | "
                + format(entry["pr_auc"], ".4f")
                + " | "
                + format(entry["w_spearman"], ".4f")
                + " | "
                + format(entry["ci_low"], ".4f")
                + " to "
                + format(entry["ci_high"], ".4f")
                + " | "
                + str(entry["n_candidates"])
                + " |"
            )

    if all(h in heads for h in ("classification", "regression")):
        lines += [
            "",
            "## Two-head CLS",
            "",
            "CLS is the harmonic mean of a separation term and a ranking term. With two",
            "heads the natural construction takes PR-AUC from the classifier and weighted",
            "Spearman from the regressor, which is what this column is. Each head's own",
            "single-vector CLS is in the tables above, for comparability with the earlier",
            "audit, which scored one vector on both components.",
            "",
            "| representation | classifier PR-AUC | regressor wSpearman | two-head CLS |",
            "| --- | --- | --- | --- |",
        ]
        for label in sorted(results, key=lambda k: -results[k].get("two_head_cls", -1)):
            if "two_head_cls" not in results[label]:
                continue
            lines.append(
                "| `"
                + label
                + "` | "
                + format(results[label]["classification"]["pr_auc"], ".4f")
                + " | "
                + format(results[label]["regression"]["w_spearman"], ".4f")
                + " | "
                + format(results[label]["two_head_cls"], ".4f")
                + " |"
            )

    lines += [
        "",
        "## Per-family breakdown",
        "",
        "Three families hold no active enzyme, so PR-AUC is undefined within them and a",
        "ranking correlation is undefined against an all-zero target. Those folds are",
        "marked `undefined` rather than scored as zero, per the handling rule in",
        "`reports/split_verification.md`. Their predictions still enter the pooled vector,",
        "because the pooled metric is computed once over all 57 rows and those rows are",
        "genuine negatives a model must not rank highly.",
        "",
        "| representation | head | family | n | actives | mean predicted score | per-family metric |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for label in sorted(results):
        for head in heads:
            entry = results[label].get(head)
            if entry is None:
                continue
            for family, stats in sorted(entry["per_family"].items()):
                lines.append(
                    "| `"
                    + label
                    + "` | "
                    + head
                    + " | "
                    + family
                    + " | "
                    + str(stats["n"])
                    + " | "
                    + str(stats["n_active"])
                    + " | "
                    + format(stats["mean_score"], ".4f")
                    + " | "
                    + ("undefined, no active" if stats["zero_active"] else "defined")
                    + " |"
                )

    lines += [
        "",
        "## What this table is not, and what the nulls did to it",
        "",
        "**These are raw numbers. Read them with `reports/statistical_validation.md`.** No",
        "score here has, on its own, been compared against a dimensionality-matched noise",
        "control, a search-capacity null at matched free-parameter count, or a label",
        "permutation, and no pairwise difference here has been tested against the smallest",
        "difference this sample size can resolve.",
        "",
        "Once those controls are applied, the ordering above changes materially:",
        "",
        "- **No representation under either head clears the CLS gate.** The highest CLS,",
        "  0.3739, sits below the search-capacity null p95 of 0.4433 at the one free",
        "  parameter this benchmark uses, and every CLS bootstrap interval includes zero.",
        "- **The median minimum resolvable CLS difference is 0.4816**, larger than every",
        "  CLS in the table, so the CLS ordering is not resolvable on this panel at all.",
        "- **On PR-AUC, ESM-2 650M and 8M clear their noise controls and then fail label",
        "  permutation**, at 0.4220 against a permuted p95 of 0.5217 and 0.3706 against",
        "  0.5676 respectively.",
        "- **`kmer4` is the only representation surviving all three controls**, and its",
        "  attribution shows its signal is strongly associated with sequence length",
        "  (Spearman +0.5212 of its out-of-fold score against length) and with family",
        "  structure, rather than with any specific sequence motif. See",
        "  `reports/interpretation.md`.",
        "",
        "The one-sentence answer is in `reports/FINAL_REPORT.md`; the manuscript-style",
        "account is in `reports/MANUSCRIPT_SUMMARY.md`.",
    ]
    (RESULTS / "taskA_representations.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    raise SystemExit(main())
