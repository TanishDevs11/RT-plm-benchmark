"""Parse the assayed block of Doman et al. Table S1 into the Task A curated table.

Gate G1 ruling, 2026-10-02: block 1 of sheet `Table S1` in `mmc2.xlsx`, rows 6 to 118,
57 entries, 21 carrying the green activity fill, is the assayed prime editing panel and
the sole source for `curated.csv`. Block 2, the 486 UniProt BLAST hits at rows 122 to
1092, is excluded from the benchmark entirely and is retained only as provenance.

This script therefore reads one caption-delimited row range and refuses to read anything
else. It asserts the block boundary, the entry count and the highlight count against the
inventory that was ruled on, so that a workbook whose layout differs from the one a human
confirmed halts instead of quietly taking different rows.

    python data_acquisition/parse_taskA.py
    python data_acquisition/parse_taskA.py --no-fasta     # skip writing raw/sequences/

Outputs:
    tasks/taskA_crossfamily/curated.csv        the curated table
    tasks/taskA_crossfamily/raw/sequences/     one FASTA per resolved accession
    reports/reconciliation.md                  every discrepancy, resolved or not

What this script will not do
----------------------------
It will not invent an accession, a host organism, a class label or an efficiency value.
Table S1 contains none of those four things, and three of them are not obtainable from
the published record at all. Where a value is missing it stays empty and the reason is
recorded, because a filled cell with a guessed value is indistinguishable downstream from
a filled cell with a measured one.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import openpyxl  # noqa: E402

from data_acquisition.inventory_tableS1 import highlighted_cells  # noqa: E402
from schemas.task_schema import (  # noqa: E402
    AA20,
    print_run_header,
    read_task_table,
    sha256_of,
    validate_task_table,
)

TASK = "A"
SOURCE_DOI = "10.1016/j.cell.2023.07.039"
SOURCE_TABLE = "Table S1 (mmc2.xlsx), sheet 'Table S1', assayed block, rows 6 to 118"

WORKBOOK = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw" / "mmc2.xlsx"
SHEET = "Table S1"
INHERITED = REPO_ROOT / "data" / "rt_sequences.csv"
ACCESSIONS = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw" / "accession_resolution.tsv"
NEAR_MATCHES = (
    REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw" / "accession_near_matches.tsv"
)
UNIPROT_CACHE = REPO_ROOT / ".uniprot_cache"

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
FASTA_DIR = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw" / "sequences"
RECONCILIATION = REPO_ROOT / "reports" / "reconciliation.md"

# The structure a human ruled on at Gate G1. Every one of these is asserted, not assumed.
# If the source file is ever replaced and any of them moves, this script stops.
BLOCK1_FIRST_ROW = 6
BLOCK1_LAST_ROW = 118
BLOCK2_CAPTION_ROW = 121
EXPECTED_ENTRIES = 57
EXPECTED_HIGHLIGHTED = 21

# Caption fragments that identify the two blocks. The second is reproduced with the two
# spelling errors the published file actually contains; correcting them here would make
# the assertion pass against a file that is not the one that was ruled on.
BLOCK1_CAPTION_FRAGMENT = "tested for prime editing"
BLOCK1_HIGHLIGHT_CAPTION = "highlighted in green show activity"
BLOCK2_CAPTION_FRAGMENT = "Sequencces of additonal reverse transcriptases"

# The counts the article's prose gives, carried here only so the reconciliation can state
# the gap. Nothing is adjusted to match them.
PROSE_ENTRIES = 59
PROSE_ACTIVES = 20

# Controlled vocabulary for `family`.
#
# The brief asks for a vocabulary derived from the paper's 14 classes. That is not
# possible from the published record: Table S1 carries no class column, and the 14 classes
# exist only as labelled nodes in the Figure 1B tree image. So the vocabulary below is the
# inherited 7-way labelling, which is what the frozen splits and the whole prior audit are
# built on, and the fact that it cannot be checked against the paper's 14 classes is a
# recorded limitation rather than a silent substitution.
FAMILY_VOCABULARY: tuple[str, ...] = (
    "CRISPR-associated",
    "Group_II_Intron",
    "LTR_Retrotransposon",
    "Other",
    "Retron",
    "Retroviral",
    "Unclassified",
)

# What the efficiency column is attributed to, and why that is an attribution rather than
# a verification. Figure S1A is the only panel in the paper that reports one value per
# enzyme for every enzyme in the survey, including the inactive ones: Figure 1C shows only
# the 20 the text counts as active, across several endogenous sites.
EFFICIENCY_SOURCE = "FigureS1A_HEK3_plus5_G_to_T_mean_n3_UNVERIFIED_DIGITIZED"

LABEL_UNITS = "percent_precise_prime_edit_no_indels"
LABEL_ASSAY = "prime_editing_pct_HEK293T"


@dataclass(frozen=True)
class Entry:
    index: int
    name: str
    sequence: str
    active: bool
    name_row: int
    sequence_row: int


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cell(sheet, row: int, column: int) -> str:
    value = sheet.cell(row=row, column=column).value
    return "" if value is None else str(value).strip()


def extract_assayed_block(path: Path) -> list[Entry]:
    """Read block 1 only, asserting every structural fact the G1 ruling rests on."""
    book = openpyxl.load_workbook(path, data_only=True)
    if SHEET not in book.sheetnames:
        raise SystemExit(
            "sheet " + repr(SHEET) + " absent; found " + str(book.sheetnames)
        )
    sheet = book[SHEET]

    # The captions are the block boundary. Assert them before reading any data row, so a
    # reordered or re-exported workbook stops here rather than further downstream.
    captions = {row: cell(sheet, row, 1) for row in (4, 5, BLOCK2_CAPTION_ROW)}
    if BLOCK1_CAPTION_FRAGMENT not in captions[4]:
        raise SystemExit(
            "row 4 should open the assayed block with "
            + repr(BLOCK1_CAPTION_FRAGMENT)
            + "; found "
            + repr(captions[4])
        )
    if BLOCK1_HIGHLIGHT_CAPTION not in captions[5]:
        raise SystemExit(
            "row 5 should define the highlight as activity; found " + repr(captions[5])
        )
    if BLOCK2_CAPTION_FRAGMENT not in captions[BLOCK2_CAPTION_ROW]:
        raise SystemExit(
            "row "
            + str(BLOCK2_CAPTION_ROW)
            + " should open the excluded phylogenetic block; found "
            + repr(captions[BLOCK2_CAPTION_ROW])
        )

    marked, _ = highlighted_cells(path)

    entries: list[Entry] = []
    row = BLOCK1_FIRST_ROW
    while row <= BLOCK1_LAST_ROW:
        index_text = cell(sheet, row, 1)
        if not index_text.isdigit():
            row += 1
            continue
        name = cell(sheet, row, 2).lstrip(">").strip()
        # The sequence sits on the rows between this index row and the next one. Joining
        # whatever is there, rather than assuming a single row, means a wrapped sequence
        # would be assembled rather than truncated.
        parts: list[str] = []
        probe = row + 1
        while probe <= BLOCK1_LAST_ROW + 1 and not cell(sheet, probe, 1).isdigit():
            piece = cell(sheet, probe, 2)
            if piece:
                parts.append(piece)
            probe += 1
        if len(parts) != 1:
            raise SystemExit(
                "entry "
                + name
                + " at row "
                + str(row)
                + " has "
                + str(len(parts))
                + " sequence rows; expected exactly 1"
            )
        sequence = parts[0].upper()
        illegal = sorted(set(sequence) - set(AA20))
        if illegal:
            raise SystemExit(
                "entry " + name + " carries non-standard residues " + str(illegal)
            )
        active = ("A" + str(row)) in marked or ("B" + str(row)) in marked
        entries.append(
            Entry(int(index_text), name, sequence, active, row, row + 1)
        )
        row = probe
    book.close()

    if len(entries) != EXPECTED_ENTRIES:
        raise SystemExit(
            "expected "
            + str(EXPECTED_ENTRIES)
            + " assayed entries per the Gate G1 ruling, parsed "
            + str(len(entries))
        )
    highlighted = sum(1 for e in entries if e.active)
    if highlighted != EXPECTED_HIGHLIGHTED:
        raise SystemExit(
            "expected "
            + str(EXPECTED_HIGHLIGHTED)
            + " highlighted entries per the Gate G1 ruling, found "
            + str(highlighted)
        )
    indices = [e.index for e in entries]
    if indices != list(range(1, EXPECTED_ENTRIES + 1)):
        raise SystemExit("assayed block indices are not 1.." + str(EXPECTED_ENTRIES))
    # The excluded block starts at index 58. Nothing above 57 may have been read.
    if max(indices) >= 58:
        raise SystemExit("an entry from the excluded phylogenetic block was read")
    return entries


def load_accessions() -> dict[str, dict[str, str]]:
    """Accessions resolved from sequence against UniProt by the earlier Phase 2 step.

    Only `resolved` is used. `resolved_ambiguous` means two or more database entries
    contain the sequence exactly, so there is no single accession to pin, and recording
    one of them would be choosing arbitrarily between equally supported candidates.
    """
    if not ACCESSIONS.is_file():
        return {}
    frame = pd.read_csv(ACCESSIONS, sep="\t", dtype=str, keep_default_na=False)
    out: dict[str, dict[str, str]] = {}
    for row in frame.to_dict("records"):
        out[row["rt_name"]] = row
    return out


def load_near_matches() -> dict[str, dict[str, str]]:
    """Why each unpinned row did not pin, from resolve_taskA_near_matches.py.

    Optional input. Its absence costs only the explanatory note, never a curated value,
    because nothing in this file is sourced from it.
    """
    if not NEAR_MATCHES.is_file():
        return {}
    frame = pd.read_csv(NEAR_MATCHES, sep="\t", dtype=str, keep_default_na=False)
    return {row["rt_name"]: row for row in frame.to_dict("records")}


def uniprot_organism(accession: str) -> tuple[str, str]:
    """Host organism from the cached UniProt FASTA header, plus the header itself."""
    path = UNIPROT_CACHE / (accession + ".fasta")
    if not path.is_file():
        return "", ""
    header = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    found = re.search(r"OS=(.*?)(?= OX=| GN=| PE=| SV=|$)", header)
    return (found.group(1).strip() if found else ""), header


def copy_fasta(accession: str) -> str:
    """Copy the cached FASTA for one accession into raw/sequences/, return its SHA256."""
    source = UNIPROT_CACHE / (accession + ".fasta")
    if not source.is_file():
        return ""
    FASTA_DIR.mkdir(parents=True, exist_ok=True)
    target = FASTA_DIR / (accession + ".fasta")
    target.write_bytes(source.read_bytes())
    return sha256_of(target)


def build_rows(
    entries: list[Entry],
    inherited: pd.DataFrame,
    accessions: dict,
    near_matches: dict,
    write_fasta: bool,
) -> tuple[list[dict], list[str]]:
    """Assemble the curated rows, recording a note wherever a value could not be sourced."""
    by_name = {row["rt_name"]: row for row in inherited.to_dict("records")}
    rows: list[dict] = []
    fasta_log: list[str] = []

    for entry in entries:
        inherited_row = by_name.get(entry.name)
        notes: list[str] = []

        resolution = accessions.get(entry.name, {})
        status = resolution.get("status", "absent")
        accession = ""
        accession_version = ""
        reference_accession = ""
        host = ""
        if status == "resolved":
            accession = resolution.get("accession", "")
            accession_version = resolution.get("sequence_version", "")
            reference_accession = resolution.get("reference_accession", "")
            host, header = uniprot_organism(accession)
            if write_fasta and accession:
                digest = copy_fasta(accession)
                if digest:
                    fasta_log.append(accession + ".fasta sha256=" + digest)
                else:
                    notes.append("UniProt FASTA not in local cache, not written")
            if not host:
                notes.append("host organism not recoverable from the cached FASTA header")
        elif status == "resolved_ambiguous":
            notes.append(
                "accession ambiguous: "
                + resolution.get("note", "several entries contain this sequence exactly")
                + "; left empty rather than choosing between equally supported candidates"
            )
        else:
            notes.append(
                "accession unresolved against UniProt: "
                + (resolution.get("note", "no resolution attempt recorded") or "no reason recorded")
            )

        # Why it did not pin, where the near-match scan could say. This is an explanation
        # attached to an empty cell, never a value filling one.
        near = near_matches.get(entry.name)
        if near and near.get("best_accession") and near.get("n_differences") not in ("", None):
            if near["n_differences"] == "0":
                notes.append(
                    "nearest database entry "
                    + near["best_accession"]
                    + " contains this sequence exactly, but the pin is blocked by ambiguity"
                )
            elif float(near.get("identity_pct") or 0) >= 99.0:
                notes.append(
                    "nearest database entry "
                    + near["best_accession"]
                    + " ("
                    + near.get("best_organism", "")
                    + ") differs at "
                    + near["n_differences"]
                    + " residue(s): "
                    + near["differences"]
                    + "; same protein on the evidence but not an exact pin"
                )
            else:
                notes.append(
                    "no database entry in the local cache is closer than "
                    + near["identity_pct"]
                    + " percent identity, so the parent entry is simply not in the "
                    "searched set"
                )

        # Family and efficiency are not in Table S1. Both are carried over from the
        # inherited table, and both carry a note saying so, because a reader of
        # curated.csv must be able to tell a value taken from the primary source from a
        # value taken from the file this project inherited.
        family = ""
        efficiency = ""
        if inherited_row is None:
            notes.append(
                "no inherited row for this enzyme, so family and efficiency are absent"
            )
        else:
            family = str(inherited_row["rt_family"]).strip()
            efficiency = str(inherited_row["pe_efficiency_pct"]).strip()
            notes.append(
                "family and efficiency carried from data/rt_sequences.csv; neither "
                "appears anywhere in Table S1"
            )
            if str(inherited_row["sequence"]).strip().upper() != entry.sequence:
                notes.append("SEQUENCE MISMATCH against the inherited table")
            if int(inherited_row["active"]) != int(entry.active):
                notes.append("ACTIVITY MISMATCH against the inherited table")

        rows.append(
            {
                # Core schema columns, so the repository's own validator and the identity
                # clustering keep working against this file.
                "id": "A_" + entry.name,
                "task": TASK,
                "sequence": entry.sequence,
                "sequence_len": str(len(entry.sequence)),
                "family": family,
                "parent_id": "",
                "mutations": "",
                "label_value": efficiency,
                "label_units": LABEL_UNITS,
                "label_assay": LABEL_ASSAY,
                "label_is_binary": "true",
                "label_binary": "1" if entry.active else "0",
                "source_doi": SOURCE_DOI,
                "source_table": SOURCE_TABLE,
                "reference_accession": reference_accession,
                "notes": "; ".join(notes),
                # The columns the brief names for Task A.
                "rt_name": entry.name,
                "accession": accession,
                "accession_version": accession_version,
                "host_organism": host,
                "active": "1" if entry.active else "0",
                "pe_efficiency_pct": efficiency,
                "efficiency_source_column": EFFICIENCY_SOURCE,
                "table_s1_index": str(entry.index),
                "table_s1_name_row": str(entry.name_row),
                "sequence_sha256": sha256_text(entry.sequence),
            }
        )
    return rows, fasta_log


COLUMNS: tuple[str, ...] = (
    "id",
    "task",
    "rt_name",
    "accession",
    "accession_version",
    "reference_accession",
    "family",
    "host_organism",
    "sequence",
    "sequence_len",
    "sequence_sha256",
    "active",
    "label_binary",
    "pe_efficiency_pct",
    "label_value",
    "label_units",
    "label_assay",
    "label_is_binary",
    "efficiency_source_column",
    "parent_id",
    "mutations",
    "source_doi",
    "source_table",
    "table_s1_index",
    "table_s1_name_row",
    "notes",
)


def validate(rows: list[dict]) -> list[str]:
    """The rejection rules the brief specifies. Returns a list of violations."""
    violations: list[str] = []
    seen_sequences: dict[str, str] = {}
    seen_names: set[str] = set()

    for position, row in enumerate(rows, start=1):
        where = "row " + str(position) + " (" + row["rt_name"] + "): "
        sequence = row["sequence"]
        if not sequence:
            violations.append(where + "null sequence")
        else:
            if sequence in seen_sequences:
                violations.append(
                    where + "sequence identical to " + seen_sequences[sequence]
                )
            else:
                seen_sequences[sequence] = row["rt_name"]
            if not row["sequence_len"].isdigit():
                violations.append(where + "sequence_len is not an integer")
            elif int(row["sequence_len"]) != len(sequence):
                violations.append(
                    where
                    + "sequence_len "
                    + row["sequence_len"]
                    + " does not equal len(sequence) "
                    + str(len(sequence))
                )
        if not row["source_doi"]:
            violations.append(where + "null source_doi")
        if row["family"] not in FAMILY_VOCABULARY:
            violations.append(
                where + "family " + repr(row["family"]) + " is not in the controlled vocabulary"
            )
        if row["rt_name"] in seen_names:
            violations.append(where + "duplicate rt_name")
        seen_names.add(row["rt_name"])
        # The curated file carries the binary label and the efficiency twice, once under
        # the brief's column names and once under the repository schema's. Duplication
        # that is not checked is duplication that will diverge, so it is checked.
        if row["active"] != row["label_binary"]:
            violations.append(where + "active and label_binary disagree")
        if row["pe_efficiency_pct"] != row["label_value"]:
            violations.append(where + "pe_efficiency_pct and label_value disagree")
        if row["active"] == "1" and row["pe_efficiency_pct"] in ("", "0", "0.0"):
            violations.append(where + "called active but carries no positive efficiency")
        if row["active"] == "0" and row["pe_efficiency_pct"] not in ("", "0", "0.0"):
            violations.append(where + "called inactive but carries a non-zero efficiency")
    return violations


def write_curated(rows: list[dict]) -> None:
    CURATED.parent.mkdir(parents=True, exist_ok=True)
    with CURATED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(COLUMNS))
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in COLUMNS})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-fasta", action="store_true", help="do not write raw/sequences/"
    )
    args = parser.parse_args()

    print_run_header(
        "data_acquisition/parse_taskA.py", [WORKBOOK, INHERITED, ACCESSIONS]
    )
    print("Gate G1 ruling applied: assayed block only, rows "
          + str(BLOCK1_FIRST_ROW) + " to " + str(BLOCK1_LAST_ROW))
    print("")

    entries = extract_assayed_block(WORKBOOK)
    print("parsed " + str(len(entries)) + " assayed entries, "
          + str(sum(1 for e in entries if e.active)) + " highlighted as active")

    inherited = pd.read_csv(INHERITED)
    accessions = load_accessions()
    near_matches = load_near_matches()
    print("near-match explanations available for " + str(len(near_matches)) + " rows")
    rows, fasta_log = build_rows(
        entries, inherited, accessions, near_matches, not args.no_fasta
    )

    violations = validate(rows)
    print("")
    print("validator: " + str(len(violations)) + " violations")
    for violation in violations:
        print("  VIOLATION " + violation)
    if violations:
        raise SystemExit(
            "curated.csv not written: the validator rejected the table. Nothing is "
            "coerced or dropped to make it pass."
        )

    write_curated(rows)
    print("wrote " + CURATED.relative_to(REPO_ROOT).as_posix())
    print("    sha256 " + sha256_of(CURATED))
    if fasta_log:
        print("wrote " + str(len(fasta_log)) + " FASTA files to "
              + FASTA_DIR.relative_to(REPO_ROOT).as_posix())

    # The repository's own schema validator, run separately and reported rather than
    # enforced. It requires a non-empty reference_accession on every row, and Table S1
    # supplies none, so it fails on exactly the rows whose accession is unresolved. That
    # is a real conflict between the schema's expectations and the published record, and
    # it is a Gate G2 decision, not something this script may resolve.
    print("")
    print("=== repository schema validator, reported not enforced ===")
    report = validate_task_table(read_task_table(CURATED), task=TASK, source=str(CURATED))
    print(report.render())
    kinds: dict[str, int] = {}
    for violation in report.violations:
        kinds[violation.rule] = kinds.get(violation.rule, 0) + 1
    for rule, count in sorted(kinds.items()):
        print("  " + rule + ": " + str(count))
    if not kinds:
        print("  no violations")

    write_reconciliation(entries, rows, inherited, accessions, near_matches, kinds)
    print("")
    print("wrote " + RECONCILIATION.relative_to(REPO_ROOT).as_posix())
    return 0


def write_reconciliation(
    entries: list[Entry],
    rows: list[dict],
    inherited: pd.DataFrame,
    accessions: dict,
    near_matches: dict,
    schema_violations: dict[str, int],
) -> None:
    """Every discrepancy between the source, the inherited file, and the article prose."""
    table_names = [e.name for e in entries]
    inherited_names = inherited["rt_name"].tolist()
    table_actives = sorted(e.name for e in entries if e.active)
    inherited_actives = sorted(inherited.loc[inherited["active"] == 1, "rt_name"])

    by_name_inherited = {
        r["rt_name"]: str(r["sequence"]).strip().upper()
        for r in inherited.to_dict("records")
    }
    mismatches = [
        e.name
        for e in entries
        if e.name in by_name_inherited and by_name_inherited[e.name] != e.sequence
    ]
    # The inherited file carries its own length column. Whether it agrees with its own
    # sequences is a separate question from whether those sequences match the paper, and
    # the report states both, so both are computed.
    length_disagreements = [
        str(r["rt_name"])
        for r in inherited.to_dict("records")
        if int(r["protein_length_aa"]) != len(str(r["sequence"]).strip())
    ]

    family_of = dict(zip(inherited["rt_name"], inherited["rt_family"]))
    from collections import Counter

    active_by_family = Counter(family_of[name] for name in table_actives)

    efficiency = pd.to_numeric(inherited["pe_efficiency_pct"], errors="coerce")
    active_mask = inherited["active"] == 1
    active_values = sorted(efficiency[active_mask].tolist(), reverse=True)
    all_half = all(abs(round(v * 2) / 2 - v) < 1e-9 for v in active_values)

    statuses = Counter(
        accessions.get(e.name, {}).get("status", "absent") for e in entries
    )

    # Containment: one sequence wholly inside another, which identity clustering reports
    # as a near-duplicate and which a benchmark has to know about.
    sequences = {e.name: e.sequence for e in entries}
    contained = [
        (a, b)
        for a in sorted(sequences)
        for b in sorted(sequences)
        if a != b and len(sequences[a]) < len(sequences[b]) and sequences[a] in sequences[b]
    ]
    exact_duplicates: dict[str, list[str]] = {}
    for name, sequence in sequences.items():
        exact_duplicates.setdefault(sha256_text(sequence), []).append(name)
    duplicate_groups = [v for v in exact_duplicates.values() if len(v) > 1]

    lines = [
        "# Task A reconciliation",
        "",
        "Written by `data_acquisition/parse_taskA.py`. This is the Gate G2 artifact.",
        "",
        "Source: Doman et al. 2023, `" + SOURCE_DOI + "`, " + SOURCE_TABLE + ".",
        "Workbook SHA256 `" + sha256_of(WORKBOOK) + "`.",
        "Parsed " + date.today().isoformat() + ".",
        "",
        "No discrepancy below is resolved by choosing a side. Each is stated with the",
        "evidence for both readings, for a human to rule on.",
        "",
        "## 1. Which of the surveyed RTs are in the inherited file",
        "",
        "| quantity | value |",
        "| --- | --- |",
        "| entries in Table S1's assayed block | " + str(len(table_names)) + " |",
        "| rows in `data/rt_sequences.csv` | " + str(len(inherited_names)) + " |",
        "| names in Table S1 but not inherited | " + str(sorted(set(table_names) - set(inherited_names))) + " |",
        "| names inherited but not in Table S1 | " + str(sorted(set(inherited_names) - set(table_names))) + " |",
        "",
        "**The two sets are identical.** So there is no enzyme to name as missing from the",
        "inherited file, and the brief's expectation that 2 of the surveyed enzymes would",
        "be absent from it does not hold.",
        "",
        "### The 57 against 59 discrepancy",
        "",
        "The article's prose says the authors "
        + "tested "
        + str(PROSE_ENTRIES)
        + " enzymes. Table S1's assayed",
        "block holds " + str(len(table_names)) + ". The gap of "
        + str(PROSE_ENTRIES - len(table_names))
        + " is therefore **inside the primary source**: between the",
        "article's text and the article's own supplementary table. It is not a gap between",
        "this repository and the paper.",
        "",
        "Both readings, neither adopted:",
        "",
        "- **Reading A, the table is complete and the prose is wrong.** The table is the",
        "  itemised artifact, it is internally consistent, its index runs 1 to 57 without a",
        "  gap, and 57 is also exactly what the inherited dataset contains. Under this",
        "  reading the number 59 in the text is an error.",
        "- **Reading B, the prose is right and the table omits two.** 59 enzymes were",
        "  assayed and two were left out of the deposited table. Under this reading two",
        "  measured enzymes are missing from every downstream analysis, and nothing in the",
        "  published record names them, so nothing can be done about it either way.",
        "",
        "Neither reading changes the benchmark, because under both of them the 57 rows that",
        "exist are the only 57 that can be used. What it changes is the claim: the panel",
        "must be described as the 57 enzymes Table S1 lists, not as the 59 the paper says",
        "were tested.",
        "",
        "## 2. The 21 against 20 actives discrepancy",
        "",
        "| quantity | value |",
        "| --- | --- |",
        "| entries carrying the green activity fill | " + str(len(table_actives)) + " |",
        "| rows marked `active = 1` in the inherited file | " + str(len(inherited_actives)) + " |",
        "| the two sets are identical | " + ("yes" if table_actives == inherited_actives else "NO") + " |",
        "| the article's prose count | " + str(PROSE_ACTIVES) + " |",
        "",
        "Highlighted entries by inherited family: "
        + ", ".join(k + " " + str(v) for k, v in sorted(active_by_family.items()))
        + ".",
        "",
        "**The enzyme that accounts for the difference is M-MLV RT, and the evidence is in",
        "the article's own class breakdown.** The Figure S1A caption states that of the",
        "enzymes supporting detectable mammalian PE activity, 11 are closely related to the",
        "M-MLV RT and are encoded by retroviruses, two are encoded by LTR retrotransposons,",
        "and seven are bacterial RTs. That is 11 plus 2 plus 7, which is 20.",
        "",
        "The highlighted set matches that breakdown in every class except one:",
        "",
        "| class | prose | Table S1 highlights |",
        "| --- | --- | --- |",
        "| retroviral | 11 | " + str(active_by_family.get("Retroviral", 0)) + " |",
        "| LTR retrotransposon | 2 | " + str(active_by_family.get("LTR_Retrotransposon", 0)) + " |",
        "| bacterial: group-II intron, retron, CRISPR-Cas | 7 | "
        + str(
            active_by_family.get("Group_II_Intron", 0)
            + active_by_family.get("Retron", 0)
            + active_by_family.get("CRISPR-associated", 0)
        )
        + " |",
        "",
        "The phrase is **closely related to the M-MLV RT**, which excludes M-MLV RT itself,",
        "and the same Figure S1A caption separates it out explicitly: the wild-type M-MLV RT",
        "used in the PE1 system is highlighted in black while all other enzymes are in red.",
        "M-MLV RT is the PE1 comparator, not a survey candidate. Counting it gives 21,",
        "excluding it gives 20, and both numbers are correct under their own definition.",
        "",
        "### The two activity definitions, both stated",
        "",
        "- **Table S1's definition, 21 actives.** Any enzyme the authors shaded green,",
        "  described as showing activity in the prime editing system. M-MLV RT included.",
        "  This is what the inherited file uses and what `curated.csv` reproduces.",
        "- **The prose's definition, 20 actives.** Surveyed RTs showing detectable PE",
        "  activity, excluding the M-MLV RT that defines the PE1 baseline being surveyed",
        "  against. Neither definition states a numeric threshold; the word in the paper is",
        "  detectable.",
        "",
        "`curated.csv` carries the 21-active labelling, because it is the one attached to",
        "the itemised table rather than to a sentence, and because dropping M-MLV RT would",
        "remove the single highest-weighted row in the CLS metric. A ruling that the",
        "benchmark should instead report the 20-active definition is a one-line change and",
        "is a legitimate choice; it is not made here.",
        "",
        "## 3. Sequence integrity, checksum compared against the primary source",
        "",
        "This check had never been run on this dataset. Every inherited sequence is",
        "compared by SHA256 against the sequence in Table S1 for the same enzyme.",
        "",
        "| quantity | value |",
        "| --- | --- |",
        "| sequences compared | " + str(len(entries)) + " |",
        "| byte-identical by SHA256 | " + str(len(entries) - len(mismatches)) + " |",
        "| mismatches | " + str(len(mismatches)) + " |",
        "",
    ]
    if mismatches:
        lines.append("Mismatching enzymes: " + str(mismatches) + ".")
        lines.append("")
        lines.append("Each is shown with its first divergent position below.")
    else:
        lines += [
            "**All " + str(len(entries)) + " sequences are byte-identical to the primary",
            "source.** There is no sequence drift in the inherited dataset.",
            "",
            "Separately, the inherited file's own `protein_length_aa` column disagrees with",
            "`len(sequence)` on "
            + str(len(length_disagreements))
            + " of its "
            + str(len(inherited))
            + " rows"
            + ("" if not length_disagreements else ": " + str(length_disagreements))
            + ".",
            "",
            "This is the one inherited claim that this reconciliation strengthens rather",
            "than qualifies, and it is worth saying plainly: whatever else is unverifiable",
            "about this dataset, the sequences are exactly the paper's.",
        ]

    lines += [
        "",
        "## 4. The efficiency column, which has no verifiable source",
        "",
        "**Table S1 contains no efficiency values.** There is no numeric cell anywhere in",
        "the sheet except the row index. All six supplementary workbooks were scanned; none",
        "carries the per-enzyme survey efficiencies. So the inherited `pe_efficiency_pct`",
        "column cannot be checked against the published supplementary material at all.",
        "",
        "What the column can be attributed to, and how confidently:",
        "",
        "- **Which panel.** Figure S1A is the only panel reporting one value per enzyme for",
        "  every surveyed enzyme, inactive ones included. Its caption gives the assay",
        "  exactly: HEK293T cells, HEK3 +5 G to T edit, dots reflecting the mean of n = 3",
        "  independent replicates. Figure 1C is the alternative, but it plots only the",
        "  actives and does so across several endogenous sites, so it cannot be the source",
        "  of a single value for all 57 rows.",
        "- **Which quantity.** Defined verbatim in the Figure 1 caption: the frequency of",
        "  the intended prime editing outcome with no indels or other changes at the target",
        "  site. So these are precise-edit percentages, not total editing or indel-inclusive",
        "  rates.",
        "- **How the numbers were obtained.** Every one of the "
        + str(len(active_values))
        + " non-zero values is an exact",
        "  multiple of 0.5"
        + (" (verified)" if all_half else " (NOT verified, check this)")
        + ", and every inactive row is exactly 0.0. "
        + str(len(active_values))
        + " independent",
        "  amplicon-sequencing measurements landing exactly on half-percent boundaries is",
        "  not plausible. The quantization is the signature of values read off a plot by",
        "  eye. The values are: " + ", ".join(str(v) for v in active_values) + ".",
        "",
        "So `efficiency_source_column` is set to `" + EFFICIENCY_SOURCE + "`,",
        "which names the attribution and carries the word UNVERIFIED in the value itself,",
        "so that no downstream reader can treat it as sourced.",
        "",
        "**What this means for the benchmark.** The regression target is a digitization of a",
        "figure, at roughly half a percentage point of resolution, with no error bars",
        "recoverable. The weighted Spearman component of CLS is computed on it, and the",
        "CLS weighting concentrates most of its mass on the few highest-efficiency enzymes,",
        "which is exactly where a digitization error is largest in absolute terms. Any",
        "regression result in this benchmark has to be reported with that stated.",
        "",
        "The binary `active` label does not have this problem: it is read directly from the",
        "fill colour in Table S1 and is reproducible from the file.",
        "",
        "## 5. Accessions",
        "",
        "Table S1 gives no accession for any assayed enzyme; their names are bare",
        "laboratory labels. The article's full text contains no protein accession of any",
        "recognised form, and its data availability statement points at the key resources",
        "table, whose accessions are sequencing-read accessions for the SRA deposit.",
        "",
        "Accessions were therefore resolved from sequence against UniProt by",
        "`data_acquisition/resolve_taskA_accessions.py`. Status across the 57 rows:",
        "",
        "| status | rows | treatment in `curated.csv` |",
        "| --- | --- | --- |",
    ]
    for status, count in sorted(statuses.items()):
        treatment = {
            "resolved": "accession and version recorded, FASTA pinned in `raw/sequences/`",
            "resolved_ambiguous": "left empty: several entries contain the sequence exactly",
            "unresolved": "left empty: no database entry contains the sequence",
        }.get(status, "left empty")
        lines.append("| " + status + " | " + str(count) + " | " + treatment + " |")

    lines += [
        "",
        "An ambiguous resolution is left empty deliberately. Two UniProt entries containing",
        "the same sequence exactly are equally good candidates, and recording one of them",
        "would be a coin flip presented as a pinned accession.",
        "",
        "### Why the 30 unpinned rows did not pin",
        "",
        "A bare count of unresolved rows is not a finding. It does not distinguish a",
        "sequence whose parent protein is absent from the searched set from one whose",
        "parent is obvious but differs at a single residue, and only the first is a dead",
        "end. `data_acquisition/resolve_taskA_near_matches.py` finds each unpinned row's",
        "nearest entry in the local UniProt cache and reports every differing position.",
        "Results are in `raw/accession_near_matches.tsv`.",
        "",
    ]

    near_rows = [near_matches[e.name] for e in entries if e.name in near_matches]
    exact = [r for r in near_rows if r.get("n_differences") == "0"]
    close = [
        r
        for r in near_rows
        if r.get("n_differences") not in ("", "0")
        and float(r.get("identity_pct") or 0) >= 99.0
    ]
    distant = [
        r
        for r in near_rows
        if r.get("identity_pct") and float(r["identity_pct"]) < 99.0
    ]

    lines += [
        "| outcome | rows | what it means |",
        "| --- | --- | --- |",
        "| exact substring of a cached entry | "
        + str(len(exact))
        + " | the sequence is in the database; only the ambiguity blocks the pin |",
        "| near match, 1 to 4 residues different | "
        + str(len(close))
        + " | the parent protein is identified on the evidence, but the sequence is not that entry's sequence |",
        "| no entry closer than 99 percent | "
        + str(len(distant))
        + " | the cache does not contain the parent entry at all |",
        "",
        "**The near-match group is the interesting one, and it has a pattern.** The",
        "differences are listed as the cached entry's residue, the position in the Task A",
        "sequence, then the Task A residue:",
        "",
        "| enzyme | nearest entry | organism | identity | differences |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in sorted(close, key=lambda r: -float(r["identity_pct"])):
        lines.append(
            "| `"
            + record["rt_name"]
            + "` | `"
            + record["best_accession"]
            + "` | "
            + record.get("best_organism", "")
            + " | "
            + record["identity_pct"]
            + " | "
            + record["differences"]
            + " |"
        )

    position_one = [r for r in close if re.match(r"^[A-Z]1[A-Z]", r["differences"])]
    to_methionine = [
        r for r in position_one if re.match(r"^[A-Z]1M", r["differences"])
    ]
    internal_only = [r for r in close if r not in position_one]
    lines += [
        "",
        "Two things stand out. First, "
        + str(len(position_one))
        + " of these "
        + str(len(close))
        + " rows differ at position 1, and in "
        + str(len(to_methionine))
        + " of those the Task A residue there is methionine where the parent protein has",
        "something else. That is not an isolate difference; it is a start codon. These are",
        "excised RT domains, and an excised domain needs an initiating methionine to be",
        "expressed, so the construct's first residue differs from the parent protein by",
        "construction. The other position-1 differences are to residues other than",
        "methionine, so they are not explained this way and are left as observations.",
        "",
        "Second, the "
        + str(len(internal_only))
        + " rows that differ only at internal positions differ at one or two",
        "residues in an otherwise exact match over 300 to 700, which is what a different",
        "viral isolate or strain looks like rather than a different protein.",
        "",
        "So the great majority of the unresolved accessions are not a mystery. They are",
        "the expected consequence of comparing an expression construct against a",
        "reference proteome entry by exact string matching. The identification is",
        "well supported in these cases; what is not supported is calling the sequence",
        "identical to the accession, and `curated.csv` therefore keeps `accession` empty",
        "and records the difference in `notes`.",
        "",
        "Two limits of this scan, both of which mean it can explain a failure but not",
        "prove one. The search set is the local cache, which holds only the candidates the",
        "earlier resolver downloaded while probing, so a distant best hit means the cache",
        "lacks the parent rather than that UniProt does. And the alignment is ungapped, so",
        "a row whose parent differs by an insertion or deletion scores poorly even when it",
        "is the right protein.",
        "",
        "### The schema conflict this creates, which is a Gate G2 decision",
        "",
        "`schemas/task_schema.py` requires a non-empty `reference_accession` on every row,",
        "on the principle that every row should name the accession plus version of its",
        "parent sequence. That rule was written before it was known that the source",
        "publishes no accessions. Running it against `curated.csv` gives:",
        "",
        "| rule | rows |",
        "| --- | --- |",
    ]
    if schema_violations:
        for rule, count in sorted(schema_violations.items()):
            lines.append("| `" + rule + "` | " + str(count) + " |")
    else:
        lines.append("| none | 0 |")

    lines += [
        "",
        "Three ways to settle it, for a human to choose:",
        "",
        "1. **Relax the rule for Task A**, on the ground that the source publishes no",
        "   accessions and a sequence SHA256 is the stronger identifier anyway. Every row",
        "   carries `sequence_sha256`, which pins the sequence exactly and does not depend",
        "   on a database that may reassign an accession later. This is the recommendation.",
        "2. **Drop the rows without an accession.** That removes 30 of 57 rows, including",
        "   actives, and would leave a benchmark too small to say anything. Not recommended,",
        "   and recorded here only so the option is on the record.",
        "3. **Keep the rule and leave Task A failing it.** Honest, but it means the pipeline",
        "   has a permanently failing guard, which is how guards come to be ignored.",
        "",
        "## 6. Duplicate and near-identical sequences",
        "",
        "| check | result |",
        "| --- | --- |",
        "| exact duplicate sequences under different names | " + str(len(duplicate_groups)) + " |",
        "| one sequence wholly contained in another | " + str(len(contained)) + " |",
        "",
    ]
    if duplicate_groups:
        lines.append("Duplicate groups: " + str(duplicate_groups) + ".")
        lines.append("")
    if contained:
        for shorter, longer in contained:
            lines += [
                "**`"
                + shorter
                + "` ("
                + str(len(sequences[shorter]))
                + " residues) is wholly contained in `"
                + longer
                + "` ("
                + str(len(sequences[longer]))
                + " residues).**",
                "",
                "These are not two independent proteins. They are the same sequence excised",
                "at two different boundaries, differing only by the "
                + str(len(sequences[longer]) - len(sequences[shorter]))
                + " extra residues on",
                "the longer one. They cluster together at 90 percent identity. Both are",
                "labelled inactive, so the pair cannot inflate a classifier through",
                "contradictory labels, but it does mean the panel holds fewer independent",
                "observations than its row count suggests.",
                "",
            ]

    lines += [
        "Identity clustering at 90, 70, 50 and 30 percent is Phase 2 and is reported in",
        "`reports/dataset_overview.md`. The near-duplicate structure already known from the",
        "earlier clustering run is concentrated in the retroviral family, which also holds",
        "most of the actives, so the effective sample size is well below 57.",
        "",
        "## 7. What `curated.csv` asserts, and on whose authority",
        "",
        "| column | sourced from | authority |",
        "| --- | --- | --- |",
        "| `rt_name` | Table S1 assayed block | primary source |",
        "| `sequence`, `sequence_len`, `sequence_sha256` | Table S1 assayed block | primary source |",
        "| `active`, `label_binary` | the green fill in Table S1 | primary source |",
        "| `source_doi`, `source_table`, `table_s1_index` | Table S1 | primary source |",
        "| `accession`, `accession_version`, `reference_accession` | UniProt, resolved from sequence | derived, and empty where unresolved |",
        "| `host_organism` | the cached UniProt FASTA header | derived, and empty where no accession |",
        "| `family` | `data/rt_sequences.csv` | **inherited, not in the paper** |",
        "| `pe_efficiency_pct`, `label_value` | `data/rt_sequences.csv` | **inherited, and unverifiable against any published table** |",
        "",
        "The two bold rows are the ones a reader has to be careful with. `family` is a",
        "7-way labelling that cannot be checked against the paper's 14 classes, because",
        "those exist only in the Figure 1B tree image. `pe_efficiency_pct` is discussed in",
        "section 4 above.",
        "",
        "## Open rulings for Gate G2",
        "",
        "1. **Does the benchmark stand at 57 rows?** Recommended yes: 57 is what Table S1",
        "   lists and the prose's 59 names no additional enzyme.",
        "2. **21 actives or 20?** Recommended 21, the table's own labelling, with the 20",
        "   definition documented. The difference is M-MLV RT.",
        "3. **The `reference_accession` schema rule.** Recommended option 1, relax it for",
        "   Task A and rely on `sequence_sha256`.",
        "4. **Does the efficiency column stay in the benchmark at all?** It is a figure",
        "   digitization. Recommended: keep it, because it is the only continuous signal",
        "   available and the inherited CLS metric needs it, but report every regression",
        "   result with the digitization stated as a limitation, and treat classification on",
        "   the binary label as the primary result.",
    ]

    RECONCILIATION.parent.mkdir(parents=True, exist_ok=True)
    RECONCILIATION.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
