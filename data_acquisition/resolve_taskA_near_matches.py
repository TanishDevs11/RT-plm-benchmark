"""Explain why Task A accessions did not resolve, by finding each row's nearest database entry.

`resolve_taskA_accessions.py` pins an accession only when the Task A sequence is an exact
substring of a database entry. 30 of 57 rows failed that test, and a bare "unresolved" is
not a useful finding: it does not distinguish a sequence whose parent protein is simply
not in the searched set from a sequence whose parent is obvious but differs at a single
residue. Those two cases call for different handling and only one of them is a dead end.

So this script takes every row without a pinned accession and finds its best ungapped
alignment against every UniProt entry already in the local cache, reporting the identity,
the difference count and each differing position. The result is a reason per row.

    python data_acquisition/resolve_taskA_near_matches.py
    python data_acquisition/resolve_taskA_near_matches.py --min-identity 95

Output: tasks/taskA_crossfamily/raw/accession_near_matches.tsv

A near match is not a pin and this script never writes one into `curated.csv`. A sequence
that differs from an accession at even one residue is not that accession's sequence, and
recording it as though it were would make the difference invisible to everything
downstream. The point here is to say what the difference is, so that a human can rule on
whether a one-residue isolate difference counts as an identification.

Two limits of the method, both load bearing:

  * The search set is the local cache, which holds the candidates the earlier resolver
    already downloaded while probing. A row with no good hit here means the cache does not
    contain its parent, not that no such entry exists in UniProt.
  * The alignment is ungapped. A row whose parent differs by an insertion or deletion will
    score poorly even though it is the right protein.

Both mean this script can explain a failure but cannot prove one.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition.parse_taskA import extract_assayed_block  # noqa: E402
from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

WORKBOOK = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw" / "mmc2.xlsx"
INHERITED = REPO_ROOT / "data" / "rt_sequences.csv"
RESOLUTION = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw" / "accession_resolution.tsv"
CACHE = REPO_ROOT / ".uniprot_cache"
OUT = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw" / "accession_near_matches.tsv"

# Identity at or above which a hit is called a near match worth a human ruling. 99 percent
# over a 600 residue domain is a handful of residues, which is what an isolate difference
# or a hand-edited construct looks like. Below about 95 percent the hit is a homolog rather
# than the same protein, and naming it would be an identification this script cannot make.
NEAR_MATCH_IDENTITY = 99.0

FIELDS = (
    "rt_name",
    "sequence_len",
    "prior_status",
    "best_accession",
    "best_entry_name",
    "best_organism",
    "best_sequence_version",
    "parent_start",
    "parent_end",
    "identity_pct",
    "n_differences",
    "differences",
    "verdict",
)


def load_cache() -> dict[str, tuple[str, str]]:
    entries: dict[str, tuple[str, str]] = {}
    for path in sorted(CACHE.glob("*.fasta")):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if not lines:
            continue
        sequence = "".join(line.strip() for line in lines[1:] if line.strip())
        if sequence:
            entries[path.stem] = (lines[0], sequence.upper())
    return entries


def header_field(header: str, key: str) -> str:
    found = re.search(key + r"=(.*?)(?= [A-Z][A-Z]=|$)", header)
    return found.group(1).strip() if found else ""


def entry_name(header: str) -> str:
    found = re.match(r">(?:tr|sp)\|[^|]+\|(\S+)", header)
    return found.group(1) if found else ""


def best_ungapped(query: str, entries: dict[str, tuple[str, str]]) -> tuple:
    """Best ungapped placement of `query` inside any cached entry."""
    best_accession, best_matches, best_offset = "", -1, 0
    for accession, (_header, subject) in entries.items():
        if len(subject) < len(query):
            continue
        for offset in range(0, len(subject) - len(query) + 1):
            matches = 0
            window = subject[offset : offset + len(query)]
            for a, b in zip(window, query):
                if a == b:
                    matches += 1
            if matches > best_matches:
                best_accession, best_matches, best_offset = accession, matches, offset
    return best_accession, best_matches, best_offset


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--min-identity",
        type=float,
        default=NEAR_MATCH_IDENTITY,
        help="identity percent at or above which a hit is called a near match",
    )
    args = parser.parse_args()

    print_run_header(
        "data_acquisition/resolve_taskA_near_matches.py", [WORKBOOK, RESOLUTION]
    )
    # Sequences come from Table S1 itself rather than from curated.csv, so this scan runs
    # before the parse and the parse reads its output. The other order would be circular.
    assayed = extract_assayed_block(WORKBOOK)
    prior = {}
    if RESOLUTION.is_file():
        frame = pd.read_csv(RESOLUTION, sep="\t", dtype=str, keep_default_na=False)
        prior = {row["rt_name"]: row.get("status", "") for row in frame.to_dict("records")}

    entries = load_cache()
    print("cached UniProt entries searched: " + str(len(entries)))
    # A row needs explaining when the earlier resolver did not pin it exactly.
    todo = [
        {"rt_name": entry.name, "sequence": entry.sequence}
        for entry in assayed
        if prior.get(entry.name, "unresolved") != "resolved"
    ]
    print("rows without a pinned accession: " + str(len(todo)))
    print("near-match threshold: " + str(args.min_identity) + " percent identity")
    print("")

    rows = []
    counts = {"exact": 0, "near": 0, "homolog_only": 0, "no_candidate": 0}
    for record in todo:
        name = record["rt_name"]
        query = record["sequence"]
        accession, matches, offset = best_ungapped(query, entries)
        if not accession:
            rows.append(
                {
                    "rt_name": name,
                    "sequence_len": str(len(query)),
                    "prior_status": prior.get(name, ""),
                    "best_accession": "",
                    "best_entry_name": "",
                    "best_organism": "",
                    "best_sequence_version": "",
                    "parent_start": "",
                    "parent_end": "",
                    "identity_pct": "",
                    "n_differences": "",
                    "differences": "",
                    "verdict": "no cached entry is at least as long as this sequence",
                }
            )
            counts["no_candidate"] += 1
            print("%-22s no candidate" % name)
            continue

        header, subject = entries[accession]
        window = subject[offset : offset + len(query)]
        differences = [
            (position + 1, window[position], query[position], offset + position + 1)
            for position in range(len(query))
            if window[position] != query[position]
        ]
        identity = 100.0 * matches / len(query)
        if not differences:
            verdict = (
                "exact substring of this entry; the prior run recorded it as "
                + (prior.get(name) or "unresolved")
                + ", so the ambiguity rather than the sequence is what blocks the pin"
            )
            counts["exact"] += 1
        elif identity >= args.min_identity:
            verdict = (
                "near match, "
                + str(len(differences))
                + " residue difference(s); same protein on the evidence, but not an exact "
                "pin, so the accession is left empty and the difference is recorded"
            )
            counts["near"] += 1
        else:
            verdict = (
                "homolog only at "
                + str(round(identity, 2))
                + " percent; the cache does not contain this row's parent entry"
            )
            counts["homolog_only"] += 1

        rows.append(
            {
                "rt_name": name,
                "sequence_len": str(len(query)),
                "prior_status": prior.get(name, ""),
                "best_accession": accession,
                "best_entry_name": entry_name(header),
                "best_organism": header_field(header, "OS"),
                "best_sequence_version": header_field(header, "SV"),
                "parent_start": str(offset + 1),
                "parent_end": str(offset + len(query)),
                "identity_pct": str(round(identity, 4)),
                "n_differences": str(len(differences)),
                "differences": ";".join(
                    subject_residue + str(query_position) + query_residue
                    for query_position, subject_residue, query_residue, _parent in differences
                ),
                "verdict": verdict,
            }
        )
        print(
            "%-22s %-12s identity=%6.2f%% diffs=%-3d %s"
            % (name, accession, identity, len(differences), verdict[:60])
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FIELDS), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print("")
    for kind, count in sorted(counts.items()):
        print(kind + ": " + str(count))
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    print("    sha256 " + sha256_of(OUT))
    print("")
    print("No accession from this scan is written into curated.csv. A near match is")
    print("evidence for an identification, not an identification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
