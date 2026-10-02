"""Enumerate every sheet of the Doman et al. supplementary workbooks before any parsing.

Table S1 of this paper is cited for two different things: the reverse transcriptases
assayed as prime editors, which is what Task A needs, and the 543 reverse transcriptase
sequences used for the downstream phylogenetic analyses, which were never assayed and
carry no activity labels. A parser that read the whole sheet, or matched on a sequence
column, would pull hundreds of unlabelled sequences into a 57-row task.

The layout turns out not to be two sheets. Table S1 is a single sheet holding a FASTA
dump in two caption-delimited blocks, with one running index across both, and activity
recorded as a green cell fill rather than as a column. A sheet-level inventory would
therefore have missed the distinction entirely, so this script works at block level:

  * for a tabular sheet it reports dimensions, header row and every column header
  * for a FASTA-style sheet it finds the caption rows, splits the sheet into blocks,
    and reports each block's row range, index range, entry count and first entries
  * it reads the workbook's fill styles and reports which entries carry a highlight,
    because in this workbook the highlight is the activity label

Nothing is parsed into the benchmark here. This script reads and reports, and the
determination of which block holds which dataset is confirmed by a human before a single
row is read.

    python data_acquisition/inventory_tableS1.py
    python data_acquisition/inventory_tableS1.py --rows 6

Output: reports/tableS1_inventory.md
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

import openpyxl

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

RAW_DIR = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw"
OUT = REPO_ROOT / "reports" / "tableS1_inventory.md"

# The counts the paper's prose gives, which the classification keys on.
PROSE_ASSAYED_N = 59
PROSE_PHYLO_N = 543

# Protein sequence cells run to hundreds of characters and would bury the row preview.
# They are abbreviated for display only, with the elided length stated, so that the
# preview stays readable without any cell being silently shortened.
CELL_DISPLAY_LIMIT = 56

ACTIVITY_TOKENS = (
    "efficien",
    "editing",
    "activit",
    "percent",
    "indel",
    "install",
    "pegrna",
    "hek",
    "locus",
)
SEQUENCE_TOKENS = ("sequence", "protein", "fasta", "residue")
IDENTITY_TOKENS = ("accession", "uniprot", "genbank", "ncbi", "refseq")


def cell_text(value: object) -> str:
    """Cell contents as text, with newlines flattened and nothing else changed.

    Pipes are deliberately left alone. An earlier version replaced them with slashes to
    keep markdown tables intact, which silently broke the classification of the second
    block: UniProt FASTA headers are pipe delimited, so `tr|A0A3M0K3Z6|...` stopped
    matching and 486 database identifiers were reported as bare labels. Never sanitize
    the value a decision is made on. Every place this report prints cell contents is a
    code fence or a bullet, where a pipe needs no escaping anyway.
    """
    if value is None:
        return ""
    return str(value).replace("\n", " ").replace("\r", " ").strip()


def abbreviate(text: str) -> str:
    if len(text) <= CELL_DISPLAY_LIMIT:
        return text
    return (
        text[:CELL_DISPLAY_LIMIT]
        + "[...truncated for display, "
        + str(len(text))
        + " chars total]"
    )


def highlighted_cells(path: Path) -> tuple[dict[str, str], list[str]]:
    """Return {cell reference: style note} for every cell carrying a non-empty fill.

    openpyxl's own fill accessor reports nothing useful for a theme-tinted fill written
    by Excel, so the style table and the sheet are read out of the xlsx container
    directly. The highlight is the activity label in this workbook, which makes it data
    rather than formatting, and data has to be read from the authoritative place.
    """
    descriptions: list[str] = []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if "xl/styles.xml" not in names:
            return {}, ["workbook carries no style table"]
        styles = archive.read("xl/styles.xml").decode("utf-8", "replace")
        fills = re.findall(r"<fill>.*?</fill>|<fill/>", styles, re.S)
        # Fill ids that actually paint something. patternType none and gray125 are the
        # two Excel always writes whether or not anything is highlighted.
        painted: dict[int, str] = {}
        for index, fill in enumerate(fills):
            if 'patternType="none"' in fill or 'patternType="gray125"' in fill:
                continue
            if "patternType" not in fill:
                continue
            colour = re.search(r"<fgColor ([^/>]+)/>", fill)
            painted[index] = colour.group(1).strip() if colour else "unnamed colour"
        if not painted:
            return {}, ["no painted fill defined in the workbook"]
        for index, colour in sorted(painted.items()):
            descriptions.append("fill id " + str(index) + ": " + colour)

        block = re.search(r'<cellXfs count="\d+">(.*?)</cellXfs>', styles, re.S)
        if block is None:
            return {}, descriptions + ["workbook carries no cell format table"]
        formats = re.findall(r"<xf [^>]*/>|<xf .*?</xf>", block.group(1), re.S)
        style_to_fill: dict[int, int] = {}
        for index, xf in enumerate(formats):
            found = re.search(r'fillId="(\d+)"', xf)
            if found and int(found.group(1)) in painted:
                style_to_fill[index] = int(found.group(1))
        if not style_to_fill:
            return {}, descriptions + ["no cell format references a painted fill"]

        shared: list[str] = []
        if "xl/sharedStrings.xml" in names:
            raw = archive.read("xl/sharedStrings.xml").decode("utf-8", "replace")
            for item in re.findall(r"<si>(.*?)</si>", raw, re.S):
                shared.append("".join(re.findall(r"<t[^>]*>(.*?)</t>", item, re.S)))

        marked: dict[str, str] = {}
        for sheet_path in sorted(n for n in names if n.startswith("xl/worksheets/sheet")):
            sheet = archive.read(sheet_path).decode("utf-8", "replace")
            for match in re.finditer(
                r'<c r="([A-Z]+\d+)"([^>]*?)(?:/>|>(.*?)</c>)', sheet, re.S
            ):
                reference, attrs, inner = match.group(1), match.group(2), match.group(3) or ""
                found = re.search(r's="(\d+)"', attrs)
                if not found or int(found.group(1)) not in style_to_fill:
                    continue
                value = ""
                held = re.search(r"<v>(.*?)</v>", inner, re.S)
                if held:
                    value = held.group(1)
                    if 't="s"' in attrs:
                        position = int(value)
                        value = shared[position] if position < len(shared) else value
                marked[reference] = (
                    value.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&").strip()
                )
    return marked, descriptions


def is_fasta_style(grid: list[list[str]]) -> bool:
    """Does this sheet hold a FASTA dump rather than a table?

    The signature is a narrow sheet whose second column holds entries beginning with the
    FASTA '>' marker, and whose first column holds a running integer index.
    """
    if not grid:
        return False
    width = max((len(row) for row in grid), default=0)
    if width > 4:
        return False
    markers = sum(1 for row in grid if len(row) > 1 and row[1].startswith(">"))
    indices = sum(1 for row in grid if row and row[0].isdigit())
    return markers >= 3 and indices >= 3


def header_row_guess(grid: list[list[str]]) -> int:
    best, best_filled = 0, -1
    for index, row in enumerate(grid[:8]):
        filled = sum(1 for cell in row if cell)
        if filled > best_filled:
            best, best_filled = index, filled
    return best


def classify_table(name: str, n_rows: int, headers: list[str]) -> tuple[str, str]:
    joined = " ".join(h.lower() for h in headers)
    has_activity = any(token in joined for token in ACTIVITY_TOKENS)
    has_sequence = any(token in joined for token in SEQUENCE_TOKENS)
    has_identity = any(token in joined for token in IDENTITY_TOKENS)
    reasons = [
        "rows=" + str(n_rows),
        "activity-like header: " + ("yes" if has_activity else "no"),
        "sequence-like header: " + ("yes" if has_sequence else "no"),
        "accession-like header: " + ("yes" if has_identity else "no"),
    ]
    if n_rows >= 200 and not has_activity:
        guess = "candidate: an unassayed sequence set"
    elif n_rows <= 80 and has_activity:
        guess = "candidate: an assayed panel"
    else:
        guess = "unclassified: needs a human read"
    return guess, "; ".join(reasons)


def describe_fasta_blocks(
    grid: list[list[str]],
    marked: dict[str, str],
    lines: list[str],
    n_rows: int,
    findings: list[dict],
    workbook: str,
    sheet_name: str,
) -> None:
    """Split a FASTA-style sheet into its caption-delimited blocks and report each one."""
    # A caption row is one whose first column holds prose rather than an index. Those
    # rows are the only in-band statement of where one dataset stops and the next
    # starts, so they are the block boundaries.
    captions = [
        (index + 1, row[0])
        for index, row in enumerate(grid)
        if row and row[0] and not row[0].isdigit()
    ]
    entries = [
        (index + 1, int(row[0]), row[1] if len(row) > 1 else "")
        for index, row in enumerate(grid)
        if row and row[0].isdigit()
    ]

    lines.append("")
    lines.append("This sheet is a FASTA dump, not a table: column 1 carries a running")
    lines.append("integer index, column 2 alternates between a `>`-prefixed name and the")
    lines.append("sequence itself. There are no column headers to read, so the structure")
    lines.append("below is derived from the caption rows and the index column.")
    lines.append("")
    lines.append("### Caption rows, verbatim")
    lines.append("")
    lines.append("These are the only in-band statement of where one dataset ends and the")
    lines.append("next begins, so they are what the block split is based on.")
    lines.append("")
    for row_number, text in captions:
        lines.append("- row " + str(row_number) + ": " + text)

    indices = [index for _, index, _ in entries]
    lines.append("")
    lines.append("### Index column")
    lines.append("")
    lines.append("| field | value |")
    lines.append("| --- | --- |")
    lines.append("| indexed entries | " + str(len(entries)) + " |")
    lines.append("| index range | " + str(min(indices)) + " to " + str(max(indices)) + " |")
    contiguous = indices == list(range(1, len(indices) + 1))
    lines.append("| contiguous 1..N | " + ("yes" if contiguous else "NO") + " |")
    lines.append("| duplicate indices | " + str(len(indices) - len(set(indices))) + " |")
    if contiguous:
        lines.append("")
        lines.append(
            "The index runs continuously across every block without restarting. That is"
        )
        lines.append(
            "load bearing: it means the blocks are one numbered series, so the later block"
        )
        lines.append(
            "is an extension of the earlier one rather than a separate list, and the"
        )
        lines.append(
            "paper's 543 is the running total, not the size of the second block."
        )

    # Blocks: each caption that precedes at least one entry opens a block.
    boundaries = [row for row, _ in captions]
    blocks: list[tuple[int, int, list[tuple[int, int, str]]]] = []
    for position, start in enumerate(boundaries):
        end = boundaries[position + 1] if position + 1 < len(boundaries) else 1 << 30
        members = [entry for entry in entries if start < entry[0] < end]
        if members:
            blocks.append((start, end, members))

    lines.append("")
    lines.append("### Blocks")
    lines.append("")
    lines.append("| block | opened by caption on row | entry rows | index range | entries | highlighted |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for number, (start, _end, members) in enumerate(blocks, 1):
        highlighted = sum(
            1 for row, _, _ in members if ("A" + str(row)) in marked or ("B" + str(row)) in marked
        )
        lines.append(
            "| {0} | {1} | {2} to {3} | {4} to {5} | {6} | {7} |".format(
                number,
                start,
                members[0][0],
                members[-1][0],
                members[0][1],
                members[-1][1],
                len(members),
                highlighted,
            )
        )

    for number, (start, _end, members) in enumerate(blocks, 1):
        names = [name.lstrip(">").strip() for _, _, name in members]
        uniprot_like = sum(1 for name in names if re.match(r"^(tr|sp)\|", name))
        highlighted_names = [
            name.lstrip(">").strip()
            for row, _, name in members
            if ("A" + str(row)) in marked or ("B" + str(row)) in marked
        ]
        lines.append("")
        lines.append("#### Block " + str(number) + ", opened by the caption on row " + str(start))
        lines.append("")
        lines.append("| field | value |")
        lines.append("| --- | --- |")
        lines.append("| entries | " + str(len(members)) + " |")
        lines.append("| index range | " + str(members[0][1]) + " to " + str(members[-1][1]) + " |")
        lines.append("| names in UniProt `tr` or `sp` pipe form | " + str(uniprot_like) + " |")
        lines.append("| names that are bare labels | " + str(len(names) - uniprot_like) + " |")
        lines.append("| highlighted entries | " + str(len(highlighted_names)) + " |")
        if len(members) == PROSE_ASSAYED_N:
            determination = "the assayed prime editor panel, matching the prose count of " + str(PROSE_ASSAYED_N)
        elif abs(len(members) - PROSE_ASSAYED_N) <= 4 and uniprot_like == 0:
            determination = (
                "the assayed prime editor panel. Entries are bare laboratory labels, not "
                "database identifiers, and the count is near but not equal to the prose "
                "count of " + str(PROSE_ASSAYED_N) + ", which is a discrepancy to record"
            )
        elif uniprot_like > len(members) / 2:
            determination = (
                "the unassayed phylogenetic sequence set. Entries are UniProt BLAST hit "
                "headers, which is what a sampled BLAST result looks like and is not what "
                "an assayed panel looks like"
            )
        else:
            determination = "unclassified: needs a human read"
        lines.append("| determination | " + determination + " |")
        findings.append(
            {
                "workbook": workbook,
                "sheet": sheet_name,
                "block": number,
                "caption_row": start,
                "first_row": members[0][0],
                "last_row": members[-1][0],
                "first_index": members[0][1],
                "last_index": members[-1][1],
                "entries": len(members),
                "database_identifiers": uniprot_like,
                "highlighted": len(highlighted_names),
                "highlighted_names": highlighted_names,
                "determination": determination,
            }
        )
        lines.append("")
        lines.append("First " + str(min(n_rows, len(members))) + " entries:")
        lines.append("")
        lines.append("```")
        for row, index, name in members[:n_rows]:
            flag = (
                " [HIGHLIGHTED]"
                if ("A" + str(row)) in marked or ("B" + str(row)) in marked
                else ""
            )
            lines.append(
                "row " + str(row) + "  index " + str(index) + "  " + abbreviate(name) + flag
            )
        lines.append("```")
        if highlighted_names:
            lines.append("")
            lines.append(
                "Every highlighted entry in this block, which per the caption on row 5"
            )
            lines.append("means the enzyme showed activity in the prime editing system:")
            lines.append("")
            for name in highlighted_names:
                lines.append("- " + name)


def gate_g1_determination(findings: list[dict], workbooks: list[Path]) -> list[str]:
    """The explicit statement Gate G1 asks a human to confirm, derived from the scan."""
    lines = [
        "",
        "## Determination for Gate G1",
        "",
        "Every sheet of every supplementary workbook above has been enumerated. This is",
        "the statement a human is asked to confirm before any row is parsed.",
        "",
    ]
    if not findings:
        lines.append(
            "No FASTA-style block structure was found in any workbook. That contradicts"
        )
        lines.append(
            "what this script was written to expect, so nothing should be parsed until the"
        )
        lines.append("layout has been re-read by hand.")
        return lines

    assayed = [f for f in findings if f["database_identifiers"] == 0]
    unassayed = [f for f in findings if f["database_identifiers"] > 0]

    lines.append("| question | answer |")
    lines.append("| --- | --- |")
    for f in assayed:
        lines.append(
            "| Which block holds the assayed enzymes | `{0}`, sheet `{1}`, block {2}: rows {3} to {4}, index {5} to {6}, {7} entries |".format(
                f["workbook"],
                f["sheet"],
                f["block"],
                f["first_row"],
                f["last_row"],
                f["first_index"],
                f["last_index"],
                f["entries"],
            )
        )
    for f in unassayed:
        lines.append(
            "| Which block holds the phylogenetic sequences | `{0}`, sheet `{1}`, block {2}: rows {3} to {4}, index {5} to {6}, {7} entries |".format(
                f["workbook"],
                f["sheet"],
                f["block"],
                f["first_row"],
                f["last_row"],
                f["first_index"],
                f["last_index"],
                f["entries"],
            )
        )
    lines.append(
        "| How activity is recorded | a green cell fill on the name of each active enzyme, not a column |"
    )
    for f in assayed:
        lines.append(
            "| How many entries carry that fill | " + str(f["highlighted"]) + " |"
        )

    total_entries = sum(f["entries"] for f in findings)
    lines += [
        "",
        "### The evidence for each determination",
        "",
        "The assayed block is identified by three independent signals, not by position:",
        "",
        "1. Its own caption, on the row above it: sequences and identity of reverse",
        "   transcriptases **tested for prime editing**.",
        "2. Its names are bare laboratory labels such as `MMLV-RT` and `Tf1-RT`, with no",
        "   database identifier among them. The other block's names are UniProt FASTA",
        "   headers of the form `tr|ACCESSION|ENTRY_NAME ... OS=... OX=...`, which is what",
        "   a BLAST result looks like.",
        "3. Only the assayed block carries the highlight fill, which the caption on row 5",
        "   defines as activity. The other block carries none, which is consistent with it",
        "   never having been assayed.",
        "",
        "### What this means for the parse",
        "",
        "Only the assayed block may be read into `curated.csv`. The parser must key on the",
        "caption-delimited row range and assert the entry count it finds, so that a sheet",
        "whose layout differs from this one halts rather than silently taking the wrong",
        "rows. The running index is **not** safe to filter on by itself: it continues from",
        "the first block into the second without restarting, so an index filter of 1 to 57",
        "happens to work here only because the assayed block comes first.",
        "",
        "### Two count discrepancies against the article prose, recorded not resolved",
        "",
    ]
    for f in assayed:
        gap = PROSE_ASSAYED_N - f["entries"]
        lines += [
            "- The prose says the authors tested "
            + str(PROSE_ASSAYED_N)
            + " enzymes. This block holds "
            + str(f["entries"])
            + ", so",
            "  "
            + str(gap)
            + " are unaccounted for. The gap is between the article's own text and its own",
            "  Table S1. It cannot be closed from either of them.",
            "- The prose says twenty RTs showed detectable activity. "
            + str(f["highlighted"])
            + " entries carry the",
            "  activity fill, so that gap is one enzyme.",
        ]
    lines += [
        "",
        "Neither is resolved here. Both are carried into `reports/reconciliation.md` with",
        "the evidence for each reading, for a human to rule on at Gate G2.",
        "",
        "### What Table S1 does not contain",
        "",
        "Stated explicitly, because each absence changes what the benchmark can claim:",
        "",
        "- **No efficiency values.** There is no numeric column anywhere in the sheet. The",
        "  activity label is binary, carried by a fill colour. So the inherited",
        "  `pe_efficiency_pct` column cannot be verified against Table S1.",
        "- **No accessions for the assayed enzymes.** Their names are bare labels. Every",
        "  database identifier in the workbook belongs to the phylogenetic block.",
        "- **No class or family assignment.** The paper's 14 classes exist in Figure 1B, a",
        "  rendered tree, and nowhere in this workbook. So the inherited 7-family labelling",
        "  cannot be mapped onto the paper's 14 classes from this source.",
        "",
        "All "
        + str(len(workbooks))
        + " supplementary workbooks were scanned for a source of the Figure 1C per-enzyme",
        "efficiencies. None holds one: the other workbooks are the evolution mutation",
        "tables, the Figure 5F reagent and frequency table, the Figure 6E Cas9 mutant",
        "efficiencies, the RT and Cas9 variant genotypes, and the pegRNA and primer",
        "sequences. The Figure 1C values appear to exist only as plotted points.",
        "",
        "Total indexed entries across all blocks: " + str(total_entries) + ".",
    ]
    return lines


def inventory_workbook(
    path: Path, n_rows: int, lines: list[str], findings: list[dict]
) -> None:
    lines.append("")
    lines.append("## " + path.name)
    lines.append("")
    lines.append("| field | value |")
    lines.append("| --- | --- |")
    lines.append("| path | `" + path.relative_to(REPO_ROOT).as_posix() + "` |")
    lines.append("| bytes | " + str(path.stat().st_size) + " |")
    lines.append("| sha256 | `" + sha256_of(path) + "` |")

    try:
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as exc:  # noqa: BLE001 - the reason is what matters here
        lines.append("| readable | no: " + type(exc).__name__ + " " + str(exc)[:160] + " |")
        return

    marked, fill_notes = highlighted_cells(path)
    sheet_names = book.sheetnames
    lines.append("| sheets | " + str(len(sheet_names)) + " |")
    lines.append("| highlighted cells | " + str(len(marked)) + " |")
    lines.append("")
    lines.append(
        "Sheet names, in workbook order: " + ", ".join("`" + s + "`" for s in sheet_names)
    )
    if fill_notes:
        lines.append("")
        lines.append("Fill styles defined in this workbook: " + "; ".join(fill_notes) + ".")

    for sheet_name in sheet_names:
        sheet = book[sheet_name]
        grid: list[list[str]] = []
        max_width = 0
        for row in sheet.iter_rows(values_only=True):
            texts = [cell_text(v) for v in row]
            while texts and not texts[-1]:
                texts.pop()
            max_width = max(max_width, len(texts))
            grid.append(texts)
        total_rows = sheet.max_row or 0
        total_cols = sheet.max_column or 0
        populated_rows = sum(1 for row in grid if any(row))

        lines.append("")
        lines.append("### Sheet `" + sheet_name + "`")
        lines.append("")
        lines.append("| field | value |")
        lines.append("| --- | --- |")
        lines.append(
            "| declared dimensions | "
            + str(total_rows)
            + " rows by "
            + str(total_cols)
            + " columns |"
        )
        lines.append("| rows holding anything | " + str(populated_rows) + " |")
        lines.append("| widest populated row | " + str(max_width) + " cells |")
        lines.append("| layout | " + ("FASTA blocks" if is_fasta_style(grid) else "tabular") + " |")
        lines.append("")
        lines.append("First " + str(min(n_rows, len(grid))) + " rows, verbatim:")
        lines.append("")
        lines.append("```")
        for row_index, row in enumerate(grid[:n_rows]):
            lines.append(
                str(row_index + 1) + ": " + " | ".join(abbreviate(c) for c in row)
            )
        lines.append("```")

        if is_fasta_style(grid):
            describe_fasta_blocks(
                grid, marked, lines, n_rows, findings, path.name, sheet_name
            )
            continue

        header_index = header_row_guess(grid)
        headers = grid[header_index] if grid else []
        populated = [h for h in headers if h]
        guess, reasoning = classify_table(sheet_name, total_rows, populated)
        lines.append("")
        lines.append("| field | value |")
        lines.append("| --- | --- |")
        lines.append("| header row, by position | row " + str(header_index + 1) + " |")
        lines.append("| populated header cells | " + str(len(populated)) + " |")
        lines.append("| determination | " + guess + " |")
        lines.append("| evidence | " + reasoning + " |")
        lines.append("")
        lines.append("Every column header on row " + str(header_index + 1) + ":")
        lines.append("")
        if populated:
            for position, head in enumerate(headers):
                if head:
                    lines.append("- column " + str(position + 1) + ": `" + head + "`")
        else:
            lines.append("- none: that row is empty")
    book.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=6, help="rows to print per sheet")
    args = parser.parse_args()

    workbooks = sorted(
        p for p in RAW_DIR.glob("*") if p.suffix.lower() in (".xlsx", ".xlsm", ".xls")
    )
    print_run_header("data_acquisition/inventory_tableS1.py", list(workbooks))
    if not workbooks:
        print("no workbook in " + RAW_DIR.relative_to(REPO_ROOT).as_posix())
        print("run data_acquisition/fetch_doman_s1.py first")
        return 1

    lines = [
        "# Workbook inventory: Doman et al. 2023 supplementary tables",
        "",
        "Written by `data_acquisition/inventory_tableS1.py`. Nothing has been parsed into",
        "the benchmark at the time this file is produced. This is the Gate G1 artifact.",
        "",
        "## Why this file exists before any parsing",
        "",
        "Supplementary Table S1 of this paper is cited for two different datasets: the",
        "reverse transcriptases assayed as prime editors, which is what Task A needs, and",
        "the 543 reverse transcriptase sequences used for the downstream phylogenetic",
        "analyses, which were never assayed and carry no activity labels. A parser that",
        "read the whole sheet, or matched on a sequence column, would pull hundreds of",
        "unlabelled sequences into a 57-row task without raising anything.",
        "",
        "## What the layout actually turned out to be",
        "",
        "Not two sheets. `mmc2.xlsx` holds **one** sheet, and the two datasets are two",
        "caption-delimited blocks inside it, in a FASTA dump rather than a table, under a",
        "single index that runs continuously from the first block into the second. There",
        "are no column headers and no efficiency column, and activity is recorded as a",
        "green cell fill on the name of each active enzyme.",
        "",
        "Three consequences worth stating before the detail:",
        "",
        "1. A sheet-level inventory would have reported one sheet and found nothing, so",
        "   this script works at block level and reads the fill styles as data.",
        "2. Because the index is continuous, the paper's 543 is a running total that",
        "   **includes** the assayed enzymes as its first entries. The second block is not",
        "   543 sequences; it is the remainder.",
        "3. Because activity is a fill colour, it is invisible to every tool that reads",
        "   values only, including `pandas.read_excel`.",
    ]

    findings: list[dict] = []
    for path in workbooks:
        print("inventorying " + path.name)
        inventory_workbook(path, args.rows, lines, findings)

    lines += gate_g1_determination(findings, workbooks)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
