"""Tests that the Task A parser halts rather than adapting, and that its validator rejects.

Runs as a plain script, and also under pytest:

    python data_acquisition/test_parse_taskA.py

Two things are being guarded.

The first is the Gate G1 ruling. A human confirmed that one specific row range of one
specific sheet is the assayed panel, and the parser's job is to read that range and
nothing else. If the workbook is ever replaced by a different version, a re-export, or a
file with the same name and different contents, the parser must stop. The failure it
exists to prevent is reading 543 unlabelled phylogenetic sequences into a 57-row task,
which would not raise anything on its own.

The second is the curation validator. It is the only thing standing between a malformed
row and every downstream phase, so each of its rules gets a row that violates exactly
that rule and nothing else.

The structural tests need the real workbook. They skip, loudly, if it is absent.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition import parse_taskA as parser  # noqa: E402

WORKBOOK = parser.WORKBOOK


def a_valid_row(**overrides) -> dict:
    """One row that passes every rule, so a test can break exactly one thing."""
    sequence = "MKTAYIAKQRQISFVKSHFSRQ"
    row = {
        "rt_name": "Test-RT",
        "sequence": sequence,
        "sequence_len": str(len(sequence)),
        "source_doi": parser.SOURCE_DOI,
        "family": "Retroviral",
        "active": "1",
        "label_binary": "1",
        "pe_efficiency_pct": "12.5",
        "label_value": "12.5",
    }
    row.update(overrides)
    return row


def test_a_valid_row_passes() -> None:
    assert parser.validate([a_valid_row()]) == [], "the baseline row must pass"


def test_rejects_a_null_sequence() -> None:
    violations = parser.validate([a_valid_row(sequence="", sequence_len="0")])
    assert any("null sequence" in v for v in violations), violations


def test_rejects_a_duplicate_sequence() -> None:
    first = a_valid_row(rt_name="First-RT")
    second = a_valid_row(rt_name="Second-RT")
    violations = parser.validate([first, second])
    assert any("identical to" in v for v in violations), violations


def test_rejects_a_null_source_doi() -> None:
    violations = parser.validate([a_valid_row(source_doi="")])
    assert any("null source_doi" in v for v in violations), violations


def test_rejects_a_length_that_disagrees_with_the_sequence() -> None:
    violations = parser.validate([a_valid_row(sequence_len="999")])
    assert any("does not equal len(sequence)" in v for v in violations), violations


def test_rejects_a_family_outside_the_controlled_vocabulary() -> None:
    violations = parser.validate([a_valid_row(family="Retroviral-ish")])
    assert any("not in the controlled vocabulary" in v for v in violations), violations


def test_rejects_disagreement_between_the_duplicated_label_columns() -> None:
    """active and label_binary carry the same fact under two names; they must agree."""
    violations = parser.validate([a_valid_row(label_binary="0")])
    assert any("disagree" in v for v in violations), violations
    violations = parser.validate([a_valid_row(label_value="99.0")])
    assert any("disagree" in v for v in violations), violations


def test_rejects_an_active_row_with_no_efficiency() -> None:
    violations = parser.validate(
        [a_valid_row(pe_efficiency_pct="0.0", label_value="0.0")]
    )
    assert any("no positive efficiency" in v for v in violations), violations


def test_rejects_an_inactive_row_carrying_an_efficiency() -> None:
    violations = parser.validate([a_valid_row(active="0", label_binary="0")])
    assert any("non-zero efficiency" in v for v in violations), violations


def test_the_real_workbook_yields_the_ruled_on_structure() -> None:
    if not WORKBOOK.is_file():
        print("    skipped: " + WORKBOOK.name + " is not present")
        return
    entries = parser.extract_assayed_block(WORKBOOK)
    assert len(entries) == parser.EXPECTED_ENTRIES, len(entries)
    assert sum(1 for e in entries if e.active) == parser.EXPECTED_HIGHLIGHTED
    assert [e.index for e in entries] == list(range(1, parser.EXPECTED_ENTRIES + 1))
    # Nothing from the excluded phylogenetic block may appear. Its names are UniProt
    # FASTA headers, so no assayed name may look like one.
    assert not any("|" in e.name for e in entries), "a BLAST hit header was read"
    assert all(e.name_row <= parser.BLOCK1_LAST_ROW for e in entries)


def test_the_parser_halts_when_the_expected_entry_count_changes() -> None:
    """A changed source must stop the parser, not silently produce a different table."""
    if not WORKBOOK.is_file():
        print("    skipped: " + WORKBOOK.name + " is not present")
        return
    original = parser.EXPECTED_ENTRIES
    parser.EXPECTED_ENTRIES = original + 1
    try:
        parser.extract_assayed_block(WORKBOOK)
    except SystemExit as error:
        assert "assayed entries" in str(error), str(error)
    else:
        raise AssertionError("parser accepted a block of the wrong size")
    finally:
        parser.EXPECTED_ENTRIES = original


def test_the_parser_halts_when_the_highlight_count_changes() -> None:
    if not WORKBOOK.is_file():
        print("    skipped: " + WORKBOOK.name + " is not present")
        return
    original = parser.EXPECTED_HIGHLIGHTED
    parser.EXPECTED_HIGHLIGHTED = original + 1
    try:
        parser.extract_assayed_block(WORKBOOK)
    except SystemExit as error:
        assert "highlighted entries" in str(error), str(error)
    else:
        raise AssertionError("parser accepted the wrong number of active labels")
    finally:
        parser.EXPECTED_HIGHLIGHTED = original


def test_the_parser_halts_when_the_block_caption_moves() -> None:
    """The captions are the block boundary, so they are asserted before any data row."""
    if not WORKBOOK.is_file():
        print("    skipped: " + WORKBOOK.name + " is not present")
        return
    original = parser.BLOCK1_CAPTION_FRAGMENT
    parser.BLOCK1_CAPTION_FRAGMENT = "a caption this workbook does not contain"
    try:
        parser.extract_assayed_block(WORKBOOK)
    except SystemExit as error:
        assert "should open the assayed block" in str(error), str(error)
    else:
        raise AssertionError("parser read a block whose caption did not match")
    finally:
        parser.BLOCK1_CAPTION_FRAGMENT = original


def main() -> int:
    tests = [
        test_a_valid_row_passes,
        test_rejects_a_null_sequence,
        test_rejects_a_duplicate_sequence,
        test_rejects_a_null_source_doi,
        test_rejects_a_length_that_disagrees_with_the_sequence,
        test_rejects_a_family_outside_the_controlled_vocabulary,
        test_rejects_disagreement_between_the_duplicated_label_columns,
        test_rejects_an_active_row_with_no_efficiency,
        test_rejects_an_inactive_row_carrying_an_efficiency,
        test_the_real_workbook_yields_the_ruled_on_structure,
        test_the_parser_halts_when_the_expected_entry_count_changes,
        test_the_parser_halts_when_the_highlight_count_changes,
        test_the_parser_halts_when_the_block_caption_moves,
    ]
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
