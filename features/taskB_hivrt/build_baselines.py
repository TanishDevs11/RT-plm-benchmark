"""Build the baseline feature matrices for the HIV-1 RT phenotype task.

The mutation one-hot is the real competition here, not a straw man. It is the classic
representation for this dataset, it is what rules-based systems approximate, and two
decades of work suggests it is hard to beat. Every other representation in this task has
to clear it.

Unlike the single-substitution library in the M-MLV task, isolates here differ at many
positions at once, so k-mer and whole-sequence descriptors are **not** degenerate and are
legitimate baselines rather than labelled controls. That difference is measured rather
than asserted: the pairwise cosine similarity of each block is reported, so the contrast
with the M-MLV task's 0.9840 median is visible.

Blocks produced, each as its own matrix aligned to the isolate table:

  `mutation_onehot`   one binary indicator per observed position-and-residue
  `drm`               counts and indicators over the published HIVDB major resistance positions
  `physicochemical`   whole-sequence descriptors plus summaries over the mutated positions
  `kmer3`             3-mer frequencies over the reconstructed sequence

No scaling, no imputation, no feature selection. Raw values plus the column names, with
scaling and imputation left to the inner loop of the modelling phase.

    python features/taskB_hivrt/build_baselines.py

Outputs:
    features/taskB_hivrt/<block>.npz, with `features`, `columns` and `ids`
    features/taskB_hivrt/FEATURE_DICTIONARY.md
    features/taskB_hivrt/degeneracy.json
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_hivrt"
ISOLATES = TASK_DIR / "curated_isolates.csv"
REFERENCE = TASK_DIR / "reference.fasta"
OUT_DIR = REPO_ROOT / "features" / "taskB_hivrt"
DICTIONARY = OUT_DIR / "FEATURE_DICTIONARY.md"
DEGENERACY = OUT_DIR / "degeneracy.json"

PRIMARY_DATASET = "filtered"
AA20 = "ACDEFGHIKLMNPQRSTVWY"
UNKNOWN = "X"

# The major drug resistance positions HIVDB publishes on its genotype-phenotype dataset
# page, quoted there as the positions used for its own filtering. Reproduced exactly.
HIVDB_MAJOR = {
    "NRTI": (41, 65, 70, 74, 75, 151, 184, 210, 215),
    "NNRTI": (100, 101, 103, 106, 181, 188, 190, 230),
}
# The specific residues HIVDB names for the NNRTI positions. The NRTI list is given by
# position only on that page, so no residue restriction is applied there.
HIVDB_NNRTI_RESIDUES = {
    100: "I", 101: "P", 103: "N", 106: "AM", 181: "CIA",
    188: "CLH", 190: "AESQ", 230: "L",
}

# Thymidine analogue mutation packages, which travel together under treatment selection.
TAM1 = ("M41L", "L210W", "T215Y")
TAM2 = ("D67N", "K70R", "T215F", "K219Q")

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


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_reference() -> str:
    return "".join(
        line.strip()
        for line in REFERENCE.read_text(encoding="utf-8").splitlines()
        if line and not line.startswith(">")
    ).upper()


def mutation_onehot(rows: list[dict]) -> tuple[np.ndarray, list[str]]:
    """One binary indicator per position-and-residue actually observed.

    The full space is 560 positions by 20 residues, 11200 columns, of which the great
    majority are never observed. Dropping a column that is zero in every row is provably
    inert: it is zero in every training and test subset too, so no model can predict
    differently with it present. It is not feature selection, and no frequency threshold
    is applied, because a threshold would discard columns that carry signal using a
    statistic computed over all rows including the held-out ones.
    """
    observed: set[tuple[int, str]] = set()
    parsed: list[list[tuple[int, str]]] = []
    for row in rows:
        entries: list[tuple[int, str]] = []
        for token in (row["mutations"] or "").split(";"):
            token = token.strip()
            if len(token) < 3:
                continue
            position_text = token[1:-1]
            residue = token[-1]
            if not position_text.isdigit() or residue not in AA20:
                continue
            entry = (int(position_text), residue)
            entries.append(entry)
            observed.add(entry)
        parsed.append(entries)
    columns = sorted(observed)
    index = {entry: position for position, entry in enumerate(columns)}
    matrix = np.zeros((len(rows), len(columns)), dtype=np.float32)
    for row_index, entries in enumerate(parsed):
        for entry in entries:
            matrix[row_index, index[entry]] = 1.0
    names = [str(position) + residue for position, residue in columns]
    return matrix, names


def drm_features(rows: list[dict], reference: str) -> tuple[np.ndarray, list[str]]:
    """Counts and indicators over the published HIVDB major resistance positions."""
    columns: list[str] = []
    for drug_class, positions in HIVDB_MAJOR.items():
        for position in positions:
            columns.append("major_" + drug_class + "_" + str(position))
    columns += [
        "n_major_NRTI",
        "n_major_NNRTI",
        "n_mutations_total",
        "tam1_count",
        "tam2_count",
        "tam1_complete",
        "tam2_complete",
    ]
    index = {name: position for position, name in enumerate(columns)}
    matrix = np.zeros((len(rows), len(columns)), dtype=np.float32)

    for row_index, row in enumerate(rows):
        tokens = [t.strip() for t in (row["mutations"] or "").split(";") if t.strip()]
        positions_mutated: set[int] = set()
        for token in tokens:
            text = token[1:-1]
            if text.isdigit():
                positions_mutated.add(int(text))
        for drug_class, positions in HIVDB_MAJOR.items():
            hits = 0
            for position in positions:
                if position in positions_mutated:
                    matrix[row_index, index["major_" + drug_class + "_" + str(position)]] = 1.0
                    hits += 1
            matrix[row_index, index["n_major_" + drug_class]] = float(hits)
        matrix[row_index, index["n_mutations_total"]] = float(len(tokens))
        tam1 = sum(1 for m in TAM1 if m in tokens)
        tam2 = sum(1 for m in TAM2 if m in tokens)
        matrix[row_index, index["tam1_count"]] = float(tam1)
        matrix[row_index, index["tam2_count"]] = float(tam2)
        matrix[row_index, index["tam1_complete"]] = 1.0 if tam1 == len(TAM1) else 0.0
        matrix[row_index, index["tam2_complete"]] = 1.0 if tam2 == len(TAM2) else 0.0
    return matrix, columns


def physicochemical(rows: list[dict], reference: str) -> tuple[np.ndarray, list[str]]:
    columns = [
        "n_unknown_positions",
        "n_mutations",
        "mean_hydropathy",
        "mean_volume",
        "net_charge",
        "fraction_polar",
        "fraction_aromatic",
        "sum_delta_hydropathy",
        "sum_delta_volume",
        "sum_delta_charge",
        "mean_abs_delta_hydropathy",
    ]
    matrix = np.zeros((len(rows), len(columns)), dtype=np.float32)
    for row_index, row in enumerate(rows):
        sequence = row["sequence"]
        determinate = [a for a in sequence if a in AA20]
        length = max(1, len(determinate))
        delta_h = delta_v = delta_c = 0.0
        abs_h = 0.0
        tokens = [t.strip() for t in (row["mutations"] or "").split(";") if t.strip()]
        for token in tokens:
            wild, mutant = token[0], token[-1]
            if wild in AA20 and mutant in AA20:
                dh = HYDROPATHY[mutant] - HYDROPATHY[wild]
                delta_h += dh
                abs_h += abs(dh)
                delta_v += VOLUME[mutant] - VOLUME[wild]
                delta_c += CHARGE.get(mutant, 0.0) - CHARGE.get(wild, 0.0)
        values = [
            float(row["n_unknown_positions"]),
            float(len(tokens)),
            sum(HYDROPATHY[a] for a in determinate) / length,
            sum(VOLUME[a] for a in determinate) / length,
            sum(CHARGE.get(a, 0.0) for a in determinate),
            sum(1 for a in determinate if a in POLAR) / length,
            sum(1 for a in determinate if a in "FWY") / length,
            delta_h,
            delta_v,
            delta_c,
            abs_h / max(1, len(tokens)),
        ]
        matrix[row_index] = np.asarray(values, dtype=np.float32)
    return matrix, columns


def kmer_matrix(rows: list[dict], k: int) -> tuple[np.ndarray, list[str]]:
    observed: dict[str, int] = {}
    counts: list[Counter] = []
    for row in rows:
        sequence = row["sequence"]
        counter = Counter(
            sequence[i : i + k]
            for i in range(len(sequence) - k + 1)
            if UNKNOWN not in sequence[i : i + k]
        )
        counts.append(counter)
        for kmer in counter:
            observed.setdefault(kmer, len(observed))
    matrix = np.zeros((len(rows), len(observed)), dtype=np.float32)
    for row_index, counter in enumerate(counts):
        total = max(1, sum(counter.values()))
        for kmer, count in counter.items():
            matrix[row_index, observed[kmer]] = count / total
    columns = [k for k, _ in sorted(observed.items(), key=lambda kv: kv[1])]
    return matrix, columns


def cosine_summary(matrix: np.ndarray, seed: int = 1729, sample: int = 200000) -> dict:
    rng = np.random.default_rng(seed)
    norms = np.linalg.norm(matrix, axis=1)
    norms[norms == 0] = 1.0
    unit = matrix / norms[:, None]
    n = len(unit)
    left = rng.integers(0, n, size=sample)
    right = rng.integers(0, n, size=sample)
    keep = left != right
    values = np.einsum("ij,ij->i", unit[left[keep]], unit[right[keep]])
    return {
        "n_pairs": int(values.size),
        "min": float(values.min()),
        "median": float(np.median(values)),
        "max": float(values.max()),
        "sd": float(values.std(ddof=1)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", default=PRIMARY_DATASET, choices=("filtered", "unfiltered"))
    args = parser.parse_args()

    print_run_header("features/taskB_hivrt/build_baselines.py", [ISOLATES, REFERENCE])
    reference = load_reference()
    rows = [r for r in read(ISOLATES) if r["dataset"] == args.dataset]
    ids = [r["drug_class"] + ":" + r["isolate_id"] for r in rows]
    print("dataset: " + args.dataset + ", isolate rows: " + str(len(rows)))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    blocks = {
        "mutation_onehot": mutation_onehot(rows),
        "drm": drm_features(rows, reference),
        "physicochemical": physicochemical(rows, reference),
        "kmer3": kmer_matrix(rows, 3),
    }

    degeneracy: dict = {"dataset": args.dataset, "n_rows": len(rows), "blocks": {}}
    for name, (matrix, columns) in blocks.items():
        path = OUT_DIR / (args.dataset + "_" + name + ".npz")
        np.savez_compressed(
            path,
            features=matrix,
            columns=np.array(columns, dtype=object),
            ids=np.array(ids, dtype=object),
        )
        summary = cosine_summary(matrix)
        degeneracy["blocks"][name] = {
            "shape": list(matrix.shape),
            "cosine": summary,
            "sha256": sha256_of(path),
        }
        print(
            "  "
            + name.ljust(18)
            + str(matrix.shape)
            + "  median pairwise cosine "
            + format(summary["median"], ".4f")
        )

    DEGENERACY.write_text(json.dumps(degeneracy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_dictionary(blocks, degeneracy, args.dataset, len(rows))
    print("")
    print("wrote " + DEGENERACY.relative_to(REPO_ROOT).as_posix())
    print("wrote " + DICTIONARY.relative_to(REPO_ROOT).as_posix())
    return 0


def write_dictionary(blocks: dict, degeneracy: dict, dataset: str, n_rows: int) -> None:
    lines = [
        "# Task B HIV-1 RT baseline feature dictionary",
        "",
        "Written by `features/taskB_hivrt/build_baselines.py`. No scaling, no imputation,",
        "no feature selection: raw values plus column names, with scaling and imputation",
        "left to the inner loop of the modelling phase.",
        "",
        "Dataset: `" + dataset + "`, " + str(n_rows) + " isolate rows. Rows are keyed by",
        "`drug_class:isolate_id`, because an isolate id can appear in both drug classes with",
        "a class-specific reconstructed sequence.",
        "",
        "## Blocks",
        "",
        "| block | shape | median pairwise cosine | what it is |",
        "| --- | --- | --- | --- |",
    ]
    described = {
        "mutation_onehot": "one binary indicator per observed position-and-residue; the classic baseline for this dataset and the one every other representation has to beat",
        "drm": "indicators and counts over the major drug resistance positions HIVDB publishes, plus the TAM1 and TAM2 package counts",
        "physicochemical": "whole-sequence descriptors plus summed physicochemical changes across the mutated positions",
        "kmer3": "3-mer frequencies over the reconstructed sequence, skipping any k-mer containing an indeterminate position",
    }
    for name, entry in degeneracy["blocks"].items():
        lines.append(
            "| `"
            + name
            + "` | "
            + str(tuple(entry["shape"]))
            + " | "
            + format(entry["cosine"]["median"], ".4f")
            + " | "
            + described[name]
            + " |"
        )

    lines += [
        "",
        "## Why these are baselines here and controls in the M-MLV task",
        "",
        "In the M-MLV saturated mutagenesis task every row is a single substitution in one",
        "protein, so k-mer and whole-sequence features have a median pairwise cosine",
        "similarity of 0.9840 and 0.999998 respectively: they cannot distinguish the",
        "variants at all, and a near-zero score from them says nothing about the",
        "representation.",
        "",
        "That does not hold here. Isolates differ at many positions at once, so the same",
        "blocks carry real variation, as the median cosine column above shows. They are",
        "legitimate competitors rather than labelled controls, and a near-zero score from",
        "one of them would be a finding about the representation.",
        "",
        "## The one-hot vocabulary rule",
        "",
        "The full space is 560 positions by 20 residues, 11200 columns, of which most are",
        "never observed. Only observed position-and-residue combinations get a column.",
        "",
        "Dropping a column that is zero in every row is **provably inert**: it is zero in",
        "every training and test subset too, so no model fitted on any fold can predict",
        "differently with it present. It is not feature selection. No frequency threshold is",
        "applied, because a threshold would discard columns carrying signal on the basis of",
        "a statistic computed over all rows including the held-out ones.",
        "",
        "## Column definitions",
        "",
        "| column | units | computation |",
        "| --- | --- | --- |",
        "| `<position><residue>` | binary | 1 if the isolate carries that residue at that position |",
        "| `major_<class>_<position>` | binary | 1 if the isolate is mutated at a published HIVDB major resistance position for that drug class |",
        "| `n_major_NRTI`, `n_major_NNRTI` | count | number of major positions mutated |",
        "| `n_mutations_total` | count | mutations relative to consensus B |",
        "| `tam1_count`, `tam2_count` | count | members of each thymidine analogue mutation package present |",
        "| `tam1_complete`, `tam2_complete` | binary | 1 if the whole package is present |",
        "| `n_unknown_positions` | count | positions encoded X; a sequencing-coverage proxy, not biology |",
        "| `mean_hydropathy`, `mean_volume` | Kyte-Doolittle units, cubic angstroms | averaged over determinate residues |",
        "| `net_charge`, `fraction_polar`, `fraction_aromatic` | charges, fractions | over determinate residues |",
        "| `sum_delta_*` | per-mutation sums | change from wild-type to mutant residue, summed over the isolate's mutations |",
        "| `mean_abs_delta_hydropathy` | Kyte-Doolittle units | mean absolute hydropathy change per mutation |",
        "",
        "The HIVDB major resistance positions, reproduced from the source's own dataset page:",
        "",
        "| class | positions |",
        "| --- | --- |",
    ]
    for drug_class, positions in HIVDB_MAJOR.items():
        lines.append("| " + drug_class + " | " + ", ".join(str(p) for p in positions) + " |")
    lines += [
        "",
        "`n_unknown_positions` deserves a warning. It is a count of positions the assay did",
        "not resolve, so it measures sequencing coverage rather than biology. If it turns out",
        "to carry predictive weight, that is a property of how the data was collected and",
        "must be reported as such rather than as a finding about resistance.",
    ]
    DICTIONARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
