"""Acquire Supplementary Table S1 of Doman et al. 2023 from the open access record.

The target is the supplementary workbook of:

    Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al.
    "Phage-assisted evolution and protein engineering yield compact, efficient
    prime editors." Cell 2023, 186(18):3983-4002.e26.
    DOI 10.1016/j.cell.2023.07.039, PMC accession PMC10482982.

Four routes are attempted in a fixed order, cheapest and most scriptable first. Every
attempt is logged with its exact URL, HTTP status, byte count, content type and SHA256,
whether it succeeded or not, so that a later reader can see which routes were tried and
what each one returned rather than only seeing the one that worked.

    python data_acquisition/fetch_doman_s1.py
    python data_acquisition/fetch_doman_s1.py --route 1          # one route only
    python data_acquisition/fetch_doman_s1.py --dry-run          # probe, keep nothing

Nothing here parses a spreadsheet. The file is stored byte for byte as served, and the
inventory step that follows is a separate script, so that a parsing mistake can never be
confused with an acquisition mistake. On total failure the script writes a manual fetch
note and exits non-zero; it never substitutes a different file for the one it wanted.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import tarfile
import time
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header  # noqa: E402

PMC_ID = "PMC10482982"
DOI = "10.1016/j.cell.2023.07.039"

# Task A lives in tasks/taskA_crossfamily/ in this repository. The brief names
# tasks/taskA/; the longer name is the one already carried by PROVENANCE.md, the frozen
# splits and the audit, so it is kept and the alias recorded here, rather than creating a
# second directory holding the same task.
RAW_DIR = REPO_ROOT / "tasks" / "taskA_crossfamily" / "raw"
CHECKSUMS = RAW_DIR / "CHECKSUMS.txt"
ATTEMPT_LOG = REPO_ROOT / "data_acquisition" / "fetch_doman_s1_attempts.json"
MANUAL_NOTE = REPO_ROOT / "data_acquisition" / "MANUAL_FETCH_TABLE_S1.md"

# A contact address is part of being a well behaved client against EBI and NCBI, both of
# which ask for one.
USER_AGENT = (
    "RT-plm-benchmark/0.1 (open benchmark of protein representations for reverse "
    "transcriptase function; contact shyamarunach@gmail.com)"
)
HEADERS = {"User-Agent": USER_AGENT}

# One polite pause between routes. Not a retry loop: a route that fails is recorded as
# failed and the next one is tried, because hammering a failing endpoint is both rude and
# uninformative.
PAUSE_SECONDS = 2

# Separate connect and read timeouts. The Europe PMC supplementary endpoint serves a
# chunked archive of every supplementary file for an article, which for this paper is
# hundreds of megabytes, and it does stall mid-stream. A read timeout is what turns a
# stall into a recorded failure instead of a process that hangs until something kills it.
CONNECT_TIMEOUT = 30
READ_TIMEOUT = 90
TIMEOUT = (CONNECT_TIMEOUT, READ_TIMEOUT)

# Large bodies are streamed to disk rather than held in memory, and progress is printed so
# a stall is visible while it is happening rather than only afterwards.
CHUNK_BYTES = 1 << 20
PROGRESS_EVERY = 16 << 20

# Scratch space for archives that are downloaded only to be opened, not kept. These are
# intermediate artifacts: what gets committed is the spreadsheet inside them.
SCRATCH = REPO_ROOT / ".fetch_cache"

# Supplementary spreadsheet extensions. Cell serves its supplementary files as mmc1,
# mmc2 and so on, and the brief names mmc2 as the expected Table S1 file.
SHEET_SUFFIXES = (".xlsx", ".xls", ".xlsm")


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
    members: list[str] = field(default_factory=list)

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
            "members": self.members,
        }

    def log(self) -> None:
        print(
            "route {0} | {1} | status={2} | type={3} | bytes={4} | sha256={5} | {6}".format(
                self.route,
                self.url,
                self.status,
                self.content_type,
                self.bytes_received,
                (self.sha256 or "none")[:16],
                self.outcome,
            )
        )
        if self.detail:
            print("    " + self.detail)
        sys.stdout.flush()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def looks_like_xlsx(payload: bytes) -> tuple[bool, str]:
    """Is this payload really an xlsx workbook, or something wearing the extension?

    This guard is load bearing rather than defensive. Both NCBI and the publisher answer
    a request for a supplementary binary with HTTP 200 and an HTML interstitial when they
    decide the client is a robot: a bot check, a cookie wall, or an error page. Those
    responses are a few kilobytes of HTML served under the requested filename, so a
    fetcher that trusts the status code and the URL suffix will write an HTML page into
    the raw directory as `mmc2.xlsx` and every later stage will read a file that is not
    the table. An xlsx is a zip container, so the first four bytes settle it.
    """
    if len(payload) < 4:
        return False, "fewer than 4 bytes"
    if payload[:4] != b"PK\x03\x04":
        head = payload[:80].decode("utf-8", "replace").replace("\n", " ")
        return False, "not a zip container; first bytes are " + repr(head)
    try:
        archive = zipfile.ZipFile(io.BytesIO(payload))
    except zipfile.BadZipFile as exc:
        return False, "zip magic but unreadable: " + str(exc)[:120]
    names = archive.namelist()
    archive.close()
    if "[Content_Types].xml" not in names:
        return False, "zip without [Content_Types].xml; members " + str(names[:6])
    if not any(n.startswith("xl/") for n in names):
        return False, "zip is not a spreadsheet package; members " + str(names[:6])
    return True, "xlsx package, " + str(len(names)) + " members"


def get(url: str, attempt: Attempt) -> bytes | None:
    """Fetch one small URL into memory, recording everything observed about the response.

    Used for pages and service records. Archives go through `get_to_file`.
    """
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
    attempt.sha256 = sha256_bytes(payload)
    if response.status_code != 200:
        attempt.outcome = "non-200"
        attempt.detail = payload[:200].decode("utf-8", "replace")
        return None
    if not payload:
        attempt.outcome = "empty body"
        return None
    return payload


def get_to_file(url: str, attempt: Attempt, dest: Path) -> Path | None:
    """Stream one URL to disk, printing progress, and hash it as it arrives.

    Nothing is held in memory, so an archive of any size is as cheap as a small one, and
    the printed byte count makes a stall visible while it is happening.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    received = 0
    try:
        with requests.get(url, headers=HEADERS, timeout=TIMEOUT, stream=True) as response:
            attempt.status = response.status_code
            attempt.content_type = response.headers.get("Content-Type")
            declared = response.headers.get("Content-Length")
            if response.status_code != 200:
                body = response.content[:200]
                attempt.bytes_received = len(body)
                attempt.sha256 = sha256_bytes(body)
                attempt.outcome = "non-200"
                attempt.detail = body.decode("utf-8", "replace")
                return None
            print(
                "    streaming to "
                + dest.name
                + ", declared length "
                + (declared or "unknown")
            )
            sys.stdout.flush()
            next_mark = PROGRESS_EVERY
            with dest.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=CHUNK_BYTES):
                    if not chunk:
                        continue
                    handle.write(chunk)
                    digest.update(chunk)
                    received += len(chunk)
                    if received >= next_mark:
                        print("    received " + str(received >> 20) + " MiB")
                        sys.stdout.flush()
                        next_mark += PROGRESS_EVERY
    except requests.RequestException as exc:
        attempt.bytes_received = received
        attempt.sha256 = digest.hexdigest()
        attempt.outcome = "transport error after " + str(received) + " bytes"
        attempt.detail = type(exc).__name__ + ": " + str(exc)[:300]
        return None
    attempt.bytes_received = received
    attempt.sha256 = digest.hexdigest()
    if received == 0:
        attempt.outcome = "empty body"
        return None
    return dest


def spreadsheets_in_zip(path: Path, attempt: Attempt) -> dict[str, bytes]:
    """Return every spreadsheet member of a zip archive on disk, keyed by its name."""
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        attempt.outcome = "not a zip"
        attempt.detail = str(exc)[:200]
        return {}
    names = archive.namelist()
    attempt.members = names
    found = {}
    rejected = []
    for name in names:
        if not name.lower().endswith(SHEET_SUFFIXES):
            continue
        payload = archive.read(name)
        ok, why = looks_like_xlsx(payload)
        if ok:
            found[name] = payload
        else:
            rejected.append(name + " (" + why + ")")
    archive.close()
    if rejected:
        attempt.detail = "rejected as not a workbook: " + "; ".join(rejected)
    return found


def route1() -> tuple[list[Attempt], dict[str, bytes]]:
    """Europe PMC supplementary files endpoint: a zip of every supplementary file.

    Two variants are tried. `includeInlineImage=false` is attempted first because the
    default archive for this article carries the inline figure images as well, which runs
    to hundreds of megabytes and stalls mid-stream; the tables are the same either way,
    so asking for the smaller archive is both faster and kinder to the service.
    """
    base = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/" + PMC_ID + "/supplementaryFiles"
    )
    variants = (
        ("Europe PMC supplementaryFiles, no inline images", base + "?includeInlineImage=false"),
        ("Europe PMC supplementaryFiles, full archive", base),
    )
    attempts: list[Attempt] = []
    for index, (label, url) in enumerate(variants):
        attempt = Attempt(1, label, url)
        attempts.append(attempt)
        if index:
            time.sleep(PAUSE_SECONDS)
        archive = get_to_file(
            url, attempt, SCRATCH / (PMC_ID + "_europepmc_suppl_" + str(index) + ".zip")
        )
        if archive is None:
            continue
        sheets = spreadsheets_in_zip(archive, attempt)
        if not sheets:
            if attempt.outcome == "not attempted":
                attempt.outcome = "zip held no spreadsheet"
                attempt.detail = "members: " + ", ".join(attempt.members[:20])
            continue
        attempt.outcome = "success, {0} spreadsheet members".format(len(sheets))
        attempt.detail = "members: " + ", ".join(sorted(sheets))
        return attempts, sheets
    return attempts, {}


def route2() -> tuple[list[Attempt], dict[str, bytes]]:
    """NCBI PMC Open Access service: an XML pointer to a package, then the package."""
    url = "https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=" + PMC_ID
    attempts = []
    attempt = Attempt(2, "NCBI OA service record", url)
    attempts.append(attempt)
    payload = get(url, attempt)
    if payload is None:
        return attempts, {}
    text = payload.decode("utf-8", "replace")
    links = re.findall(r'href="([^"]+)"', text)
    if not links:
        attempt.outcome = "no package link in OA record"
        attempt.detail = text[:300]
        return attempts, {}
    attempt.outcome = "record returned {0} link(s)".format(len(links))
    attempt.detail = "links: " + ", ".join(links)
    for link in links:
        # The OA service still advertises ftp:// for some records; the same path is
        # served over https, which is what is used here.
        candidate = link.replace(
            "ftp://ftp.ncbi.nlm.nih.gov", "https://ftp.ncbi.nlm.nih.gov"
        )
        sub = Attempt(2, "NCBI OA package", candidate)
        attempts.append(sub)
        time.sleep(PAUSE_SECONDS)
        package = get_to_file(
            candidate, sub, SCRATCH / (PMC_ID + "_oa_" + Path(candidate).name)
        )
        if package is None:
            continue
        if candidate.endswith(".tar.gz") or candidate.endswith(".tgz"):
            try:
                tar = tarfile.open(package, mode="r:gz")
            except tarfile.TarError as exc:
                sub.outcome = "not a readable tar"
                sub.detail = str(exc)[:200]
                continue
            names = tar.getnames()
            sub.members = names
            sheets = {}
            for name in names:
                if name.lower().endswith(SHEET_SUFFIXES):
                    handle = tar.extractfile(name)
                    if handle is not None:
                        sheets[Path(name).name] = handle.read()
            if sheets:
                sub.outcome = "success, {0} spreadsheet members".format(len(sheets))
                sub.detail = "members: " + ", ".join(sorted(sheets))
                return attempts, sheets
            sub.outcome = "package held no spreadsheet"
            sub.detail = "members: " + ", ".join(names[:20])
            continue
        sheets = spreadsheets_in_zip(package, sub)
        if sheets:
            sub.outcome = "success, {0} spreadsheet members".format(len(sheets))
            return attempts, sheets
    return attempts, {}


def route3() -> tuple[list[Attempt], dict[str, bytes]]:
    """PMC article page: resolve the supplementary binaries from the rendered HTML."""
    url = "https://pmc.ncbi.nlm.nih.gov/articles/" + PMC_ID + "/"
    attempts = []
    attempt = Attempt(3, "PMC article page", url)
    attempts.append(attempt)
    payload = get(url, attempt)
    if payload is None:
        return attempts, {}
    text = payload.decode("utf-8", "replace")
    hrefs = set(re.findall(r'href="([^"]*mmc\d+[^"]*)"', text))
    hrefs |= set(re.findall(r'href="([^"]*/bin/[^"]+)"', text))
    if not hrefs:
        attempt.outcome = "no supplementary link found in page"
        return attempts, {}
    attempt.outcome = "page listed {0} supplementary link(s)".format(len(hrefs))
    attempt.detail = "links: " + ", ".join(sorted(hrefs))
    sheets: dict[str, bytes] = {}
    for href in sorted(hrefs):
        if not href.lower().endswith(SHEET_SUFFIXES):
            continue
        absolute = (
            href if href.startswith("http") else "https://pmc.ncbi.nlm.nih.gov" + href
        )
        sub = Attempt(3, "PMC supplementary binary", absolute)
        attempts.append(sub)
        time.sleep(PAUSE_SECONDS)
        body = get(absolute, sub)
        if body is None:
            continue
        ok, why = looks_like_xlsx(body)
        if not ok:
            # NCBI answers a scripted request for a supplementary binary with HTTP 200
            # and a bot-check page. Accepting it would put an HTML page in raw/ under the
            # name of the table, so it is refused here and the reason is recorded.
            sub.outcome = "rejected, served HTML rather than a workbook"
            sub.detail = why
            continue
        sub.outcome = "success, " + why
        sheets[Path(absolute).name] = body
    return attempts, sheets


def route4() -> tuple[list[Attempt], dict[str, bytes]]:
    """Publisher. Expected to be blocked by bot protection; recorded either way."""
    attempts = []
    targets = (
        ("Cell full text", "https://www.cell.com/cell/fulltext/S0092-8674(23)00854-1"),
        (
            "Cell mmc2 attachment",
            "https://www.cell.com/cms/10.1016/j.cell.2023.07.039/attachment/mmc2.xlsx",
        ),
    )
    for label, url in targets:
        attempt = Attempt(4, label, url)
        attempts.append(attempt)
        time.sleep(PAUSE_SECONDS)
        payload = get(url, attempt)
        if payload is None:
            continue
        if url.lower().endswith(SHEET_SUFFIXES):
            ok, why = looks_like_xlsx(payload)
            if not ok:
                attempt.outcome = "rejected, served HTML rather than a workbook"
                attempt.detail = why
                continue
            attempt.outcome = "success, " + why
            return attempts, {Path(url).name: payload}
        attempt.outcome = "page fetched, not a spreadsheet"
    return attempts, {}


def store(sheets: dict[str, bytes], source_url: str) -> list[tuple[str, str, int]]:
    """Write every fetched spreadsheet unmodified into raw/ and record its checksum."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    rows = []
    lines = [
        "# Checksums for the Doman et al. 2023 supplementary files",
        "#",
        "# Written by data_acquisition/fetch_doman_s1.py. Each file is stored exactly as",
        "# served, byte for byte. Nothing here has been opened in a spreadsheet",
        "# application, because a save from one can rewrite a numeric cell to its",
        "# displayed precision, and a silently rounded activity value is an invented",
        "# activity value.",
        "#",
        "# article DOI: " + DOI,
        "# PMC accession: " + PMC_ID,
        "# access date: " + today,
        "",
        "filename\tsha256\tbytes\tsource_url",
    ]
    for name in sorted(sheets):
        payload = sheets[name]
        # Last line of defence. Every route already checks, and this checks again, so
        # that no future route can reach raw/ without having been validated once.
        ok, why = looks_like_xlsx(payload)
        if not ok:
            raise SystemExit(
                "refusing to store " + name + " in raw/: " + why
            )
        target = RAW_DIR / Path(name).name
        target.write_bytes(payload)
        digest = sha256_bytes(payload)
        rows.append((target.name, digest, len(payload)))
        lines.append(
            "\t".join([target.name, digest, str(len(payload)), source_url])
        )
        print("stored " + target.relative_to(REPO_ROOT).as_posix())
        print("    sha256=" + digest + " bytes=" + str(len(payload)))
    CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + CHECKSUMS.relative_to(REPO_ROOT).as_posix())
    return rows


def write_manual_note(attempts: list[Attempt]) -> None:
    lines = [
        "# Manual fetch required: Doman et al. 2023 Supplementary Table S1",
        "",
        "Every scripted route failed. The file this pipeline needs is:",
        "",
        "| field | value |",
        "| --- | --- |",
        "| file | `mmc2.xlsx`, the supplementary workbook holding Table S1 |",
        "| article | Doman et al., Cell 186(18):3983-4002.e26, 2023 |",
        "| DOI | `" + DOI + "` |",
        "| PMC accession | `" + PMC_ID + "` |",
        "| destination | `tasks/taskA_crossfamily/raw/mmc2.xlsx` |",
        "",
        "Place the file exactly as downloaded. Do not open and re-save it: a spreadsheet",
        "application can rewrite a numeric cell to its displayed precision on save, and",
        "a silently rounded activity value is an invented activity value.",
        "",
        "## Routes tried",
        "",
        "| route | URL | status | bytes | outcome |",
        "| --- | --- | --- | --- | --- |",
    ]
    for attempt in attempts:
        lines.append(
            "| {0} | `{1}` | {2} | {3} | {4} |".format(
                attempt.route,
                attempt.url,
                attempt.status,
                attempt.bytes_received,
                attempt.outcome,
            )
        )
    lines += [
        "",
        "Rerun `python data_acquisition/fetch_doman_s1.py` after placing the file to",
        "have its checksum recorded, or run the inventory step directly.",
        "",
    ]
    MANUAL_NOTE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + MANUAL_NOTE.relative_to(REPO_ROOT).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--route", type=int, choices=(1, 2, 3, 4), help="attempt one route only"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="probe the routes, store nothing"
    )
    args = parser.parse_args()

    print_run_header("data_acquisition/fetch_doman_s1.py")
    print("target: Supplementary Table S1, " + DOI + " (" + PMC_ID + ")")
    print("destination: " + RAW_DIR.relative_to(REPO_ROOT).as_posix())
    print("")

    wanted = [args.route] if args.route else [1, 2, 3, 4]
    attempts: list[Attempt] = []
    sheets: dict[str, bytes] = {}
    source_url = ""

    for route in wanted:
        if route == 1:
            batch, got = route1()
        elif route == 2:
            batch, got = route2()
        elif route == 3:
            batch, got = route3()
        else:
            batch, got = route4()
        for attempt in batch:
            attempt.log()
        attempts.extend(batch)
        if got:
            sheets = got
            source_url = batch[-1].url
            print("route {0} satisfied the request; later routes not attempted".format(route))
            break
        time.sleep(PAUSE_SECONDS)

    ATTEMPT_LOG.write_text(
        json.dumps(
            {
                "doi": DOI,
                "pmc": PMC_ID,
                "access_date": date.today().isoformat(),
                "attempts": [a.as_dict() for a in attempts],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print("")
    print("wrote " + ATTEMPT_LOG.relative_to(REPO_ROOT).as_posix())

    if not sheets:
        print("")
        print("FAILED: no route returned a supplementary spreadsheet.")
        write_manual_note(attempts)
        return 1

    if args.dry_run:
        print("")
        print("dry run: {0} spreadsheet(s) found, nothing written".format(len(sheets)))
        for name in sorted(sheets):
            print("    " + name + " bytes=" + str(len(sheets[name])))
        return 0

    print("")
    store(sheets, source_url)
    if MANUAL_NOTE.is_file():
        # A manual fetch note from an earlier failed run would now be describing a file
        # that is present, which is worse than having no note at all.
        MANUAL_NOTE.unlink()
        print("removed the stale " + MANUAL_NOTE.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
