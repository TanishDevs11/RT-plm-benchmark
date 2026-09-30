"""Build the handcrafted feature matrix, one per task.

Rules this script obeys
-----------------------
No scaling. No imputation. No feature selection. Every one of those is a fit, and a fit
belongs inside a cross-validation fold in the modelling phase, not here. What comes out is
raw values plus an explicit missingness mask, so that a downstream fold can decide for
itself what to do about a missing structural feature without having to guess whether a zero
means zero or means absent.

The k-mer question
------------------
The brief asks for selected k-mer frequencies with k and the selection rule fixed a priori.
There is a tension: any rule that picks k-mers by how they are distributed in this dataset is
feature selection, which is forbidden here. So the selection is made structurally rather than
statistically: k is 3, and the alphabet is reduced from 20 residues to 7 physicochemical
groups, giving 7 cubed, so 343 features, all of which are emitted. Nothing is chosen by
looking at the data, and nothing is dropped.

Structural features
-------------------
Computed from the inherited models in `data/structures/`. Two things about those models are
recorded rather than assumed:

First, their provenance is undocumented in this repository. The brief calls them AlphaFold
models; the files carry a `PARENT N/A` header and a B-factor column whose global maximum
across all 57 files is 0.99, so the column is a per-atom confidence on a zero to one scale
rather than a pLDDT on a zero to one hundred scale. The feature is therefore named
`struct_confidence_mean` and not `plddt`, because calling it pLDDT would assert a provenance
nobody has established.

Second, two structures do not correspond one to one with their sequences, and both are handled
explicitly rather than silently:

- `Vp96-RT` has no file of that name. `Vp-96.pdb` is sequence-identical to it at all 312
  residues, so the correspondence is established by sequence rather than by guessing at a
  filename, and it is recorded in the feature dictionary.
- `Gs-RT` has a structure of 426 residues against a sequence of 419. Only aggregate
  structural features are computed here, so the mismatch does not corrupt anything, but it
  means per-residue structural features cannot be aligned for this row without an alignment.
  `struct_n_residues` is emitted so the discrepancy is visible in the matrix itself.
- `Line1-RT` has no structure at all. Its structural features are missing, and the mask says
  so.

    python features/build_handcrafted.py
"""

from __future__ import annotations

import argparse
import csv
import itertools
import math
import sys
import warnings
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, read_task_table, sha256_of  # noqa: E402

warnings.filterwarnings("ignore")

AA20 = "ACDEFGHIKLMNPQRSTVWY"

# Seven physicochemical groups covering all twenty residues exactly once. Fixed a priori;
# this is the whole of the k-mer selection rule.
REDUCED_GROUPS: dict[str, str] = {
    "a": "AGV",
    "b": "ILFP",
    "c": "YMTS",
    "d": "HNQW",
    "e": "RK",
    "f": "DE",
    "g": "C",
}
REDUCED_OF = {residue: group for group, members in REDUCED_GROUPS.items() for residue in members}
KMER_K = 3

# Theoretical maximum solvent accessible surface area per residue, in square angstroms, from
# Tien et al. 2013. Used only as the denominator for relative solvent accessibility.
MAX_ASA: dict[str, float] = {
    "A": 129.0, "R": 274.0, "N": 195.0, "D": 193.0, "C": 167.0,
    "E": 223.0, "Q": 225.0, "G": 104.0, "H": 224.0, "I": 197.0,
    "L": 201.0, "K": 236.0, "M": 224.0, "F": 240.0, "P": 159.0,
    "S": 155.0, "T": 172.0, "W": 285.0, "Y": 263.0, "V": 174.0,
}

# A residue is conventionally called exposed above this relative accessibility.
EXPOSED_THRESHOLD = 0.25

STRUCTURE_DIR = REPO_ROOT / "data/structures"
# Established by sequence identity, not by filename similarity. See the module docstring.
STRUCTURE_ALIASES: dict[str, str] = {"Vp96-RT": "Vp-96"}

TASK_SOURCES: dict[str, tuple[Path, Path]] = {
    "A": (REPO_ROOT / "tasks/taskA_crossfamily/curated.csv", REPO_ROOT / "data/rt_sequences.csv"),
    "A2": (REPO_ROOT / "tasks/taskA2_evolved/curated.csv", REPO_ROOT / "nonexistent"),
    "B": (REPO_ROOT / "tasks/taskB_mmlv_dms/curated.csv", REPO_ROOT / "nonexistent"),
}

OUT_DIR = REPO_ROOT / "features/handcrafted"

DIPEPTIDES = ["".join(p) for p in itertools.product(AA20, repeat=2)]
REDUCED_KMERS = ["".join(p) for p in itertools.product(sorted(REDUCED_GROUPS), repeat=KMER_K)]

STRUCT_COLUMNS = [
    "struct_n_residues",
    "struct_confidence_mean",
    "struct_confidence_min",
    "struct_confidence_max",
    "struct_confidence_std",
    "struct_ss_frac_helix",
    "struct_ss_frac_strand",
    "struct_ss_frac_loop",
    "struct_rsa_mean",
    "struct_rsa_std",
    "struct_frac_exposed",
    "struct_radius_of_gyration",
]


def load_task(task: str) -> tuple[list[tuple[str, str, str]], str]:
    """Return [(id, sequence, structure_key)] plus a note on the source used."""
    curated, fallback = TASK_SOURCES[task]
    if curated.is_file():
        frame = read_task_table(curated)
        rows = [
            (str(r["id"]), str(r["sequence"]).strip().upper(), str(r["id"]).removeprefix("A_"))
            for r in frame.to_dict("records")
        ]
        return rows, "curated.csv"
    if fallback.is_file():
        with fallback.open(encoding="utf-8") as handle:
            records = list(csv.DictReader(handle))
        return (
            [("A_" + r["rt_name"], r["sequence"].strip().upper(), r["rt_name"]) for r in records],
            "PROVISIONAL, from " + fallback.relative_to(REPO_ROOT).as_posix(),
        )
    return [], "absent"


def composition(sequence: str) -> dict[str, float]:
    total = len(sequence)
    counts = {residue: 0 for residue in AA20}
    for residue in sequence:
        if residue in counts:
            counts[residue] += 1
    return {"aac_" + residue: counts[residue] / total for residue in AA20}


def dipeptide_composition(sequence: str) -> dict[str, float]:
    counts = {pair: 0 for pair in DIPEPTIDES}
    windows = 0
    for index in range(len(sequence) - 1):
        pair = sequence[index : index + 2]
        if pair in counts:
            counts[pair] += 1
            windows += 1
    denominator = windows if windows else 1
    return {"dpc_" + pair: counts[pair] / denominator for pair in DIPEPTIDES}


def reduced_kmer_frequencies(sequence: str) -> dict[str, float]:
    reduced = "".join(REDUCED_OF.get(residue, "") for residue in sequence)
    counts = {kmer: 0 for kmer in REDUCED_KMERS}
    windows = 0
    for index in range(len(reduced) - KMER_K + 1):
        kmer = reduced[index : index + KMER_K]
        if kmer in counts:
            counts[kmer] += 1
            windows += 1
    denominator = windows if windows else 1
    return {"rk3_" + kmer: counts[kmer] / denominator for kmer in REDUCED_KMERS}


def biophysical(sequence: str) -> dict[str, float | None]:
    from Bio.SeqUtils.ProtParam import ProteinAnalysis

    analysis = ProteinAnalysis(sequence)
    helix, turn, sheet = analysis.secondary_structure_fraction()
    flexibility = analysis.flexibility()
    values: dict[str, float | None] = {
        "bio_molecular_weight": analysis.molecular_weight(),
        "bio_isoelectric_point": analysis.isoelectric_point(),
        "bio_aromaticity": analysis.aromaticity(),
        "bio_instability_index": analysis.instability_index(),
        "bio_gravy": analysis.gravy(),
        "bio_protparam_frac_helix": helix,
        "bio_protparam_frac_turn": turn,
        "bio_protparam_frac_sheet": sheet,
    }
    # Flexibility is a windowed profile, so it is summarised rather than emitted per residue.
    # A sequence shorter than the window returns an empty list, which stays missing.
    if flexibility:
        array = np.asarray(flexibility, dtype=float)
        values["bio_flexibility_mean"] = float(array.mean())
        values["bio_flexibility_min"] = float(array.min())
        values["bio_flexibility_max"] = float(array.max())
        values["bio_flexibility_std"] = float(array.std())
    else:
        values["bio_flexibility_mean"] = None
        values["bio_flexibility_min"] = None
        values["bio_flexibility_max"] = None
        values["bio_flexibility_std"] = None
    return values


def structural(structure_key: str) -> tuple[dict[str, float | None], str]:
    """Aggregate structural features, or all-missing with a reason."""
    blank: dict[str, float | None] = {column: None for column in STRUCT_COLUMNS}
    filename = STRUCTURE_ALIASES.get(structure_key, structure_key)
    path = STRUCTURE_DIR / (filename + ".pdb")
    if not path.is_file():
        return blank, "no structure file"

    from Bio.PDB import PDBParser
    from Bio.PDB.SASA import ShrakeRupley
    from Bio.Data.IUPACData import protein_letters_3to1

    parser = PDBParser(QUIET=True)
    model = parser.get_structure(structure_key, path)[0]
    residues = [r for r in model.get_residues() if "CA" in r]
    if not residues:
        return blank, "structure has no alpha carbons"

    values = dict(blank)
    values["struct_n_residues"] = float(len(residues))

    # Per-residue confidence is the mean over that residue's atoms, so a large residue does
    # not weigh more than a small one.
    per_residue = np.asarray(
        [float(np.mean([a.get_bfactor() for a in r])) for r in residues], dtype=float
    )
    values["struct_confidence_mean"] = float(per_residue.mean())
    values["struct_confidence_min"] = float(per_residue.min())
    values["struct_confidence_max"] = float(per_residue.max())
    values["struct_confidence_std"] = float(per_residue.std())

    coordinates = np.asarray([r["CA"].get_coord() for r in residues], dtype=float)
    centre = coordinates.mean(axis=0)
    values["struct_radius_of_gyration"] = float(
        math.sqrt(float(np.mean(np.sum((coordinates - centre) ** 2, axis=1))))
    )

    notes: list[str] = []

    # Secondary structure from backbone geometry. Needs N, CA, C, O on every residue.
    backbone_ok = all(all(atom in r for atom in ("N", "CA", "C", "O")) for r in residues)
    if backbone_ok:
        try:
            import pydssp

            backbone = np.asarray(
                [[r["N"].get_coord(), r["CA"].get_coord(), r["C"].get_coord(), r["O"].get_coord()]
                 for r in residues],
                dtype=float,
            )
            assignment = pydssp.assign(backbone, out_type="c3")
            symbols = [str(s) for s in assignment]
            total = len(symbols) if symbols else 1
            values["struct_ss_frac_helix"] = symbols.count("H") / total
            values["struct_ss_frac_strand"] = symbols.count("E") / total
            values["struct_ss_frac_loop"] = symbols.count("-") / total
        except Exception as error:  # noqa: BLE001
            notes.append("secondary structure unavailable: " + type(error).__name__)
    else:
        notes.append("secondary structure unavailable: incomplete backbone")

    try:
        ShrakeRupley().compute(model, level="R")
        accessibility: list[float] = []
        for residue in residues:
            name = residue.get_resname().capitalize()
            one = protein_letters_3to1.get(name)
            reference = MAX_ASA.get(one) if one else None
            if reference:
                accessibility.append(float(residue.sasa) / reference)
        if accessibility:
            array = np.asarray(accessibility, dtype=float)
            values["struct_rsa_mean"] = float(array.mean())
            values["struct_rsa_std"] = float(array.std())
            values["struct_frac_exposed"] = float(np.mean(array > EXPOSED_THRESHOLD))
        else:
            notes.append("no standard residue for relative accessibility")
    except Exception as error:  # noqa: BLE001
        notes.append("solvent accessibility unavailable: " + type(error).__name__)

    return values, "; ".join(notes)


def build_task(task: str) -> int:
    rows, note = load_task(task)
    print("")
    print("=== task " + task + " ===")
    print("  rows: " + str(len(rows)) + ", source: " + note)
    if not rows:
        print("  nothing to build")
        return 0
    if note.startswith("PROVISIONAL"):
        print("  NOTE: identifiers are provisional, minted as A_<rt_name>, because no")
        print("  curated.csv exists yet. Only sequences are used, and the sequences are final,")
        print("  so these values do not change when curated.csv arrives. They are not a result.")

    feature_rows: list[dict[str, object]] = []
    mask_rows: list[dict[str, object]] = []
    structure_notes: list[tuple[str, str]] = []

    for identifier, sequence, structure_key in rows:
        features: dict[str, object] = {"id": identifier, "length": float(len(sequence))}
        features.update(composition(sequence))
        features.update(dipeptide_composition(sequence))
        features.update(reduced_kmer_frequencies(sequence))
        features.update(biophysical(sequence))
        struct_values, struct_note = structural(structure_key)
        features.update(struct_values)
        if struct_note:
            structure_notes.append((identifier, struct_note))
        feature_rows.append(features)
        mask_rows.append(
            {"id": identifier}
            | {k: (1 if v is None else 0) for k, v in features.items() if k != "id"}
        )

    columns = ["id"] + [c for c in feature_rows[0] if c != "id"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix_path = OUT_DIR / ("task" + task + "_features.csv")
    mask_path = OUT_DIR / ("task" + task + "_missing_mask.csv")

    for path, records in ((matrix_path, feature_rows), (mask_path, mask_rows)):
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns, restval="")
            writer.writeheader()
            for record in records:
                writer.writerow({k: ("" if v is None else v) for k, v in record.items()})

    missing_by_column = {
        column: sum(int(r[column]) for r in mask_rows) for column in columns if column != "id"
    }
    incomplete = {k: v for k, v in missing_by_column.items() if v}

    print("  feature columns: " + str(len(columns) - 1))
    print(
        "    length 1, composition 20, dipeptide "
        + str(len(DIPEPTIDES))
        + ", reduced tripeptide "
        + str(len(REDUCED_KMERS))
        + ", biophysical 12, structural "
        + str(len(STRUCT_COLUMNS))
    )
    print("  wrote " + matrix_path.relative_to(REPO_ROOT).as_posix() + " sha256=" + sha256_of(matrix_path))
    print("  wrote " + mask_path.relative_to(REPO_ROOT).as_posix() + " sha256=" + sha256_of(mask_path))
    print("  columns with any missing value: " + str(len(incomplete)))
    for column, count in sorted(incomplete.items()):
        print("    " + column + ": " + str(count) + " of " + str(len(rows)) + " rows missing")
    if structure_notes:
        print("  structural notes:")
        for identifier, message in structure_notes:
            print("    " + identifier + ": " + message)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build handcrafted feature matrices.")
    parser.parse_args(argv)
    inputs = [p for p in (REPO_ROOT / "data/rt_sequences.csv",) if p.exists()]
    print_run_header("features/build_handcrafted.py", inputs)
    print("")
    print("no scaling, no imputation, no feature selection; raw values plus a missingness mask")
    for task in TASK_SOURCES:
        build_task(task)
    print("")
    print("Variant-specific features (substitution identity, BLOSUM62 score, position) are not")
    print("emitted, because no task with variant rows exists yet: Task B is blocked on its")
    print("activity values. They are implemented when Task B is built, not before.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
