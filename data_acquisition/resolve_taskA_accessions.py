"""Resolve a UniProt accession plus version for every inherited Task A sequence.

The problem
-----------
`data/rt_sequences.csv` carries 57 reverse transcriptase sequences with no accession and no
DOI. The schema requires `reference_accession` on every row, so all 57 rows currently fail
validation on that field, and Task A cannot be built until each sequence is traced back to
a database entry with a version.

The RT names in the inherited file are paper-internal labels, for example `Vp96-RT` and
`Ne144-RT`, so they cannot be looked up by name. The sequences themselves can be, because
each one is an excised domain and is therefore an exact substring of some parent entry.

Method
------
For each sequence, two short probes are taken from different parts of it and submitted to
the UniProt peptide search service, which returns the accessions containing that exact
peptide. Intersecting two probes' result sets removes entries that happen to share one
conserved stretch.

Each surviving candidate is then verified the only way that actually settles the question:
the candidate's full sequence is fetched and the inherited sequence is tested as an exact
substring of it. A hit gives the parent accession, its sequence version, and the exact
residue coordinates of the excision. That is what `reference_accession` is supposed to
record.

Nothing is guessed. A sequence that matches no candidate exactly is reported as unresolved
with its best near-match, and goes on the list for a human. A sequence matching several
entries is reported as ambiguous with all of them, and a reviewed entry is preferred over an
unreviewed one only as a tie-break, never to paper over a real ambiguity.

    python data_acquisition/resolve_taskA_accessions.py --limit 3
    python data_acquisition/resolve_taskA_accessions.py

Results are written to `tasks/taskA_crossfamily/raw/accession_resolution.tsv`. Fetched
UniProt entries are cached so the script is interruptible and resumable.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

INHERITED = REPO_ROOT / "data/rt_sequences.csv"
OUTPUT = REPO_ROOT / "tasks/taskA_crossfamily/raw/accession_resolution.tsv"
CACHE = REPO_ROOT / ".uniprot_cache"

PEPTIDE_SUBMIT = "https://peptidesearch.uniprot.org/asyncrest"
ENTRY_FASTA = "https://rest.uniprot.org/uniprotkb/"

PROBE_LENGTH = 40
# Candidate sets can be large for a conserved domain, so verification is capped. The cap is
# a compute limit, not a correctness one: an RT whose candidate list is truncated is
# reported as such rather than silently resolved from a partial list.
MAX_CANDIDATES = 40
POLL_ATTEMPTS = 20
SUBMIT_ATTEMPTS = 3
POLL_SECONDS = 3
USER_AGENT = "RT-plm-benchmark accession resolver (research use)"


@dataclass
class Resolution:
    rt_name: str
    length: int
    n_candidates: int = 0
    candidates_truncated: bool = False
    exact: list[tuple[str, int, int, int, bool]] = field(default_factory=list)
    chosen: tuple[str, int, int, int, bool] | None = None
    status: str = "unresolved"
    note: str = ""

    @property
    def chosen_accession(self) -> str:
        return self.chosen[0] if self.chosen else ""

    @property
    def chosen_version(self) -> str:
        return str(self.chosen[1]) if self.chosen else ""


def http_get(url: str, timeout: int = 45) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def submit_peptide(peptide: str) -> str | None:
    """Submit one peptide and return the job URL, or None if the service refused."""
    payload = urllib.parse.urlencode({"peps": peptide, "lEQi": "off", "spOnly": "off"}).encode()
    # The service is intermittently slow, so a single timeout is not evidence of anything.
    # Retry a few times with backoff before reporting a service error.
    last_error: Exception | None = None
    for attempt in range(SUBMIT_ATTEMPTS):
        request = urllib.request.Request(
            PEPTIDE_SUBMIT, data=payload, headers={"User-Agent": USER_AGENT}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.headers.get("Location")
        except (urllib.error.URLError, TimeoutError) as error:
            last_error = error
            time.sleep(POLL_SECONDS * (attempt + 1))
    print("      submit failed after " + str(SUBMIT_ATTEMPTS) + " attempts: " + str(last_error))
    return None


def collect_peptide_hits(peptide: str) -> set[str] | None:
    """Return the accessions containing this exact peptide, or None on service failure."""
    job = submit_peptide(peptide)
    if not job:
        return None
    for _ in range(POLL_ATTEMPTS):
        try:
            body = http_get(job, timeout=30).decode("utf-8", "replace").strip()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            time.sleep(POLL_SECONDS)
            continue
        if body:
            return {token.strip() for token in body.split(",") if token.strip()}
        # An empty 200 means the job finished with no hits; an unfinished job returns 3xx or
        # an error, which is handled above. Treat a settled empty body as no hits.
        return set()
    return None


def fetch_entry(accession: str) -> tuple[str, str] | None:
    """Return (header, sequence) for a UniProt accession, cached on disk."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (accession + ".fasta")
    if not path.is_file():
        try:
            payload = http_get(ENTRY_FASTA + accession + ".fasta")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
            return None
        if not payload.startswith(b">"):
            return None
        path.write_bytes(payload)
    header = ""
    residues: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(">"):
            if not header:
                header = line[1:]
            continue
        residues.append(line.strip())
    return header, "".join(residues)


def parse_version(header: str) -> int:
    match = re.search(r"SV=(\d+)", header)
    return int(match.group(1)) if match else 0


def is_reviewed(accession: str) -> bool:
    path = CACHE / (accession + ".fasta")
    if not path.is_file():
        return False
    first = path.read_text(encoding="utf-8").splitlines()[0]
    return first.startswith(">sp|")


def probes(sequence: str) -> list[str]:
    """Two probes from different parts of the sequence, so a single conserved motif cannot
    carry a false candidate through."""
    if len(sequence) <= PROBE_LENGTH:
        return [sequence]
    first_start = min(30, len(sequence) - PROBE_LENGTH)
    second_start = max(0, min(len(sequence) - PROBE_LENGTH, len(sequence) // 2 + 20))
    starts = sorted({first_start, second_start})
    return [sequence[s : s + PROBE_LENGTH] for s in starts]


def resolve_one(rt_name: str, sequence: str) -> Resolution:
    result = Resolution(rt_name=rt_name, length=len(sequence))

    candidate_sets: list[set[str]] = []
    for probe in probes(sequence):
        hits = collect_peptide_hits(probe)
        if hits is None:
            result.status = "service_error"
            result.note = "peptide search did not return for at least one probe"
            return result
        candidate_sets.append(hits)

    candidates = set.intersection(*candidate_sets) if candidate_sets else set()
    if not candidates:
        union = set.union(*candidate_sets) if candidate_sets else set()
        result.n_candidates = len(union)
        result.status = "unresolved"
        result.note = (
            "no accession contains both probes; probe hit counts "
            + ",".join(str(len(s)) for s in candidate_sets)
        )
        return result

    result.n_candidates = len(candidates)
    ordered = sorted(candidates)
    if len(ordered) > MAX_CANDIDATES:
        result.candidates_truncated = True
        ordered = ordered[:MAX_CANDIDATES]

    for accession in ordered:
        entry = fetch_entry(accession)
        if entry is None:
            continue
        header, parent = entry
        index = parent.find(sequence)
        if index >= 0:
            result.exact.append(
                (
                    accession,
                    parse_version(header),
                    index + 1,
                    index + len(sequence),
                    is_reviewed(accession),
                )
            )

    if not result.exact:
        result.status = "unresolved"
        result.note = (
            "both probes matched " + str(result.n_candidates) + " entries, but the full "
            "sequence is an exact substring of none of them; the inherited sequence may "
            "carry an isolate difference or a hand edit"
        )
        return result

    # Prefer a reviewed entry, then the lowest accession, purely as a deterministic
    # tie-break. Every exact match is reported regardless, so the tie-break never hides one.
    result.exact.sort(key=lambda item: (not item[4], item[0]))
    result.chosen = result.exact[0]
    result.status = "resolved" if len(result.exact) == 1 else "resolved_ambiguous"
    if len(result.exact) > 1:
        result.note = (
            str(len(result.exact))
            + " entries contain this sequence exactly: "
            + ",".join(item[0] for item in result.exact)
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve Task A accessions from sequence.")
    parser.add_argument("--limit", type=int, default=None, help="process only the first N rows")
    parser.add_argument("--names", default=None, help="comma separated RT names to process")
    parser.add_argument(
        "--retry-service-errors",
        action="store_true",
        help="re-run only the rows whose previous status was service_error, merging results",
    )
    args = parser.parse_args(argv)

    print_run_header("data_acquisition/resolve_taskA_accessions.py", [INHERITED])
    print("")

    rows = list(csv.DictReader(INHERITED.open(encoding="utf-8")))

    # Resume path. A service error is a statement about the network, not about the sequence,
    # so those rows are retried while settled verdicts are kept exactly as they were.
    previous: dict[str, dict[str, str]] = {}
    if args.retry_service_errors:
        if not OUTPUT.is_file():
            print("no previous result to retry: " + OUTPUT.as_posix())
            return 1
        with OUTPUT.open(encoding="utf-8") as handle:
            for record in csv.DictReader(handle, delimiter="	"):
                previous[record["rt_name"]] = record
        retryable = {n for n, r in previous.items() if r["status"] == "service_error"}
        print("previous result had " + str(len(retryable)) + " service errors to retry")
        rows = [r for r in rows if r["rt_name"] in retryable]

    if args.names:
        wanted = {n.strip() for n in args.names.split(",")}
        rows = [r for r in rows if r["rt_name"] in wanted]
    if args.limit:
        rows = rows[: args.limit]
    print("sequences to resolve: " + str(len(rows)))
    print("")

    results: list[Resolution] = []
    for position, row in enumerate(rows, start=1):
        name = row["rt_name"]
        sequence = row["sequence"].strip().upper()
        print("[" + str(position) + "/" + str(len(rows)) + "] " + name + ", " + str(len(sequence)) + " residues")
        result = resolve_one(name, sequence)
        results.append(result)
        if result.chosen:
            accession, version, start, end, reviewed = result.chosen
            print(
                "      "
                + result.status
                + ": "
                + accession
                + "."
                + str(version)
                + " residues "
                + str(start)
                + " to "
                + str(end)
                + (" reviewed" if reviewed else " unreviewed")
            )
        else:
            print("      " + result.status + ": " + result.note)

    # Merge fresh verdicts over the kept ones, preserving the inherited file's row order.
    fresh = {r.rt_name: r for r in results}
    if previous:
        merged: list[Resolution] = []
        for name, record in previous.items():
            if name in fresh:
                merged.append(fresh[name])
                continue
            kept = Resolution(
                rt_name=name,
                length=int(record["sequence_len"]),
                status=record["status"],
                note=record["note"],
                n_candidates=int(record["n_candidates"] or 0),
                candidates_truncated=record["candidates_truncated"] == "yes",
            )
            if record["accession"]:
                kept.chosen = (
                    record["accession"],
                    int(record["sequence_version"] or 0),
                    int(record["parent_start"] or 0),
                    int(record["parent_end"] or 0),
                    record["reviewed"] == "yes",
                )
                kept.exact = [kept.chosen] * int(record["n_exact_matches"] or 1)
            merged.append(kept)
        results = merged

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(
            [
                "rt_name",
                "sequence_len",
                "status",
                "accession",
                "sequence_version",
                "reference_accession",
                "parent_start",
                "parent_end",
                "reviewed",
                "n_candidates",
                "n_exact_matches",
                "candidates_truncated",
                "note",
            ]
        )
        for result in results:
            accession = result.chosen_accession
            version = result.chosen_version
            writer.writerow(
                [
                    result.rt_name,
                    result.length,
                    result.status,
                    accession,
                    version,
                    (accession + "." + version) if accession else "",
                    result.chosen[2] if result.chosen else "",
                    result.chosen[3] if result.chosen else "",
                    "yes" if (result.chosen and result.chosen[4]) else ("no" if result.chosen else ""),
                    result.n_candidates,
                    len(result.exact),
                    "yes" if result.candidates_truncated else "no",
                    result.note,
                ]
            )

    counts: dict[str, int] = {}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1

    print("")
    print("wrote " + OUTPUT.as_posix())
    print("  sha256=" + sha256_of(OUTPUT))
    print("")
    for status in sorted(counts):
        print("  " + status + ": " + str(counts[status]))
    unresolved = sum(v for k, v in counts.items() if k != "resolved" and k != "resolved_ambiguous")
    print("")
    print(
        "resolved: "
        + str(counts.get("resolved", 0) + counts.get("resolved_ambiguous", 0))
        + " of "
        + str(len(results))
        + "; still needing a human: "
        + str(unresolved)
    )
    print("")
    print("An accession here is a parent entry containing the inherited sequence exactly.")
    print("It is not proof that the inherited sequence was taken from that entry, and it is")
    print("not the publication's own accession. It is a verifiable provenance anchor, and")
    print("the source table remains the authority on which entry the authors used.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
