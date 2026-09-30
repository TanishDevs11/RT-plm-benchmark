"""Resolve the reference frame for the Task B M-MLV RT variant library.

The problem
-----------
The Task B source (Li et al. 2026, DOI 10.64898/2026.07.06.736660) numbers its variants
against an M-MLV reverse transcriptase that it treats as 677 residues long, deleting the
RNase H domain at "residues L499 to P677". UniProt P03355 annotates the M-MLV
reverse transcriptase / ribonuclease H chain (p80) at Gag-Pol residues 660 to 1330, which
is 671 residues. Six residues of disagreement is exactly the size of offset that would
shift an entire saturated mutagenesis library without producing any visible error, so it
has to be settled before a single variant sequence is constructed.

What this script does
---------------------
It tests the paper's numbering against P03355 at every position the paper pins down, and
halts on any mismatch rather than adjusting an offset to make things fit. The anchors are
not chosen for convenience: they are every residue identity the paper states, taken from
its stretch boundaries, its three reported mutations, and its deletion boundaries.

It then reconstructs the paper's own arithmetic (1,494 bp of retained RT, 26.4 percent
smaller than wild type) from the resolved frame. Those two numbers are independent of the
anchors, so agreement is a second, separate confirmation.

What this script does NOT do
---------------------------
It does not write ``reference.fasta``. The sequence it writes is named
``reference_candidate_unconfirmed.fasta`` because one question remains open: PE2dR was
built from pCMV-PE2 (Addgene 132775), whose RT carries the substitutions D200N, T306K,
W313F, T330P, and L603W, and the preprint's main text never states whether the construct
retains them. The strings "pentamutant", "D200N", and "L603W" do not appear anywhere in
the main text. So the candidate written here is the unmutated frame, and the substitution
content must come from Supplementary Sequence 1 before any variant is built on it.

    python data_acquisition/resolve_mmlv_reference.py
    python data_acquisition/resolve_mmlv_reference.py --fetch
"""

from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

UNIPROT_ACCESSION = "P03355"
UNIPROT_URL = "https://rest.uniprot.org/uniprotkb/P03355.fasta"
FASTA_PATH = REPO_ROOT / "tasks/taskB_mmlv_dms/raw/uniprot_P03355.fasta"
CANDIDATE_PATH = REPO_ROOT / "tasks/taskB_mmlv_dms/raw/reference_candidate_unconfirmed.fasta"

# UniProt CHAIN "Reverse transcriptase/ribonuclease H (p80)", Gag-Pol coordinates.
P80_START = 660
P80_END = 1330

# The paper's RT numbering is hypothesised to start at the first residue of the p80 chain,
# which makes the Gag-Pol offset this value. Every anchor below tests that hypothesis.
GAGPOL_OFFSET = P80_START - 1

# The residue positions and identities the paper states, each with the phrase it comes
# from. These are the whole basis of the resolution, so each one records its own source.
ANCHORS: tuple[tuple[int, str, str], ...] = (
    (60, "S", 'stretch 1 start, "S60-Q84"'),
    (61, "I", "reported mutation I61R"),
    (67, "S", "reported mutation S67W"),
    (84, "Q", 'stretch 1 end, "S60-Q84"'),
    (95, "N", 'stretch 2 start, "N95-D124"'),
    (101, "V", "reported mutation V101R"),
    (124, "D", 'stretch 2 end, "N95-D124"'),
    (499, "L", 'RNase H deletion start, "residues L499 to P677"'),
    (677, "P", 'RNase H deletion end, "residues L499 to P677"'),
)

RNASEH_FIRST = 499
RNASEH_LAST = 677
RETAINED_LAST = RNASEH_FIRST - 1

# From the paper: the retained RT is "encoded by 1,494bp" and is "26.4% smaller than the
# wild-type MMLV-RT". Both are checked against the resolved frame.
STATED_RETAINED_BP = 1494
STATED_FRACTION_SMALLER = 0.264

# The PE2 RT substitutions, as reported for the prime editor PE2. Whether PE2dR retains
# them is the one open question this script cannot close.
PE2_SUBSTITUTIONS: tuple[tuple[str, int, str], ...] = (
    ("D", 200, "N"),
    ("T", 306, "K"),
    ("W", 313, "F"),
    ("T", 330, "P"),
    ("L", 603, "W"),
)


class ResolutionFailure(Exception):
    """Raised when the paper's numbering cannot be reconciled with the reference."""


def read_fasta(path: Path) -> tuple[str, str]:
    header = ""
    residues: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            if not header:
                header = line[1:].strip()
            continue
        residues.append(line.strip())
    return header, "".join(residues)


def fetch_fasta(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    print("fetching " + UNIPROT_URL)
    with urllib.request.urlopen(UNIPROT_URL, timeout=60) as response:
        payload = response.read()
    path.write_bytes(payload)
    print("wrote " + path.as_posix() + " bytes=" + str(len(payload)))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve the Task B reference frame.")
    parser.add_argument("--fetch", action="store_true", help="download the UniProt entry if absent")
    args = parser.parse_args(argv)

    print_run_header("data_acquisition/resolve_mmlv_reference.py")
    print("")

    if not FASTA_PATH.is_file():
        if args.fetch:
            fetch_fasta(FASTA_PATH)
        else:
            print("ABSENT: " + FASTA_PATH.as_posix())
            print("Run again with --fetch, or place the file from " + UNIPROT_URL)
            return 1

    print("input " + FASTA_PATH.as_posix() + " sha256=" + sha256_of(FASTA_PATH))
    header, gagpol = read_fasta(FASTA_PATH)
    print("header: " + header)
    print("Gag-Pol length: " + str(len(gagpol)))

    # The RT frame is open ended on purpose. The paper numbers to 677 and the annotated p80
    # chain stops at 671, so truncating at the chain boundary would make the last anchor
    # untestable, which is the opposite of what is wanted.
    rt_frame = gagpol[GAGPOL_OFFSET:]
    p80 = gagpol[P80_START - 1 : P80_END]
    print("")
    print("UniProt CHAIN p80: Gag-Pol " + str(P80_START) + " to " + str(P80_END))
    print("p80 length: " + str(len(p80)) + " residues")
    print("hypothesis: the paper's RT residue 1 is p80 residue 1, so Gag-Pol offset is " + str(GAGPOL_OFFSET))

    print("")
    print("Anchor test. Every residue identity the paper states:")
    failures: list[str] = []
    for position, expected, provenance in ANCHORS:
        if position > len(rt_frame):
            failures.append("position " + str(position) + " is beyond the available sequence")
            continue
        observed = rt_frame[position - 1]
        verdict = "OK" if observed == expected else "MISMATCH"
        if observed != expected:
            failures.append(
                "position " + str(position) + " expected " + expected + ", observed " + observed
            )
        print(
            "  "
            + str(position).rjust(4)
            + "  expected "
            + expected
            + "  observed "
            + observed
            + "  "
            + verdict.ljust(8)
            + provenance
        )

    if failures:
        print("")
        print("RESOLUTION FAILED. Do not adjust an offset to make these fit.")
        for failure in failures:
            print("  " + failure)
        raise ResolutionFailure("; ".join(failures))

    print("")
    print("All " + str(len(ANCHORS)) + " anchors match. The paper's numbering is p80 numbering.")

    # Second, independent confirmation: the paper's own two arithmetic statements.
    retained = rt_frame[:RETAINED_LAST]
    deleted_length = RNASEH_LAST - RNASEH_FIRST + 1
    total_rt = RNASEH_LAST
    retained_bp = len(retained) * 3
    fraction_smaller = deleted_length / total_rt

    print("")
    print("Arithmetic test, independent of the anchors:")
    print("  paper's RT length            " + str(total_rt) + " residues")
    print("  annotated p80 length         " + str(len(p80)) + " residues")
    print("  difference                   " + str(total_rt - len(p80)) + " residues")
    print("  RNase H deleted              " + str(RNASEH_FIRST) + " to " + str(RNASEH_LAST) + ", " + str(deleted_length) + " residues")
    print("  retained RT                  1 to " + str(RETAINED_LAST) + ", " + str(len(retained)) + " residues")
    print("  retained, in base pairs      " + str(retained_bp) + "   paper states " + str(STATED_RETAINED_BP))
    print("  fraction smaller             " + format(fraction_smaller, ".4f") + "   paper states " + format(STATED_FRACTION_SMALLER, ".3f"))

    arithmetic_failures: list[str] = []
    if retained_bp != STATED_RETAINED_BP:
        arithmetic_failures.append("retained base pairs disagree with the paper")
    if round(fraction_smaller, 3) != STATED_FRACTION_SMALLER:
        arithmetic_failures.append("size reduction disagrees with the paper")
    if arithmetic_failures:
        print("")
        for failure in arithmetic_failures:
            print("  MISMATCH " + failure)
        raise ResolutionFailure("; ".join(arithmetic_failures))
    print("  both agree.")

    print("")
    print("Consequence for the six-residue discrepancy:")
    print("  the paper's RT extends " + str(total_rt - len(p80)) + " residues past the annotated p80 chain,")
    print("  to Gag-Pol " + str(GAGPOL_OFFSET + RNASEH_LAST) + ", into the region UniProt assigns to integrase.")
    print("  residues " + str(len(p80) + 1) + " to " + str(total_rt) + " are: " + rt_frame[len(p80) : total_rt])
    print("  So 671 and 677 are both right, about different things, and there is no offset.")

    print("")
    print("PE2 substitution positions, checked against this frame:")
    for wild, position, mutant in PE2_SUBSTITUTIONS:
        observed = rt_frame[position - 1]
        fate = "retained in PE2dR" if position <= RETAINED_LAST else "DELETED with RNase H"
        verdict = "OK" if observed == wild else "MISMATCH"
        print(
            "  "
            + (wild + str(position) + mutant).ljust(8)
            + " reference residue "
            + observed
            + "  "
            + verdict.ljust(9)
            + fate
        )
        if observed != wild:
            failures.append("PE2 substitution " + wild + str(position) + mutant + " does not match")
    if failures:
        raise ResolutionFailure("; ".join(failures))
    print("")
    print("  L603W falls inside the deleted region, so if PE2dR inherits PE2's RT it is a")
    print("  tetramutant truncation carrying D200N, T306K, W313F, T330P, and not L603W.")
    print("  OPEN: the preprint main text never states the construct's substitution content.")
    print("  The strings 'pentamutant', 'D200N', and 'L603W' do not appear in it.")
    print("  This must come from Supplementary Sequence 1 before any variant is built.")

    CANDIDATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    description = (
        "PE2dR_RT_frame_candidate_UNCONFIRMED "
        + UNIPROT_ACCESSION
        + " Gag-Pol "
        + str(GAGPOL_OFFSET + 1)
        + "-"
        + str(GAGPOL_OFFSET + RETAINED_LAST)
        + " RT_frame_1-"
        + str(RETAINED_LAST)
        + " no_substitutions_applied"
    )
    lines = [">" + description]
    lines += [retained[i : i + 60] for i in range(0, len(retained), 60)]
    CANDIDATE_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("")
    print("wrote " + CANDIDATE_PATH.as_posix())
    print("  sha256=" + sha256_of(CANDIDATE_PATH))
    print("  " + str(len(retained)) + " residues, no substitutions applied")
    print("")
    print("This is a candidate, not the reference. It is deliberately not named")
    print("reference.fasta, and no Task B parser may consume it, because the substitution")
    print("content is unresolved. Gate G2 is where a human confirms the real reference.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ResolutionFailure as error:
        print("")
        print("HALTED: " + str(error))
        raise SystemExit(2) from error
