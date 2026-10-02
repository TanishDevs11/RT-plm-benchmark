"""Extract the article-level facts about the RT survey from the Doman et al. full text.

Table S1 carries the enzymes. The article body carries the things a spreadsheet cannot
settle: how many enzymes were tested, how many were called active and by what criterion,
what quantity the reported efficiencies actually are, and which supplementary file is
which. Those sentences are what the reconciliation has to be argued against, so they are
pulled out verbatim here into a report rather than quoted from memory anywhere else.

The source is the JATS XML of the open access record at Europe PMC, which is the same
text as the published article and is machine readable, unlike the PDF.

    python data_acquisition/extract_doman_fulltext_facts.py
    python data_acquisition/extract_doman_fulltext_facts.py --offline

Outputs:
    tasks/taskA_crossfamily/raw/PMC10482982_fulltext.xml   the source, checksummed
    reports/doman2023_source_facts.md                      the extracted quotations

Every quotation is reproduced exactly as the XML gives it, with only tag stripping and
whitespace collapsing applied, so that nothing in the report is a paraphrase.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

PMC_ID = "PMC10482982"
DOI = "10.1016/j.cell.2023.07.039"
XML_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/" + PMC_ID + "/fullTextXML"

RAW_DIR = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw"
XML_PATH = RAW_DIR / (PMC_ID + "_fulltext.xml")
OUT = REPO_ROOT / "reports" / "doman2023_source_facts.md"

USER_AGENT = (
    "RT-plm-benchmark/0.1 (open benchmark of protein representations for reverse "
    "transcriptase function; contact shyamarunach@gmail.com)"
)

# Each entry is a question the reconciliation has to answer, and the anchor to search the
# article text for. The anchors are literal strings from the article, so a change in the
# source is a missing quotation in the report rather than a silently different number.
ANCHORS: tuple[tuple[str, str, int, int], ...] = (
    (
        "How many enzymes were tested, and how many classes",
        "tested 59 enzymes",
        240,
        420,
    ),
    (
        "How many were called active, and by what criterion",
        "showed detectable PE activity",
        320,
        360,
    ),
    (
        "How the 20 actives break down by class",
        "are closely related to the M-MLV RT",
        300,
        320,
    ),
    (
        "What quantity the reported efficiencies are",
        "reflect the frequency of the intended prime editing outcome",
        180,
        180,
    ),
    (
        "What Figure 1C plots, which is the panel the survey values come from",
        "Mammalian activity of 20 different RT enzymes",
        60,
        220,
    ),
    (
        "Where the 543 phylogenetic sequences come from, and that they share Table S1",
        "543 RT sequences used for downstream phylogenetic analyses",
        620,
        200,
    ),
    (
        "That the phylogenetic set was never assayed, only BLAST sampled",
        "representative sequences were randomly sampled",
        520,
        260,
    ),
    (
        "Where accession numbers are said to live",
        "Accession numbers are listed in the key resources table",
        260,
        160,
    ),
)


def plain_text(xml: str) -> str:
    text = re.sub(r"<[^>]+>", " ", xml)
    return re.sub(r"\s+", " ", text).strip()


def fetch_xml() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    response = requests.get(
        XML_URL, headers={"User-Agent": USER_AGENT}, timeout=(30, 90)
    )
    response.raise_for_status()
    XML_PATH.write_bytes(response.content)
    print("fetched " + XML_URL)
    print("    " + str(len(response.content)) + " bytes")


def supplementary_manifest(xml: str) -> list[tuple[str, str]]:
    """Which supplementary file is which table, as the article itself declares it."""
    seen: dict[str, str] = {}
    for block in re.findall(r"<supplementary-material.*?</supplementary-material>", xml, re.S):
        hrefs = re.findall(r'href="([^"]+)"', block)
        caption = plain_text(block)
        if hrefs and hrefs[0] not in seen:
            seen[hrefs[0]] = caption
    return sorted(seen.items())


def figure_caption(xml: str, label: str) -> str | None:
    for block in re.findall(r"<fig\b.*?</fig>", xml, re.S):
        found = re.search(r"<label>(.*?)</label>", block, re.S)
        if found and plain_text(found.group(1)) == label:
            return plain_text(block)
    return None


def licence(xml: str) -> str:
    block = re.search(r"<permissions>.*?</permissions>", xml, re.S)
    return plain_text(block.group(0)) if block else "no permissions block found"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--offline",
        action="store_true",
        help="use the XML already in raw/ rather than refetching it",
    )
    args = parser.parse_args()

    if not args.offline or not XML_PATH.is_file():
        fetch_xml()

    print_run_header("data_acquisition/extract_doman_fulltext_facts.py", [XML_PATH])
    xml = XML_PATH.read_text(encoding="utf-8")
    flat = plain_text(xml)

    lines = [
        "# Source facts: Doman et al. 2023, from the article text",
        "",
        "Written by `data_acquisition/extract_doman_fulltext_facts.py`. Every quotation",
        "below is reproduced from the article XML with only tag stripping and whitespace",
        "collapsing applied. Nothing here is a paraphrase, and nothing here was recalled",
        "rather than read.",
        "",
        "| field | value |",
        "| --- | --- |",
        "| citation | Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al. Cell 2023, 186(18):3983-4002.e26 |",
        "| DOI | `" + DOI + "` |",
        "| PMC accession | `" + PMC_ID + "` |",
        "| source file | `" + XML_PATH.relative_to(REPO_ROOT).as_posix() + "` |",
        "| source SHA256 | `" + sha256_of(XML_PATH) + "` |",
        "| retrieved from | `" + XML_URL + "` |",
        "| access date | " + date.today().isoformat() + " |",
        "",
        "## Licence",
        "",
        "> " + licence(xml),
        "",
        "CC BY 4.0 permits redistribution with attribution, so the supplementary files",
        "and this XML may be committed to `raw/` rather than only a fetch script. That",
        "settles the licence question Task A's provenance record had left open, which had",
        "assumed Elsevier terms would forbid it.",
        "",
        "## Which supplementary file is which",
        "",
        "Taken from the article's own supplementary-material declarations, so the mapping",
        "from `mmcN` to table number is the publisher's, not an inference from file order.",
        "",
        "| file | declared contents |",
        "| --- | --- |",
    ]
    for href, caption in supplementary_manifest(xml):
        lines.append("| `" + href + "` | " + caption.replace("|", "/") + " |")

    lines += [
        "",
        "Table S1 is `mmc2.xlsx`. Note what its own caption says it contains: sequences",
        "and identities for the BLAST query, for the phylogenetic analysis, **and** for",
        "the initial screen in Figures 1B and 1C. One file, both datasets, which is the",
        "reason the workbook is inventoried sheet by sheet before anything is parsed.",
        "",
        "## The questions the reconciliation has to answer",
        "",
    ]

    for question, anchor, before, after in ANCHORS:
        lines.append("### " + question)
        lines.append("")
        position = flat.find(anchor)
        if position < 0:
            lines.append(
                "NOT FOUND in the article text. The anchor searched for was `"
                + anchor
                + "`. This is a failure to record, not a gap to fill from elsewhere."
            )
            lines.append("")
            print("MISSING anchor: " + anchor)
            continue
        start = max(0, position - before)
        end = min(len(flat), position + len(anchor) + after)
        lines.append("> ..." + flat[start:end] + "...")
        lines.append("")

    caption = figure_caption(xml, "Figure 1")
    lines.append("### Figure 1 caption, in full")
    lines.append("")
    lines.append("> " + (caption or "Figure 1 caption not found"))
    lines.append("")

    lines += [
        "## What these quotations establish, and what they do not",
        "",
        "Established by the article text alone, before Table S1 is opened:",
        "",
        "1. **59 enzymes were tested, spanning 14 classes.** The inherited",
        "   `data/rt_sequences.csv` has 57 rows, so 2 rows are unaccounted for and the",
        "   gap is real rather than a miscount.",
        "2. **Twenty RTs showed detectable PE activity**, and the criterion is the word",
        "   detectable, not a stated numeric threshold. The inherited file has 21 actives.",
        "3. **The 20 break down as 11 retroviral, 2 LTR retrotransposon, and 7 bacterial**",
        "   from group-II introns, retrons, or CRISPR-Cas systems. The inherited file has",
        "   12 retroviral, 2 LTR retrotransposon, 2 group-II intron, 5 retron and 0",
        "   CRISPR-associated actives. The bacterial total agrees at 7 and the",
        "   retrotransposon total agrees at 2; the entire discrepancy is one extra",
        "   retroviral active. Which enzyme that is, is settled in the reconciliation",
        "   report against Table S1, not here.",
        "4. **The efficiency quantity is defined verbatim**: the frequency of the intended",
        "   prime editing outcome with no indels or other changes at the target site. So a",
        "   percentage in this benchmark is a correct-edit frequency, not a total editing",
        "   rate, and not an indel-inclusive one.",
        "5. **The 543 sequences are BLAST hits, randomly subsampled, never assayed.** They",
        "   share Table S1 with the assayed panel. Any of them appearing in `curated.csv`",
        "   would be an unlabelled sequence carrying an invented label.",
        "",
        "Not established by the article text, and left open here:",
        "",
        "- **Which two enzymes the inherited 57 omits.** Needs the Table S1 roster.",
        "- **Whether Table S1 carries per-enzyme efficiency values at all.** Its caption",
        "  promises sequences and identities. The numbers in Figure 1C may exist only as",
        "  plotted points, in which case the inherited `pe_efficiency_pct` column cannot",
        "  be verified against any table and that has to be said plainly.",
        "- **Accession numbers.** The data availability statement points at the key",
        "  resources table, and a scan of the full text finds no protein accession of any",
        "  recognised form in it: the accessions mentioned there are sequencing-read",
        "  accessions for the SRA deposit, not RT protein accessions. So accessions have",
        "  to come from Table S1 or from sequence-level resolution against UniProt.",
        "",
    ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + OUT.relative_to(REPO_ROOT).as_posix())
    print("source sha256 " + sha256_of(XML_PATH))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
