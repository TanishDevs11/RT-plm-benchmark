"""Build the complete Task A handcrafted feature set from curated.csv.

This supersedes `features/build_handcrafted.py` for Task A. That script built the matrix
before the panel had a curated table, against `data/rt_sequences.csv`, and it covered
length, amino acid composition, dipeptide composition, a reduced-alphabet 3-mer block, the
Biopython physicochemical descriptors and the structural descriptors. Everything it
computes is reused here unchanged, by import rather than by copy, so the two cannot drift.

Three things are added, each because the benchmark needs them as separate representations:

  * full 3-mer and 4-mer frequencies over the 20-letter alphabet, not the reduced one
  * net charge at pH 7.4
  * the whole set aligned to `curated.csv` and keyed by `rt_name`, with each
    representation block emitted so that Phase 6 can load one without the others

Rules obeyed, from the brief's hard rules
-----------------------------------------
No scaling, no imputation, no feature selection. Each of those is a fit, and a fit belongs
inside a cross-validation fold. What comes out is raw values plus an explicit missingness
mask, so a fold can decide for itself what a missing structural feature means rather than
having to guess whether a zero means zero or means absent.

The k-mer vocabulary, and why dropping a column here is not selection
---------------------------------------------------------------------
The full spaces are 8000 3-mers and 160000 4-mers. Only 6256 and 20115 of them occur
anywhere in the 57 sequences, so the rest are identically zero in every row.

The vocabulary rule, fixed a priori: **keep every k-mer that occurs at least once
anywhere in the panel, and drop only the never-observed ones.**

That is not feature selection, and the distinction is worth being precise about. A column
that is zero in all 57 rows is zero in every training subset and every test subset of
those rows, so no model fitted on any fold can produce a different prediction with it
present than without it. Dropping it is provably inert. It uses the full row set, but only
to establish that fact, and it never looks at a label.

What is deliberately **not** done is thresholding on how many sequences a k-mer appears
in. A rule such as "keep k-mers present in at least six sequences" would cut 6256 3-mers
to 1618 and 20115 4-mers to 274, and those cuts are not inert: they discard columns that
carry signal, chosen by a statistic computed over all the rows including the test fold.
That would be feature selection outside a fold, which the brief forbids and which is one
of the mechanisms behind the artifact this repository exists to correct.

The vocabularies are written to disk so they are frozen rather than re-derived.

    python features/build_handcrafted_taskA.py
    python features/build_handcrafted_taskA.py --no-kmers    # skip the large blocks

Outputs:
    features/handcrafted/taskA_features_v2.csv        length, aac, dpc, physchem, struct
    features/handcrafted/taskA_missing_mask_v2.csv    the mask, same shape
    features/handcrafted/taskA_kmer3.npz             full 3-mer frequencies
    features/handcrafted/taskA_kmer4.npz             full 4-mer frequencies
    features/handcrafted/taskA_kmer{3,4}_vocabulary.txt
    features/handcrafted/FEATURE_DICTIONARY_TASKA.md
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "features"))

from build_handcrafted import (  # noqa: E402
    REDUCED_KMERS,
    STRUCTURE_ALIASES,
    STRUCT_COLUMNS,
    biophysical,
    composition,
    dipeptide_composition,
    reduced_kmer_frequencies,
    structural,
)

from schemas.task_schema import AA20, print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
OUT_DIR = REPO_ROOT / "features" / "handcrafted"
FEATURES = OUT_DIR / "taskA_features_v2.csv"
MASK = OUT_DIR / "taskA_missing_mask_v2.csv"
DICTIONARY = OUT_DIR / "FEATURE_DICTIONARY_TASKA.md"

# Net charge is evaluated at pH 7.4, physiological pH, fixed here rather than passed in so
# that no run can quietly use a different pH from another.
CHARGE_PH = 7.4

KMER_SIZES = (3, 4)


def net_charge(sequence: str) -> float:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis

    return float(ProteinAnalysis(sequence).charge_at_pH(CHARGE_PH))


def kmer_counts(sequence: str, k: int) -> Counter:
    return Counter(sequence[i : i + k] for i in range(len(sequence) - k + 1))


def build_kmer_block(
    names: list[str], sequences: list[str], k: int
) -> tuple[np.ndarray, list[str]]:
    """Frequency matrix over every k-mer observed anywhere, in sorted order.

    Frequencies, not counts: each row is divided by that row's number of k-mer positions,
    so a long sequence does not dominate by length alone. Length is available as its own
    feature for any model that wants it.
    """
    observed: set[str] = set()
    per_row: list[Counter] = []
    for sequence in sequences:
        counts = kmer_counts(sequence, k)
        per_row.append(counts)
        observed.update(counts)
    vocabulary = sorted(observed)
    index = {kmer: position for position, kmer in enumerate(vocabulary)}
    matrix = np.zeros((len(sequences), len(vocabulary)), dtype=np.float32)
    for row, counts in enumerate(per_row):
        positions = max(1, len(sequences[row]) - k + 1)
        for kmer, count in counts.items():
            matrix[row, index[kmer]] = count / positions
    return matrix, vocabulary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-kmers", action="store_true", help="skip the 3-mer and 4-mer blocks"
    )
    args = parser.parse_args()

    print_run_header("features/build_handcrafted_taskA.py", [CURATED])
    with CURATED.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    names = [row["rt_name"] for row in rows]
    sequences = [row["sequence"] for row in rows]
    print("rows: " + str(len(rows)))

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # The tabular block: everything that is not a k-mer frequency.
    records: list[dict[str, object]] = []
    masks: list[dict[str, object]] = []
    structure_notes: list[str] = []
    for name, sequence in zip(names, sequences):
        values: dict[str, object] = {"rt_name": name, "length": len(sequence)}
        values.update(composition(sequence))
        values.update(dipeptide_composition(sequence))
        values.update(reduced_kmer_frequencies(sequence))
        values.update(biophysical(sequence))
        values["bio_net_charge_ph74"] = net_charge(sequence)
        struct, note = structural(name)
        values.update(struct)
        if note:
            structure_notes.append(name + ": " + note)
        records.append(values)
        masks.append(
            {
                key: (1 if (key != "rt_name" and value is None) else 0)
                for key, value in values.items()
            }
            | {"rt_name": name}
        )

    columns = ["rt_name", "length"]
    columns += ["aac_" + residue for residue in AA20]
    columns += sorted(k for k in records[0] if k.startswith("dpc_"))
    columns += ["rk3_" + kmer for kmer in REDUCED_KMERS]
    columns += sorted(k for k in records[0] if k.startswith("bio_"))
    columns += list(STRUCT_COLUMNS)
    missing_columns = [c for c in records[0] if c not in columns]
    if missing_columns:
        raise SystemExit("columns computed but not declared: " + str(missing_columns))

    for path, payload in ((FEATURES, records), (MASK, masks)):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, restval="")
            writer.writeheader()
            for record in payload:
                writer.writerow({c: record.get(c, "") for c in columns})
        print("wrote " + path.relative_to(REPO_ROOT).as_posix())
        print("    sha256 " + sha256_of(path) + ", " + str(len(columns)) + " columns")

    missing_total = sum(
        sum(1 for key, value in record.items() if key != "rt_name" and value is None)
        for record in records
    )
    print("missing cells: " + str(missing_total))
    for note in structure_notes:
        print("  structure note: " + note)

    vocabularies: dict[int, list[str]] = {}
    if not args.no_kmers:
        for k in KMER_SIZES:
            matrix, vocabulary = build_kmer_block(names, sequences, k)
            vocabularies[k] = vocabulary
            path = OUT_DIR / ("taskA_kmer" + str(k) + ".npz")
            np.savez_compressed(
                path, features=matrix, ids=np.array(names, dtype=object)
            )
            vocabulary_path = OUT_DIR / ("taskA_kmer" + str(k) + "_vocabulary.txt")
            vocabulary_path.write_text("\n".join(vocabulary) + "\n", encoding="utf-8")
            print(
                "wrote "
                + path.relative_to(REPO_ROOT).as_posix()
                + " shape="
                + str(matrix.shape)
                + " of "
                + str(20**k)
                + " possible"
            )
            print("    sha256 " + sha256_of(path))
            print("    vocabulary " + vocabulary_path.name + " sha256 " + sha256_of(vocabulary_path))

    write_dictionary(columns, records, vocabularies, structure_notes)
    print("wrote " + DICTIONARY.relative_to(REPO_ROOT).as_posix())
    return 0


def write_dictionary(
    columns: list[str],
    records: list[dict],
    vocabularies: dict[int, list[str]],
    structure_notes: list[str],
) -> None:
    """Define every column, its units, and how it was computed."""
    missing_per_column = {
        column: sum(1 for r in records if r.get(column) is None) for column in columns
    }
    lines = [
        "# Task A handcrafted feature dictionary",
        "",
        "Written by `features/build_handcrafted_taskA.py`. Every column emitted is defined",
        "here, with its units and its computation. A column that matters enough to compute",
        "is a column that matters enough to define.",
        "",
        "Source: `tasks/taskA_crossfamily/curated.csv`, SHA256",
        "`" + sha256_of(CURATED) + "`.",
        "",
        "Row order is the order of `curated.csv`, and the key is `rt_name`. No scaling, no",
        "imputation and no feature selection are applied: these are raw values plus a",
        "missingness mask of the same shape.",
        "",
        "## Representation blocks",
        "",
        "Phase 6 benchmarks several of these blocks separately, so each is listed with the",
        "column prefix that selects it.",
        "",
        "| block | columns | prefix | dimensionality |",
        "| --- | --- | --- | --- |",
        "| length | 1 | `length` | 1 |",
        "| amino acid composition | 20 | `aac_` | 20 |",
        "| dipeptide composition | 400 | `dpc_` | 400 |",
        "| reduced-alphabet 3-mer | " + str(len(REDUCED_KMERS)) + " | `rk3_` | " + str(len(REDUCED_KMERS)) + " |",
        "| physicochemical | "
        + str(len([c for c in columns if c.startswith("bio_")]))
        + " | `bio_` | "
        + str(len([c for c in columns if c.startswith("bio_")]))
        + " |",
        "| structural | " + str(len(STRUCT_COLUMNS)) + " | `struct_` | " + str(len(STRUCT_COLUMNS)) + " |",
    ]
    for k, vocabulary in sorted(vocabularies.items()):
        lines.append(
            "| full "
            + str(k)
            + "-mer frequency | "
            + str(len(vocabulary))
            + " | separate `.npz` | "
            + str(len(vocabulary))
            + " of "
            + str(20**k)
            + " possible |"
        )

    lines += [
        "",
        "## Column definitions",
        "",
        "| column | units | computation | missing rows |",
        "| --- | --- | --- | --- |",
        "| `rt_name` | identifier | the Table S1 laboratory label, the join key | 0 |",
        "| `length` | residues | `len(sequence)` | 0 |",
        "| `aac_X` | fraction | count of residue X divided by length, for each of the 20 standard residues | 0 |",
        "| `dpc_XY` | fraction | count of the ordered pair XY divided by the number of adjacent pairs, length minus 1, for all 400 pairs | 0 |",
        "| `rk3_GGG` | fraction | 3-mer frequency over a 7-group physicochemical alphabet rather than the 20 residues, all 343 emitted | 0 |",
    ]
    definitions = {
        "bio_molecular_weight": ("daltons", "Biopython `ProteinAnalysis.molecular_weight`"),
        "bio_isoelectric_point": ("pH", "Biopython `ProteinAnalysis.isoelectric_point`"),
        "bio_aromaticity": (
            "fraction",
            "Lobry aromaticity, the summed fraction of F, W and Y",
        ),
        "bio_instability_index": (
            "index, dimensionless",
            "Guruprasad instability index; above 40 is conventionally called unstable",
        ),
        "bio_gravy": (
            "Kyte-Doolittle units",
            "grand average of hydropathy, the mean per-residue hydropathy",
        ),
        "bio_net_charge_ph74": (
            "elementary charges",
            "Biopython `ProteinAnalysis.charge_at_pH(7.4)`, at physiological pH",
        ),
        "bio_protparam_frac_helix": (
            "fraction",
            "ProtParam secondary structure fraction, helix-favouring residues; a composition statistic, not a structural prediction",
        ),
        "bio_protparam_frac_turn": ("fraction", "ProtParam turn-favouring fraction"),
        "bio_protparam_frac_sheet": ("fraction", "ProtParam sheet-favouring fraction"),
        "bio_flexibility_mean": (
            "Vihinen flexibility units",
            "mean of the windowed flexibility profile",
        ),
        "bio_flexibility_min": ("Vihinen flexibility units", "minimum of that profile"),
        "bio_flexibility_max": ("Vihinen flexibility units", "maximum of that profile"),
        "bio_flexibility_std": (
            "Vihinen flexibility units",
            "standard deviation of that profile",
        ),
        "struct_n_residues": (
            "residues",
            "residue count in the structure file, emitted so a sequence-structure length mismatch is visible in the matrix",
        ),
        "struct_confidence_mean": (
            "zero to one",
            "mean of the PDB B-factor column. **Not named pLDDT**: the files carry a `PARENT N/A` header and the column's global maximum across all 57 files is 0.99, so it is a per-atom confidence on a zero-to-one scale, and calling it pLDDT would assert a provenance nobody has established",
        ),
        "struct_confidence_min": ("zero to one", "minimum of that column"),
        "struct_confidence_max": ("zero to one", "maximum of that column"),
        "struct_confidence_std": ("zero to one", "standard deviation of that column"),
        "struct_ss_frac_helix": (
            "fraction",
            "fraction of residues assigned helix by the geometric assignment in `build_handcrafted.py`",
        ),
        "struct_ss_frac_strand": ("fraction", "fraction assigned strand"),
        "struct_ss_frac_loop": ("fraction", "fraction assigned neither"),
        "struct_rsa_mean": (
            "fraction",
            "mean relative solvent accessibility over residues",
        ),
        "struct_rsa_std": ("fraction", "standard deviation of relative solvent accessibility"),
        "struct_frac_exposed": (
            "fraction",
            "fraction of residues above the exposure cutoff used in `build_handcrafted.py`",
        ),
        "struct_radius_of_gyration": ("angstroms", "radius of gyration of the model"),
    }
    for column in columns:
        if column in definitions:
            units, how = definitions[column]
            lines.append(
                "| `"
                + column
                + "` | "
                + units
                + " | "
                + how
                + " | "
                + str(missing_per_column[column])
                + " |"
            )

    lines += [
        "",
        "## The k-mer vocabulary rule",
        "",
        "Fixed a priori: **keep every k-mer that occurs at least once anywhere in the",
        "panel, and drop only the never-observed ones.** The vocabularies are frozen to",
        "`taskA_kmer3_vocabulary.txt` and `taskA_kmer4_vocabulary.txt` so they are not",
        "re-derived on a later run.",
        "",
    ]
    for k, vocabulary in sorted(vocabularies.items()):
        lines.append(
            "- k = "
            + str(k)
            + ": "
            + str(len(vocabulary))
            + " of "
            + str(20**k)
            + " possible k-mers occur in the panel, so "
            + str(20**k - len(vocabulary))
            + " columns are identically zero and are dropped."
        )
    lines += [
        "",
        "Dropping those columns is not feature selection. A column that is zero in all 57",
        "rows is zero in every training subset and every test subset of those rows, so no",
        "model fitted on any fold can predict differently with it present than without it.",
        "The drop is provably inert: it uses the full row set, but only to establish that",
        "fact, and it never looks at a label.",
        "",
        "What is deliberately not done is thresholding on how many sequences a k-mer",
        "appears in. A rule such as keeping only k-mers present in at least six sequences",
        "would cut the 3-mer block from 6256 columns to 1618 and the 4-mer block from",
        "20115 to 274. Those cuts are not inert: they discard columns that carry signal,",
        "selected by a statistic computed over all rows including the held-out fold. That",
        "is feature selection outside a fold, which the brief forbids, and it is one of the",
        "mechanisms behind the artifact this repository exists to correct.",
        "",
        "Values are frequencies rather than counts: each row is divided by its own number",
        "of k-mer positions, so a long sequence does not dominate by length alone. Length",
        "is available as its own feature for any model that wants it.",
        "",
        "## Missingness",
        "",
        "`taskA_missing_mask_v2.csv` has the same shape and column order as the feature",
        "file, with 1 where a value could not be computed and 0 where it could. Nothing is",
        "imputed, so a consumer can tell a real zero from an absent value.",
        "",
    ]
    absent = [c for c in columns if missing_per_column.get(c, 0) > 0]
    if absent:
        lines.append("Columns with any missing value:")
        lines.append("")
        for column in absent:
            lines.append(
                "- `" + column + "`: " + str(missing_per_column[column]) + " row(s)"
            )
    else:
        lines.append("No column has a missing value.")
    if structure_notes:
        lines += [
            "",
            "### Structure correspondence notes",
            "",
            "Carried from `features/build_handcrafted.py`, which resolved these rather than",
            "letting them pass silently.",
            "",
        ]
        for note in structure_notes:
            lines.append("- " + note)
    lines += [
        "",
        "Two further correspondence facts, recorded in `features/build_handcrafted.py` and",
        "repeated here because they change what the structural block means:",
        "",
        "- `Vp96-RT` has no file of that name; `Vp-96.pdb` is sequence-identical to it at",
        "  all 312 residues, so the correspondence is established by sequence rather than",
        "  by guessing a filename.",
        "- `Gs-RT` has a 426-residue structure against a 419-residue sequence. Only",
        "  aggregate structural features are computed, so nothing is corrupted, but",
        "  per-residue structural features cannot be aligned for that row without an",
        "  alignment. `struct_n_residues` is emitted so the discrepancy is visible in the",
        "  matrix itself.",
    ]
    DICTIONARY.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
