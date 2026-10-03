"""Tests that the Task B parser halts on a wrong reference instead of adapting to it.

Runs as a plain script, and also under pytest:

    python data_acquisition/test_parse_mmlv_dms.py

Why these are the tests that matter
-----------------------------------
A one-residue offset between the paper's numbering and the reference frame produces 1045
variant sequences that are each wrong at two positions, raises nothing, and leaves no
downstream symptom except a benchmark that quietly measures noise. There is no way to
detect it later, because every variant is internally consistent with every other.

So the parser's job is to refuse, and these tests are positive controls for refusal: each
feeds a deliberately wrong reference and asserts that the parser stops. One of them feeds
a reference shifted by exactly one residue, which is the realistic failure, and checks
that the parser reports the offset as a finding and does **not** apply it.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition import parse_mmlv_dms as parser  # noqa: E402


def real_reference() -> str:
    sequence, _, _ = parser.load_reference()
    return sequence


def write_reference(sequence: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        "w", suffix=".fasta", delete=False, encoding="utf-8"
    )
    handle.write(">synthetic reference for the test suite\n")
    for index in range(0, len(sequence), 60):
        handle.write(sequence[index : index + 60] + "\n")
    handle.close()
    return Path(handle.name)


def with_reference(sequence: str):
    """Point the parser at a synthetic reference for the duration of one check."""

    class Swap:
        def __enter__(self_inner):
            self_inner.original = parser.REFERENCE_CANDIDATE
            self_inner.adopted = parser.REFERENCE
            self_inner.path = write_reference(sequence)
            parser.REFERENCE_CANDIDATE = self_inner.path
            # Make sure the adopted reference cannot shadow the synthetic one.
            parser.REFERENCE = Path(str(self_inner.path) + ".absent")
            return self_inner

        def __exit__(self_inner, *_exc):
            parser.REFERENCE_CANDIDATE = self_inner.original
            parser.REFERENCE = self_inner.adopted
            self_inner.path.unlink(missing_ok=True)

    return Swap()


def test_the_real_reference_passes_every_assertion() -> None:
    sequence = real_reference()
    assert parser.check_reference(sequence) == [], (
        "the adopted reference fails its own anchors"
    )


def test_the_real_reference_derives_the_published_library_sizes() -> None:
    variants = parser.expected_variants()
    per_stretch = {
        stretch: sum(1 for v in variants if v["library_stretch"] == stretch)
        for stretch in parser.STRETCHES
    }
    assert per_stretch == parser.EXPECTED_PER_STRETCH, per_stretch
    assert len(variants) == 1045, len(variants)
    # Every identifier is unique, and none is the wild type.
    identifiers = [v["variant_id"] for v in variants]
    assert len(set(identifiers)) == len(identifiers)
    assert all(v["wt_aa"] != v["mut_aa"] for v in variants)


def test_a_reference_shifted_by_one_residue_halts_the_parser() -> None:
    """The realistic failure: an off-by-one frame that looks entirely plausible."""
    shifted = "A" + real_reference()[:-1]
    with with_reference(shifted):
        mismatches = parser.check_reference(shifted)
        assert mismatches, "a one-residue shift was not detected"
        try:
            parser.halt_on_mismatch(shifted, mismatches)
        except SystemExit as error:
            assert "halted on a wild-type residue mismatch" in str(error), str(error)
        else:
            raise AssertionError("the parser did not halt on a shifted reference")


def test_the_shifted_reference_reports_an_offset_without_applying_it() -> None:
    shifted = "A" + real_reference()[:-1]
    anchors = dict(parser.STRETCH_BOUNDARY_RESIDUES)
    anchors.update(parser.REPORTED_MUTATIONS)
    offset = parser.candidate_offset(shifted, anchors)
    assert offset == 1, (
        "a reference shifted by one residue should yield a candidate offset of +1, got "
        + str(offset)
    )
    # The finding must not change the parser's behaviour: it still halts.
    with with_reference(shifted):
        try:
            parser.halt_on_mismatch(shifted, parser.check_reference(shifted))
        except SystemExit:
            pass
        else:
            raise AssertionError("a resolvable offset must not stop the parser halting")


def test_a_single_corrupted_anchor_halts_the_parser() -> None:
    sequence = list(real_reference())
    # Position 61 is one of the reported mutation positions, I61R.
    sequence[60] = "W" if sequence[60] != "W" else "A"
    corrupted = "".join(sequence)
    mismatches = parser.check_reference(corrupted)
    assert any("position 61" in m for m in mismatches), mismatches
    with with_reference(corrupted):
        try:
            parser.halt_on_mismatch(corrupted, mismatches)
        except SystemExit:
            pass
        else:
            raise AssertionError("the parser did not halt on a corrupted anchor")


def test_a_corrupted_anchor_yields_no_spurious_offset() -> None:
    """One wrong residue is not a frame shift, and must not be reported as one."""
    sequence = list(real_reference())
    sequence[60] = "W" if sequence[60] != "W" else "A"
    corrupted = "".join(sequence)
    anchors = dict(parser.STRETCH_BOUNDARY_RESIDUES)
    anchors.update(parser.REPORTED_MUTATIONS)
    assert parser.candidate_offset(corrupted, anchors) is None, (
        "a single corrupted residue was misreported as a constant offset"
    )


def test_a_truncated_reference_halts_rather_than_indexing_past_the_end() -> None:
    truncated = real_reference()[:50]
    mismatches = parser.check_reference(truncated)
    assert mismatches, "a reference too short for the anchors was accepted"
    assert any("beyond the reference" in m for m in mismatches), mismatches


def test_the_parser_refuses_to_build_without_the_activity_tables() -> None:
    """The tables are absent today, and absence must be a stop, not an empty table."""
    if parser.TABLE_S6.is_file() and parser.TABLE_S7.is_file():
        print("    skipped: the activity tables are present")
        return
    assert not parser.CURATED.is_file(), (
        "curated.csv exists while the activity tables do not; it cannot have been built "
        "from the source"
    )


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
