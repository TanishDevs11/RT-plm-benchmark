"""Obtain the pCMV-PE2 plasmid sequence, the actual parent of the Task B construct.

Why this script exists
----------------------
Task B's reference had one unresolved item, and it was the one the brief calls the
highest-risk item in the pipeline: the substitution content of PE2dR. The preprint states
only that "The pCMV-PE2 plasmid was constructed via deleting RNaseH domain from RT of
pCMV-PE2 (#132775, Addgene)". It never names a point substitution, so the construct's RT
could not be written down from the preprint alone, and a reference wrong at even one
position would be wrong at that position in all 1046 variant sequences.

The parent plasmid is a public record, so the resolution is a fetch rather than a guess.

What it does, and what it refuses to do
---------------------------------------
Addgene publishes an Addgene-verified full sequence for 132775. Its GenBank file is
referenced by the sequence viewer but returns HTTP 404, so the sequence is reconstructed
from the viewer's own `sequence-lines.json`, which carries both strands as text glyphs
with explicit base-pair coordinates. That is machine-readable text served by the
depositor's own record, not a figure: no base is ever inferred, and four independent
assertions have to pass before anything is written.

1. each line declares `data-begin-bp` and `data-end-bp`, and the number of bases
   recovered has to equal that span exactly
2. each line carries both strands, and they have to be exact complements of each other
3. the lines have to tile the plasmid with no gap and no overlap, starting at zero
4. exactly one pair of glyph rows per line may satisfy 1 and 2, so an ambiguous line
   halts rather than being resolved by preference

Any failure raises. A partially reconstructed sequence is never written, because a
plasmid with a dropped line still translates and still looks like a reference.

The decisive check on this reconstruction is not in this script. It is in
`resolve_pe2dr_reference.py`, which translates the RT open reading frame and requires it
to match UniProt P03355 at every one of 677 positions except the substitutions Addgene's
own record names. A misread base would show up there as a mismatch.

    python data_acquisition/fetch_pe2_plasmid.py

Writes tasks/taskB_mmlv_dms/raw/addgene_132775_pCMV-PE2.fasta and an attempt log.
"""

from __future__ import annotations

import collections
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header  # noqa: E402

PLASMID = "132775"
PLASMID_NAME = "pCMV-PE2"
PLASMID_PAGE = "https://www.addgene.org/" + PLASMID + "/"
SEQUENCES_PAGE = PLASMID_PAGE + "sequences/"

RAW_DIR = REPO_ROOT / "tasks" / "taskB_mmlv_dms" / "raw"
OUT_FASTA = RAW_DIR / ("addgene_" + PLASMID + "_" + PLASMID_NAME + ".fasta")
CHECKSUMS = RAW_DIR / "CHECKSUMS.txt"
ATTEMPT_LOG = REPO_ROOT / "data_acquisition" / "fetch_pe2_plasmid_attempts.json"

USER_AGENT = (
    "RT-plm-benchmark/0.1 (open benchmark of protein representations for reverse "
    "transcriptase function; contact shyamarunach@gmail.com)"
)
TIMEOUT = (30, 180)

BASES = ("a", "c", "g", "t")
COMPLEMENT = str.maketrans("acgt", "tgca")

attempts: list[dict] = []


def get(url: str, label: str, referer: str | None = None) -> requests.Response | None:
    headers = {"User-Agent": USER_AGENT}
    if referer:
        headers["Referer"] = referer
    record = {"label": label, "url": url}
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
    except requests.RequestException as exc:
        record["status"] = None
        record["outcome"] = "transport error: " + type(exc).__name__
        attempts.append(record)
        print("  " + label + " | transport error | " + url)
        return None
    record["status"] = response.status_code
    record["content_type"] = response.headers.get("Content-Type")
    record["bytes_received"] = len(response.content)
    record["sha256"] = hashlib.sha256(response.content).hexdigest()
    record["outcome"] = "ok" if response.status_code == 200 else "non-200"
    attempts.append(record)
    print(
        "  {0} | status={1} | bytes={2} | {3}".format(
            label, response.status_code, len(response.content), url
        )
    )
    return response if response.status_code == 200 else None


def insert_description(page_html: str) -> str:
    """The depositor's own statement of what the RT in this plasmid is.

    Addgene renders the insert's alternative name as a field on the plasmid page. For
    132775 it names the five substitutions explicitly, which is the record the preprint
    omits. It is captured here as evidence and is never used to edit a sequence: the
    sequence itself decides, and this field is what the sequence is checked against.
    """
    match = re.search(r"Cas9\(H840A\)-M-MLVrt\(([^)]*)\)", page_html)
    return match.group(0) if match else ""


def sequence_ids(sequences_html: str) -> list[str]:
    return sorted(set(re.findall(r"/browse/sequence/(\d+)/", sequences_html)))


def viewer_urls(analysis_html: str) -> dict[str, str]:
    """The asset URLs the sequence viewer loads, as the page itself declares them."""
    block = re.search(r"sv\.initModule\(\{(.{0,4000}?)\}\s*\)", analysis_html, re.S)
    if not block:
        raise SystemExit("the sequence viewer's asset block was not found on the page")
    text = block.group(1).replace("\\u002D", "-").replace("\\u002d", "-")
    return dict(re.findall(r'(\w+):\s*"(https?://[^"]+)"', text))


def reconstruct(lines: list[dict]) -> str:
    """Rebuild the plasmid from the viewer's per-line glyphs, asserting as it goes."""
    pieces: dict[int, str] = {}
    for record in lines:
        content = record["content"]
        span = re.search(r'data-begin-bp="(\d+)"\s+data-end-bp="(\d+)"', content)
        if not span:
            raise SystemExit("a sequence line declared no base-pair span")
        begin, end = int(span.group(1)), int(span.group(2))
        width = end - begin + 1

        rows: dict[float, list[tuple[float, str]]] = collections.defaultdict(list)
        for attributes, glyph in re.findall(r"<text\b([^>]*)>([^<]*)</text>", content):
            # Lowercase only. The viewer draws a translated reading frame in the same
            # way, and A, C, G and T are also amino-acid letters: accepting uppercase
            # would mix a protein row into the nucleotide rows.
            if glyph not in BASES:
                continue
            x = re.search(r'\bx="([-\d.]+)"', attributes)
            y = re.search(r'\by="([-\d.]+)"', attributes)
            if not (x and y):
                raise SystemExit("a base glyph carried no coordinates")
            rows[float(y.group(1))].append((float(x.group(1)), glyph))

        full = {
            y: "".join(glyph for _, glyph in sorted(row))
            for y, row in rows.items()
            if len(row) == width
        }
        pairs = [
            (top, bottom)
            for top in full
            for bottom in full
            if top < bottom and full[top].translate(COMPLEMENT) == full[bottom]
        ]
        if len(pairs) != 1:
            raise SystemExit(
                "line at bp "
                + str(begin)
                + " gave "
                + str(len(pairs))
                + " complementary strand pairs; exactly one is required"
            )
        if begin in pieces:
            raise SystemExit("two lines claim to start at bp " + str(begin))
        pieces[begin] = full[pairs[0][0]]

    cursor = 0
    for begin in sorted(pieces):
        if begin != cursor:
            raise SystemExit(
                "the lines do not tile the plasmid: expected bp "
                + str(cursor)
                + ", found bp "
                + str(begin)
            )
        cursor = begin + len(pieces[begin])
    return "".join(pieces[begin] for begin in sorted(pieces))


SOURCES = {
    "preprint.pdf": "bioRxiv 10.64898/2026.07.06.736660 v1, CC-BY-NC 4.0",
    "uniprot_P03355.fasta": "https://rest.uniprot.org/uniprotkb/P03355.fasta, SV=5, CC-BY 4.0",
    "addgene_132775_pCMV-PE2.fasta": (
        "Addgene 132775 verified full sequence 259720, reconstructed from the "
        "depositor's sequence-viewer payload"
    ),
    "reference_candidate_unconfirmed.fasta": (
        "derived, superseded: P03355 RT 1 to 498 with no substitution applied. Kept "
        "because the test suite uses it as the near miss that must be rejected"
    ),
}


def write_checksums() -> None:
    """Rewrite CHECKSUMS.txt over everything in raw/, not just this script's output.

    Phase 0 asks raw/ to carry a checksum for every file in it. Appending one line would
    leave the files an earlier run fetched uncovered, so the whole directory is restated
    each time.
    """
    lines = [
        "# Checksums for the Task B source files, tasks/taskB_mmlv_dms/raw/",
        "#",
        "# Written by data_acquisition/fetch_pe2_plasmid.py over every file in the",
        "# directory. Each file is stored exactly as served or, where it is derived, with",
        "# the derivation named.",
        "#",
        "# access date: " + date.today().isoformat(),
        "#",
        "# The per-variant activity tables are absent and are not listed: the preprint",
        "# deposited no supplementary material. See MANUAL_FETCH_TASKB.md.",
        "",
    ]
    for path in sorted(RAW_DIR.iterdir()):
        if path.name in (".gitkeep", CHECKSUMS.name) or not path.is_file():
            continue
        payload = path.read_bytes()
        lines.append(hashlib.sha256(payload).hexdigest() + "  " + path.name)
        lines.append("    bytes: " + str(len(payload)))
        lines.append("    source: " + SOURCES.get(path.name, "not recorded by this script"))
    CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    print_run_header("data_acquisition/fetch_pe2_plasmid.py")
    print("")
    print("target: Addgene " + PLASMID + ", " + PLASMID_NAME + ", the parent of PE2dR")
    print("")

    page = get(PLASMID_PAGE, "plasmid page")
    if page is None:
        raise SystemExit("the plasmid page is unreachable")
    insert = insert_description(page.text)
    print("")
    print("insert, as the depositor's record states it:")
    print("  " + (insert or "NOT STATED on the page"))
    if not insert:
        raise SystemExit(
            "the insert description was not found. It is the record the preprint omits "
            "and the sequence is checked against it, so its absence is a halt"
        )

    print("")
    sequences = get(SEQUENCES_PAGE, "sequences page")
    if sequences is None:
        raise SystemExit("the sequences page is unreachable")
    ids = sequence_ids(sequences.text)
    print("  Addgene-verified full sequence id(s): " + ", ".join(ids))
    if len(ids) != 1:
        raise SystemExit(
            "expected exactly one full sequence, found " + str(len(ids)) + ". Which one "
            "is the verified full sequence is a human ruling, not a default"
        )
    sequence_id = ids[0]

    analysis_url = "https://www.addgene.org/browse/sequence/" + sequence_id + "/"
    print("")
    analysis = get(analysis_url, "sequence analysis page")
    if analysis is None:
        raise SystemExit("the sequence analysis page is unreachable")
    urls = viewer_urls(analysis.text)

    print("")
    print("route 1, the GenBank file the viewer declares:")
    genbank = get(urls["genbank"], "genbank", referer=analysis_url) if "genbank" in urls else None
    if genbank is not None:
        raise SystemExit(
            "the GenBank file is now served. It is a cleaner source than the viewer "
            "payload, so parse it directly rather than keeping the glyph route"
        )
    print("    not served. Falling back to the viewer's own sequence payload.")

    print("")
    print("route 2, the viewer's sequence lines:")
    payload = get(urls["sequence_lines"], "sequence lines", referer=analysis_url)
    if payload is None:
        raise SystemExit("the viewer's sequence payload is unreachable; nothing was written")
    lines = payload.json()
    print("    " + str(len(lines)) + " lines received")

    dna = reconstruct(lines)
    print("    reconstructed " + str(len(dna)) + " bp, all four assertions passed")
    if set(dna) - set(BASES):
        raise SystemExit("the reconstruction contains a character that is not a base")

    header = (
        ">addgene_"
        + PLASMID
        + " "
        + PLASMID_NAME
        + " Addgene-verified full sequence "
        + sequence_id
        + " "
        + str(len(dna))
        + "bp reconstructed_from_sequence_viewer_payload accessed="
        + date.today().isoformat()
    )
    body = "\n".join(dna[index : index + 60] for index in range(0, len(dna), 60))
    OUT_FASTA.write_text(header + "\n" + body + "\n", encoding="utf-8")
    write_checksums()
    print("")
    print("wrote " + OUT_FASTA.relative_to(REPO_ROOT).as_posix())
    print("  sha256 " + hashlib.sha256(OUT_FASTA.read_bytes()).hexdigest())

    ATTEMPT_LOG.write_text(
        json.dumps(
            {
                "plasmid": PLASMID,
                "plasmid_name": PLASMID_NAME,
                "access_date": date.today().isoformat(),
                "sequence_id": sequence_id,
                "insert_description": insert,
                "reconstructed_bp": len(dna),
                "viewer_urls": urls,
                "attempts": attempts,
            },
            indent=1,
        )
        + "\n",
        encoding="utf-8",
    )
    print("wrote " + ATTEMPT_LOG.relative_to(REPO_ROOT).as_posix())
    print("")
    print("Next: python data_acquisition/resolve_pe2dr_reference.py")
    print("That is where this reconstruction is checked, against UniProt P03355.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
