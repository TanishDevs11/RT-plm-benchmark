"""Acquire the Stanford HIVDB genotype-phenotype datasets for HIV-1 reverse transcriptase.

Selected at Gate G0; the reasoning is in `reports/taskB_hivrt/dataset_survey.md`. Only the
two RT drug classes are in scope: NRTI and NNRTI. PI targets protease, INI integrase and
CAI capsid, so none of those is fetched.

Both the filtered and the unfiltered variant of each class is downloaded. The filtered set
is the primary analysis because it is PhenoSense only and source-deduplicated; the
unfiltered set is needed for two separate reasons, to quantify what the filtering removes
and to recover the `PtID` and `Subtype` columns that the filtered sets do not carry.

This is an academic resource maintained as a benefit to the research community, not a
scraping target. So: one descriptive User-Agent with a contact address, a pause between
every request, no retries beyond one, and no parallelism.

    python data_acquisition/fetch_hivdb.py
    python data_acquisition/fetch_hivdb.py --dry-run

Outputs:
    tasks/taskB_hivrt/raw/*.txt            the datasets, byte for byte as served
    tasks/taskB_hivrt/raw/CHECKSUMS.txt    filename, SHA256, bytes, URL, release, date
    tasks/taskB_hivrt/reference.fasta      consensus B RT, extracted from HIVDB
    data_acquisition/fetch_hivdb_attempts.json
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

TASK_DIR = REPO_ROOT / "tasks" / "taskB_hivrt"
RAW = TASK_DIR / "raw"
CHECKSUMS = RAW / "CHECKSUMS.txt"
REFERENCE = TASK_DIR / "reference.fasta"
ATTEMPT_LOG = REPO_ROOT / "data_acquisition" / "fetch_hivdb_attempts.json"

BASE = "https://hivdb.stanford.edu"
DOWNLOAD = BASE + "/download/GenoPhenoDatasets/"
DATASET_PAGE = BASE + "/_wrapper/pages/genopheno.dataset.html"
CONSENSUS_PAGE = BASE + "/_wrapper/pages/documentPage/consensus_amino_acid_sequences.html"

# Only the reverse transcriptase drug classes.
FILES = {
    "NRTI_DataSet.txt": "NRTI, high quality filtered, PhenoSense only",
    "NRTI_DataSet.Full.txt": "NRTI, complete unfiltered, mixed assay methods",
    "NNRTI_DataSet.txt": "NNRTI, high quality filtered, PhenoSense only",
    "NNRTI_DataSet.Full.txt": "NNRTI, complete unfiltered, mixed assay methods",
    "references.txt": "publication references for the isolates",
}

USER_AGENT = (
    "RT-plm-benchmark/0.1 (academic, non-commercial benchmark of protein representations "
    "for reverse transcriptase function; contact shyamarunach@gmail.com)"
)
HEADERS = {"User-Agent": USER_AGENT}
TIMEOUT = (30, 120)
PAUSE_SECONDS = 3

CITATION = (
    "Rhee SY, Gonzales MJ, Kantor R, Betts BJ, Ravela J, Shafer RW. Human "
    "immunodeficiency virus reverse transcriptase and protease sequence database. "
    "Nucleic Acids Research. 2003;31(1):298-303. And: Shafer RW. Rationale and Uses of a "
    "Public HIV Drug-Resistance Database. J Infect Dis. 2006;194 Suppl 1:S51-8."
)

# The consensus B RT sequence must begin with this. Asserted rather than trusted, because
# the page serves several proteins and picking the wrong block would be silent.
RT_PREFIX = "PISPIETVPVKLKPGMDGPKV"
RT_EXPECTED_LENGTH = 560


@dataclass
class Attempt:
    label: str
    url: str
    status: int | None = None
    content_type: str | None = None
    bytes_received: int = 0
    sha256: str | None = None
    outcome: str = "not attempted"
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "url": self.url,
            "status": self.status,
            "content_type": self.content_type,
            "bytes_received": self.bytes_received,
            "sha256": self.sha256,
            "outcome": self.outcome,
            "detail": self.detail,
        }

    def log(self) -> None:
        print(
            "{0} | status={1} | type={2} | bytes={3} | sha256={4} | {5}".format(
                self.url,
                self.status,
                self.content_type,
                self.bytes_received,
                (self.sha256 or "none")[:16],
                self.outcome,
            )
        )
        if self.detail:
            print("    " + self.detail[:300])
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


def looks_like_dataset(payload: bytes) -> tuple[bool, str]:
    """Is this a tab-delimited dataset, or a web page served under a .txt name?

    The same guard the Task A and M-MLV fetchers needed. A publisher or a proxy answering
    with HTML under a data URL is the ordinary case, and accepting it would put a web page
    in raw/ labelled as a phenotype dataset.
    """
    head = payload[:400].lstrip()
    lowered = head[:200].lower()
    if lowered.startswith(b"<!doctype") or lowered.startswith(b"<html") or b"<head" in lowered:
        return False, "body is HTML: " + repr(head[:80].decode("utf-8", "replace"))
    text = payload[:8192].decode("utf-8", "replace")
    first = text.splitlines()[0] if text.splitlines() else ""
    if first.count("\t") < 3:
        return False, "first line has fewer than 3 tabs: " + repr(first[:120])
    return True, str(first.count("\t") + 1) + " columns on the header line"


def release_date(page: bytes) -> str:
    text = re.sub(r"<[^>]+>", " ", page.decode("utf-8", "replace"))
    found = re.search(r"Last updated on\s*([0-9]{4}-[0-9]{1,2}-[0-9]{1,2})", text)
    return found.group(1) if found else "unknown"


def stated_counts(page: bytes) -> dict[str, str]:
    """The row and isolate counts the dataset page itself advertises.

    Recorded so the parse can be reconciled against the source's own claim rather than
    against the brief, whose figures are from an earlier release.
    """
    text = re.sub(r"<[^>]+>", " ", page.decode("utf-8", "replace"))
    text = re.sub(r"\s+", " ", text)
    out: dict[str, str] = {}
    for drug in ("NRTI", "NNRTI"):
        # Two occurrences per class, filtered then unfiltered, in page order.
        found = re.findall(
            r"\b" + drug + r"\b\s*(\d+)\s*phenotype results from\s*(\d+)\s*isolates", text
        )
        for index, (results, isolates) in enumerate(found[:2]):
            kind = "filtered" if index == 0 else "unfiltered"
            out[drug + "_" + kind] = results + " results from " + isolates + " isolates"
    return out


def extract_rt_consensus(page: bytes) -> str:
    """The consensus B RT sequence from the HIVDB consensus page.

    The page carries protease, RT and integrase. The RT block is located by its own
    header, and then the result is asserted against a known prefix and length, because
    silently taking the wrong block would misnumber every position in the task.
    """
    text = page.decode("utf-8", "replace")
    text = text.replace("&#062;", ">").replace("&gt;", ">")
    text = re.sub(r"<[^>]+>", "\n", text)
    blocks: dict[str, list[str]] = {}
    current = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(">"):
            current = stripped.lstrip(">").strip().lower()
            blocks[current] = []
            continue
        if current and re.fullmatch(r"[ACDEFGHIKLMNPQRSTVWYX]+", stripped):
            blocks[current].append(stripped)
    if "rt" not in blocks:
        raise SystemExit(
            "no RT block found on the consensus page; found " + str(sorted(blocks))
        )
    sequence = "".join(blocks["rt"])
    if not sequence.startswith(RT_PREFIX):
        raise SystemExit(
            "the RT block does not begin with the expected consensus B prefix. "
            "Expected " + RT_PREFIX + ", found " + sequence[: len(RT_PREFIX)]
        )
    if len(sequence) != RT_EXPECTED_LENGTH:
        raise SystemExit(
            "the RT consensus is "
            + str(len(sequence))
            + " residues, expected "
            + str(RT_EXPECTED_LENGTH)
            + ". Refusing to write a reference of unexpected length, because every "
            "position in this task is numbered against it"
        )
    return sequence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="probe, write nothing")
    args = parser.parse_args()

    print_run_header("data_acquisition/fetch_hivdb.py")
    print("source: Stanford HIV Drug Resistance Database, genotype-phenotype datasets")
    print("scope: NRTI and NNRTI only; PI, INI and CAI do not target reverse transcriptase")
    print("")

    attempts: list[Attempt] = []

    # The dataset page first, for the release date and the source's own counts.
    attempt = Attempt("dataset page", DATASET_PAGE)
    page = get(DATASET_PAGE, attempt)
    if page is None:
        attempt.outcome = attempt.outcome or "failed"
        attempt.log()
        attempts.append(attempt)
        raise SystemExit("could not read the dataset page, so the release cannot be pinned")
    release = release_date(page)
    counts = stated_counts(page)
    attempt.outcome = "release " + release
    attempt.detail = "; ".join(k + ": " + v for k, v in sorted(counts.items()))
    attempt.log()
    attempts.append(attempt)
    time.sleep(PAUSE_SECONDS)

    # The consensus reference.
    attempt = Attempt("consensus amino acid sequences", CONSENSUS_PAGE)
    consensus_page = get(CONSENSUS_PAGE, attempt)
    if consensus_page is None:
        attempt.log()
        attempts.append(attempt)
        raise SystemExit("could not read the consensus page; the reference is required")
    rt = extract_rt_consensus(consensus_page)
    attempt.outcome = "RT consensus extracted, " + str(len(rt)) + " residues"
    attempt.log()
    attempts.append(attempt)
    time.sleep(PAUSE_SECONDS)

    # The datasets.
    payloads: dict[str, bytes] = {}
    for name, description in FILES.items():
        url = DOWNLOAD + name
        attempt = Attempt(description, url)
        body = get(url, attempt)
        time.sleep(PAUSE_SECONDS)
        if body is None:
            attempt.log()
            attempts.append(attempt)
            continue
        ok, why = looks_like_dataset(body)
        if not ok:
            attempt.outcome = "rejected, not a tab-delimited dataset"
            attempt.detail = why
            attempt.log()
            attempts.append(attempt)
            continue
        attempt.outcome = "downloaded, " + why
        attempt.detail = str(len(body.splitlines())) + " lines"
        attempt.log()
        attempts.append(attempt)
        payloads[name] = body

    ATTEMPT_LOG.write_text(
        json.dumps(
            {
                "source": "Stanford HIVDB genotype-phenotype datasets",
                "release_date": release,
                "stated_counts": counts,
                "citation": CITATION,
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

    missing = [n for n in FILES if n not in payloads]
    if missing:
        print("")
        print("FAILED to obtain: " + ", ".join(missing))
        return 1

    if args.dry_run:
        print("")
        print("dry run: nothing written")
        return 0

    RAW.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Checksums for the Stanford HIVDB genotype-phenotype datasets",
        "#",
        "# Written by data_acquisition/fetch_hivdb.py. Each file is stored exactly as",
        "# served, byte for byte.",
        "#",
        "# source: " + DOWNLOAD,
        "# database release, as printed on the dataset page: " + release,
        "# access date: " + date.today().isoformat(),
        "# scope: NRTI and NNRTI only, the two reverse transcriptase drug classes",
        "#",
        "# counts the source page advertises for this release:",
    ]
    for key, value in sorted(counts.items()):
        lines.append("#   " + key + ": " + value)
    lines += ["", "filename\tsha256\tbytes\tlines\tsource_url\tdescription"]
    for name in FILES:
        payload = payloads[name]
        target = RAW / name
        target.write_bytes(payload)
        digest = hashlib.sha256(payload).hexdigest()
        lines.append(
            "\t".join(
                [
                    name,
                    digest,
                    str(len(payload)),
                    str(len(payload.splitlines())),
                    DOWNLOAD + name,
                    FILES[name],
                ]
            )
        )
        print("stored " + target.relative_to(REPO_ROOT).as_posix() + " sha256=" + digest[:16])
    CHECKSUMS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote " + CHECKSUMS.relative_to(REPO_ROOT).as_posix())

    REFERENCE.write_text(
        ">consensus_B_RT HIVDB_consensus_amino_acid_sequences positions_1_to_"
        + str(len(rt))
        + "\n"
        + "\n".join(rt[i : i + 60] for i in range(0, len(rt), 60))
        + "\n",
        encoding="utf-8",
    )
    print("wrote " + REFERENCE.relative_to(REPO_ROOT).as_posix() + ", " + str(len(rt)) + " residues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
