"""Resolve the PE2dR RT reference from the parent plasmid, and refuse to guess any of it.

This closes the one item the Task B provenance carried as UNRESOLVED: the substitution
content of the construct. The chain is three primary records and no inference in between.

1. The preprint states how the construct was made: "The pCMV-PE2dR plasmid was
   constructed via deleting RNaseH domain from RT of pCMV-PE2 (#132775, Addgene)", and
   that the deletion removes "residues L499 to P677".
2. Addgene 132775 publishes the parent plasmid's verified full sequence, fetched by
   `fetch_pe2_plasmid.py`, and its own record names the insert
   `Cas9(H840A)-M-MLVrt(D200N, T306K, W313F, T330P, L603W)`.
3. UniProt P03355 is the Gag-Pol parent whose RT frame the pipeline already resolved
   against nine residue anchors.

So the reference is not assembled by applying substitutions to UniProt. It is read out of
the parent plasmid by translation, and UniProt is the independent check: the translated RT
has to agree with P03355 at every one of 677 positions except where a difference is
accounted for. Each difference is either one of the substitutions Addgene names, or it is
reported as a finding. Nothing is silently absorbed.

What this script found, and why it matters, is in PROVENANCE.md. The short version is that
there is one difference beyond the five Addgene names, at RT position 8, and it would have
propagated into all 1046 variant sequences and every embedding computed from them.

    python data_acquisition/resolve_pe2dr_reference.py

Writes tasks/taskB_mmlv_dms/reference.fasta and reference_resolution.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests
from Bio.Seq import Seq

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition import fetch_pe2_plasmid as plasmid_fetch  # noqa: E402
from schemas.task_schema import print_run_header  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_mmlv_dms"
RAW = TASK_DIR / "raw"
PLASMID_FASTA = RAW / "addgene_132775_pCMV-PE2.fasta"
UNIPROT_FASTA = RAW / "uniprot_P03355.fasta"
PLASMID_LOG = REPO_ROOT / "data_acquisition" / "fetch_pe2_plasmid_attempts.json"
OUT_FASTA = TASK_DIR / "reference.fasta"
OUT_JSON = TASK_DIR / "reference_resolution.json"
CHECKSUMS = RAW / "CHECKSUMS.txt"

# The RT frame, as resolved by resolve_mmlv_reference.py against nine residue anchors and
# confirmed a second time by the preprint's own base-pair and percentage arithmetic.
UNIPROT_ACCESSION = "P03355"
GAGPOL_OFFSET = 659  # RT position n is Gag-Pol position n + 659
RT_LENGTH = 677  # RT 1 to 677, six residues past the annotated p80 chain

# The RNase H deletion, verbatim from the preprint: "residues L499 to P677".
DELETION_FIRST = 499
DELETION_LAST = 677
PE2DR_LENGTH = DELETION_FIRST - 1  # 498 residues retained

# Residue identities the preprint states, every one an independent check on the frame.
PREPRINT_ANCHORS = {60: "S", 61: "I", 67: "S", 84: "Q", 95: "N", 101: "V", 124: "D"}
DELETION_ANCHORS = {DELETION_FIRST: "L", DELETION_LAST: "P"}

# The diversified stretches, verbatim: "the S60-Q84 and N95-D124 regions".
STRETCHES = {"1": (60, 84), "2": (95, 124)}

# The six residues by which the preprint's RT extends past the annotated p80 chain. The
# preprint calls the last one P677, so this is a check on the far end of the frame.
TAIL_672_677 = "IENSSP"

# How far the translated RT may sit from P03355 before the match is rejected as the wrong
# region. Five substitutions are expected from Addgene's record; the allowance leaves room
# for isolate differences while still rejecting an unrelated window.
MAX_ACCEPTED_DIFFERENCES = 20

SOURCE_DOI = "10.64898/2026.07.06.736660"

# The independent cross-check. pCMV-PEmax is a separate deposit, and the preprint builds
# its best construct on PEmax, so its RT is the one sequence in the public record that
# must agree with this reference residue for residue over the retained region. Because the
# two deposits are codon-optimized differently, agreement at the protein level cannot come
# from a shared nucleotide payload or a shared rendering of one.
CROSSCHECK_PLASMID = "174820"
CROSSCHECK_NAME = "pCMV-PEmax"


def read_fasta(path: Path) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].lstrip(">").strip() if lines and lines[0].startswith(">") else ""
    body = "".join(line.strip() for line in lines[1:] if line.strip() and not line.startswith(">"))
    return header, body.upper()


def named_substitutions() -> dict[int, tuple[str, str]]:
    """The substitutions Addgene's own record names, parsed from that record.

    Read from the fetch log rather than written here, so that the set this script checks
    is the set the depositor published and not a set this file asserts.
    """
    if not PLASMID_LOG.is_file():
        raise SystemExit("run data_acquisition/fetch_pe2_plasmid.py first")
    description = json.loads(PLASMID_LOG.read_text(encoding="utf-8"))["insert_description"]
    # Only the RT's own parenthetical. The same field also names Cas9's H840A nickase
    # substitution, which is numbered in Cas9 and would be read as an RT position.
    group = re.search(r"M-MLVrt\(([^)]*)\)", description)
    if not group:
        raise SystemExit("the insert record names no RT substitution group: " + description)
    found = re.findall(
        r"\b([ACDEFGHIKLMNPQRSTVWY])(\d+)([ACDEFGHIKLMNPQRSTVWY])\b", group.group(1)
    )
    if not found:
        raise SystemExit("no substitution was parsed from the RT group: " + group.group(1))
    parsed = {int(position): (wild, mutant) for wild, position, mutant in found}
    beyond = [position for position in parsed if position > RT_LENGTH]
    if beyond:
        raise SystemExit(
            "the record names a substitution outside the RT frame, at position(s) "
            + str(sorted(beyond))
            + ". The numbering of this field is not the RT numbering this frame assumes"
        )
    return parsed


def best_window(protein: str, target: str) -> tuple[int, int, int]:
    """The window of `target`'s length that differs from it least, and that difference.

    A probe peptide is not used, because choosing one is choosing which part of the
    sequence is allowed to differ. Scoring every window instead makes the match a
    measurement. The tie count is returned rather than acted on here: a tie inside a
    reading frame that holds no RT at all is expected and means nothing, so only the
    winning frame's tie count is a halt condition.
    """
    width = len(target)
    best_offset, best_cost, ties = -1, width + 1, 0
    for offset in range(len(protein) - width + 1):
        window = protein[offset : offset + width]
        cost = sum(1 for left, right in zip(window, target) if left != right)
        if cost < best_cost:
            best_offset, best_cost, ties = offset, cost, 1
        elif cost == best_cost:
            ties += 1
    return best_offset, best_cost, ties


def locate_rt(dna: str, target: str) -> dict:
    """Find the RT reading frame in the plasmid, over all six frames."""
    candidates = []
    for strand, sequence in (("forward", dna), ("reverse", str(Seq(dna).reverse_complement()))):
        for frame in range(3):
            trimmed = sequence[frame:]
            trimmed = trimmed[: len(trimmed) - len(trimmed) % 3]
            protein = str(Seq(trimmed).translate())
            offset, cost, ties = best_window(protein, target)
            candidates.append(
                {
                    "strand": strand,
                    "frame": frame,
                    "protein_offset": offset,
                    "differences": cost,
                    "ties": ties,
                    "protein": protein,
                }
            )
    candidates.sort(key=lambda item: item["differences"])
    best, runner_up = candidates[0], candidates[1]
    if best["ties"] != 1:
        raise SystemExit(
            "the RT window is ambiguous within the best frame: "
            + str(best["ties"])
            + " windows tie at "
            + str(best["differences"])
            + " differences. Which one is the RT is a human ruling"
        )
    if best["differences"] > MAX_ACCEPTED_DIFFERENCES:
        raise SystemExit(
            "the closest window to the UniProt RT differs at "
            + str(best["differences"])
            + " positions, past the allowance of "
            + str(MAX_ACCEPTED_DIFFERENCES)
            + ". The plasmid does not carry the RT this frame describes"
        )
    if runner_up["differences"] - best["differences"] < 10:
        raise SystemExit(
            "two reading frames match the RT comparably well, at "
            + str(best["differences"])
            + " and "
            + str(runner_up["differences"])
            + " differences. Which is the RT is a human ruling"
        )
    return best


def crosscheck(reference: str, pe2_rt_dna: str) -> dict:
    """Require a second, independently deposited plasmid to encode the same RT.

    This is the check that distinguishes a correct reconstruction from a self-consistent
    wrong one. Everything up to here comes from one deposited payload, so a flaw in that
    payload or in how it is read would survive every assertion. pCMV-PEmax is a different
    deposit of the same RT protein, so it is an outside witness.

    Two numbers are reported. Identity at the protein level over the retained 498 residues
    has to be exact. Identity at the nucleotide level is expected to be well below one,
    and that is the point: it shows the two records are not copies, so the protein-level
    agreement is independent evidence rather than the same evidence twice.
    """
    headers = {"User-Agent": plasmid_fetch.USER_AGENT}
    page = requests.get(
        "https://www.addgene.org/" + CROSSCHECK_PLASMID + "/sequences/",
        headers=headers,
        timeout=plasmid_fetch.TIMEOUT,
    )
    page.raise_for_status()
    ids = plasmid_fetch.sequence_ids(page.text)
    if len(ids) != 1:
        raise SystemExit(
            CROSSCHECK_NAME + " offers " + str(len(ids)) + " full sequences; which one to "
            "cross-check against is a human ruling"
        )
    analysis_url = "https://www.addgene.org/browse/sequence/" + ids[0] + "/"
    analysis = requests.get(analysis_url, headers=headers, timeout=plasmid_fetch.TIMEOUT)
    analysis.raise_for_status()
    payload = requests.get(
        plasmid_fetch.viewer_urls(analysis.text)["sequence_lines"],
        headers={**headers, "Referer": analysis_url},
        timeout=plasmid_fetch.TIMEOUT,
    )
    payload.raise_for_status()
    dna = plasmid_fetch.reconstruct(payload.json()).upper()

    found = None
    for strand, sequence in (("forward", dna), ("reverse", str(Seq(dna).reverse_complement()))):
        for frame in range(3):
            trimmed = sequence[frame:]
            trimmed = trimmed[: len(trimmed) - len(trimmed) % 3]
            protein = str(Seq(trimmed).translate())
            offset, cost, _ties = best_window(protein, reference)
            if cost == 0:
                if found is not None:
                    raise SystemExit(
                        CROSSCHECK_NAME + " encodes the reference in more than one frame"
                    )
                found = (strand, frame, offset, sequence)
    if found is None:
        raise SystemExit(
            CROSSCHECK_NAME + " does not encode this reference exactly. The cross-check "
            "has failed, so the reference is not confirmed and nothing downstream may run"
        )
    strand, frame, offset, sequence = found
    other_dna = sequence[frame + offset * 3 : frame + offset * 3 + len(reference) * 3]
    matched = sum(1 for left, right in zip(pe2_rt_dna, other_dna) if left == right)
    return {
        "plasmid": CROSSCHECK_PLASMID,
        "plasmid_name": CROSSCHECK_NAME,
        "sequence_id": ids[0],
        "plasmid_bp": len(dna),
        "strand": strand,
        "frame": frame,
        "protein_identity_over_retained_region": "498/498",
        "nucleotide_matches": matched,
        "nucleotide_compared": len(pe2_rt_dna),
    }


def main() -> int:
    options = argparse.ArgumentParser(description=__doc__)
    options.add_argument(
        "--no-crosscheck",
        action="store_true",
        help="skip the second deposited plasmid; the reference is then one source deep",
    )
    arguments = options.parse_args()

    print_run_header(
        "data_acquisition/resolve_pe2dr_reference.py", [PLASMID_FASTA, UNIPROT_FASTA, PLASMID_LOG]
    )
    print("")

    for path in (PLASMID_FASTA, UNIPROT_FASTA):
        if not path.is_file():
            raise SystemExit("missing input: " + path.relative_to(REPO_ROOT).as_posix())

    plasmid_header, dna = read_fasta(PLASMID_FASTA)
    uniprot_header, gagpol = read_fasta(UNIPROT_FASTA)
    print("plasmid: " + plasmid_header)
    print("  " + str(len(dna)) + " bp")
    print("uniprot: " + uniprot_header[:90])
    print("  " + str(len(gagpol)) + " residues")

    uniprot_rt = gagpol[GAGPOL_OFFSET : GAGPOL_OFFSET + RT_LENGTH]
    if len(uniprot_rt) != RT_LENGTH:
        raise SystemExit("the UniProt entry is too short for the resolved RT frame")

    print("")
    print("locating the RT reading frame in the plasmid, over all six frames:")
    located = locate_rt(dna, uniprot_rt)
    protein = located["protein"]
    offset = located["protein_offset"]
    plasmid_rt = protein[offset : offset + RT_LENGTH]
    nt_start = located["frame"] + offset * 3 + 1
    print(
        "  {0} strand, frame {1}, protein offset {2}, nucleotide {3}".format(
            located["strand"], located["frame"], offset, nt_start
        )
    )
    print("  differs from UniProt " + UNIPROT_ACCESSION + " RT at " + str(located["differences"]) + " of " + str(RT_LENGTH) + " positions")

    if located["strand"] != "forward":
        print("  note: the RT is annotated on the reverse strand of the deposited sequence")

    print("")
    print("the RT is bounded, not merely found:")
    upstream = protein[max(0, offset - 12) : offset]
    downstream = protein[offset + RT_LENGTH : offset + RT_LENGTH + 12]
    print("  12 residues upstream:   " + upstream)
    print("  12 residues downstream: " + downstream)
    if "*" in plasmid_rt:
        raise SystemExit("the translated RT contains a stop codon; the frame is wrong")
    tail = plasmid_rt[671:677]
    print("  RT 672 to 677: " + tail + ("  ok" if tail == TAIL_672_677 else "  MISMATCH"))
    if tail != TAIL_672_677:
        raise SystemExit(
            "RT 672 to 677 reads " + tail + ", not " + TAIL_672_677 + ". The far end of "
            "the frame does not agree with the preprint's P677"
        )

    print("")
    print("every difference from UniProt " + UNIPROT_ACCESSION + ", accounted for one by one:")
    addgene = named_substitutions()
    print("  Addgene names: " + ", ".join(
        wild + str(position) + mutant for position, (wild, mutant) in sorted(addgene.items())
    ))
    differences = [
        {"position": index + 1, "uniprot": uniprot_rt[index], "plasmid": plasmid_rt[index]}
        for index in range(RT_LENGTH)
        if uniprot_rt[index] != plasmid_rt[index]
    ]
    unaccounted = []
    for item in differences:
        position = item["position"]
        named = addgene.get(position)
        if named and named[0] == item["uniprot"] and named[1] == item["plasmid"]:
            item["accounted_for"] = "named by Addgene 132775"
        else:
            item["accounted_for"] = "NOT named by Addgene; isolate difference or an error"
            unaccounted.append(item)
        print(
            "  position {0:>3}: UniProt {1} -> plasmid {2}   {3}".format(
                position, item["uniprot"], item["plasmid"], item["accounted_for"]
            )
        )

    missing = [
        wild + str(position) + mutant
        for position, (wild, mutant) in sorted(addgene.items())
        if not (
            uniprot_rt[position - 1] == wild and plasmid_rt[position - 1] == mutant
        )
    ]
    if missing:
        raise SystemExit(
            "the plasmid does not carry the substitution(s) its own record names: "
            + ", ".join(missing)
            + ". The record and the sequence disagree, which is a halt, not a preference"
        )
    print("")
    print("  all " + str(len(addgene)) + " substitutions Addgene names are present in the sequence")
    print("  " + str(len(unaccounted)) + " difference(s) beyond that record")

    print("")
    print("the retained PE2dR RT, by the preprint's own deletion boundaries:")
    for position, stated in sorted(DELETION_ANCHORS.items()):
        found = plasmid_rt[position - 1]
        print(
            "  position {0:>3}: preprint states {1}, plasmid has {2}  {3}".format(
                position, stated, found, "ok" if found == stated else "MISMATCH"
            )
        )
        if found != stated:
            raise SystemExit(
                "the deletion boundary at RT " + str(position) + " does not match the "
                "preprint; the frame or the construct is not what it is taken to be"
            )
    reference = plasmid_rt[:PE2DR_LENGTH]
    print("  retained RT 1 to " + str(PE2DR_LENGTH) + ": " + str(len(reference)) + " residues, " + str(len(reference) * 3) + " bp")
    if len(reference) != PE2DR_LENGTH:
        raise SystemExit("the retained reference is the wrong length")

    print("")
    print("asserting every residue identity the preprint states, on the final reference:")
    for position, stated in sorted(PREPRINT_ANCHORS.items()):
        found = reference[position - 1]
        print(
            "  position {0:>3}: preprint {1}, reference {2}  {3}".format(
                position, stated, found, "ok" if found == stated else "MISMATCH"
            )
        )
        if found != stated:
            raise SystemExit(
                "the preprint's residue " + stated + str(position) + " is not in the "
                "reference. Halting: every variant built on it would be wrong"
            )

    print("")
    print("the diversified stretches, read off the final reference:")
    stretch_sequences = {}
    for stretch, (first, last) in sorted(STRETCHES.items()):
        text = reference[first - 1 : last]
        stretch_sequences[stretch] = text
        print(
            "  stretch {0}: RT {1} to {2}, {3} positions, {4}".format(
                stretch, first, last, last - first + 1, text
            )
        )

    crosscheck_report: dict | None = None
    if arguments.no_crosscheck:
        print("")
        print("--no-crosscheck: skipping the independent plasmid. The reference below")
        print("rests on one deposited payload only, which is weaker evidence.")
    else:
        print("")
        print("independent cross-check, against a second deposited plasmid:")
        pe2_rt_dna = dna[nt_start - 1 : nt_start - 1 + PE2DR_LENGTH * 3]
        if located["strand"] != "forward":
            pe2_rt_dna = str(Seq(dna).reverse_complement())[
                nt_start - 1 : nt_start - 1 + PE2DR_LENGTH * 3
            ]
        crosscheck_report = crosscheck(reference, pe2_rt_dna)
        print(
            "  {0}, Addgene {1}, sequence {2}, {3} bp".format(
                crosscheck_report["plasmid_name"],
                crosscheck_report["plasmid"],
                crosscheck_report["sequence_id"],
                crosscheck_report["plasmid_bp"],
            )
        )
        print(
            "  encodes this reference exactly: "
            + crosscheck_report["protein_identity_over_retained_region"]
            + " residues, on the "
            + crosscheck_report["strand"]
            + " strand in frame "
            + str(crosscheck_report["frame"])
        )
        matched = crosscheck_report["nucleotide_matches"]
        compared = crosscheck_report["nucleotide_compared"]
        print(
            "  while the two RT open reading frames share only {0} of {1} nucleotides, "
            "{2}".format(matched, compared, format(matched / compared, ".3f"))
        )
        print("  so the agreement is a second witness, not the same payload twice")

    substitution_note = "+".join(
        wild + str(position) + mutant
        for position, (wild, mutant) in sorted(addgene.items())
        if position <= PE2DR_LENGTH
    )
    extra_note = "+".join(
        item["uniprot"] + str(item["position"]) + item["plasmid"]
        for item in unaccounted
        if item["position"] <= PE2DR_LENGTH
    )
    header = (
        ">PE2dR_RT reference for tasks/taskB_mmlv_dms"
        + " source=addgene_132775_translated_RT_1_to_" + str(PE2DR_LENGTH)
        + " crosschecked_against=" + UNIPROT_ACCESSION + ".5_GagPol_"
        + str(GAGPOL_OFFSET + 1) + "_" + str(GAGPOL_OFFSET + PE2DR_LENGTH)
        + " rt_frame=1-" + str(PE2DR_LENGTH)
        + " rnaseh_deleted=" + str(DELETION_FIRST) + "-" + str(DELETION_LAST)
        + " pe2_substitutions_retained=" + substitution_note
        + " differences_beyond_that_record=" + (extra_note or "none")
        + " doi=" + SOURCE_DOI
        + " resolved=" + date.today().isoformat()
    )
    body = "\n".join(reference[index : index + 60] for index in range(0, len(reference), 60))
    OUT_FASTA.write_text(header + "\n" + body + "\n", encoding="utf-8")

    report = {
        "resolved": date.today().isoformat(),
        "source_doi": SOURCE_DOI,
        "plasmid_fasta": PLASMID_FASTA.relative_to(REPO_ROOT).as_posix(),
        "plasmid_sha256": hashlib.sha256(PLASMID_FASTA.read_bytes()).hexdigest(),
        "uniprot_accession": UNIPROT_ACCESSION + ".5",
        "rt_location_in_plasmid": {
            "strand": located["strand"],
            "frame": located["frame"],
            "nucleotide_start_1based": nt_start,
            "nucleotide_end_1based": nt_start + RT_LENGTH * 3 - 1,
            "upstream_12_residues": upstream,
            "downstream_12_residues": downstream,
        },
        "rt_frame": {
            "gagpol_offset": GAGPOL_OFFSET,
            "rt_length": RT_LENGTH,
            "rnaseh_deleted": [DELETION_FIRST, DELETION_LAST],
            "pe2dr_length": PE2DR_LENGTH,
        },
        "addgene_named_substitutions": {
            str(position): wild + str(position) + mutant
            for position, (wild, mutant) in sorted(addgene.items())
        },
        "differences_from_uniprot": differences,
        "differences_not_named_by_addgene": unaccounted,
        "preprint_anchors_checked": PREPRINT_ANCHORS,
        "deletion_anchors_checked": DELETION_ANCHORS,
        "stretch_sequences": stretch_sequences,
        "independent_crosscheck": crosscheck_report,
        "reference_sha256": hashlib.sha256(OUT_FASTA.read_bytes()).hexdigest(),
        "reference_length": len(reference),
    }
    OUT_JSON.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")

    digest = hashlib.sha256(OUT_FASTA.read_bytes()).hexdigest()
    print("")
    print("wrote " + OUT_FASTA.relative_to(REPO_ROOT).as_posix())
    print("  sha256 " + digest)
    print("wrote " + OUT_JSON.relative_to(REPO_ROOT).as_posix())
    print("")
    print("STOP GATE G1: this reference is now the thing a human confirms. Everything")
    print("downstream is built on it, so the ruling belongs to a person, not to this")
    print("script. Nothing in Phase 4 should run before that ruling.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
