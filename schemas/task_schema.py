"""Shared row schema for every per-task table in this benchmark, plus its validator.

Why this module exists
----------------------
Activity measurements in the reverse transcriptase literature are not commensurable.
Prime editing efficiency in HEK293T, retron msDNA production, DGR adenine mutagenesis
rate, and in vitro retroviral polymerase specific activity are four different physical
quantities in four different units, and assay type is almost perfectly confounded with
RT family. Merging them into one label column would turn a family-held-out split into an
assay-held-out split, and any model fitted on the result would be learning which
publication a sequence came from.

So there is no merged label column in this repository. Each assay is its own task with
its own label scale, its own split, and its own reported metric. This module is the
mechanism that enforces that: it defines the row schema every ``curated.csv`` must
satisfy, and it refuses to concatenate two tables whose labels are measured in different
units.

The validator is deliberately strict and never repairs. A row that does not satisfy the
schema is reported as a violation for a human to resolve, and is not coerced, filled, or
dropped.
"""

from __future__ import annotations

import argparse
import hashlib
import platform
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# The single shared seed for the whole pipeline. Anything stochastic imports this rather
# than declaring its own, so that one number reproduces every run.
GLOBAL_SEED = 1729

AA20 = "ACDEFGHIKLMNPQRSTVWY"

# Tokens that are read as "no value recorded". Missing stays missing; nothing downstream
# is permitted to fill one of these in.
NULL_TOKENS = frozenset({"", "na", "n/a", "nan", "none", "null"})

CORE_COLUMNS: tuple[str, ...] = (
    "id",
    "task",
    "sequence",
    "sequence_len",
    "family",
    "parent_id",
    "mutations",
    "label_value",
    "label_units",
    "label_assay",
    "label_is_binary",
    "label_binary",
    "source_doi",
    "source_table",
    "reference_accession",
    "notes",
)

# Every task identifier the schema recognises. A table declaring anything else is
# rejected, because a new task needs a deliberate edit here and a note in its own
# PROVENANCE.md, not an ad hoc string in a CSV.
TASKS: tuple[str, ...] = ("A", "B", "C_retron", "C_dgr", "C_retroviral")

# Row identifiers carry their task, so that a stray row cannot be mistaken for one
# belonging to another table once the file is out of its directory.
ID_PREFIX: dict[str, str] = {
    "A": "A_",
    "B": "B_",
    "C_retron": "Cretron_",
    "C_dgr": "Cdgr_",
    "C_retroviral": "Crv_",
}

# Controlled vocabulary for label_assay. The point of a closed vocabulary is that an
# assay cannot be renamed into compatibility with another one by accident.
ASSAY_VOCABULARY: dict[str, str] = {
    "prime_editing_pct_HEK293T": (
        "Percent precise prime editing at a defined genomic locus in HEK293T, read out "
        "by amplicon sequencing."
    ),
    "prime_editing_normalized_wt_centred": (
        "Prime editing efficiency rescaled so that the wild-type parent is zero, in the "
        "normalization the source publication defines."
    ),
    "retron_msdna_production": "msDNA yield attributable to a retron reverse transcriptase.",
    "retron_recombineering_efficiency": (
        "Recombineering or editing efficiency in a retron-based donor system."
    ),
    "dgr_mutagenic_homing": "Mutagenic homing or retrohoming frequency of a DGR cassette.",
    "dgr_adenine_mutagenesis_rate": "Adenine-specific mutagenesis rate in a DGR variable region.",
    "retroviral_invitro_specific_activity": (
        "In vitro polymerase specific activity, for example nmol dNTP incorporated per "
        "mg of protein per unit time."
    ),
    "retroviral_invitro_processivity": "In vitro processivity of a retroviral reverse transcriptase.",
    "retroviral_invitro_fidelity": "In vitro misincorporation or fidelity measurement.",
}

# Which assays may legitimately appear in which task table. This is the structural guard
# against the failure the whole design exists to prevent: a retron msDNA number arriving
# in the prime editing task.
ASSAY_BY_TASK: dict[str, frozenset[str]] = {
    "A": frozenset({"prime_editing_pct_HEK293T"}),
    "B": frozenset({"prime_editing_normalized_wt_centred"}),
    "C_retron": frozenset({"retron_msdna_production", "retron_recombineering_efficiency"}),
    "C_dgr": frozenset({"dgr_mutagenic_homing", "dgr_adenine_mutagenesis_rate"}),
    "C_retroviral": frozenset(
        {
            "retroviral_invitro_specific_activity",
            "retroviral_invitro_processivity",
            "retroviral_invitro_fidelity",
        }
    ),
}

# Columns beyond the core schema that a given task is allowed to carry. Undeclared extra
# columns are a violation: a column that matters enough to compute is a column that
# matters enough to declare here.
EXTRA_COLUMNS_BY_TASK: dict[str, tuple[str, ...]] = {
    "A": (),
    # The two M-MLV RT sub-libraries were screened separately, so anything downstream
    # that handles batch structure or defines a stretch-held-out split needs this.
    "B": ("library_stretch",),
    "C_retron": (),
    "C_dgr": (),
    "C_retroviral": (),
}

_MUTATION_RE = re.compile("^([" + AA20 + "])([0-9]+)([" + AA20 + "])$")
_SEQUENCE_RE = re.compile("^[" + AA20 + "X]+$")
_BOOL_TRUE = frozenset({"true", "1", "yes"})
_BOOL_FALSE = frozenset({"false", "0", "no"})


class SchemaViolation(Exception):
    """Raised when a table, or an operation on tables, breaks the schema contract."""


@dataclass(frozen=True)
class Violation:
    rule: str
    detail: str
    row: int | None = None
    column: str | None = None

    def __str__(self) -> str:
        where = "table" if self.row is None else "row " + str(self.row)
        if self.column:
            where = where + ", column " + self.column
        return "[" + self.rule + "] " + where + ": " + self.detail


@dataclass
class ValidationReport:
    source: str
    task: str | None
    n_rows: int
    violations: list[Violation] = field(default_factory=list)
    warnings: list[Violation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.violations

    def raise_if_failed(self) -> ValidationReport:
        if self.violations:
            lines = "\n".join("  " + str(v) for v in self.violations)
            raise SchemaViolation(
                self.source
                + ": "
                + str(len(self.violations))
                + " schema violation(s)\n"
                + lines
            )
        return self

    def render(self) -> str:
        head = (
            self.source
            + ": task="
            + str(self.task)
            + " rows="
            + str(self.n_rows)
            + " violations="
            + str(len(self.violations))
            + " warnings="
            + str(len(self.warnings))
        )
        body = ["  VIOLATION " + str(v) for v in self.violations]
        body += ["  warning   " + str(w) for w in self.warnings]
        return "\n".join([head] + body)


def is_null(value: object) -> bool:
    """True when a cell records no value. Distinguishes absence from the string '0'."""
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return str(value).strip().lower() in NULL_TOKENS


def _as_bool(value: object) -> bool | None:
    token = str(value).strip().lower()
    if token in _BOOL_TRUE:
        return True
    if token in _BOOL_FALSE:
        return False
    return None


def read_task_table(path: str | Path) -> pd.DataFrame:
    """Read a curated.csv with every column as text.

    Reading as text is deliberate. Pandas type inference would silently turn an empty
    label into NaN and a mutation list into a float, and the validator needs to see what
    the file actually says.
    """
    return pd.read_csv(path, dtype=str, keep_default_na=False, na_filter=False)


def sha256_of(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def library_versions() -> dict[str, str]:
    versions = {"python": platform.python_version(), "pandas": pd.__version__}
    for name in ("numpy", "Bio", "torch", "sklearn", "scipy"):
        try:
            module = __import__(name)
        except ImportError:
            versions[name] = "absent"
        else:
            versions[name] = getattr(module, "__version__", "unknown")
    return versions


def print_run_header(script: str, inputs: list[str | Path] | None = None) -> None:
    """Emit the provenance header every script in this pipeline is required to print."""
    print("script: " + script)
    print("seed: " + str(GLOBAL_SEED))
    print("platform: " + platform.platform())
    for name, version in library_versions().items():
        print("version " + name + ": " + version)
    for item in inputs or []:
        path = Path(item)
        if path.exists():
            print("input " + path.as_posix() + " sha256=" + sha256_of(path))
        else:
            print("input " + path.as_posix() + " sha256=ABSENT")
    sys.stdout.flush()


def _validate_columns(df: pd.DataFrame, task: str | None, report: ValidationReport) -> None:
    missing = [c for c in CORE_COLUMNS if c not in df.columns]
    if missing:
        report.violations.append(
            Violation("columns.missing", "core columns absent: " + str(missing))
        )
    declared = set(CORE_COLUMNS)
    if task is not None:
        declared |= set(EXTRA_COLUMNS_BY_TASK.get(task, ()))
    undeclared = [c for c in df.columns if c not in declared]
    if undeclared:
        report.violations.append(
            Violation(
                "columns.undeclared",
                "columns not declared for this task: "
                + str(undeclared)
                + "; add them to EXTRA_COLUMNS_BY_TASK in schemas/task_schema.py if "
                "they are intended",
            )
        )


def _validate_task_column(df: pd.DataFrame, report: ValidationReport) -> str | None:
    if "task" not in df.columns:
        return None
    present = sorted({str(v).strip() for v in df["task"]})
    unknown = [t for t in present if t not in TASKS]
    if unknown:
        report.violations.append(
            Violation("task.unknown", "task values not in " + str(list(TASKS)) + ": " + str(unknown))
        )
    if len(present) > 1:
        report.violations.append(
            Violation(
                "task.mixed",
                "one table must hold exactly one task, found "
                + str(present)
                + "; this is the merged-label failure the schema exists to prevent",
            )
        )
        return None
    return present[0] if present else None


def _validate_units(df: pd.DataFrame, report: ValidationReport) -> None:
    if "label_units" not in df.columns:
        return
    units = sorted({str(v).strip() for v in df["label_units"]})
    if len(units) > 1:
        report.violations.append(
            Violation(
                "label_units.inconsistent",
                "all rows in a task must share one label_units, found " + str(units),
            )
        )


def _validate_rows(df: pd.DataFrame, task: str | None, report: ValidationReport) -> None:
    ids: set[str] = set()
    sequences: dict[str, int] = {}
    known_ids = set(df["id"]) if "id" in df.columns else set()
    allowed_assays = ASSAY_BY_TASK.get(task or "", None)
    prefix = ID_PREFIX.get(task or "", None)

    for position, row in enumerate(df.to_dict("records"), start=1):

        def add(rule: str, detail: str, column: str | None = None, _p: int = position) -> None:
            report.violations.append(Violation(rule, detail, row=_p, column=column))

        row_id = str(row.get("id", "")).strip()
        if is_null(row_id):
            add("id.null", "every row needs a stable identifier", "id")
        else:
            if row_id in ids:
                add("id.duplicate", "identifier " + repr(row_id) + " appears more than once", "id")
            ids.add(row_id)
            if prefix and not row_id.startswith(prefix):
                add("id.prefix", "identifier " + repr(row_id) + " must start with " + repr(prefix), "id")

        sequence = str(row.get("sequence", "")).strip()
        if is_null(sequence):
            add("sequence.null", "sequence is required", "sequence")
        else:
            if sequence != sequence.upper():
                add("sequence.case", "sequence must be uppercase", "sequence")
            if not _SEQUENCE_RE.match(sequence):
                bad = sorted(set(sequence) - set(AA20 + "X"))
                add("sequence.alphabet", "illegal residue symbols " + str(bad), "sequence")
            if "X" in sequence:
                report.warnings.append(
                    Violation(
                        "sequence.unknown_residue",
                        "sequence contains X, an unresolved residue",
                        row=position,
                        column="sequence",
                    )
                )
            if sequence in sequences:
                add(
                    "sequence.duplicate",
                    "sequence identical to row "
                    + str(sequences[sequence])
                    + "; a duplicate sequence carrying two labels is an unresolved "
                    "conflict, not two rows",
                    "sequence",
                )
            else:
                sequences[sequence] = position

            declared_len = str(row.get("sequence_len", "")).strip()
            if not declared_len.isdigit():
                add("sequence_len.type", "expected an integer, found " + repr(declared_len), "sequence_len")
            elif int(declared_len) != len(sequence):
                add(
                    "sequence_len.mismatch",
                    "declared " + declared_len + ", sequence is " + str(len(sequence)) + " residues",
                    "sequence_len",
                )

        if is_null(row.get("family")):
            add("family.null", "family or parent protein is required", "family")

        mutations = str(row.get("mutations", "")).strip()
        parent_id = str(row.get("parent_id", "")).strip()
        if is_null(mutations):
            if not is_null(parent_id):
                add(
                    "parent_id.unexpected",
                    "a row with no mutations is a wild type and must not name a parent",
                    "parent_id",
                )
        else:
            for token in mutations.split(";"):
                token = token.strip()
                if not _MUTATION_RE.match(token):
                    add(
                        "mutations.format",
                        repr(token) + " is not of the form wild-type residue, position, new residue",
                        "mutations",
                    )
            if is_null(parent_id):
                add("parent_id.null", "a variant row must name its wild-type row", "parent_id")
            elif parent_id not in known_ids:
                add("parent_id.dangling", "parent " + repr(parent_id) + " is not an id in this table", "parent_id")

        label_value = str(row.get("label_value", "")).strip()
        if is_null(label_value):
            add(
                "label_value.null",
                "a curated task row carries a measured value; an unmeasured enzyme does "
                "not belong in a task table and must never be imputed",
                "label_value",
            )
        else:
            try:
                float(label_value)
            except ValueError:
                add("label_value.type", "not a number: " + repr(label_value), "label_value")

        if is_null(row.get("label_units")):
            add("label_units.null", "label_units is required", "label_units")

        assay = str(row.get("label_assay", "")).strip()
        if assay not in ASSAY_VOCABULARY:
            add(
                "label_assay.vocabulary",
                repr(assay)
                + " is not in the controlled vocabulary; add it to ASSAY_VOCABULARY "
                "with a definition if it is a genuinely new assay",
                "label_assay",
            )
        elif allowed_assays is not None and assay not in allowed_assays:
            add(
                "label_assay.wrong_task",
                repr(assay)
                + " is not an assay of task "
                + str(task)
                + "; allowed: "
                + str(sorted(allowed_assays)),
                "label_assay",
            )

        is_binary = _as_bool(row.get("label_is_binary"))
        binary = str(row.get("label_binary", "")).strip()
        if is_binary is None:
            add(
                "label_is_binary.type",
                "expected a boolean, found " + repr(row.get("label_is_binary")),
                "label_is_binary",
            )
        elif is_binary:
            if is_null(binary):
                add("label_binary.null", "label_is_binary is true, so a call is required", "label_binary")
            elif _as_bool(binary) is None:
                add("label_binary.type", "not an active or inactive call: " + repr(binary), "label_binary")
        else:
            if not is_null(binary):
                add(
                    "label_binary.unexpected",
                    "label_is_binary is false, so label_binary must be empty",
                    "label_binary",
                )

        if is_null(row.get("source_doi")):
            add("source_doi.null", "every row must cite the publication it came from", "source_doi")
        if is_null(row.get("source_table")):
            add("source_table.null", "every row must name the table or figure it came from", "source_table")
        if is_null(row.get("reference_accession")):
            add(
                "reference_accession.null",
                "every row must name the accession plus version of its parent sequence",
                "reference_accession",
            )


def validate_task_table(
    df: pd.DataFrame, task: str | None = None, source: str = "<in memory>"
) -> ValidationReport:
    """Validate one task table. Returns a report; call ``raise_if_failed`` to enforce."""
    report = ValidationReport(source=source, task=task, n_rows=len(df))
    if len(df) == 0:
        report.violations.append(Violation("table.empty", "table has no rows"))
        return report
    observed = _validate_task_column(df, report)
    if task is None:
        report.task = observed
        task = observed
    elif observed is not None and observed != task:
        report.violations.append(
            Violation("task.mismatch", "expected task " + str(task) + ", table declares " + str(observed))
        )
    _validate_columns(df, task, report)
    _validate_units(df, report)
    if all(c in df.columns for c in ("id", "sequence")):
        _validate_rows(df, task, report)
    return report


def validate_file(path: str | Path, task: str | None = None) -> ValidationReport:
    path = Path(path)
    return validate_task_table(read_task_table(path), task=task, source=path.as_posix())


def assert_concatenable(frames: list[pd.DataFrame], names: list[str] | None = None) -> None:
    """Refuse a concatenation that would produce a merged label column.

    Two tables may only be stacked when they agree on task, label_units, and label_assay.
    Anything else is the forbidden merge: it produces a column whose values mean different
    physical things in different rows, and a family-held-out split over such a column is
    silently an assay-held-out split.
    """
    names = names or ["frame[" + str(i) + "]" for i in range(len(frames))]
    if len(frames) != len(names):
        raise SchemaViolation("assert_concatenable: one name is required per frame")
    seen: dict[str, set[tuple[str, ...]]] = {}
    for name, frame in zip(names, frames):
        for column in ("task", "label_units", "label_assay"):
            if column not in frame.columns:
                raise SchemaViolation(name + ": column " + repr(column) + " absent, cannot be checked")
            values = tuple(sorted({str(v).strip() for v in frame[column]}))
            seen.setdefault(column, set()).add(values)
    for column, value_sets in seen.items():
        if len(value_sets) > 1:
            raise SchemaViolation(
                "refusing to concatenate: "
                + column
                + " differs across tables ("
                + str(sorted(value_sets))
                + "). Labels are never merged across assays in this repository. If you "
                "need rows from two tasks side by side, join them inside explicitly "
                "labelled representation-analysis code and keep the label columns separate."
            )


def safe_concat(frames: list[pd.DataFrame], names: list[str] | None = None) -> pd.DataFrame:
    """Concatenate task tables only when the schema permits it."""
    assert_concatenable(frames, names)
    return pd.concat(frames, ignore_index=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate curated task tables.")
    parser.add_argument("paths", nargs="+", help="one or more curated.csv files")
    parser.add_argument("--task", default=None, help="expected task identifier")
    args = parser.parse_args(argv)

    print_run_header("schemas/task_schema.py", list(args.paths))
    failed = 0
    for path in args.paths:
        if not Path(path).exists():
            print(path + ": ABSENT, nothing to validate")
            failed += 1
            continue
        report = validate_file(path, task=args.task)
        print(report.render())
        failed += 0 if report.ok else 1
    print("tables checked: " + str(len(args.paths)) + ", failing: " + str(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
