"""Reconstruct HIV-1 RT sequences from the HIVDB datasets, and halt rather than adapt.

Two outputs, deliberately separated:

  `curated_isolates.csv`  one row per isolate: the reconstructed sequence and metadata
  `curated.csv`           one row per isolate-drug measurement: the label, joined by id

The separation is not tidiness. Each isolate carries up to six NRTI or five NNRTI
measurements, so a single flat table would repeat a 560-residue sequence six times and,
worse, would invite a split that separates an isolate's own rows. Keeping the sequence in
an isolate table makes the isolate the unit of grouping structurally rather than by
convention.

The wild-type assertion
-----------------------
`CompMutList` states a wild-type residue for every mutation, for example `K65R`. Every one
of those is asserted against the consensus B reference, and the parser **halts on the
first mismatch**. On a mismatch it reports the first ten, tests whether one constant offset
resolves all of them, states that offset as a finding, and stops without applying it.

The cross-check
---------------
The filtered datasets carry position columns for only part of RT, 240 positions for NRTI
and 318 for NNRTI, while `CompMutList` covers the whole 560. So the reconstruction uses
the position columns where they exist and `CompMutList` beyond them, and **the two are
cross-checked against each other wherever both speak**. A disagreement there would mean one
of the two encodings is being misread, which is exactly the kind of error that produces a
plausible wrong answer.

Ambiguity rules, stated once and applied uniformly
--------------------------------------------------
Every position cell falls into exactly one category, and every category is counted:

  `-`            the consensus residue from the reference
  a letter       that residue
  `.`            not sequenced          -> `X`
  two or more    a mixture              -> `X`, never coerced to one residue
  `~`            a deletion             -> `X`
  `*`            a stop codon           -> `X`
  `#`            an insertion           -> `X`
  beyond range   not reported by this file; taken from `CompMutList`, else the reference

`X` means "not a determinate single residue". It is not a residue and it is not a guess;
the per-category counts are reported so no reader has to infer what an `X` stands for.

    python data_acquisition/parse_hivdb.py
    python data_acquisition/parse_hivdb.py --check-reference-only

Outputs:
    tasks/taskB_hivrt/curated_isolates.csv
    tasks/taskB_hivrt/curated.csv
    tasks/taskB_hivrt/parse_report.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

TASK_DIR = REPO_ROOT / "tasks" / "taskB_hivrt"
RAW = TASK_DIR / "raw"
REFERENCE = TASK_DIR / "reference.fasta"
CURATED = TASK_DIR / "curated.csv"
ISOLATES = TASK_DIR / "curated_isolates.csv"
REPORT = TASK_DIR / "parse_report.json"

SOURCE = "Stanford HIV Drug Resistance Database, genotype-phenotype datasets"
# Per-row provenance as a short token. The full citation lives in PROVENANCE.md and in
# parse_report.json; repeating a 60-character string on 57375 rows would add several
# megabytes of identical text to a file people have to open.
SOURCE_TOKEN = "HIVDB"
CITATION_SHORT = "Rhee 2003 NAR 31(1):298-303; Shafer 2006 JID 194 Suppl 1:S51-8"
REFERENCE_NAME = "HIVDB consensus B RT, positions 1 to 560"

DRUGS = {
    "NRTI": ("3TC", "ABC", "AZT", "D4T", "DDI", "TDF"),
    "NNRTI": ("EFV", "NVP", "ETR", "RPV", "DOR"),
}
DATASETS = {
    ("NRTI", "filtered"): "NRTI_DataSet.txt",
    ("NRTI", "unfiltered"): "NRTI_DataSet.Full.txt",
    ("NNRTI", "filtered"): "NNRTI_DataSet.txt",
    ("NNRTI", "unfiltered"): "NNRTI_DataSet.Full.txt",
}
# Counts the source page advertises for release 2026-04-22, asserted rather than assumed.
ADVERTISED = {
    ("NRTI", "filtered"): (10666, 1867),
    ("NRTI", "unfiltered"): (29505, 5369),
    ("NNRTI", "filtered"): (5659, 2272),
    ("NNRTI", "unfiltered"): (11545, 4913),
}

STANDARD_AA = set("ACDEFGHIKLMNPQRSTVWY")
UNKNOWN = "X"
NULL_TOKENS = {"", "NA", "NULL", "ND", "."}


def load_reference() -> str:
    lines = REFERENCE.read_text(encoding="utf-8").splitlines()
    sequence = "".join(l.strip() for l in lines if l and not l.startswith(">")).upper()
    if not sequence:
        raise SystemExit("reference.fasta is empty; run data_acquisition/fetch_hivdb.py")
    return sequence


def normalise_token(token: str) -> tuple[str, str] | None:
    """Return (normalised token, category), or None if it carries no mutation.

    Three formatting artefacts appear in the source and are repaired explicitly rather
    than discarded: an internal space as in `R211 K`, a trailing period as in `K102K.`,
    and the literal `NULL`. Insertions use a `_` as in `T69S_SG`, which is kept as its own
    category because the inserted residues cannot be placed in a fixed-length alignment.
    """
    raw = token.strip()
    if not raw or raw.upper() in {"NULL", "NA", "NONE"}:
        return None
    cleaned = raw.replace(" ", "").rstrip(".")
    if "_" in cleaned:
        return cleaned, "insertion"
    if re.fullmatch(r"[A-Z]\d+[A-Za-z*~#]+", cleaned):
        return cleaned, "substitution"
    return cleaned, "unparsed"


def parse_mutations(field: str) -> tuple[list[tuple[str, int, str]], Counter, list[str]]:
    """Mutations as (wild-type, position, mutant), plus category counts and oddities."""
    out: list[tuple[str, int, str]] = []
    categories: Counter = Counter()
    unparsed: list[str] = []
    for token in (field or "").split(","):
        result = normalise_token(token)
        if result is None:
            categories["null_token"] += 1
            continue
        cleaned, category = result
        categories[category] += 1
        if category == "unparsed":
            unparsed.append(cleaned)
            continue
        base = cleaned.split("_")[0] if category == "insertion" else cleaned
        found = re.fullmatch(r"([A-Z])(\d+)([A-Za-z*~#]+)", base)
        if not found:
            categories["unparsed"] += 1
            unparsed.append(cleaned)
            continue
        out.append((found.group(1), int(found.group(2)), found.group(3)))
    return out, categories, unparsed


def candidate_offset(reference: str, stated: list[tuple[str, int, str]]) -> int | None:
    """Does one constant offset resolve every mismatch? Reported, never applied."""
    for offset in range(-10, 11):
        if offset == 0:
            continue
        ok = True
        for wild, position, _ in stated:
            index = position + offset - 1
            if not (0 <= index < len(reference)) or reference[index] != wild:
                ok = False
                break
        if ok:
            return offset
    return None


def halt_on_mismatch(reference: str, mismatches: list[tuple], stated: list) -> None:
    print("")
    print("WILD-TYPE RESIDUE ASSERTION FAILED on " + str(len(mismatches)) + " mutation(s).")
    print("The numbering convention does not match the reference, so every reconstructed")
    print("sequence would be silently wrong. Halting without applying any correction.")
    print("")
    for isolate, token, wild, position, found in mismatches[:10]:
        print(
            "  isolate "
            + str(isolate)
            + ": "
            + token
            + " states "
            + wild
            + " at position "
            + str(position)
            + ", reference has "
            + found
        )
    if len(mismatches) > 10:
        print("  ... and " + str(len(mismatches) - 10) + " more")
    offset = candidate_offset(reference, stated)
    print("")
    if offset is None:
        print("No single constant offset in the range -10 to +10 resolves all of them.")
        print("That rules out a simple frame shift and points at a different reference.")
    else:
        print("A constant offset of " + format(offset, "+d") + " would resolve every stated residue.")
        print("Reported as a finding for a human ruling. **Not applied.**")
    raise SystemExit(
        "halted on a wild-type residue mismatch; the reference must be ruled on before "
        "any sequence is reconstructed"
    )


def reconstruct(
    row: dict, reference: str, position_columns: list[str], mutations: list[tuple[str, int, str]]
) -> tuple[str, Counter, list[str]]:
    """One isolate's sequence, with every ambiguity category counted."""
    residues = list(reference)
    categories: Counter = Counter()
    conflicts: list[str] = []
    covered = len(position_columns)

    for index, column in enumerate(position_columns):
        value = (row.get(column) or "").strip()
        position = index + 1
        if value == "-":
            categories["consensus"] += 1
            continue
        if value == "":
            categories["empty_cell"] += 1
            residues[position - 1] = UNKNOWN
            continue
        if value == ".":
            categories["not_sequenced"] += 1
            residues[position - 1] = UNKNOWN
            continue
        if value == "~":
            categories["deletion"] += 1
            residues[position - 1] = UNKNOWN
            continue
        if value == "*":
            categories["stop_codon"] += 1
            residues[position - 1] = UNKNOWN
            continue
        if value == "#":
            categories["insertion"] += 1
            residues[position - 1] = UNKNOWN
            continue
        if value == UNKNOWN:
            # The source's own ambiguity code for an unresolved residue. Distinct from a
            # mixture, which names candidate residues, and from a position that was not
            # sequenced at all.
            categories["source_ambiguous_X"] += 1
            residues[position - 1] = UNKNOWN
            continue
        if len(value) > 1:
            categories["mixture"] += 1
            residues[position - 1] = UNKNOWN
            continue
        if value in STANDARD_AA:
            categories["substitution"] += 1
            residues[position - 1] = value
            continue
        categories["unrecognised_cell"] += 1
        residues[position - 1] = UNKNOWN

    # Beyond the position columns this file does not report, so CompMutList is the only
    # source. Within them, the two must agree; a disagreement is recorded, not smoothed.
    for wild, position, mutant in mutations:
        if not (1 <= position <= len(reference)):
            categories["mutation_out_of_range"] += 1
            continue
        determinate = len(mutant) == 1 and mutant in STANDARD_AA
        if position <= covered:
            cell = (row.get(position_columns[position - 1]) or "").strip()
            expected = mutant if determinate else None
            if cell == "-" :
                conflicts.append(
                    str(row.get("SeqID"))
                    + ": "
                    + wild
                    + str(position)
                    + mutant
                    + " listed in CompMutList but position column says consensus"
                )
            elif expected is not None and cell != expected and len(cell) == 1:
                conflicts.append(
                    str(row.get("SeqID"))
                    + ": "
                    + wild
                    + str(position)
                    + mutant
                    + " against position column "
                    + cell
                )
            continue
        categories["beyond_position_columns"] += 1
        residues[position - 1] = mutant if determinate else UNKNOWN
    return "".join(residues), categories, conflicts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-reference-only",
        action="store_true",
        help="assert the wild-type residues and stop, writing nothing",
    )
    args = parser.parse_args()

    inputs = [REFERENCE] + [RAW / name for name in DATASETS.values()]
    print_run_header("data_acquisition/parse_hivdb.py", inputs)
    reference = load_reference()
    print("reference: " + REFERENCE_NAME + ", " + str(len(reference)) + " residues")
    print("")

    report: dict = {
        "source": SOURCE,
        "citation": CITATION_SHORT,
        "reference": REFERENCE_NAME,
        "reference_sha256": sha256_of(REFERENCE),
        "reference_length": len(reference),
        "datasets": {},
        "ambiguity_rules": {
            "-": "the consensus residue from the reference",
            "letter": "that residue",
            ".": "not sequenced, encoded as X",
            "two or more letters": "a mixture, encoded as X, never coerced to one residue",
            "~": "a deletion, encoded as X",
            "*": "a stop codon, encoded as X",
            "#": "an insertion, encoded as X",
            "X": "the source's own ambiguity code for an unresolved residue, kept as X",
            "beyond the position columns": "taken from CompMutList, else the reference",
        },
    }

    isolate_rows: list[dict] = []
    label_rows: list[dict] = []
    all_stated: list[tuple[str, int, str]] = []
    all_mismatches: list[tuple] = []

    for (drug_class, variant), filename in DATASETS.items():
        path = RAW / filename
        if not path.is_file():
            raise SystemExit("missing input " + path.as_posix())
        with path.open(encoding="utf-8", errors="replace") as handle:
            rows = list(csv.DictReader(handle, delimiter="\t"))
        position_columns = [c for c in rows[0] if re.fullmatch(r"P\d+", c)]
        position_columns.sort(key=lambda c: int(c[1:]))
        drugs = DRUGS[drug_class]

        categories: Counter = Counter()
        token_categories: Counter = Counter()
        conflicts: list[str] = []
        unparsed_tokens: Counter = Counter()
        results = 0
        na_cells = 0
        mutation_counts: list[int] = []

        for row in rows:
            mutations, token_cats, unparsed = parse_mutations(row.get("CompMutList", ""))
            token_categories.update(token_cats)
            unparsed_tokens.update(unparsed)
            for wild, position, mutant in mutations:
                all_stated.append((wild, position, mutant))
                if 1 <= position <= len(reference) and reference[position - 1] != wild:
                    all_mismatches.append(
                        (row.get("SeqID"), wild + str(position) + mutant, wild, position,
                         reference[position - 1])
                    )
            sequence, cats, row_conflicts = reconstruct(
                row, reference, position_columns, mutations
            )
            categories.update(cats)
            conflicts.extend(row_conflicts)
            mutation_counts.append(len(mutations))

            isolate_id = str(row.get("SeqID", "")).strip()
            isolate_rows.append(
                {
                    "isolate_id": isolate_id,
                    "drug_class": drug_class,
                    "dataset": variant,
                    "sequence": sequence,
                    "sequence_len": str(len(sequence)),
                    "n_unknown_positions": str(sequence.count(UNKNOWN)),
                    "n_mutations": str(len(mutations)),
                    "mutations": ";".join(w + str(p) + m for w, p, m in mutations),
                    "position_columns_reported": str(len(position_columns)),
                    "ptid": str(row.get("PtID", "") or ""),
                    "subtype": str(row.get("Subtype", "") or ""),
                    "method": str(row.get("Method", "") or ""),
                    "isolate_type": str(row.get("Type", "") or ""),
                    "seq_type": str(row.get("SeqType", "") or ""),
                    "ref_id": str(row.get("RefID", "") or ""),
                    "source": SOURCE_TOKEN,
                    "reference_accession": REFERENCE_NAME,
                }
            )

            for drug in drugs:
                value = (row.get(drug) or "").strip()
                if value == "" or value.upper() in NULL_TOKENS:
                    na_cells += 1
                    continue
                try:
                    fold = float(value)
                except ValueError:
                    na_cells += 1
                    continue
                results += 1
                label_rows.append(
                    {
                        "isolate_id": isolate_id,
                        "drug": drug,
                        "drug_class": drug_class,
                        "dataset": variant,
                        "fold": value,
                        "log10_fold": (
                            format(math.log10(fold), ".6f") if fold > 0 else ""
                        ),
                        "fold_is_positive": "1" if fold > 0 else "0",
                        "source": SOURCE_TOKEN,
                    }
                )

        expected_results, expected_isolates = ADVERTISED[(drug_class, variant)]
        print("=== " + drug_class + ", " + variant + " ===")
        print(
            "  isolates "
            + str(len(rows))
            + " against advertised "
            + str(expected_isolates)
            + ("  ok" if len(rows) == expected_isolates else "  MISMATCH")
        )
        print(
            "  phenotype results "
            + str(results)
            + " against advertised "
            + str(expected_results)
            + ("  ok" if results == expected_results else "  MISMATCH")
        )
        print("  position columns reported: " + str(len(position_columns)) + " of 560")
        print("  CompMutList token categories: " + str(dict(token_categories)))
        print("  position cell categories: " + str(dict(categories)))
        print("  position-column against CompMutList conflicts: " + str(len(conflicts)))
        if unparsed_tokens:
            print("  unparsed tokens: " + str(dict(unparsed_tokens.most_common(5))))
        report["datasets"][drug_class + "_" + variant] = {
            "file": filename,
            "sha256": sha256_of(path),
            "isolates": len(rows),
            "isolates_advertised": expected_isolates,
            "results": results,
            "results_advertised": expected_results,
            "na_cells": na_cells,
            "position_columns_reported": len(position_columns),
            "drugs": list(drugs),
            "token_categories": dict(token_categories),
            "position_cell_categories": dict(categories),
            "n_conflicts": len(conflicts),
            "conflict_examples": conflicts[:20],
            "unparsed_tokens": dict(unparsed_tokens),
            "mutations_per_isolate": {
                "min": min(mutation_counts),
                "median": sorted(mutation_counts)[len(mutation_counts) // 2],
                "max": max(mutation_counts),
            },
        }
        print("")

    print("wild-type assertions checked: " + str(len(all_stated)))
    print("mismatches: " + str(len(all_mismatches)))
    if all_mismatches:
        halt_on_mismatch(reference, all_mismatches, all_stated)
    print("every stated wild-type residue matches the consensus B reference; no offset")
    report["wild_type_assertions"] = len(all_stated)
    report["wild_type_mismatches"] = 0

    if args.check_reference_only:
        print("")
        print("--check-reference-only: stopping, nothing written")
        return 0

    # ---------------------------------------------------------------------------
    # Right-censoring, detected distributionally rather than by marker.
    #
    # No label in any file carries a `>` or `<`. That is not the same as no censoring.
    # The filtered datasets are truncated at a fold resistance of 100, and the truncation
    # is reported as a point value: 45.2 percent of filtered 3TC values are exactly 100.0,
    # against 1.0 percent in the unfiltered set, which reaches 5000.
    #
    # The evidence that this is truncation and not a real mode: of the 2196 isolate-drug
    # pairs whose filtered value is exactly 100.0 and which also appear unfiltered, 2176
    # have an unfiltered value above 100, with a median of 200. Only 16 are genuinely 100.
    # Where the two are not capped they agree exactly 98.5 percent of the time, so these
    # are the same measurements at different precision.
    #
    # Handling rule, stated once and applied uniformly:
    #   1. a value equal to its dataset-and-drug maximum, where that maximum carries an
    #      implausible share of the mass, is flagged `censored`
    #   2. where the same isolate and drug has a higher value in the unfiltered set, that
    #      value is recovered and the row is flagged `censoring_recovered`
    #   3. a censored value that cannot be recovered is retained for rank-based metrics,
    #      which tolerate ties, and excluded from RMSE and MAE, where squaring the distance
    #      to a bound is meaningless
    # Nothing is dropped and nothing is imputed.
    CENSOR_CEILING = 100.0
    CENSOR_MASS_THRESHOLD = 0.02

    by_drug_dataset: dict[tuple[str, str], list[float]] = {}
    for row in label_rows:
        by_drug_dataset.setdefault((row["dataset"], row["drug"]), []).append(float(row["fold"]))
    censored_drugs = set()
    for key, values in by_drug_dataset.items():
        if not values:
            continue
        at_ceiling = sum(1 for v in values if v == CENSOR_CEILING)
        # Two conditions, both required. The mass condition alone produced a false
        # positive: unfiltered DOR has 5.9 percent of its values at exactly 100 while its
        # maximum is 50000, so 100 there is a round number people report rather than a
        # bound. A truncation point must also be the maximum the dataset attains.
        if max(values) != CENSOR_CEILING:
            continue
        if at_ceiling / len(values) >= CENSOR_MASS_THRESHOLD:
            censored_drugs.add(key)

    uncensored_lookup: dict[tuple[str, str], float] = {}
    for row in label_rows:
        if row["dataset"] == "unfiltered":
            uncensored_lookup[(row["drug"], row["isolate_id"])] = float(row["fold"])

    censoring_counts: Counter = Counter()
    for row in label_rows:
        fold = float(row["fold"])
        key = (row["dataset"], row["drug"])
        is_censored = key in censored_drugs and fold == CENSOR_CEILING
        row["censored"] = "1" if is_censored else "0"
        row["censoring_recovered"] = "0"
        row["fold_original"] = row["fold"]
        if not is_censored:
            continue
        censoring_counts[row["drug"] + "/" + row["dataset"]] += 1
        recovered = uncensored_lookup.get((row["drug"], row["isolate_id"]))
        if recovered is not None and recovered > fold:
            row["fold"] = format(recovered, "g")
            row["log10_fold"] = format(math.log10(recovered), ".6f")
            row["censoring_recovered"] = "1"
            censoring_counts[row["drug"] + "/" + row["dataset"] + "/recovered"] += 1
    report["censoring"] = {
        "ceiling": CENSOR_CEILING,
        "mass_threshold": CENSOR_MASS_THRESHOLD,
        "drugs_flagged": sorted(d + "/" + ds for ds, d in censored_drugs),
        "counts": dict(censoring_counts),
        "rule": (
            "a value equal to the dataset-and-drug maximum carrying at least 2 percent of "
            "the mass is flagged censored; where the unfiltered set holds a higher value "
            "for the same isolate and drug it is recovered; an unrecovered censored value "
            "is kept for rank metrics and excluded from RMSE and MAE"
        ),
    }
    print("")
    print("censoring: " + str(len(censored_drugs)) + " drug-dataset combinations truncated at "
          + format(CENSOR_CEILING, "g"))
    for key, count in sorted(censoring_counts.items()):
        print("  " + key + ": " + str(count))

    isolate_columns = list(isolate_rows[0].keys())
    with ISOLATES.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=isolate_columns)
        writer.writeheader()
        writer.writerows(isolate_rows)
    label_columns = list(label_rows[0].keys())
    with CURATED.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=label_columns)
        writer.writeheader()
        writer.writerows(label_rows)

    report["curated_isolates_rows"] = len(isolate_rows)
    report["curated_rows"] = len(label_rows)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("")
    print("wrote " + ISOLATES.relative_to(REPO_ROOT).as_posix() + ", " + str(len(isolate_rows)) + " rows")
    print("    sha256 " + sha256_of(ISOLATES))
    print("wrote " + CURATED.relative_to(REPO_ROOT).as_posix() + ", " + str(len(label_rows)) + " rows")
    print("    sha256 " + sha256_of(CURATED))
    print("wrote " + REPORT.relative_to(REPO_ROOT).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
