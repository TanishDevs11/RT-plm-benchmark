"""Preflight check for the acquisition inputs.

This script holds the manifest of files the Phase 2 parsers expect, and reports which of
them are present, with a SHA256 for each one that is. It exits non-zero when a required
file is absent.

It exists so that a missing supplementary table is a loud, early, specific failure rather
than something a parser discovers halfway through and works around. Nothing in this
pipeline is permitted to proceed past a missing file by inventing its contents, and the
first line of that defence is knowing exactly which files are not there.

    python data_acquisition/check_inputs.py
    python data_acquisition/check_inputs.py --priority 1

The manifest mirrors data_acquisition/MANUAL_FETCH.md. If the two disagree, the checklist
a human reads is the one that is wrong, and this file is the one to trust, because this one
is executed.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402


@dataclass(frozen=True)
class ExpectedInput:
    path: str
    task: str
    purpose: str
    required: bool
    priority: int
    source: str
    # True when a script may fetch this without a human, so an absence here is a task to
    # run rather than a task to ask someone to do.
    automatable: bool = False


# Every path is relative to the repository root. A file listed as required is one without
# which the corresponding task cannot be built at all.
EXPECTED: tuple[ExpectedInput, ...] = (
    # Priority 1: Task B. The reference sequence gates all 1046 Task B rows.
    ExpectedInput(
        path="tasks/taskB_mmlv_dms/raw/supplementary_sequences.pdf",
        task="B",
        purpose=(
            "PE2dR RT protein sequence, the reference every Task B variant is built on; "
            "resolves the 671 against 677 numbering conflict and the pentamutant question"
        ),
        required=True,
        priority=1,
        source="https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.supplementary-material",
    ),
    ExpectedInput(
        path="tasks/taskB_mmlv_dms/raw/table_s6.xlsx",
        task="B",
        purpose="per-variant activity for one of the two libraries; which stretch is unconfirmed",
        required=True,
        priority=1,
        source="https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.supplementary-material",
    ),
    ExpectedInput(
        path="tasks/taskB_mmlv_dms/raw/table_s7.xlsx",
        task="B",
        purpose="per-variant activity for the other library",
        required=True,
        priority=1,
        source="https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.supplementary-material",
    ),
    ExpectedInput(
        path="tasks/taskB_mmlv_dms/raw/reference.fasta",
        task="B",
        purpose=(
            "the adopted PE2dR RT reference, written by the Phase 2 resolver rather than "
            "downloaded; absent until the sequence above has been read and confirmed"
        ),
        required=True,
        priority=1,
        source="derived in Phase 2 from supplementary_sequences.pdf",
    ),
    ExpectedInput(
        path="tasks/taskB_mmlv_dms/raw/preprint.pdf",
        task="B",
        purpose="main text, so the label definition and stretch boundaries can be re-checked offline",
        required=False,
        priority=1,
        source="https://www.biorxiv.org/content/10.64898/2026.07.06.736660v1.full.pdf",
    ),
    ExpectedInput(
        path="tasks/taskB_mmlv_dms/raw/addgene_132775_pCMV-PE2.gb",
        task="B",
        purpose="parent plasmid sequence, needed only if the supplementary sequences do not settle the pentamutant question",
        required=False,
        priority=1,
        source="https://www.addgene.org/132775/sequences/",
    ),
    # Priority 2: Task A. Without these, no Task A row can carry an accession, and no Task
    # A row passes the schema validator.
    ExpectedInput(
        path="tasks/taskA_crossfamily/raw/doman2023_table_s1.xlsx",
        task="A",
        purpose=(
            "the 59-enzyme cross-family panel: names, classes, efficiencies; resolves 57 "
            "against 59, 21 actives against 20, and the 7 against 14 class coarsening"
        ),
        required=True,
        priority=2,
        source="https://www.cell.com/cell/fulltext/S0092-8674(23)00854-1#supplementaryMaterial",
    ),
    ExpectedInput(
        path="tasks/taskA_crossfamily/raw/doman2023.pdf",
        task="A",
        purpose="verbatim label definition and the paper's detectable-activity threshold",
        required=False,
        priority=2,
        source="https://www.cell.com/cell/pdf/S0092-8674(23)00854-1.pdf",
    ),
    ExpectedInput(
        path="tasks/taskB_mmlv_dms/raw/uniprot_P03355.fasta",
        task="B",
        purpose=(
            "M-MLV Gag-Pol; its p80 chain at 660 to 1330 is the canonical RT frame, and the "
            "frame resolution in resolve_mmlv_reference.py is checked against it"
        ),
        required=True,
        priority=1,
        source="https://rest.uniprot.org/uniprotkb/P03355.fasta",
        automatable=True,
    ),
    # Task A2, opened by the Gate G1 ruling. Its values sit in the same Cell supplementary
    # set as Task A, so it needs a ruling and a parse rather than a separate download.
    ExpectedInput(
        path="tasks/taskA2_evolved/raw/doman2023_pe6_efficiencies.xlsx",
        task="A2",
        purpose="PE6a to PE6g measured efficiencies; may be the same file as Task A Table S1",
        required=False,
        priority=3,
        source="https://www.cell.com/cell/fulltext/S0092-8674(23)00854-1#supplementaryMaterial",
    ),
)


def resolve(entry: ExpectedInput) -> Path:
    return REPO_ROOT / entry.path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report which acquisition inputs are present.")
    parser.add_argument("--priority", type=int, default=None, help="check only this priority tier")
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="report and exit zero even when a required input is absent; for inventory only",
    )
    args = parser.parse_args(argv)

    print_run_header("data_acquisition/check_inputs.py")

    entries = [e for e in EXPECTED if args.priority is None or e.priority == args.priority]
    present: list[ExpectedInput] = []
    missing_required: list[ExpectedInput] = []
    missing_optional: list[ExpectedInput] = []

    print("")
    for entry in sorted(entries, key=lambda e: (e.priority, e.path)):
        path = resolve(entry)
        tier = "required" if entry.required else "optional"
        if path.is_file():
            present.append(entry)
            print(
                "PRESENT  p"
                + str(entry.priority)
                + " task="
                + entry.task
                + " "
                + entry.path
                + " bytes="
                + str(path.stat().st_size)
                + " sha256="
                + sha256_of(path)
            )
        else:
            (missing_required if entry.required else missing_optional).append(entry)
            how = "script can fetch" if entry.automatable else "human must fetch"
            print("ABSENT   p" + str(entry.priority) + " task=" + entry.task + " " + entry.path)
            print("         " + tier + ", " + how)
            print("         purpose: " + entry.purpose)
            print("         source:  " + entry.source)

    print("")
    print(
        "inputs checked: "
        + str(len(entries))
        + ", present: "
        + str(len(present))
        + ", required missing: "
        + str(len(missing_required))
        + ", optional missing: "
        + str(len(missing_optional))
    )

    if missing_required:
        print("")
        print("Required inputs are absent, so no task table can be built yet.")
        print("See data_acquisition/MANUAL_FETCH.md for where to get each one.")
        print("Do not proceed past a missing file by inventing its contents.")
        if not args.allow_missing:
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
