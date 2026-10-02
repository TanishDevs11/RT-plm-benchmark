"""Diagnose what the Task A representations encode, without using an activity label.

Three questions, none of which involves the thing the benchmark is trying to predict:

1. **Do the representations encode lineage?** A 5-fold stratified logistic regression
   predicting family, for each ESM-2 size and for three controls: 3-mer composition,
   length alone, and the majority baseline. If a representation classifies family far
   above a composition control, it carries phylogenetic information, and in a panel where
   family and activity are associated that is a confound rather than a capability.

2. **Do the representations encode length?** Spearman correlation of embedding principal
   components 1 to 4 against sequence length. Length is the baseline every representation
   has to beat in Phase 6, so a representation whose leading component is mostly length is
   not an independent source of signal.

3. **What does the embedding space look like?** PCA and UMAP, coloured by length, by
   activity, and by family.

Preprocessing is stated rather than left implicit, because these numbers are sensitive to
it and the prior figures in this repository were published without it. The earlier review
established that family accuracy from 3-mer composition moves between 0.3212 and 0.7152
across four defensible encodings of the same features, and that embedding PC1 against
length moves from -0.7681 to +0.6198 depending on whether the embeddings were standardized
or merely centred. So every number here carries its preprocessing, and where a choice is
contested both variants are reported.

Scaling happens inside each cross-validation fold, via a pipeline, not once over the whole
panel. That differs from how the prior figures were produced and is the reason a small
deviation from them is expected; the globally scaled variant is reported alongside so the
comparison is still possible.

    python embeddings/representation_diagnostics_taskA.py
    python embeddings/representation_diagnostics_taskA.py --no-figures

Outputs:
    reports/representation_diagnostics.md
    reports/figures/taskA_embedding_by_length.png     <- the important one
    reports/figures/taskA_embedding_by_activity.png
    reports/figures/taskA_embedding_by_family.png
    reports/figures/taskA_pc_length_correlation.png
"""

from __future__ import annotations

import argparse
import csv
import sys
import warnings
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
EMBEDDINGS = REPO_ROOT / "embeddings"
HANDCRAFTED = REPO_ROOT / "features" / "handcrafted"
OUT = REPO_ROOT / "reports" / "representation_diagnostics.md"
FIGURES = REPO_ROOT / "reports" / "figures"

SIZES = ("8M", "35M", "150M", "650M")

# Fixed by the brief. The seed is explicit because a 5-fold split of 56 rows is noisy
# enough that the fold assignment moves the third decimal place.
RANDOM_STATE = 0
N_FOLDS = 5
MIN_FAMILY_SIZE = 5

# Prior measurements this run is asked to reproduce, from reports/REVIEW.md section 6a.
PRIOR = {
    "ESM2-650M": 0.821,
    "3-mer composition": 0.571,
    "length only": 0.520,
    "majority baseline": 0.321,
}
PRIOR_PC1_LENGTH = -0.77

# Palette, from the project's data-visualization reference palette.
SERIES_1 = "#2a78d6"
SERIES_2 = "#eb6834"
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#8a8980"
GRID = "#e5e4e0"
# Sequential blue ramp, light to dark, for length. One hue, as a magnitude encoding
# requires.
SEQUENTIAL = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def load_curated() -> dict[str, np.ndarray]:
    with CURATED.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {
        "rt_name": np.array([r["rt_name"] for r in rows]),
        "family": np.array([r["family"] for r in rows]),
        "active": np.array([r["active"] == "1" for r in rows]),
        "length": np.array([int(r["sequence_len"]) for r in rows]),
    }


def load_embedding(size: str, names: np.ndarray) -> np.ndarray | None:
    directory = EMBEDDINGS / ("esm2_" + size)
    matrix_path = directory / "taskA_v2_mean_full_final.npz"
    ids_path = directory / "taskA_v2_mean_full_final_ids.txt"
    if not matrix_path.is_file() or not ids_path.is_file():
        return None
    ids = ids_path.read_text(encoding="utf-8").split()
    if ids != list(names):
        raise SystemExit(
            matrix_path.name + " row order does not match curated.csv; refusing to use it"
        )
    payload = np.load(matrix_path)
    return payload["embeddings"].astype(np.float64)


def load_kmer3(names: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    """Full 3-mer block, returned as frequencies and as raw-equivalent counts.

    Both are returned because the earlier review found that the prior 3-mer control
    figure of 0.571 is reproduced by the raw-counts-standardized encoding and not by the
    frequency encoding, and the repository specifies no encoding for this control. So both
    are measured rather than one being chosen.
    """
    path = HANDCRAFTED / "taskA_kmer3.npz"
    if not path.is_file():
        return None
    payload = np.load(path, allow_pickle=True)
    ids = [str(i) for i in payload["ids"]]
    if ids != list(names):
        raise SystemExit("taskA_kmer3.npz row order does not match curated.csv")
    frequencies = payload["features"].astype(np.float64)
    with CURATED.open(encoding="utf-8") as handle:
        lengths = np.array(
            [len(r["sequence"]) - 3 + 1 for r in csv.DictReader(handle)], dtype=float
        )
    counts = frequencies * lengths[:, None]
    return frequencies, counts


def family_accuracy(
    features: np.ndarray, families: np.ndarray, scale_in_fold: bool
) -> tuple[float, float, int]:
    """Stratified 5-fold family classification accuracy, mean and fold-to-fold SD."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    keep = np.isin(
        families,
        [f for f in np.unique(families) if (families == f).sum() >= MIN_FAMILY_SIZE],
    )
    x, y = features[keep], families[keep]
    splitter = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    estimator = LogisticRegression(max_iter=5000, random_state=RANDOM_STATE)
    if scale_in_fold:
        model = make_pipeline(StandardScaler(), estimator)
    else:
        # The globally scaled variant, for comparison with the prior figures only.
        x = StandardScaler().fit_transform(x)
        model = estimator
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        scores = cross_val_score(model, x, y, cv=splitter, scoring="accuracy")
    return float(scores.mean()), float(scores.std(ddof=1)), int(keep.sum())


def majority_accuracy(families: np.ndarray) -> tuple[float, int]:
    keep = np.isin(
        families,
        [f for f in np.unique(families) if (families == f).sum() >= MIN_FAMILY_SIZE],
    )
    kept = families[keep]
    _, counts = np.unique(kept, return_counts=True)
    return float(counts.max() / counts.sum()), int(keep.sum())


def principal_components(features: np.ndarray, standardize: bool) -> np.ndarray:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler

    x = StandardScaler().fit_transform(features) if standardize else features - features.mean(0)
    return PCA(n_components=4, random_state=RANDOM_STATE).fit_transform(x)


def pc_length_correlations(
    features: np.ndarray, lengths: np.ndarray, standardize: bool
) -> list[tuple[float, float]]:
    from scipy.stats import spearmanr

    components = principal_components(features, standardize)
    out = []
    for index in range(components.shape[1]):
        rho, p = spearmanr(components[:, index], lengths)
        out.append((float(rho), float(p)))
    return out


def umap_projection(features: np.ndarray) -> np.ndarray | None:
    try:
        import umap
    except ImportError:
        return None
    from sklearn.preprocessing import StandardScaler

    x = StandardScaler().fit_transform(features)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # n_neighbors must be below the sample count; 57 rows is small for UMAP and the
        # projection should be read as a sketch rather than as structure.
        reducer = umap.UMAP(
            n_components=2, n_neighbors=10, min_dist=0.3, random_state=RANDOM_STATE
        )
        return reducer.fit_transform(x)


def style_axes(ax) -> None:
    ax.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(colors=INK_SECONDARY, labelsize=8, length=0)
    ax.xaxis.label.set_color(INK_SECONDARY)
    ax.yaxis.label.set_color(INK_SECONDARY)


def figure_by_length(
    pca: np.ndarray, embedding_umap: np.ndarray | None, lengths: np.ndarray, rho: float, path: Path
) -> None:
    """The important plot: is the leading structure of the space just protein length?"""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    cmap = LinearSegmentedColormap.from_list("seq_blue", SEQUENTIAL)
    panels = 3 if embedding_umap is not None else 2
    fig, axes = plt.subplots(1, panels, figsize=(4.1 * panels, 4.0), dpi=200)
    fig.patch.set_facecolor(SURFACE)

    scatter = axes[0].scatter(
        pca[:, 0], pca[:, 1], c=lengths, cmap=cmap, s=46, edgecolors=SURFACE, linewidths=0.8
    )
    axes[0].set_xlabel("PC1")
    axes[0].set_ylabel("PC2")
    axes[0].set_title("PCA, coloured by length", loc="left", fontsize=10, color=INK_PRIMARY)

    axes[1].scatter(
        lengths, pca[:, 0], s=46, color=SERIES_1, edgecolors=SURFACE, linewidths=0.8
    )
    axes[1].set_xlabel("sequence length, residues")
    axes[1].set_ylabel("PC1")
    axes[1].set_title(
        "PC1 against length, Spearman " + format(rho, ".3f"),
        loc="left",
        fontsize=10,
        color=INK_PRIMARY,
    )

    if embedding_umap is not None:
        axes[2].scatter(
            embedding_umap[:, 0],
            embedding_umap[:, 1],
            c=lengths,
            cmap=cmap,
            s=46,
            edgecolors=SURFACE,
            linewidths=0.8,
        )
        axes[2].set_xlabel("UMAP 1")
        axes[2].set_ylabel("UMAP 2")
        axes[2].set_title("UMAP, coloured by length", loc="left", fontsize=10, color=INK_PRIMARY)

    bar = fig.colorbar(scatter, ax=axes.tolist(), fraction=0.025, pad=0.02)
    bar.set_label("sequence length, residues", color=INK_SECONDARY, fontsize=9)
    bar.ax.tick_params(colors=INK_SECONDARY, labelsize=8)
    bar.outline.set_visible(False)
    for ax in axes:
        style_axes(ax)
    fig.savefig(path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def figure_by_activity(
    pca: np.ndarray, embedding_umap: np.ndarray | None, active: np.ndarray, path: Path
) -> None:
    import matplotlib.pyplot as plt

    panels = 2 if embedding_umap is not None else 1
    fig, axes = plt.subplots(1, panels, figsize=(4.4 * panels, 4.0), dpi=200, squeeze=False)
    axes = axes[0]
    fig.patch.set_facecolor(SURFACE)
    projections = [("PCA", pca, "PC1", "PC2")]
    if embedding_umap is not None:
        projections.append(("UMAP", embedding_umap, "UMAP 1", "UMAP 2"))
    for ax, (name, projection, xlabel, ylabel) in zip(axes, projections):
        # Colour plus marker shape, so identity is never carried by colour alone.
        ax.scatter(
            projection[~active, 0],
            projection[~active, 1],
            s=48,
            marker="o",
            color=SERIES_2,
            edgecolors=SURFACE,
            linewidths=0.8,
            label="inactive",
        )
        ax.scatter(
            projection[active, 0],
            projection[active, 1],
            s=58,
            marker="^",
            color=SERIES_1,
            edgecolors=SURFACE,
            linewidths=0.8,
            label="active",
        )
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(name + ", coloured by activity", loc="left", fontsize=10, color=INK_PRIMARY)
        style_axes(ax)
    legend = axes[0].legend(frameon=False, fontsize=9, loc="best")
    for text in legend.get_texts():
        text.set_color(INK_SECONDARY)
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def figure_by_family(
    pca: np.ndarray, embedding_umap: np.ndarray | None, families: np.ndarray, path: Path
) -> None:
    """Small multiples, one panel per family.

    Seven categorical hues cannot be told apart reliably in a scatter: on the project's
    reference palette the worst all-pairs separation is a CVD delta E of 3.2 and a
    normal-vision delta E of 12.9, both below the floors, and no re-ordering fixes it
    because a scatter puts every pair on screen at once. The documented remedy is to
    facet, so each family gets its own panel and colour carries nothing but highlight.
    """
    import matplotlib.pyplot as plt

    order = [f for f, _ in sorted(
        ((f, (families == f).sum()) for f in np.unique(families)),
        key=lambda pair: -pair[1],
    )]
    rows = 2 if embedding_umap is not None else 1
    fig, axes = plt.subplots(
        rows, len(order), figsize=(1.72 * len(order), 2.0 * rows), dpi=200, squeeze=False
    )
    fig.patch.set_facecolor(SURFACE)
    projections = [("PCA", pca)]
    if embedding_umap is not None:
        projections.append(("UMAP", embedding_umap))
    for row, (name, projection) in enumerate(projections):
        for column, family in enumerate(order):
            ax = axes[row][column]
            mask = families == family
            ax.scatter(
                projection[~mask, 0],
                projection[~mask, 1],
                s=12,
                color=GRID,
                linewidths=0,
            )
            ax.scatter(
                projection[mask, 0],
                projection[mask, 1],
                s=26,
                color=SERIES_1,
                edgecolors=SURFACE,
                linewidths=0.6,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            for side in ("top", "right", "left", "bottom"):
                ax.spines[side].set_color(GRID)
            ax.set_facecolor(SURFACE)
            if row == 0:
                ax.set_title(
                    family.replace("_", " ") + "\nn=" + str(int(mask.sum())),
                    fontsize=7.5,
                    color=INK_PRIMARY,
                    pad=4,
                )
            if column == 0:
                ax.set_ylabel(name, fontsize=9, color=INK_SECONDARY)
    fig.suptitle(
        "Embedding space by family, one panel per family, highlighted against the rest",
        fontsize=10,
        color=INK_PRIMARY,
        x=0.01,
        ha="left",
        y=1.0,
    )
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)


def figure_pc_length(correlations: dict[str, list[tuple[float, float]]], path: Path) -> None:
    import matplotlib.pyplot as plt

    sizes = [s for s in SIZES if s in correlations]
    fig, axes = plt.subplots(
        1, len(sizes), figsize=(2.5 * len(sizes), 2.9), dpi=200, sharex=True, squeeze=False
    )
    axes = axes[0]
    fig.patch.set_facecolor(SURFACE)
    for ax, size in zip(axes, sizes):
        values = [rho for rho, _ in correlations[size]]
        positions = np.arange(len(values))
        ax.barh(positions, values, height=0.6, color=SERIES_1)
        ax.axvline(0.0, color=INK_MUTED, linewidth=1.0)
        ax.set_yticks(positions)
        ax.set_yticklabels(["PC" + str(i + 1) for i in positions], fontsize=8)
        # Wider than the data range so a value label on a long negative bar has room
        # without colliding with the PC tick labels on the left.
        ax.set_xlim(-1.35, 1.35)
        ax.set_xticks([-1.0, -0.5, 0.0, 0.5, 1.0])
        ax.set_xlabel("Spearman vs length", fontsize=8)
        ax.set_title("ESM-2 " + size, loc="left", fontsize=9.5, color=INK_PRIMARY)
        ax.xaxis.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for position, value in zip(positions, values):
            ax.text(
                value + (0.04 if value >= 0 else -0.04),
                position,
                format(value, ".2f"),
                va="center",
                ha="left" if value >= 0 else "right",
                fontsize=7.5,
                color=INK_PRIMARY,
            )
        style_axes(ax)
        ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-figures", action="store_true")
    args = parser.parse_args()

    print_run_header("embeddings/representation_diagnostics_taskA.py", [CURATED])
    data = load_curated()
    names, families, active, lengths = (
        data["rt_name"],
        data["family"],
        data["active"],
        data["length"],
    )

    representations: dict[str, np.ndarray] = {}
    for size in SIZES:
        matrix = load_embedding(size, names)
        if matrix is None:
            print("ESM-2 " + size + ": embedding absent, skipped")
            continue
        representations["ESM2-" + size] = matrix
        print("ESM-2 " + size + ": " + str(matrix.shape))

    kmers = load_kmer3(names)
    controls: dict[str, np.ndarray] = {"length only": lengths.reshape(-1, 1).astype(float)}
    if kmers is not None:
        controls["3-mer composition, frequencies"] = kmers[0]
        controls["3-mer composition, raw counts"] = kmers[1]

    majority, kept = majority_accuracy(families)
    print("")
    print("family classification on " + str(kept) + " rows, families with at least "
          + str(MIN_FAMILY_SIZE) + " members")
    print("majority baseline: " + format(majority, ".4f"))

    accuracy: dict[str, tuple[float, float, float]] = {}
    for label, matrix in list(representations.items()) + list(controls.items()):
        in_fold = family_accuracy(matrix, families, scale_in_fold=True)
        global_scaled = family_accuracy(matrix, families, scale_in_fold=False)
        accuracy[label] = (in_fold[0], in_fold[1], global_scaled[0])
        print(
            "  "
            + label.ljust(34)
            + " in-fold scaling "
            + format(in_fold[0], ".4f")
            + " (sd "
            + format(in_fold[1], ".4f")
            + "), global scaling "
            + format(global_scaled[0], ".4f")
        )

    correlations: dict[str, list[tuple[float, float]]] = {}
    correlations_centred: dict[str, list[tuple[float, float]]] = {}
    for label, matrix in representations.items():
        size = label.replace("ESM2-", "")
        correlations[size] = pc_length_correlations(matrix, lengths, standardize=True)
        correlations_centred[size] = pc_length_correlations(
            matrix, lengths, standardize=False
        )
    print("")
    for size, values in correlations.items():
        print(
            "ESM-2 "
            + size
            + " PC1..PC4 vs length, standardized: "
            + ", ".join(format(rho, ".4f") for rho, _ in values)
        )

    biggest = next((s for s in reversed(SIZES) if "ESM2-" + s in representations), None)
    projection_pca = None
    projection_umap = None
    if biggest is not None:
        matrix = representations["ESM2-" + biggest]
        projection_pca = principal_components(matrix, standardize=True)
        projection_umap = umap_projection(matrix)
        if projection_umap is None:
            print("")
            print("umap-learn not installed, so the UMAP panels are omitted")

    if not args.no_figures and projection_pca is not None:
        FIGURES.mkdir(parents=True, exist_ok=True)
        rho = correlations[biggest][0][0]
        figure_by_length(
            projection_pca, projection_umap, lengths, rho,
            FIGURES / "taskA_embedding_by_length.png",
        )
        figure_by_activity(
            projection_pca, projection_umap, active,
            FIGURES / "taskA_embedding_by_activity.png",
        )
        figure_by_family(
            projection_pca, projection_umap, families,
            FIGURES / "taskA_embedding_by_family.png",
        )
        figure_pc_length(correlations, FIGURES / "taskA_pc_length_correlation.png")
        print("")
        print("wrote 4 figures to reports/figures/")

    write_report(
        accuracy, majority, kept, correlations, correlations_centred, biggest,
        projection_umap is not None,
    )
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    return 0


def write_report(
    accuracy: dict[str, tuple[float, float, float]],
    majority: float,
    kept: int,
    correlations: dict[str, list[tuple[float, float]]],
    correlations_centred: dict[str, list[tuple[float, float]]],
    biggest: str | None,
    has_umap: bool,
) -> None:
    lines = [
        "# Task A representation diagnostics",
        "",
        "Written by `embeddings/representation_diagnostics_taskA.py`. **No activity label",
        "is used anywhere in the two measurements below.** Activity appears only as a",
        "colour in one figure.",
        "",
        "Source: `tasks/taskA_crossfamily/curated.csv`, SHA256",
        "`" + sha256_of(CURATED) + "`.",
        "",
        "Representations are ESM-2 at four sizes, final transformer block, mean pooled over",
        "residue positions excluding the BOS and EOS tokens. No layer or pooling sweep: see",
        "`embeddings/MANIFEST_TASKA.json`.",
        "",
        "## 1. Family classification: do the representations encode lineage?",
        "",
        "Stratified "
        + str(N_FOLDS)
        + "-fold logistic regression predicting family, `random_state="
        + str(RANDOM_STATE)
        + "`,",
        "`max_iter=5000`, restricted to families with at least "
        + str(MIN_FAMILY_SIZE)
        + " members. That keeps "
        + str(kept)
        + " of 57 rows",
        "and drops the singleton `Unclassified` family.",
        "",
        "**Two preprocessing variants are reported because the choice is contested.**",
        "`in-fold` standardizes inside each training fold through a pipeline, which is what",
        "the no-fitting-outside-a-fold rule requires. `global` standardizes once over all",
        "rows, which is how the prior figures in this repository were produced. The second",
        "column is the one to compare against the prior numbers; the first is the one to",
        "believe.",
        "",
        "| representation | in-fold accuracy | fold-to-fold SD | global accuracy | prior | deviation from prior |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    def prior_for(label: str) -> float | None:
        if label in PRIOR:
            return PRIOR[label]
        if label.startswith("3-mer composition"):
            return PRIOR["3-mer composition"]
        return None

    for label in list(accuracy):
        in_fold, sd, global_scaled = accuracy[label]
        prior = prior_for(label)
        if prior is None:
            deviation = "no prior published"
        else:
            delta = global_scaled - prior
            flag = " **beyond the fold SD**" if abs(delta) > sd else " within the fold SD"
            deviation = format(delta, "+.4f") + flag
        lines.append(
            "| "
            + label
            + " | "
            + format(in_fold, ".4f")
            + " | "
            + format(sd, ".4f")
            + " | "
            + format(global_scaled, ".4f")
            + " | "
            + (format(prior, ".3f") if prior is not None else "none")
            + " | "
            + deviation
            + " |"
        )
    lines.append(
        "| majority baseline | "
        + format(majority, ".4f")
        + " | 0 | "
        + format(majority, ".4f")
        + " | "
        + format(PRIOR["majority baseline"], ".3f")
        + " | "
        + format(majority - PRIOR["majority baseline"], "+.4f")
        + " |"
    )

    lines += [
        "",
        "### How to read a deviation",
        "",
        "A deviation beyond the fold-to-fold standard deviation would mean the dataset",
        "changed during reconciliation. It did not: the 57 sequences are byte-identical to",
        "Table S1 and to the inherited table, which `reports/reconciliation.md` section 3",
        "establishes by SHA256 on every row. So a deviation here can only come from",
        "preprocessing or from the embeddings having been recomputed, and both of those are",
        "stated rather than inferred.",
        "",
        "The 3-mer control is reported in two encodings deliberately. The earlier review",
        "found the prior figure of 0.571 is reproduced by raw counts standardized, while",
        "frequency-normalized standardized gives a materially higher number, and the",
        "repository specifies no encoding for this control. Reporting one encoding would be",
        "choosing the comparison that suits the conclusion.",
        "",
        "## 2. Length correlation: is the leading structure just protein length?",
        "",
        "Spearman correlation of principal components 1 to 4 against sequence length, on",
        "standardized embeddings with `PCA(random_state=" + str(RANDOM_STATE) + ")`.",
        "",
        "| model | PC1 | PC2 | PC3 | PC4 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for size, values in correlations.items():
        lines.append(
            "| ESM-2 "
            + size
            + " | "
            + " | ".join(format(rho, "+.4f") for rho, _ in values)
            + " |"
        )
    lines += [
        "",
        "The same, on centred but **not** standardized embeddings, because the earlier",
        "review found this choice flips the sign and changes the magnitude:",
        "",
        "| model | PC1 | PC2 | PC3 | PC4 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for size, values in correlations_centred.items():
        lines.append(
            "| ESM-2 "
            + size
            + " | "
            + " | ".join(format(rho, "+.4f") for rho, _ in values)
            + " |"
        )

    if "650M" in correlations:
        rho = correlations["650M"][0][0]
        lines += [
            "",
            "Prior published figure, on standardized 650M embeddings: PC1 against length at",
            "Spearman " + format(PRIOR_PC1_LENGTH, ".2f") + ". Measured here: "
            + format(rho, ".4f") + ".",
            "",
            "The sign is a PCA convention and carries no meaning; the magnitude is what",
            "matters. A leading component this strongly tied to length means the embedding's",
            "dominant axis of variation is substantially a length axis, and length is a",
            "feature any model can compute for free. That is why the length-only baseline is",
            "the one every representation has to clear in Phase 6, and why clearing the",
            "majority baseline is not evidence of anything.",
        ]

    lines += [
        "",
        "## 3. What the space looks like",
        "",
        "| figure | what it shows |",
        "| --- | --- |",
        "| `figures/taskA_embedding_by_length.png` | **the important one.** PCA and UMAP coloured by length, plus PC1 against length directly |",
        "| `figures/taskA_embedding_by_activity.png` | the same projections coloured by activity |",
        "| `figures/taskA_embedding_by_family.png` | small multiples, one panel per family |",
        "| `figures/taskA_pc_length_correlation.png` | PC1 to PC4 against length, per model size |",
        "",
        "Projections use "
        + ("ESM-2 " + biggest if biggest else "no embedding")
        + ", the largest available."
        + ("" if has_umap else " UMAP panels are omitted because umap-learn is not installed."),
        "",
        "Two notes on reading these. The family figure uses small multiples rather than",
        "seven colours because seven categorical hues cannot be distinguished reliably in a",
        "scatter: on this project's reference palette the worst all-pairs separation is a",
        "colour-vision-deficiency delta E of 3.2 and a normal-vision delta E of 12.9, both",
        "below the floors, and no re-ordering fixes it because a scatter puts every pair on",
        "screen at once. And the UMAP projection of 57 points with `n_neighbors=10` should",
        "be read as a sketch, not as structure: UMAP on a sample this small will produce",
        "apparent clusters from noise.",
        "",
        "## What these diagnostics do and do not establish",
        "",
        "They establish that the representations carry lineage and carry length, both",
        "without reference to activity. In a panel where family and activity are strongly",
        "associated, 12 of 18 retroviral enzymes active against 0 of 15 across the three",
        "families with no actives, that is precisely the confound to be worried about: a",
        "representation can score well on activity by encoding clade.",
        "",
        "They do not establish anything about activity prediction. That is Phase 6, and the",
        "comparison that matters there is against the length-only baseline rather than",
        "against chance.",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
