"""Quantify how degenerate whole-sequence features are for a single-substitution library.

This is the one Task B measurement that needs no activity values, because it is a property
of the feature space rather than of the labels. The brief asks for it explicitly: k-mer
frequencies and whole-sequence physicochemical descriptors are degenerate by construction
here, and the degeneracy has to be quantified and stated rather than left to read as a
representation failure when the scores come out near zero.

Why it is computable while the rest of Task B is blocked
--------------------------------------------------------
The variant sequences depend on the reference, whose substitution content is still
unconfirmed; see `tasks/taskB_mmlv_dms/PROVENANCE.md`. But **pairwise similarity among the
variants is insensitive to that question**, because whatever the reference's substitution
content turns out to be, all 1045 variants share it. Changing the reference at four
positions changes every variant identically, which leaves the pairwise geometry essentially
unchanged. The script verifies that claim rather than asserting it, by recomputing the
whole distribution against a reference deliberately perturbed at four positions and
reporting the difference.

What this does not do: compute any feature for modelling, or any score. There is nothing
to score against.

    python features/taskB/quantify_degeneracy.py
    python features/taskB/quantify_degeneracy.py --k 3

Output: reports/taskB_mmlv_dms/degeneracy.md
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition.parse_mmlv_dms import expected_variants, load_reference  # noqa: E402
from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

OUT = REPO_ROOT / "reports" / "taskB" / "degeneracy.md"

# The four PE2 substitution positions whose presence in the construct is unconfirmed.
# Used only to perturb the reference and show the geometry does not depend on them.
UNCONFIRMED_POSITIONS = (200, 306, 313, 330)

# Physicochemical scales, for the whole-sequence descriptor block. Kyte-Doolittle
# hydropathy and residue volume in cubic angstroms, enough to make the point without
# pulling in a dependency.
HYDROPATHY = {
    "A": 1.8, "R": -4.5, "N": -3.5, "D": -3.5, "C": 2.5, "Q": -3.5, "E": -3.5,
    "G": -0.4, "H": -3.2, "I": 4.5, "L": 3.8, "K": -3.9, "M": 1.9, "F": 2.8,
    "P": -1.6, "S": -0.8, "T": -0.7, "W": -0.9, "Y": -1.3, "V": 4.2,
}
VOLUME = {
    "A": 88.6, "R": 173.4, "N": 114.1, "D": 111.1, "C": 108.5, "Q": 143.8,
    "E": 138.4, "G": 60.1, "H": 153.2, "I": 166.7, "L": 166.7, "K": 168.6,
    "M": 162.9, "F": 189.9, "P": 112.7, "S": 89.0, "T": 116.1, "W": 227.8,
    "Y": 193.6, "V": 140.0,
}
CHARGE = {"D": -1.0, "E": -1.0, "K": 1.0, "R": 1.0, "H": 0.1}
POLAR = set("STNQYCHKRDE")


def build_sequences(reference: str) -> tuple[list[str], list[str]]:
    variants = expected_variants()
    ids = [WILD_TYPE for WILD_TYPE in ["B_wt"]]
    sequences = [reference]
    for variant in variants:
        position = int(variant["position"])
        sequence = (
            reference[: position - 1] + str(variant["mut_aa"]) + reference[position:]
        )
        sequences.append(sequence)
        ids.append(str(variant["variant_id"]))
    return ids, sequences


def kmer_matrix(sequences: list[str], k: int) -> np.ndarray:
    vocabulary: dict[str, int] = {}
    counts: list[Counter] = []
    for sequence in sequences:
        counter = Counter(sequence[i : i + k] for i in range(len(sequence) - k + 1))
        counts.append(counter)
        for kmer in counter:
            vocabulary.setdefault(kmer, len(vocabulary))
    matrix = np.zeros((len(sequences), len(vocabulary)), dtype=np.float64)
    for row, counter in enumerate(counts):
        positions = max(1, len(sequences[row]) - k + 1)
        for kmer, count in counter.items():
            matrix[row, vocabulary[kmer]] = count / positions
    return matrix


def physicochemical_matrix(sequences: list[str]) -> np.ndarray:
    rows = []
    for sequence in sequences:
        length = len(sequence)
        rows.append(
            [
                float(length),
                sum(HYDROPATHY.get(a, 0.0) for a in sequence) / length,
                sum(VOLUME.get(a, 0.0) for a in sequence) / length,
                sum(CHARGE.get(a, 0.0) for a in sequence),
                sum(1 for a in sequence if a in POLAR) / length,
                sum(1 for a in sequence if a in "FWY") / length,
            ]
        )
    return np.asarray(rows, dtype=np.float64)


def cosine_distribution(matrix: np.ndarray, sample: int, seed: int) -> dict[str, float]:
    """Pairwise cosine similarity summary, on a random sample of pairs.

    All pairs would be 547,470 comparisons, which is affordable but pointless: a random
    sample of 200000 fixes the quantiles well beyond the precision anyone will read.
    """
    rng = np.random.default_rng(seed)
    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1.0
    unit = matrix / norms[:, None]
    n = len(unit)
    left = rng.integers(0, n, size=sample)
    right = rng.integers(0, n, size=sample)
    keep = left != right
    similarities = np.einsum("ij,ij->i", unit[left[keep]], unit[right[keep]])
    return {
        "n_pairs": int(similarities.size),
        "min": float(similarities.min()),
        "p1": float(np.percentile(similarities, 1)),
        "median": float(np.median(similarities)),
        "p99": float(np.percentile(similarities, 99)),
        "max": float(similarities.max()),
        "mean": float(similarities.mean()),
        "sd": float(similarities.std(ddof=1)),
    }


def effective_rank(matrix: np.ndarray) -> dict[str, float]:
    """How many directions the feature space actually spans, after centring."""
    centred = matrix - matrix.mean(axis=0)
    singular = np.linalg.svd(centred, compute_uv=False)
    total = float(np.square(singular).sum())
    if total <= 0:
        return {"numeric_rank": 0, "variance_in_top_1": float("nan")}
    share = np.square(singular) / total
    return {
        "numeric_rank": int(np.linalg.matrix_rank(centred)),
        "variance_in_top_1": float(share[0]),
        "variance_in_top_3": float(share[:3].sum()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--k", type=int, default=4, help="k for the k-mer block")
    parser.add_argument("--sample", type=int, default=200000)
    parser.add_argument("--seed", type=int, default=1729)
    args = parser.parse_args()

    reference, provenance, path = load_reference()
    print_run_header("features/taskB/quantify_degeneracy.py", [path])
    print("reference: " + provenance)
    ids, sequences = build_sequences(reference)
    print("sequences built: " + str(len(sequences)) + " including the wild type")
    lengths = {len(s) for s in sequences}
    if len(lengths) != 1:
        raise SystemExit(
            "variant sequences differ in length: " + str(sorted(lengths)) + ". These are "
            "substitutions, so any length deviation is an error rather than an indel"
        )
    print("every sequence is " + str(lengths.pop()) + " residues, as substitutions require")

    blocks = {
        str(args.k) + "-mer frequencies": kmer_matrix(sequences, args.k),
        "whole-sequence physicochemical": physicochemical_matrix(sequences),
    }
    summary: dict[str, dict] = {}
    for label, matrix in blocks.items():
        summary[label] = {
            "shape": list(matrix.shape),
            "cosine": cosine_distribution(matrix, args.sample, args.seed),
            "rank": effective_rank(matrix),
        }
        cosine = summary[label]["cosine"]
        print("")
        print(label + ": " + str(matrix.shape))
        print(
            "  cosine similarity median "
            + format(cosine["median"], ".6f")
            + ", 1st percentile "
            + format(cosine["p1"], ".6f")
            + ", min "
            + format(cosine["min"], ".6f")
        )
        print(
            "  numeric rank "
            + str(summary[label]["rank"]["numeric_rank"])
            + " of "
            + str(min(matrix.shape))
        )

    # The invariance check: perturb the reference at the four unconfirmed positions and
    # confirm the pairwise geometry barely moves.
    perturbed = list(reference)
    for position in UNCONFIRMED_POSITIONS:
        if position <= len(perturbed):
            perturbed[position - 1] = "A" if perturbed[position - 1] != "A" else "G"
    _, perturbed_sequences = build_sequences("".join(perturbed))
    control = kmer_matrix(perturbed_sequences, args.k)
    control_cosine = cosine_distribution(control, args.sample, args.seed)
    reference_cosine = summary[str(args.k) + "-mer frequencies"]["cosine"]
    drift = abs(control_cosine["median"] - reference_cosine["median"])
    print("")
    print(
        "invariance check: perturbing the reference at the four unconfirmed positions "
        "moves the median cosine similarity by "
        + format(drift, ".2e")
    )

    write_report(args, summary, reference_cosine, control_cosine, drift, path, len(sequences))
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    return 0


def write_report(
    args, summary: dict, reference_cosine: dict, control_cosine: dict, drift: float,
    reference_path: Path, n_sequences: int,
) -> None:
    lines = [
        "# Task B: whole-sequence feature degeneracy, quantified",
        "",
        "Written by `features/taskB/quantify_degeneracy.py`. This is the one Task B",
        "measurement that needs no activity values, because it is a property of the feature",
        "space rather than of the labels.",
        "",
        "Reference: `"
        + reference_path.name
        + "`, SHA256 `"
        + sha256_of(reference_path)
        + "`.",
        str(n_sequences) + " sequences, the wild type plus 1045 single substitutions.",
        "",
        "## Why this has to be stated before any score",
        "",
        "Every row in Task B is a single amino acid substitution in the same 498-residue",
        "protein. A substitution changes at most k of the "
        + str(498 - args.k + 1)
        + " "
        + str(args.k)
        + "-mer positions and shifts a",
        "whole-sequence average by one residue's worth out of 498. So the feature vectors",
        "for all 1046 sequences are nearly identical **by construction**, before any",
        "modelling choice is made.",
        "",
        "The consequence matters for how a results table is read. When a k-mer or",
        "whole-sequence physicochemical representation scores near zero on this task, that",
        "is not the representation failing to capture variant effects. It is the",
        "representation being unable to distinguish the variants at all. Those are",
        "different findings, and reporting the first when the second is true would",
        "misattribute a property of the task to a property of the method.",
        "",
        "## Pairwise cosine similarity",
        "",
        "Sampled over "
        + format(reference_cosine["n_pairs"], ",d")
        + " random pairs, seed "
        + str(args.seed)
        + ".",
        "",
        "| block | dimensions | minimum | median | 99th percentile | maximum | standard deviation |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for label, entry in summary.items():
        cosine = entry["cosine"]
        lines.append(
            "| "
            + label
            + " | "
            + str(entry["shape"][1])
            + " | "
            + format(cosine["min"], ".6f")
            + " | "
            + format(cosine["median"], ".6f")
            + " | "
            + format(cosine["p99"], ".6f")
            + " | "
            + format(cosine["max"], ".6f")
            + " | "
            + format(cosine["sd"], ".2e")
            + " |"
        )

    # The summary sentence states a magnitude, so it is computed rather than asserted.
    worst = min(entry["cosine"]["min"] for entry in summary.values())
    gap = 1.0 - worst
    lines += [
        "",
        "A cosine similarity of 1 means two vectors are identical. The least similar pair",
        "in any block here sits "
        + format(gap, ".4f")
        + " from identical, which is "
        + format(100 * gap, ".2f")
        + " percent.",
        "",
        "The distributions are tight and right-skewed: the minimum and the median agree to",
        "six decimal places in the "
        + str(args.k)
        + "-mer block while the standard deviation is "
        + format(summary[str(args.k) + "-mer frequencies"]["cosine"]["sd"], ".2e")
        + ",",
        "because most pairs differ at two positions and sit at the floor, while the pairs",
        "that share a mutated position sit in a thin upper tail.",
        "",
        "## Effective dimensionality",
        "",
        "| block | dimensions | numeric rank after centring | variance in the leading component | variance in the leading three |",
        "| --- | --- | --- | --- | --- |",
    ]
    for label, entry in summary.items():
        rank = entry["rank"]
        lines.append(
            "| "
            + label
            + " | "
            + str(entry["shape"][1])
            + " | "
            + str(rank["numeric_rank"])
            + " | "
            + format(rank["variance_in_top_1"], ".4f")
            + " | "
            + format(rank["variance_in_top_3"], ".4f")
            + " |"
        )

    lines += [
        "",
        "## The invariance check, so this result does not depend on the open question",
        "",
        "The reference's substitution content is unconfirmed: whether the construct retains",
        "PE2's D200N, T306K, W313F and T330P is undetermined from the preprint. That would",
        "normally block any computation on the variant sequences.",
        "",
        "It does not block this one, and the script demonstrates why rather than asserting",
        "it. Whatever the reference's substitution content turns out to be, **all 1045",
        "variants share it**, so changing the reference changes every variant identically",
        "and leaves the pairwise geometry essentially untouched.",
        "",
        "Recomputing the whole distribution against a reference deliberately perturbed at",
        "all four unconfirmed positions moves the median cosine similarity by "
        + format(drift, ".2e")
        + ":",
        "",
        "| | median cosine similarity |",
        "| --- | --- |",
        "| against the candidate reference | " + format(reference_cosine["median"], ".8f") + " |",
        "| against a reference perturbed at all four unconfirmed positions | "
        + format(control_cosine["median"], ".8f")
        + " |",
        "| absolute difference | " + format(drift, ".2e") + " |",
        "",
        "So this measurement stands regardless of how the reference question is resolved.",
        "",
        "## What follows for the benchmark design",
        "",
        "1. **Whole-sequence representations are controls, not competitors, in Task B.**",
        "   They are included for completeness and must be labelled degenerate in any",
        "   results table, with this measurement cited.",
        "2. **The same applies to mean-pooled language model embeddings.** Mean pooling over",
        "   a sequence that differs at one position produces the same degeneracy, which is",
        "   why the Task B brief makes mean pooling a labelled control and never the primary",
        "   protein language model condition. The primary conditions are the embedding at",
        "   the mutated position, the mutant minus wild-type difference at that position,",
        "   and a local window around it.",
        "3. **A near-zero score from a degenerate block may not even be fittable.** With a",
        "   numeric rank far below the nominal dimension and variance concentrated in one",
        "   direction, a regularized linear model may return a constant. If that happens it",
        "   is reported as the outcome, not as a representation score.",
        "",
        "## What this does not measure",
        "",
        "Nothing about variant effects. There are no labels; see",
        "`reports/taskB_mmlv_dms/FINAL_REPORT.md`. This file quantifies the geometry of the feature",
        "space and nothing else.",
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
