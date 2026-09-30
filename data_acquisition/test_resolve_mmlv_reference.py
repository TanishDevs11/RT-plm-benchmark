"""Tests that the reference resolver halts on a wrong reference instead of adapting to it.

Runs as a plain script:

    python data_acquisition/test_resolve_mmlv_reference.py

The point of the resolver is that it refuses. A resolver that quietly shifted an offset
until the anchors lined up would be worse than no resolver at all, because it would
produce a confident wrong answer for an entire saturated mutagenesis library. So the tests
here are mostly positive controls for failure: each feeds a deliberately corrupted
reference and asserts that the script stops.

These tests need tasks/taskB_mmlv_dms/raw/uniprot_P03355.fasta to be present. Fetch it
with:

    python data_acquisition/resolve_mmlv_reference.py --fetch
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from data_acquisition import resolve_mmlv_reference as resolver  # noqa: E402

REAL_FASTA = REPO_ROOT / "tasks/taskB_mmlv_dms/raw/uniprot_P03355.fasta"


def _write_fasta(directory: Path, residues: str, name: str = "corrupted.fasta") -> Path:
    path = directory / name
    lines = [">test corrupted reference"]
    lines += [residues[i : i + 60] for i in range(0, len(residues), 60)]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _run_against(residues: str) -> tuple[int | None, Exception | None]:
    """Run the resolver against a given Gag-Pol sequence, isolated from the repository."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        original_fasta = resolver.FASTA_PATH
        original_candidate = resolver.CANDIDATE_PATH
        resolver.FASTA_PATH = _write_fasta(tmp_path, residues)
        resolver.CANDIDATE_PATH = tmp_path / "candidate.fasta"
        try:
            return resolver.main([]), None
        except Exception as error:  # noqa: BLE001
            return None, error
        finally:
            resolver.FASTA_PATH = original_fasta
            resolver.CANDIDATE_PATH = original_candidate


def _real_gagpol() -> str:
    _, residues = resolver.read_fasta(REAL_FASTA)
    return residues


def _substitute(residues: str, rt_position: int, new_residue: str) -> str:
    """Change one residue, addressed in the paper's RT numbering."""
    index = resolver.GAGPOL_OFFSET + rt_position - 1
    assert residues[index] != new_residue, "the test must actually change something"
    return residues[:index] + new_residue + residues[index + 1 :]


def test_accepts_the_real_reference() -> None:
    code, error = _run_against(_real_gagpol())
    assert error is None, "resolver raised on the genuine reference: " + repr(error)
    assert code == 0, "resolver did not succeed on the genuine reference"


def test_halts_on_a_wrong_residue_at_a_mutation_anchor() -> None:
    """I61 is where the paper's reported mutation I61R lands. Break it."""
    corrupted = _substitute(_real_gagpol(), 61, "A")
    code, error = _run_against(corrupted)
    assert isinstance(error, resolver.ResolutionFailure), (
        "expected ResolutionFailure, got code=" + repr(code) + " error=" + repr(error)
    )
    assert "61" in str(error), str(error)


def test_halts_on_a_wrong_residue_at_a_stretch_boundary() -> None:
    corrupted = _substitute(_real_gagpol(), 124, "A")
    code, error = _run_against(corrupted)
    assert isinstance(error, resolver.ResolutionFailure), (
        "expected ResolutionFailure, got code=" + repr(code) + " error=" + repr(error)
    )
    assert "124" in str(error), str(error)


def test_halts_on_a_wrong_deletion_boundary() -> None:
    """P677 is the anchor that settles the 671 against 677 question. It must be load bearing."""
    corrupted = _substitute(_real_gagpol(), 677, "A")
    code, error = _run_against(corrupted)
    assert isinstance(error, resolver.ResolutionFailure), (
        "expected ResolutionFailure, got code=" + repr(code) + " error=" + repr(error)
    )
    assert "677" in str(error), str(error)


def test_halts_on_a_six_residue_frame_shift() -> None:
    """The exact failure the resolver exists to catch.

    Deleting six residues ahead of the RT start is what a wrong frame looks like: every
    anchor moves by six, so a resolver that tolerated it would mis-place all 1045 variants.
    """
    residues = _real_gagpol()
    shifted = residues[: resolver.GAGPOL_OFFSET] + residues[resolver.GAGPOL_OFFSET + 6 :]
    code, error = _run_against(shifted)
    assert isinstance(error, resolver.ResolutionFailure), (
        "a six-residue frame shift was not caught: code=" + repr(code) + " error=" + repr(error)
    )


def test_halts_on_a_truncated_reference() -> None:
    """A reference that stops at the annotated p80 boundary cannot reach anchor 677."""
    residues = _real_gagpol()[: resolver.P80_END]
    code, error = _run_against(residues)
    assert isinstance(error, resolver.ResolutionFailure), (
        "a reference too short for anchor 677 was accepted: code=" + repr(code) + " error=" + repr(error)
    )


def main() -> int:
    if not REAL_FASTA.is_file():
        print("SKIP: " + REAL_FASTA.as_posix() + " is absent")
        print("Fetch it with: python data_acquisition/resolve_mmlv_reference.py --fetch")
        return 1
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
