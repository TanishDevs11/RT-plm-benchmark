"""Tests that the HIVDB parser halts on a wrong reference instead of adapting to it.

Runs as a plain script, and also under pytest:

    python data_acquisition/test_parse_hivdb.py

The failure these guard against is the same one that dominates every sequence
reconstruction in this repository: an offset between the source's numbering and the
reference frame. Here it would misplace every mutation in 14421 isolates at once, raise
nothing, and leave a benchmark that quietly measures the wrong thing.

The protection is that the source states a wild-type residue for every mutation it lists,
229531 of them, and the parser asserts all of them. These tests feed deliberately wrong
references and require the parser to stop.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition import parse_hivdb as parser  # noqa: E402


def reference() -> str:
    return parser.load_reference()


def test_the_reference_is_the_expected_length_and_prefix() -> None:
    sequence = reference()
    assert len(sequence) == 560, len(sequence)
    assert sequence.startswith("PISPIETVPVKLKPGMDGPKV"), sequence[:25]


def test_mutation_tokens_parse_into_the_expected_categories() -> None:
    mutations, categories, unparsed = parser.parse_mutations("K65R, S68G")
    assert mutations == [("K", 65, "R"), ("S", 68, "G")], mutations
    assert categories["substitution"] == 2
    assert not unparsed


def test_the_three_source_formatting_artefacts_are_repaired_explicitly() -> None:
    """An internal space, a trailing period, and the literal NULL all appear in the data."""
    mutations, categories, unparsed = parser.parse_mutations("R211 K, K102K., NULL")
    assert ("R", 211, "K") in mutations, mutations
    assert ("K", 102, "K") in mutations, mutations
    assert categories["null_token"] == 1
    assert not unparsed, unparsed


def test_insertions_are_their_own_category_and_keep_their_wild_type() -> None:
    """T69 insertions are a real NRTI resistance mechanism and must not be discarded."""
    mutations, categories, unparsed = parser.parse_mutations("T69S_SG")
    assert categories["insertion"] == 1
    assert mutations == [("T", 69, "S")], mutations
    assert not unparsed


def test_candidate_offset_finds_a_real_shift() -> None:
    sequence = reference()
    # Build stated mutations from the real reference, then shift every position by one so
    # they describe a frame offset by exactly +1.
    stated = [(sequence[position - 1], position + 1, "A") for position in (65, 100, 184, 215)]
    assert parser.candidate_offset(sequence, stated) == -1, parser.candidate_offset(
        sequence, stated
    )


def test_candidate_offset_returns_none_for_a_single_wrong_residue() -> None:
    """One wrong residue is not a frame shift and must not be reported as one."""
    sequence = reference()
    stated = [(sequence[position - 1], position, "A") for position in (65, 100, 184)]
    wrong = "W" if sequence[214] != "W" else "A"
    stated.append((wrong, 215, "A"))
    assert parser.candidate_offset(sequence, stated) is None


def test_the_parser_halts_on_a_wild_type_mismatch() -> None:
    sequence = reference()
    mismatches = [("SEQ1", "W65R", "W", 65, sequence[64])]
    stated = [("W", 65, "R")]
    try:
        parser.halt_on_mismatch(sequence, mismatches, stated)
    except SystemExit as error:
        assert "halted on a wild-type residue mismatch" in str(error), str(error)
    else:
        raise AssertionError("the parser did not halt on a wild-type mismatch")


def test_a_shifted_reference_is_detected_across_the_sequence() -> None:
    """The realistic failure: a reference off by one that looks entirely plausible.

    A one-residue shift does not make *every* position mismatch, because wherever the
    reference happens to repeat a residue the shifted frame still agrees. What matters is
    that the great majority mismatch, so the assertion cannot be passed by chance, and
    that the parser halts on the ones that do.
    """
    sequence = reference()
    shifted = "A" + sequence[:-1]
    positions = list(range(2, len(sequence) + 1))
    stated = [(sequence[position - 1], position, "A") for position in positions]
    mismatches = [
        ("SEQ" + str(index), wild + str(position) + "A", wild, position, shifted[position - 1])
        for index, (wild, position, _) in enumerate(stated)
        if shifted[position - 1] != wild
    ]
    detected = len(mismatches) / len(stated)
    assert detected > 0.9, (
        "a one-residue shift was detected at only "
        + format(100 * detected, ".1f")
        + " percent of positions; the guard is too weak"
    )
    try:
        parser.halt_on_mismatch(shifted, mismatches, stated)
    except SystemExit:
        pass
    else:
        raise AssertionError("the parser did not halt on a shifted reference")


def test_ambiguity_is_never_coerced_to_a_residue() -> None:
    """Every indeterminate category must become X, never a guessed residue."""
    sequence = reference()
    columns = ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]
    row = {
        "SeqID": "SYNTH",
        "P1": "-",
        "P2": ".",
        "P3": "VI",
        "P4": "~",
        "P5": "*",
        "P6": "X",
        "P7": "A",
    }
    built, categories, conflicts = parser.reconstruct(row, sequence, columns, [])
    assert built[0] == sequence[0], "a consensus cell did not take the reference residue"
    for index in range(1, 6):
        assert built[index] == "X", (
            "position " + str(index + 1) + " was coerced to " + built[index]
        )
    assert built[6] == "A"
    assert categories["not_sequenced"] == 1
    assert categories["mixture"] == 1
    assert categories["deletion"] == 1
    assert categories["stop_codon"] == 1
    assert categories["source_ambiguous_X"] == 1
    assert not conflicts


def test_a_disagreement_between_the_two_encodings_is_recorded() -> None:
    """CompMutList and the position columns both speak; a conflict must be reported."""
    sequence = reference()
    columns = ["P1", "P2"]
    row = {"SeqID": "SYNTH", "P1": "-", "P2": "-"}
    # Claim a mutation at position 1 that the position column says is consensus.
    _, _, conflicts = parser.reconstruct(
        row, sequence, columns, [(sequence[0], 1, "W")]
    )
    assert conflicts, "a CompMutList against position-column conflict was not recorded"
    assert "consensus" in conflicts[0]


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
