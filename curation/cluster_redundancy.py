"""Identity clustering for redundancy control, within each task and across tasks.

Why this runs before any split is used
--------------------------------------
Family-level splitting alone does not prevent leakage once variant rows exist. Two variants
of the same protein are more than 99 percent identical, so a random split over Task B would
be close to meaningless. And a protein can appear in two tasks at once: M-MLV RT is a Task A
row at 677 residues and is also the parent of every Task B variant at 498 residues. Any
statement about generalization has to be made against a measured redundancy structure rather
than an assumed one.

Clustering parameters, fixed a priori
------------------------------------
Thresholds: 90, 70, and 50 percent sequence identity, as the brief specifies.

Coverage: ``--cov-mode 1 -c 0.8``, so coverage is measured over the target. This choice is
load bearing and is not the MMseqs2 default, so the reason is recorded here. These sequences
are excised domains with different boundaries: the Task A M-MLV RT row is 677 residues and
the Task B parent is the same protein truncated to 498. Their bidirectional coverage is
498/677, which is 0.74, so under the default bidirectional coverage at 0.8 they would not
cluster, and the single most important cross-task duplicate in this benchmark would go
unreported. Coverage over the target detects containment, which is what redundancy between
differently excised domains actually looks like.

Sensitivity: ``-s 7.5``, the high-sensitivity setting, because the panel is small enough
that speed is irrelevant and a missed homology here would understate leakage.

Nothing here is fitted and nothing is selected. Cluster assignments are a description of the
data, written once to a file and then frozen.

    python curation/cluster_redundancy.py --mmseqs <path to mmseqs binary>
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, read_task_table, sha256_of  # noqa: E402

IDENTITY_THRESHOLDS = (90, 70, 50)
COVERAGE = "0.8"
COVERAGE_MODE = "1"
SENSITIVITY = "7.5"

# Where each task's sequences come from. A curated.csv is the authority once it exists; the
# inherited file is a clearly flagged fallback so that Phase 3 can run on Task A before its
# accessions are resolved.
TASK_SOURCES: dict[str, tuple[Path, Path]] = {
    "A": (
        REPO_ROOT / "tasks/taskA_crossfamily/curated.csv",
        REPO_ROOT / "data/rt_sequences.csv",
    ),
    "A2": (REPO_ROOT / "tasks/taskA2_evolved/curated.csv", REPO_ROOT / "nonexistent"),
    "B": (REPO_ROOT / "tasks/taskB_mmlv_dms/curated.csv", REPO_ROOT / "nonexistent"),
}

TASK_DIR = {
    "A": REPO_ROOT / "tasks/taskA_crossfamily",
    "A2": REPO_ROOT / "tasks/taskA2_evolved",
    "B": REPO_ROOT / "tasks/taskB_mmlv_dms",
}

CROSS_TASK_DIR = REPO_ROOT / "reports"


def load_task(task: str) -> tuple[dict[str, str], str]:
    """Return {id: sequence} for a task, plus a note on which source was used."""
    curated, fallback = TASK_SOURCES[task]
    if curated.is_file():
        frame = read_task_table(curated)
        return (
            {str(r["id"]): str(r["sequence"]).strip().upper() for r in frame.to_dict("records")},
            "curated.csv",
        )
    if fallback.is_file():
        rows = list(csv.DictReader(fallback.open(encoding="utf-8")))
        # Identifiers are minted here the same way the Task A parser will mint them, so the
        # cluster files stay valid once curated.csv exists.
        return (
            {"A_" + r["rt_name"]: r["sequence"].strip().upper() for r in rows},
            "FALLBACK " + fallback.relative_to(REPO_ROOT).as_posix(),
        )
    return {}, "absent"


def write_fasta(path: Path, sequences: dict[str, str]) -> None:
    lines: list[str] = []
    for identifier, sequence in sequences.items():
        lines.append(">" + identifier)
        lines += [sequence[i : i + 60] for i in range(0, len(sequence), 60)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_mmseqs(binary: str, fasta: Path, threshold: int, workdir: Path) -> dict[str, str]:
    """Cluster one FASTA at one identity threshold. Returns {member: representative}."""
    # The Windows build runs under a compatibility layer that will not create a temporary
    # directory whose parents are absent, so both are made here rather than by mmseqs.
    workdir.mkdir(parents=True, exist_ok=True)
    prefix = workdir / ("clu" + str(threshold))
    tmp = workdir / ("tmp" + str(threshold))
    tmp.mkdir(parents=True, exist_ok=True)
    command = [
        binary,
        "easy-cluster",
        str(fasta),
        str(prefix),
        str(tmp),
        "--min-seq-id",
        str(threshold / 100),
        "-c",
        COVERAGE,
        "--cov-mode",
        COVERAGE_MODE,
        "-s",
        SENSITIVITY,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        raise RuntimeError("mmseqs easy-cluster failed at threshold " + str(threshold))
    table = Path(str(prefix) + "_cluster.tsv")
    if not table.is_file():
        raise RuntimeError("mmseqs produced no cluster table at threshold " + str(threshold))
    assignment: dict[str, str] = {}
    for line in table.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        representative, member = line.split("\t")[:2]
        assignment[member] = representative
    return assignment


def cluster_ids(assignment: dict[str, str]) -> dict[str, int]:
    """Give each representative a stable integer id, ordered by representative name."""
    representatives = sorted(set(assignment.values()))
    lookup = {rep: index + 1 for index, rep in enumerate(representatives)}
    return lookup


def write_clusters(path: Path, assignment: dict[str, str], task_of: dict[str, str] | None = None) -> None:
    lookup = cluster_ids(assignment)
    sizes = Counter(assignment.values())
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        header = ["id", "cluster_id", "cluster_representative", "cluster_size"]
        if task_of is not None:
            header.insert(1, "task")
        writer.writerow(header)
        for member in sorted(assignment):
            representative = assignment[member]
            row = [member, lookup[representative], representative, sizes[representative]]
            if task_of is not None:
                row.insert(1, task_of.get(member, "?"))
            writer.writerow(row)


def describe(assignment: dict[str, str]) -> str:
    sizes = Counter(assignment.values())
    distribution = Counter(sizes.values())
    parts = [str(size) + ":" + str(count) for size, count in sorted(distribution.items())]
    return (
        str(len(assignment))
        + " sequences, "
        + str(len(sizes))
        + " clusters, size:count "
        + " ".join(parts)
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Identity clustering for redundancy control.")
    parser.add_argument(
        "--mmseqs",
        default=os.environ.get("MMSEQS_BIN", "mmseqs"),
        help="path to the mmseqs binary, or set MMSEQS_BIN",
    )
    args = parser.parse_args(argv)

    binary = shutil.which(args.mmseqs) or args.mmseqs
    if not Path(binary).is_file() and shutil.which(binary) is None:
        print("mmseqs not found at " + str(args.mmseqs))
        print("Pass --mmseqs <path> or set MMSEQS_BIN.")
        return 1

    print_run_header("curation/cluster_redundancy.py")
    version = subprocess.run([binary, "version"], capture_output=True, text=True)
    print("mmseqs binary: " + binary)
    print("mmseqs version: " + version.stdout.strip())
    print(
        "parameters fixed a priori: thresholds "
        + ",".join(str(t) for t in IDENTITY_THRESHOLDS)
        + "; -c "
        + COVERAGE
        + " --cov-mode "
        + COVERAGE_MODE
        + " -s "
        + SENSITIVITY
    )
    print("")

    loaded: dict[str, dict[str, str]] = {}
    for task in TASK_SOURCES:
        sequences, note = load_task(task)
        print("task " + task + ": " + str(len(sequences)) + " sequences, source " + note)
        if sequences:
            loaded[task] = sequences
    if not loaded:
        print("no task has sequences yet; nothing to cluster")
        return 1

    with tempfile.TemporaryDirectory() as tmp:
        workdir = Path(tmp)

        for task, sequences in loaded.items():
            fasta = workdir / ("task_" + task + ".fasta")
            write_fasta(fasta, sequences)
            print("")
            print("=== task " + task + " ===")
            for threshold in IDENTITY_THRESHOLDS:
                assignment = run_mmseqs(binary, fasta, threshold, workdir / ("t" + task + str(threshold)))
                out = TASK_DIR[task] / "splits" / ("clusters_" + str(threshold) + ".tsv")
                write_clusters(out, assignment)
                print("  " + str(threshold) + "%: " + describe(assignment))
                print("        wrote " + out.relative_to(REPO_ROOT).as_posix() + " sha256=" + sha256_of(out))

        print("")
        print("=== across tasks ===")
        if len(loaded) < 2:
            print("only one task has sequences, so there is no cross-task comparison to make.")
            print("This is not a clean bill of health: Task B is blocked on its activity")
            print("values, and the M-MLV RT duplicate between Task A and the Task B parent")
            print("cannot be measured until Task B exists. Recorded as an open item.")
        else:
            combined: dict[str, str] = {}
            task_of: dict[str, str] = {}
            for task, sequences in loaded.items():
                for identifier, sequence in sequences.items():
                    combined[identifier] = sequence
                    task_of[identifier] = task
            fasta = workdir / "all_tasks.fasta"
            write_fasta(fasta, combined)
            for threshold in IDENTITY_THRESHOLDS:
                assignment = run_mmseqs(binary, fasta, threshold, workdir / ("x" + str(threshold)))
                out = CROSS_TASK_DIR / ("clusters_cross_task_" + str(threshold) + ".tsv")
                write_clusters(out, assignment, task_of=task_of)
                members = defaultdict(list)
                for member, representative in assignment.items():
                    members[representative].append(member)
                mixed = {
                    rep: ids
                    for rep, ids in members.items()
                    if len({task_of[i] for i in ids}) > 1
                }
                print("  " + str(threshold) + "%: " + describe(assignment))
                print("        wrote " + out.relative_to(REPO_ROOT).as_posix())
                print("        clusters spanning more than one task: " + str(len(mixed)))
                for rep, ids in sorted(mixed.items()):
                    tasks = sorted({task_of[i] for i in ids})
                    print("          " + rep + " spans " + ",".join(tasks) + ", " + str(len(ids)) + " members")

    print("")
    print("Cluster assignments are descriptive and frozen. No model, no fit, no selection.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
