"""Construct the 1046 Task B variant sequences, which the labels do not gate.

Phase 1 of the Task B brief has two halves. One half needs the activity tables: the
`efficiency` column, and therefore `curated.csv`. The other half does not: both libraries
are exactly saturating, so the identity of every variant and its full mutant sequence
follow from the reference and the two stretch boundaries alone, with no activity value
anywhere in the derivation.

That half can be finished, and is finished here. What this produces is **not**
`curated.csv` and is deliberately impossible to mistake for it: the file is named
`variants_unlabelled.csv`, it carries no `efficiency` column at all rather than an empty
one, and every row states `label_status`. A table with a blank label column is the kind of
file that gets joined by accident; a table with no label column cannot be.

Three things are checked that nothing else checks:

1. every substitution is applied at a position whose reference residue matches the
   identifier's stated wild-type residue, and the result differs from the reference at
   exactly one position. A two-position difference means the construction is wrong even
   if the position numbering is right
2. the identifier set matches the four frozen split files exactly. Those were frozen
   before the reference was resolved from the parent plasmid, so this is a real check: if
   the resolution had changed any residue inside a diversified stretch, every identifier
   at that position would have changed and the frozen splits would be silently invalid
3. all 1046 sequences are distinct

    python data_acquisition/build_mmlv_variant_sequences.py

Writes tasks/taskB_mmlv_dms/variants_unlabelled.csv.
"""

from __future__ import annotations

import csv
import hashlib
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition import parse_mmlv_dms as parser  # noqa: E402
from schemas.task_schema import print_run_header  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_mmlv_dms"
SPLITS = TASK_DIR / "splits"
OUT = TASK_DIR / "variants_unlabelled.csv"

LABEL_STATUS = "absent_not_publicly_deposited"
REFERENCE_ACCESSION = "addgene_132775_RT_1_498_crosschecked_P03355.5_and_addgene_174820"

COLUMNS = [
    "variant_id",
    "sequence",
    "sequence_len",
    "wt_aa",
    "position",
    "mut_aa",
    "mutations",
    "library_stretch",
    "is_wildtype",
    "label_status",
    "source_doi",
    "reference_accession",
    "notes",
]


def frozen_identifiers() -> dict[str, set[str]]:
    """The identifier set each frozen split file declares."""
    sets: dict[str, set[str]] = {}
    for path in sorted(SPLITS.glob("*.csv")):
        with path.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            raise SystemExit(path.name + " is empty")
        key = "id" if "id" in rows[0] else "variant_id"
        if key not in rows[0]:
            raise SystemExit(path.name + " carries no identifier column")
        sets[path.name] = {row[key] for row in rows}
    if not sets:
        raise SystemExit("no frozen split files found; they are a required input here")
    return sets


def main() -> int:
    reference, provenance, reference_path = parser.load_reference()
    print_run_header("data_acquisition/build_mmlv_variant_sequences.py", [reference_path])
    print("")
    print("reference: " + provenance)
    print("reference length: " + str(len(reference)) + " residues")

    mismatches = parser.check_reference(reference)
    if mismatches:
        parser.halt_on_mismatch(reference, mismatches)
    print(
        "all "
        + str(len(parser.all_anchors()))
        + " residue assertions passed, and the length is the retained construct's"
    )

    rows: list[dict] = []
    for variant in parser.expected_variants():
        position = variant["position"]
        wild, mutant = variant["wt_aa"], variant["mut_aa"]
        if reference[position - 1] != wild:
            raise SystemExit(
                "position " + str(position) + " holds " + reference[position - 1]
                + " but the identifier states " + wild + "; halting"
            )
        sequence = reference[: position - 1] + mutant + reference[position:]
        if len(sequence) != len(reference):
            raise SystemExit("a substitution changed the sequence length at " + str(position))
        differences = sum(1 for left, right in zip(reference, sequence) if left != right)
        if differences != 1:
            raise SystemExit(
                "the variant at position " + str(position) + " differs from the reference "
                "at " + str(differences) + " positions; exactly one is required"
            )
        rows.append(
            {
                "variant_id": variant["variant_id"],
                "sequence": sequence,
                "sequence_len": len(sequence),
                "wt_aa": wild,
                "position": position,
                "mut_aa": mutant,
                "mutations": wild + str(position) + mutant,
                "library_stretch": variant["library_stretch"],
                "is_wildtype": "no",
                "label_status": LABEL_STATUS,
                "source_doi": parser.SOURCE_DOI,
                "reference_accession": REFERENCE_ACCESSION,
                "notes": "",
            }
        )

    rows.append(
        {
            "variant_id": parser.WILD_TYPE_ID,
            "sequence": reference,
            "sequence_len": len(reference),
            "wt_aa": "",
            "position": "",
            "mut_aa": "",
            "mutations": "",
            "library_stretch": "1;2",
            "is_wildtype": "yes",
            "label_status": LABEL_STATUS,
            "source_doi": parser.SOURCE_DOI,
            "reference_accession": REFERENCE_ACCESSION,
            "notes": (
                "one row, not two. Each library carries its own wild-type construct, but "
                "both are fixed at zero by the definition of the normalization, so they "
                "are not two independent measurements, and two rows would carry an "
                "identical sequence"
            ),
        }
    )

    print("")
    print("constructed " + str(len(rows)) + " sequences:")
    for stretch in sorted(parser.STRETCHES):
        count = sum(1 for row in rows if row["library_stretch"] == stretch)
        expected = parser.EXPECTED_PER_STRETCH[stretch]
        print(
            "  stretch "
            + stretch
            + ": "
            + str(count)
            + ", source states "
            + str(expected)
            + ("  ok" if count == expected else "  MISMATCH")
        )
    print("  wild type: 1")

    sequences = {row["sequence"] for row in rows}
    if len(sequences) != len(rows):
        raise SystemExit(
            "only " + str(len(sequences)) + " distinct sequences for " + str(len(rows))
            + " rows; two variants collide"
        )
    print("  all " + str(len(rows)) + " sequences distinct")

    print("")
    print("reconciling against the frozen split files:")
    built = {row["variant_id"] for row in rows}
    for name, declared in frozen_identifiers().items():
        only_split = sorted(declared - built)
        only_built = sorted(built - declared)
        status = "ok" if not (only_split or only_built) else "MISMATCH"
        print("  " + name.ljust(42) + str(len(declared)) + " ids  " + status)
        if only_split or only_built:
            print("    in the split only: " + ", ".join(only_split[:10]))
            print("    in the build only: " + ", ".join(only_built[:10]))
            raise SystemExit(
                "the frozen split " + name + " does not describe the variant set this "
                "reference derives. The splits were frozen before the reference was "
                "resolved, so either the reference moved a residue inside a diversified "
                "stretch or the splits are stale. This is a human ruling"
            )

    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    print("")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    print("  sha256 " + hashlib.sha256(OUT.read_bytes()).hexdigest())
    print("  " + str(len(COLUMNS)) + " columns, and no efficiency column, by design")
    print("")
    print("This is not curated.csv and must not be renamed to it. curated.csv carries")
    print("labels; this file states that there are none. Date: " + date.today().isoformat())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
