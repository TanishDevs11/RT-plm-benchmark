"""Construct the Task B variant table, and halt rather than adapt if the numbering is wrong.

The single highest-risk operation in this task is applying a substitution at a position
whose numbering convention is not what the parser assumes. A one-residue offset between
the paper's numbering and the reference frame would produce 1045 variant sequences that
are each wrong at two positions, with no error raised anywhere and no downstream symptom
except a benchmark that quietly measures nothing. So this parser asserts the wild-type
residue stated by the source against the reference at every position, and **halts on the
first mismatch**.

What it will not do on a mismatch: auto-correct, search for an offset and apply it, or
skip the row. It reports the first ten mismatches, tests whether one constant offset would
resolve all of them, states that candidate offset as a finding, and stops. Applying an
offset is a human ruling, because an offset that happens to fix the anchors can still be
the wrong biological frame.

Two modes
---------
`--check-reference` validates the reference against every position the source pins down
and needs no activity values. It is the mode that can run today, because the activity
tables are not publicly available; see `data_acquisition/MANUAL_FETCH_TASKB.md`.

The default mode additionally reads the activity tables and writes `curated.csv`. It halts
with a specific message if they are absent, which is the correct outcome rather than an
error to work around.

    python data_acquisition/parse_mmlv_dms.py --check-reference
    python data_acquisition/parse_mmlv_dms.py

Output: tasks/taskB_mmlv_dms/curated.csv, once the activity tables exist.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import AA20, print_run_header, sha256_of  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_mmlv_dms"
RAW = TASK_DIR / "raw"
REFERENCE = RAW / "reference.fasta"
REFERENCE_CANDIDATE = RAW / "reference_candidate_unconfirmed.fasta"
CURATED = TASK_DIR / "curated.csv"

# The activity tables. Absent as of 2026-10-03: the preprint deposited no supplementary
# material and the work has not been published. See MANUAL_FETCH_TASKB.md.
TABLE_S6 = RAW / "table_s6.xlsx"
TABLE_S7 = RAW / "table_s7.xlsx"

SOURCE_DOI = "10.64898/2026.07.06.736660"
SOURCE_TABLE = "Supplementary Tables S6 and S7"

# Library boundaries, verbatim from the preprint: "all possible single-amino acid
# substitutions for the S60-Q84 and N95-D124 regions". The residue letters in those
# labels are themselves assertions about the reference, and they are checked below.
STRETCHES: dict[str, tuple[int, int]] = {"1": (60, 84), "2": (95, 124)}
STRETCH_BOUNDARY_RESIDUES = {60: "S", 84: "Q", 95: "N", 124: "D"}

# Every other residue identity the preprint states, from its reported mutations. Each is
# an independent check on the frame.
REPORTED_MUTATIONS = {61: "I", 101: "V", 67: "S"}

# Expected counts, from the preprint: "Library Stretch 1 (475 variants + WT) and Library
# Stretch 2 (570 variants + WT)". 25 positions times 19 is 475; 30 times 19 is 570.
EXPECTED_PER_STRETCH = {"1": 475, "2": 570}

WILD_TYPE_ID = "B_wt"


def load_reference() -> tuple[str, str, Path]:
    """The adopted reference if it exists, otherwise the unconfirmed candidate."""
    for path, status in ((REFERENCE, "adopted"), (REFERENCE_CANDIDATE, "UNCONFIRMED")):
        if path.is_file():
            lines = path.read_text(encoding="utf-8").splitlines()
            header = lines[0].lstrip(">") if lines and lines[0].startswith(">") else ""
            sequence = "".join(
                line.strip() for line in lines[1:] if line.strip() and not line.startswith(">")
            ).upper()
            return sequence, status + ": " + header, path
    raise SystemExit(
        "no reference found. Expected " + REFERENCE.name + " or " + REFERENCE_CANDIDATE.name
    )


def expected_variants() -> list[dict]:
    """Every variant the saturating libraries must contain, from the stretch boundaries.

    Determined without any activity value: both libraries are exactly saturating, so the
    identifier set is fixed by the boundaries and the reference alone. That makes this set
    a reconciliation check as well as a construction: when the tables arrive, any variant
    they hold that is not here, or any identifier here they do not hold, is a discrepancy
    to be logged rather than absorbed.
    """
    sequence, _, _ = load_reference()
    out: list[dict] = []
    for stretch, (first, last) in STRETCHES.items():
        for position in range(first, last + 1):
            wild = sequence[position - 1]
            for mutant in AA20:
                if mutant == wild:
                    continue
                out.append(
                    {
                        "variant_id": "B_" + wild + str(position) + mutant,
                        "wt_aa": wild,
                        "position": position,
                        "mut_aa": mutant,
                        "library_stretch": stretch,
                    }
                )
    return out


def check_reference(sequence: str) -> list[str]:
    """Assert every residue identity the source states. Returns a list of mismatches."""
    mismatches: list[str] = []
    anchors = dict(STRETCH_BOUNDARY_RESIDUES)
    anchors.update(REPORTED_MUTATIONS)
    for position, stated in sorted(anchors.items()):
        if position > len(sequence):
            mismatches.append(
                "position " + str(position) + " is beyond the reference, length "
                + str(len(sequence))
            )
            continue
        found = sequence[position - 1]
        if found != stated:
            mismatches.append(
                "position "
                + str(position)
                + ": source states "
                + stated
                + ", reference has "
                + found
            )
    return mismatches


def candidate_offset(sequence: str, stated: dict[int, str]) -> int | None:
    """Does one constant offset resolve every mismatch? Reported, never applied."""
    for offset in range(-10, 11):
        if offset == 0:
            continue
        if all(
            1 <= position + offset <= len(sequence)
            and sequence[position + offset - 1] == residue
            for position, residue in stated.items()
        ):
            return offset
    return None


def halt_on_mismatch(sequence: str, mismatches: list[str]) -> None:
    """Report, offer a candidate offset as a finding, and stop."""
    print("")
    print("WILD-TYPE RESIDUE ASSERTION FAILED on " + str(len(mismatches)) + " position(s).")
    print("The numbering convention does not match the reference, so every variant built")
    print("on it would be silently wrong. Halting without applying any correction.")
    print("")
    for line in mismatches[:10]:
        print("  " + line)
    if len(mismatches) > 10:
        print("  ... and " + str(len(mismatches) - 10) + " more")
    anchors = dict(STRETCH_BOUNDARY_RESIDUES)
    anchors.update(REPORTED_MUTATIONS)
    offset = candidate_offset(sequence, anchors)
    print("")
    if offset is None:
        print("No single constant offset in the range -10 to +10 resolves all of them.")
        print("That rules out a simple frame shift and points at a different reference.")
    else:
        print(
            "A constant offset of "
            + format(offset, "+d")
            + " would resolve every stated residue."
        )
        print("Reported as a finding for a human ruling. **Not applied.** An offset that")
        print("happens to fit the anchors can still be the wrong biological frame.")
    raise SystemExit(
        "halted on a wild-type residue mismatch; the reference must be ruled on before "
        "any variant is constructed"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-reference",
        action="store_true",
        help="validate the reference only; needs no activity values",
    )
    args = parser.parse_args()

    sequence, provenance, path = load_reference()
    print_run_header("data_acquisition/parse_mmlv_dms.py", [path])
    print("reference: " + provenance)
    print("reference length: " + str(len(sequence)) + " residues")
    print("")

    anchors = dict(STRETCH_BOUNDARY_RESIDUES)
    anchors.update(REPORTED_MUTATIONS)
    print("asserting " + str(len(anchors)) + " residue identities the source states:")
    for position, stated in sorted(anchors.items()):
        found = sequence[position - 1] if position <= len(sequence) else "?"
        print(
            "  position "
            + str(position).rjust(3)
            + ": source "
            + stated
            + ", reference "
            + found
            + ("  ok" if found == stated else "  MISMATCH")
        )

    mismatches = check_reference(sequence)
    if mismatches:
        halt_on_mismatch(sequence, mismatches)
    print("")
    print("all " + str(len(anchors)) + " wild-type residue assertions passed")

    variants = expected_variants()
    per_stretch = {
        stretch: sum(1 for v in variants if v["library_stretch"] == stretch)
        for stretch in STRETCHES
    }
    print("")
    print("expected variant set, derived from the stretch boundaries:")
    for stretch, count in sorted(per_stretch.items()):
        expected = EXPECTED_PER_STRETCH[stretch]
        print(
            "  stretch "
            + stretch
            + ": "
            + str(count)
            + " variants, source states "
            + str(expected)
            + ("  ok" if count == expected else "  MISMATCH")
        )
        if count != expected:
            raise SystemExit(
                "stretch " + stretch + " derives " + str(count) + " variants against the "
                "source's " + str(expected) + "; the boundaries or the reference are wrong"
            )
    print("  total: " + str(len(variants)) + " variants plus the wild type")

    if args.check_reference:
        print("")
        print("--check-reference: stopping here, as asked. No table was read and nothing")
        print("was written.")
        print("")
        print("One question remains open and is a halt condition for the default mode:")
        print("the construct's substitution content. The strings pentamutant, D200N,")
        print("T306K, W313F, T330P and L603W appear nowhere in the preprint, so whether")
        print("the parent RT is wild-type MMLV-RT truncated or the PE2 pentamutant")
        print("truncated is undetermined. The reference above is the unmutated frame.")
        return 0

    missing = [p.name for p in (TABLE_S6, TABLE_S7) if not p.is_file()]
    if missing:
        print("")
        print("CANNOT BUILD curated.csv: the activity tables are absent: " + ", ".join(missing))
        print("")
        print("This is the correct outcome, not a failure to work around. The preprint")
        print("deposited no supplementary material, the work has not been published, and")
        print("seven repository searches found nothing. See")
        print("data_acquisition/MANUAL_FETCH_TASKB.md for exactly what is needed.")
        print("")
        print("There is no acceptable substitute for these labels. A simulated scan or")
        print("values digitized from a figure would make every downstream number")
        print("meaningless while looking exactly like a result.")
        return 1

    raise SystemExit(
        "the activity tables are present but the table parser is not written. It is "
        "deliberately not written speculatively: the column layout of Tables S6 and S7 "
        "is unknown until the files exist, and a parser guessing at it would be untested "
        "code producing a curated dataset. Write it against the real files."
    )


if __name__ == "__main__":
    raise SystemExit(main())
