"""Tests for the task schema and its validator.

Runs as a plain script so continuous integration needs no test runner:

    python schemas/test_task_schema.py

The suite is only meaningful if it is capable of failing, so every rejection test
constructs a table that is valid except for the one defect under test, and then asserts
that exactly that rule fires. A test that merely asserted "some violation occurred" would
pass even if the validator rejected the table for the wrong reason.

The central test is ``test_rejects_merged_two_task_table``, which proves that the
forbidden operation is actually blocked: two tasks measured in different units cannot be
concatenated into one label column.
"""

from __future__ import annotations

import hashlib

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.task_schema import (  # noqa: E402
    SchemaViolation,
    assert_concatenable,
    safe_concat,
    validate_task_table,
)

# A minimal but genuinely schema-valid Task A row, used as the base that each rejection
# test perturbs in exactly one way.
SEQ_ONE = "MTLNIEDEYRLHETSKEPDVSLGSTWLSDFPQAWAETGGMGLAVRQAPLIIPLKATSTPVSIKQYPMSQEARLGIKPHIQRLLDQGILVPCQSPWNTPLLPVKK"
SEQ_TWO = "GDALLAAWYQVRTRSKTAGIDGISVELFAHFLDEELKRLAHQLQQDIYHPLPALGFYRAKKSGGHRLIGIPTVRDRIVQRLLLRSLYPALEETFQDCSFAYRP"
SEQ_THREE = "ISSQFIDINNFQRAWEKVADKRGCAGVDGETISSFASNQTVNVYQLMNSVADGSYQPFPCKQVIIPKRNGSQRELKIPTIRDRIVQQALLNVISPLMEEKFSP"


def task_a_row(row_id: str, sequence: str, label: str = "12.5") -> dict[str, str]:
    return {
        "id": row_id,
        "task": "A",
        "sequence": sequence,
        "sequence_len": str(len(sequence)),
        "family": "Retroviral",
        "parent_id": "",
        "mutations": "",
        "label_value": label,
        "label_units": "percent_editing_HEK293T",
        "label_assay": "prime_editing_pct_HEK293T",
        "label_is_binary": "true",
        "label_binary": "1",
        "source_doi": "10.0000/placeholder",
        "source_table": "Supplementary Table 1",
        "reference_accession": "PLACEHOLDER.1",
        "notes": "synthetic row used only by the schema test suite",
    }


def task_b_row(
    row_id: str,
    sequence: str,
    mutations: str = "",
    parent_id: str = "",
    label: str = "0",
) -> dict[str, str]:
    return {
        "id": row_id,
        "task": "B",
        "sequence": sequence,
        "sequence_len": str(len(sequence)),
        "family": "MMLV_RT_PE2dR",
        "parent_id": parent_id,
        "mutations": mutations,
        "label_value": label,
        "label_units": "normalized_-1_1",
        "label_assay": "prime_editing_normalized_wt_centred",
        "label_is_binary": "false",
        "label_binary": "",
        "source_doi": "10.0000/placeholder-b",
        "source_table": "Supplementary Table 2",
        "reference_accession": "PLACEHOLDER_B.1",
        "notes": "synthetic row used only by the schema test suite",
        "library_stretch": "1",
    }


def frame(rows: list[dict[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(rows, dtype=str)


def rules(report) -> set[str]:
    return {v.rule for v in report.violations}


def test_valid_task_a_table_passes() -> None:
    df = frame([task_a_row("A_one", SEQ_ONE), task_a_row("A_two", SEQ_TWO, label="0")])
    report = validate_task_table(df, task="A")
    assert report.ok, report.render()


def test_valid_task_b_table_with_variant_passes() -> None:
    wild_type = task_b_row("B_wt", SEQ_ONE)
    variant_sequence = "A" + SEQ_ONE[1:]
    variant = task_b_row(
        "B_var_M1A",
        variant_sequence,
        mutations="M1A",
        parent_id="B_wt",
        label="-0.42",
    )
    report = validate_task_table(frame([wild_type, variant]), task="B")
    assert report.ok, report.render()


def test_rejects_duplicate_sequence_within_a_task() -> None:
    df = frame([task_a_row("A_one", SEQ_ONE), task_a_row("A_two", SEQ_ONE, label="3.1")])
    report = validate_task_table(df, task="A")
    assert "sequence.duplicate" in rules(report), report.render()


def test_rejects_inconsistent_label_units_within_a_task() -> None:
    first = task_a_row("A_one", SEQ_ONE)
    second = task_a_row("A_two", SEQ_TWO)
    second["label_units"] = "fold_over_control"
    report = validate_task_table(frame([first, second]), task="A")
    assert "label_units.inconsistent" in rules(report), report.render()


def test_rejects_null_source_doi() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["source_doi"] = ""
    report = validate_task_table(frame([row]), task="A")
    assert "source_doi.null" in rules(report), report.render()


def test_rejects_two_tasks_inside_one_table() -> None:
    df = frame([task_a_row("A_one", SEQ_ONE), task_b_row("B_wt", SEQ_TWO)])
    report = validate_task_table(df)
    assert "task.mixed" in rules(report), report.render()
    assert "label_units.inconsistent" in rules(report), report.render()


def test_rejects_merged_two_task_table() -> None:
    """The forbidden operation: stacking two assays into one label column."""
    task_a = frame([task_a_row("A_one", SEQ_ONE), task_a_row("A_two", SEQ_TWO, label="0")])
    task_b = frame([task_b_row("B_wt", SEQ_THREE)])

    raised = False
    try:
        safe_concat([task_a, task_b], ["taskA", "taskB"])
    except SchemaViolation as error:
        raised = True
        message = str(error)
        assert "label_units" in message or "task" in message, message
    assert raised, "safe_concat merged two tasks with different label_units"

    raised = False
    try:
        assert_concatenable([task_a, task_b], ["taskA", "taskB"])
    except SchemaViolation:
        raised = True
    assert raised, "assert_concatenable permitted a cross-assay merge"

    # A merged frame, if someone builds one by hand with plain pandas, must still fail
    # validation. The guard is not only on the helper.
    merged = pd.concat([task_a, task_b], ignore_index=True)
    report = validate_task_table(merged)
    assert not report.ok, "a hand-merged two-task frame passed validation"
    assert "task.mixed" in rules(report), report.render()


def test_allows_concatenation_within_one_task() -> None:
    first = frame([task_a_row("A_one", SEQ_ONE)])
    second = frame([task_a_row("A_two", SEQ_TWO, label="0")])
    stacked = safe_concat([first, second], ["shardA", "shardB"])
    assert len(stacked) == 2
    assert validate_task_table(stacked, task="A").ok


def test_rejects_assay_belonging_to_another_task() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["label_assay"] = "retron_msdna_production"
    report = validate_task_table(frame([row]), task="A")
    assert "label_assay.wrong_task" in rules(report), report.render()


def test_evolved_cohort_rejects_the_cross_family_assay() -> None:
    """The A2 ruling, enforced.

    PE6-class editors were selected for activity and measured in their own scaffolds, so
    their efficiency is not the survey's efficiency even though both are a percentage. If
    the two shared an assay term they could be stacked, which is the merge the G1 ruling
    decided against.
    """
    row = task_a_row("A2_pe6a", SEQ_ONE)
    row["task"] = "A2"
    row["editor_name"] = "PE6a"
    row["derived_from_rt"] = "Ec48-RT"
    report = validate_task_table(frame([row]), task="A2")
    assert "label_assay.wrong_task" in rules(report), report.render()

    row["label_assay"] = "prime_editing_pct_HEK293T_evolved_editor"
    report = validate_task_table(frame([row]), task="A2")
    assert report.ok, report.render()


def test_evolved_cohort_cannot_be_stacked_onto_task_a() -> None:
    task_a = frame([task_a_row("A_one", SEQ_ONE)])
    evolved = task_a_row("A2_pe6a", SEQ_TWO)
    evolved["task"] = "A2"
    evolved["label_assay"] = "prime_editing_pct_HEK293T_evolved_editor"
    evolved["editor_name"] = "PE6a"
    evolved["derived_from_rt"] = "Ec48-RT"
    raised = False
    try:
        safe_concat([task_a, frame([evolved])], ["taskA", "taskA2"])
    except SchemaViolation:
        raised = True
    assert raised, "the evolved cohort was stacked onto Task A"


def test_rejects_assay_outside_the_vocabulary() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["label_assay"] = "editing_activity"
    report = validate_task_table(frame([row]), task="A")
    assert "label_assay.vocabulary" in rules(report), report.render()


def test_rejects_sequence_length_mismatch() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["sequence_len"] = str(len(SEQ_ONE) + 1)
    report = validate_task_table(frame([row]), task="A")
    assert "sequence_len.mismatch" in rules(report), report.render()


def test_rejects_imputed_absence_of_a_label() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["label_value"] = ""
    report = validate_task_table(frame([row]), task="A")
    assert "label_value.null" in rules(report), report.render()


def test_rejects_dangling_parent_id() -> None:
    variant = task_b_row(
        "B_var", "A" + SEQ_ONE[1:], mutations="M1A", parent_id="B_absent", label="-0.1"
    )
    report = validate_task_table(frame([variant]), task="B")
    assert "parent_id.dangling" in rules(report), report.render()


def test_rejects_variant_without_a_parent() -> None:
    variant = task_b_row("B_var", "A" + SEQ_ONE[1:], mutations="M1A", label="-0.1")
    report = validate_task_table(frame([variant]), task="B")
    assert "parent_id.null" in rules(report), report.render()


def test_rejects_malformed_mutation_token() -> None:
    wild_type = task_b_row("B_wt", SEQ_ONE)
    variant = task_b_row(
        "B_var", "A" + SEQ_ONE[1:], mutations="Met1Ala", parent_id="B_wt", label="-0.1"
    )
    report = validate_task_table(frame([wild_type, variant]), task="B")
    assert "mutations.format" in rules(report), report.render()


def test_rejects_undeclared_extra_column() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["predicted_activity"] = "0.9"
    report = validate_task_table(frame([row]), task="A")
    assert "columns.undeclared" in rules(report), report.render()


def test_rejects_identifier_without_its_task_prefix() -> None:
    row = task_a_row("rt_one", SEQ_ONE)
    report = validate_task_table(frame([row]), task="A")
    assert "id.prefix" in rules(report), report.render()


def test_rejects_binary_call_on_a_task_that_has_none() -> None:
    row = task_b_row("B_wt", SEQ_ONE)
    row["label_binary"] = "1"
    report = validate_task_table(frame([row]), task="B")
    assert "label_binary.unexpected" in rules(report), report.render()


def test_rejects_missing_binary_call_where_one_is_declared() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["label_binary"] = ""
    report = validate_task_table(frame([row]), task="A")
    assert "label_binary.null" in rules(report), report.render()


def test_accession_exempt_task_accepts_a_sequence_digest_instead() -> None:
    """Task A may omit reference_accession, by the Gate G2 ruling, but not identity."""
    row = task_a_row("A_one", SEQ_ONE)
    row["reference_accession"] = ""
    row["sequence_sha256"] = hashlib.sha256(SEQ_ONE.encode("utf-8")).hexdigest()
    report = validate_task_table(frame([row]), task="A")
    assert report.ok, report.render()
    assert "reference_accession.absent" in [w.rule for w in report.warnings], report.render()


def test_accession_exempt_task_still_requires_some_identifier() -> None:
    """The exemption must not degrade into no identifier at all."""
    row = task_a_row("A_one", SEQ_ONE)
    row["reference_accession"] = ""
    row["sequence_sha256"] = ""
    report = validate_task_table(frame([row]), task="A")
    assert "sequence_sha256.null" in rules(report), report.render()


def test_accession_exempt_task_rejects_a_digest_of_another_sequence() -> None:
    """A digest that does not hash this row's sequence identifies the wrong thing."""
    row = task_a_row("A_one", SEQ_ONE)
    row["reference_accession"] = ""
    row["sequence_sha256"] = hashlib.sha256(b"a different sequence").hexdigest()
    report = validate_task_table(frame([row]), task="A")
    assert "sequence_sha256.mismatch" in rules(report), report.render()


def test_accession_exempt_task_rejects_a_malformed_digest() -> None:
    row = task_a_row("A_one", SEQ_ONE)
    row["reference_accession"] = ""
    row["sequence_sha256"] = "not-a-digest"
    report = validate_task_table(frame([row]), task="A")
    assert "sequence_sha256.format" in rules(report), report.render()


def test_a_task_without_the_exemption_still_requires_an_accession() -> None:
    """The relaxation is per task. Task B must not inherit it."""
    row = task_b_row("B_wt", SEQ_ONE)
    row["reference_accession"] = ""
    report = validate_task_table(frame([row]), task="B")
    assert "reference_accession.null" in rules(report), report.render()


def main() -> int:
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except AssertionError as error:
            failures += 1
            print("FAIL " + test.__name__ + ": " + str(error))
        except Exception as error:  # noqa: BLE001
            failures += 1
            print("ERROR " + test.__name__ + ": " + type(error).__name__ + ": " + str(error))
        else:
            print("pass " + test.__name__)
    print("tests: " + str(len(tests)) + ", failures: " + str(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
