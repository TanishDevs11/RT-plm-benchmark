"""Acquire the M-MLV RT saturated mutagenesis variant table, or establish that it is absent.

Target work:

    Li H, Wang Y, Zhang C, Tun TT, Yu S, Hu C, Yu H. "Saturated mutagenesis screen of
    M-MLV reverse transcriptase identifies variants enhancing prime editing efficiency."
    bioRxiv, posted 2026-07-07, CC BY-NC.

What is needed is Supplementary Tables S6 and S7, the per-variant normalized editing
efficiencies for libraries L1 and L2, plus Supplementary Sequence 1, the PE2dR construct
protein sequence. Without the first, Task B has no labels; without the second, every
variant sequence would be built on an unconfirmed reference.

The DOI, verified rather than assumed
-------------------------------------
The brief names `10.1101/2026.07.06.736660`. That DOI does not resolve: the bioRxiv API
returns "no posts found" for it. The work resolves under prefix `10.64898`, which is what
every route here uses and what every Task B row records. The PDF's own header reads
`10.1101`, which is where the brief's value comes from, so this is a defect in the
preprint rather than in the brief.

Routes, in the brief's order
----------------------------
1. the bioRxiv supplementary-material page for the resolved DOI
2. the bioRxiv API, to resolve the current version and any published-journal DOI, then
   retry route 1 and the publisher against whatever that returns
3. the published journal or a PMC mirror, if the work has appeared
4. author-deposited repositories: Zenodo, Dryad, OSF, and GitHub. Screen papers often
   deposit a variant table separately from the PDF, so this is searched explicitly rather
   than assumed away

Also tried, because it is cheap and sometimes lists supplementary files the rendered page
does not: the JATS XML the API points at.

    python data_acquisition/fetch_mmlv_dms.py
    python data_acquisition/fetch_mmlv_dms.py --route 4

On total failure this writes `data_acquisition/MANUAL_FETCH_TASKB.md` and exits non-zero.
It never substitutes a different dataset and never reconstructs a value from a figure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header  # noqa: E402

DOI = "10.64898/2026.07.06.736660"
BRIEF_DOI = "10.1101/2026.07.06.736660"
TITLE_QUERY = "Saturated mutagenesis screen of M-MLV reverse transcriptase"

RAW_DIR = REPO_ROOT / "tasks" / "taskB_mmlv_dms" / "raw"
CHECKSUMS = RAW_DIR / "CHECKSUMS.txt"
ATTEMPT_LOG = REPO_ROOT / "data_acquisition" / "fetch_mmlv_dms_attempts.json"
MANUAL_NOTE = REPO_ROOT / "data_acquisition" / "MANUAL_FETCH_TASKB.md"

USER_AGENT = (
    "RT-plm-benchmark/0.1 (open benchmark of protein representations for reverse "
    "transcriptase function; contact shyamarunach@gmail.com)"
)
HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT = (30, 90)
PAUSE_SECONDS = 2

# Extensions that could carry a per-variant table. A PDF is not enough: the values have to
# be machine readable, and reading them off a figure is forbidden.
#
# `.txt` is deliberately absent. bioRxiv serves its own full-text page at a URL ending
# `.full.txt`, and including the extension made the first run of this script "succeed" by
# downloading the article's HTML and storing it as a variant table. That is the same
# failure the Task A fetcher had: a route that reports success because the status code was
# 200 and the URL looked right.
DATA_SUFFIXES = (".xlsx", ".xls", ".xlsm", ".csv", ".tsv", ".zip")

# URL fragments that are the article itself rather than a supplementary file.
ARTICLE_URL_MARKERS = (".full", ".full-text", ".abstract", ".article-info", "/content/early/")

# Container signatures. An xlsx is a zip; a legacy xls is an OLE compound file.
ZIP_MAGIC = bytes([0x50, 0x4B, 0x03, 0x04])
OLE_MAGIC = bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1])


@dataclass
class Attempt:
    route: int
    label: str
    url: str
    status: int | None = None
    content_type: str | None = None
    bytes_received: int = 0
    sha256: str | None = None
    outcome: str = "not attempted"
    detail: str = ""
    found: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "route": self.route,
            "label": self.label,
            "url": self.url,
            "status": self.status,
            "content_type": self.content_type,
            "bytes_received": self.bytes_received,
            "sha256": self.sha256,
            "outcome": self.outcome,
            "detail": self.detail,
            "found": self.found,
        }

    def log(self) -> None:
        print(
            "route {0} | {1} | status={2} | type={3} | bytes={4} | {5}".format(
                self.route,
                self.url,
                self.status,
                self.content_type,
                self.bytes_received,
                self.outcome,
            )
        )
        if self.detail:
            print("    " + self.detail[:400])
        sys.stdout.flush()


def get(url: str, attempt: Attempt) -> bytes | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as exc:
        attempt.outcome = "transport error"
        attempt.detail = type(exc).__name__ + ": " + str(exc)[:300]
        return None
    attempt.status = response.status_code
    attempt.content_type = response.headers.get("Content-Type")
    payload = response.content
    attempt.bytes_received = len(payload)
    attempt.sha256 = hashlib.sha256(payload).hexdigest()
    if response.status_code != 200:
        attempt.outcome = "non-200"
        return None
    if not payload:
        attempt.outcome = "empty body"
        return None
    return payload


def data_links(html: str, base: str) -> list[str]:
    """Any link from a page that could be a machine-readable table."""
    found = []
    for href in re.findall(r'href="([^"]+)"', html):
        lowered = href.lower()
        if any(marker in lowered for marker in ARTICLE_URL_MARKERS):
            continue
        if lowered.endswith(DATA_SUFFIXES) or "supplementary" in lowered or "media-" in lowered:
            if href.startswith("http"):
                found.append(href)
            elif href.startswith("/"):
                found.append("https://www.biorxiv.org" + href)
            else:
                found.append(base.rstrip("/") + "/" + href)
    return sorted(set(found))


def looks_like_data(payload: bytes, content_type: str | None) -> tuple[bool, str]:
    """Is this payload a machine-readable table, or a web page wearing the extension?

    A publisher answering with HTML under a data URL is the normal case, not the odd one,
    and accepting it would put an article page in raw/ labelled as a variant table. So the
    content is checked, never the status code and the URL alone.
    """
    if len(payload) < 32:
        return False, "fewer than 32 bytes"
    if content_type and "html" in content_type.lower():
        return False, "served as " + content_type
    head = payload[:512].lstrip()
    lowered = head[:200].lower()
    if lowered.startswith(b"<!doctype") or lowered.startswith(b"<html") or b"<head" in lowered:
        return False, "body is HTML: " + repr(head[:80].decode("utf-8", "replace"))
    if payload[:4] == ZIP_MAGIC:
        return True, "zip or xlsx container"
    if payload[:8] == OLE_MAGIC:
        return True, "legacy Excel container"
    text = payload[:4096].decode("utf-8", "replace")
    if text.count(",") >= 10 or text.count("	") >= 10:
        return True, "delimited text"
    return False, "no recognisable table structure in the first 4 KiB"


def route1(doi: str) -> tuple[list[Attempt], dict[str, bytes]]:
    """The bioRxiv supplementary-material page."""
    attempts: list[Attempt] = []
    found: dict[str, bytes] = {}
    for version in ("v1", "v2", ""):
        url = "https://www.biorxiv.org/content/" + doi + version + ".supplementary-material"
        attempt = Attempt(1, "bioRxiv supplementary-material page " + (version or "current"), url)
        attempts.append(attempt)
        payload = get(url, attempt)
        time.sleep(PAUSE_SECONDS)
        if payload is None:
            continue
        html = payload.decode("utf-8", "replace")
        links = data_links(html, url)
        attempt.found = links
        if not links:
            attempt.outcome = "page served, no data-bearing supplementary link"
            continue
        attempt.outcome = "page listed " + str(len(links)) + " candidate link(s)"
        attempt.detail = "; ".join(links[:10])
        for link in links:
            if not link.lower().endswith(DATA_SUFFIXES):
                continue
            sub = Attempt(1, "bioRxiv supplementary file", link)
            attempts.append(sub)
            body = get(link, sub)
            time.sleep(PAUSE_SECONDS)
            if body is None:
                continue
            ok, why = looks_like_data(body, sub.content_type)
            if not ok:
                sub.outcome = "rejected, not a machine-readable table"
                sub.detail = why
                continue
            sub.outcome = "downloaded, " + why
            found[Path(link).name] = body
        if found:
            break
    return attempts, found


def route2(doi: str) -> tuple[list[Attempt], dict, str | None]:
    """The bioRxiv API: current version, and any published-journal DOI."""
    attempts: list[Attempt] = []
    details: dict = {}
    published_doi: str | None = None

    url = "https://api.biorxiv.org/details/biorxiv/" + doi
    attempt = Attempt(2, "bioRxiv API details", url)
    attempts.append(attempt)
    payload = get(url, attempt)
    if payload is not None:
        try:
            data = json.loads(payload.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            attempt.outcome = "response was not JSON"
        else:
            collection = data.get("collection") or []
            if not collection:
                attempt.outcome = "no posts found for this DOI"
            else:
                details = collection[-1]
                attempt.outcome = (
                    "resolved: version "
                    + str(details.get("version"))
                    + ", posted "
                    + str(details.get("date"))
                    + ", licence "
                    + str(details.get("license"))
                )
                attempt.detail = "title: " + str(details.get("title"))
    time.sleep(PAUSE_SECONDS)

    url = "https://api.biorxiv.org/pubs/biorxiv/" + doi
    attempt = Attempt(2, "bioRxiv API published version", url)
    attempts.append(attempt)
    payload = get(url, attempt)
    if payload is not None:
        try:
            data = json.loads(payload.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            attempt.outcome = "response was not JSON"
        else:
            collection = data.get("collection") or []
            if not collection:
                attempt.outcome = "no published version of this preprint exists yet"
            else:
                published_doi = collection[0].get("published_doi")
                attempt.outcome = "published as " + str(published_doi)
    return attempts, details, published_doi


def route2b(details: dict) -> tuple[list[Attempt], dict[str, bytes]]:
    """The JATS XML the API points at, which sometimes lists files the page does not."""
    attempts: list[Attempt] = []
    found: dict[str, bytes] = {}
    jats = details.get("jatsxml")
    if not jats:
        return attempts, found
    attempt = Attempt(2, "bioRxiv JATS XML", jats)
    attempts.append(attempt)
    payload = get(jats, attempt)
    if payload is None:
        return attempts, found
    xml = payload.decode("utf-8", "replace")
    blocks = re.findall(r"<supplementary-material.*?</supplementary-material>", xml, re.S)
    hrefs = re.findall(r'xlink:href="([^"]+)"', xml)
    attempt.found = sorted(set(hrefs))
    attempt.outcome = (
        str(len(blocks))
        + " supplementary-material block(s), "
        + str(len(set(hrefs)))
        + " href(s)"
    )
    if blocks:
        attempt.detail = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", blocks[0]))[:300]
    return attempts, found


def route3(published_doi: str | None) -> tuple[list[Attempt], dict[str, bytes]]:
    """The published journal version or a PMC mirror, if one exists."""
    attempts: list[Attempt] = []
    found: dict[str, bytes] = {}
    if not published_doi:
        attempt = Attempt(
            3,
            "published journal version",
            "n/a",
        )
        attempt.outcome = (
            "skipped: the bioRxiv API reports no published version, so there is no "
            "journal or PMC mirror to try"
        )
        attempts.append(attempt)
        return attempts, found

    # Europe PMC resolves a DOI to a PMC identifier when one exists, which is the
    # cheapest way to find an open-access mirror without guessing publisher URLs.
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:"
        + published_doi
        + "&format=json"
    )
    attempt = Attempt(3, "Europe PMC search by published DOI", url)
    attempts.append(attempt)
    payload = get(url, attempt)
    if payload is None:
        return attempts, found
    try:
        data = json.loads(payload.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        attempt.outcome = "response was not JSON"
        return attempts, found
    results = data.get("resultList", {}).get("result", [])
    if not results:
        attempt.outcome = "Europe PMC has no record for the published DOI"
        return attempts, found
    pmcid = results[0].get("pmcid")
    attempt.outcome = "record found, pmcid " + str(pmcid)
    if not pmcid:
        return attempts, found
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/"
        + pmcid
        + "/supplementaryFiles?includeInlineImage=false"
    )
    sub = Attempt(3, "Europe PMC supplementaryFiles", url)
    attempts.append(sub)
    body = get(url, sub)
    if body is not None:
        ok, why = looks_like_data(body, sub.content_type)
        if ok:
            sub.outcome = "archive downloaded, " + why
            found[pmcid + "_supplementary.zip"] = body
        else:
            sub.outcome = "rejected, not an archive"
            sub.detail = why
    return attempts, found


def route4() -> tuple[list[Attempt], dict[str, bytes]]:
    """Author-deposited repositories: Zenodo, Dryad, OSF, GitHub."""
    attempts: list[Attempt] = []
    found: dict[str, bytes] = {}
    queries = [
        (
            "Zenodo",
            "https://zenodo.org/api/records?q="
            + requests.utils.quote('"M-MLV reverse transcriptase" AND "prime editing"')
            + "&size=20",
            lambda d: [h.get("title", "") for h in d.get("hits", {}).get("hits", [])],
        ),
        (
            "Zenodo, by title",
            "https://zenodo.org/api/records?q="
            + requests.utils.quote('"saturated mutagenesis" AND "reverse transcriptase"')
            + "&size=20",
            lambda d: [h.get("title", "") for h in d.get("hits", {}).get("hits", [])],
        ),
        (
            "Dryad",
            "https://datadryad.org/api/v2/search?q="
            + requests.utils.quote("M-MLV reverse transcriptase prime editing"),
            lambda d: [
                x.get("title", "")
                for x in d.get("_embedded", {}).get("stash:datasets", [])
            ],
        ),
        (
            "OSF",
            "https://api.osf.io/v2/nodes/?filter[title]="
            + requests.utils.quote("saturated mutagenesis reverse transcriptase"),
            lambda d: [
                x.get("attributes", {}).get("title", "") for x in d.get("data", [])
            ],
        ),
        (
            "GitHub repositories",
            "https://api.github.com/search/repositories?q="
            + requests.utils.quote("M-MLV reverse transcriptase prime editing mutagenesis"),
            lambda d: [x.get("full_name", "") for x in d.get("items", [])],
        ),
        (
            "GitHub code, by variant table",
            "https://api.github.com/search/repositories?q="
            + requests.utils.quote("PE2 reverse transcriptase saturation mutagenesis screen"),
            lambda d: [x.get("full_name", "") for x in d.get("items", [])],
        ),
    ]
    for label, url, extract in queries:
        attempt = Attempt(4, label, url)
        attempts.append(attempt)
        payload = get(url, attempt)
        time.sleep(PAUSE_SECONDS)
        if payload is None:
            continue
        try:
            data = json.loads(payload.decode("utf-8", "replace"))
        except json.JSONDecodeError:
            attempt.outcome = "response was not JSON"
            continue
        titles = [t for t in extract(data) if t]
        attempt.found = titles
        # A hit is only interesting if it plausibly names this work. Reporting twenty
        # unrelated titles as candidates would be noise dressed as diligence.
        relevant = [
            t
            for t in titles
            if "mlv" in t.lower()
            or ("reverse transcriptase" in t.lower() and "prime" in t.lower())
            or ("mutagenesis" in t.lower() and "transcriptase" in t.lower())
        ]
        attempt.outcome = (
            str(len(titles)) + " result(s), " + str(len(relevant)) + " plausibly relevant"
        )
        if relevant:
            attempt.detail = "relevant: " + "; ".join(relevant[:10])
        elif titles:
            attempt.detail = "none relevant; first few: " + "; ".join(titles[:5])
    return attempts, found


def write_manual_note(attempts: list[Attempt], details: dict) -> None:
    lines = [
        "# Manual fetch required: Task B, the M-MLV RT saturated mutagenesis screen",
        "",
        "Every scripted route failed. **Task B has no labels and cannot proceed past",
        "acquisition.** This is a recorded outcome, not a reason to estimate, model, or",
        "reconstruct the values.",
        "",
        "## What is needed",
        "",
        "| file | why | destination |",
        "| --- | --- | --- |",
        "| Supplementary Tables S6 and S7 | the per-variant normalized editing efficiencies for libraries L1 and L2. Without these Task B has no labels at all | `tasks/taskB_mmlv_dms/raw/table_s6.xlsx`, `table_s7.xlsx` |",
        "| Supplementary Sequence 1 | the PE2dR construct protein sequence. Every one of the 1045 variants is built on it, and building them on a reference wrong at even one position would invalidate the whole task | `tasks/taskB_mmlv_dms/raw/supplementary_sequences.pdf` |",
        "",
        "## The work",
        "",
        "| field | value |",
        "| --- | --- |",
        "| title | " + str(details.get("title", "Saturated mutagenesis screen of M-MLV reverse transcriptase identifies variants enhancing prime editing efficiency")) + " |",
        "| DOI, resolved | `" + DOI + "` |",
        "| DOI in the brief, which does not resolve | `" + BRIEF_DOI + "` |",
        "| version | " + str(details.get("version", "1")) + " |",
        "| posted | " + str(details.get("date", "2026-07-07")) + " |",
        "| licence | " + str(details.get("license", "cc_by_nc")) + " |",
        "| corresponding author | " + str(details.get("author_corresponding", "Haojie Yu")) + " |",
        "",
        "## Routes tried",
        "",
        "| route | URL | status | outcome |",
        "| --- | --- | --- | --- |",
    ]
    for attempt in attempts:
        lines.append(
            "| "
            + str(attempt.route)
            + " | `"
            + attempt.url
            + "` | "
            + str(attempt.status)
            + " | "
            + attempt.outcome
            + " |"
        )
    lines += [
        "",
        "## The remaining route is the corresponding author",
        "",
        "`data_acquisition/AUTHOR_REQUEST.md` holds a drafted request, written at an",
        "earlier gate and still accurate. Nothing has been sent; sending it is a human",
        "action.",
        "",
        "If the tables arrive privately, they go in `raw/` locally and `PROVENANCE.md`",
        "records that they must not be committed, because a file shared privately by an",
        "author carries whatever terms the author sets regardless of the preprint's CC",
        "BY-NC licence. The repository would then keep the parser and the checksums only.",
        "",
        "## What must not happen",
        "",
        "There is no acceptable substitute for these labels. A simulated deep mutational",
        "scan, values digitized from a figure, or a different protein's screen would each",
        "make every downstream number meaningless while looking exactly like a result.",
    ]
    MANUAL_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + MANUAL_NOTE.relative_to(REPO_ROOT).as_posix())


def store(found: dict[str, bytes], source: str) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Checksums for the Task B source files",
        "#",
        "# Written by data_acquisition/fetch_mmlv_dms.py. Each file is stored exactly as",
        "# served, byte for byte.",
        "#",
        "# preprint DOI: " + DOI,
        "# access date: " + date.today().isoformat(),
        "",
        "filename\tsha256\tbytes\tsource",
    ]
    for name in sorted(found):
        payload = found[name]
        # Last line of defence, so no future route can reach raw/ unvalidated.
        ok, why = looks_like_data(payload, None)
        if not ok:
            raise SystemExit("refusing to store " + name + " in raw/: " + why)
        target = RAW_DIR / Path(name).name
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        lines.append("\t".join([target.name, digest, str(len(payload)), source]))
        print("stored " + target.relative_to(REPO_ROOT).as_posix() + " sha256=" + digest)
    CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + CHECKSUMS.relative_to(REPO_ROOT).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route", type=int, choices=(1, 2, 3, 4))
    args = parser.parse_args()

    print_run_header("data_acquisition/fetch_mmlv_dms.py")
    print("target: Supplementary Tables S6 and S7, plus Supplementary Sequence 1")
    print("DOI used: " + DOI)
    print("DOI in the brief, which does not resolve: " + BRIEF_DOI)
    print("")

    attempts: list[Attempt] = []
    found: dict[str, bytes] = {}
    source = ""

    # Route 2 runs first in practice even though it is second in the brief's order,
    # because it resolves the current version and any published DOI that routes 1 and 3
    # then need. Its attempts are logged under route 2 regardless.
    api_attempts, details, published_doi = route2(DOI)
    for attempt in api_attempts:
        attempt.log()
    attempts.extend(api_attempts)
    print("")

    wanted = [args.route] if args.route else [1, 2, 3, 4]
    for route in wanted:
        if route == 1:
            batch, got = route1(DOI)
        elif route == 2:
            batch, got = route2b(details)
        elif route == 3:
            batch, got = route3(published_doi)
        else:
            batch, got = route4()
        for attempt in batch:
            attempt.log()
        attempts.extend(batch)
        if got:
            found = got
            source = batch[-1].url
            print("route " + str(route) + " returned candidate files")
            break
        print("")

    ATTEMPT_LOG.write_text(
        json.dumps(
            {
                "doi": DOI,
                "brief_doi_that_does_not_resolve": BRIEF_DOI,
                "access_date": date.today().isoformat(),
                "biorxiv_details": details,
                "published_doi": published_doi,
                "attempts": [a.as_dict() for a in attempts],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("")
    print("wrote " + ATTEMPT_LOG.relative_to(REPO_ROOT).as_posix())

    if not found:
        print("")
        print("FAILED: no route returned a machine-readable variant table.")
        write_manual_note(attempts, details)
        return 1

    store(found, source)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
