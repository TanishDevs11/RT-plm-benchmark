# CI diagnosis: `ci / pipeline`

Written 2026-10-04 during the review of PR #1.

## The question this document exists to answer

**Was `ci / pipeline` already failing on `main` before PR #1?**

**Yes.** It has failed on every push to `main` in the recorded history, and it fails
on the pre-PR commit itself when that commit is pushed to the PR branch. The
documentation change is not implicated.

## Evidence

`gh run list --branch main --limit 10`: ten consecutive `failure` conclusions, the
oldest at 2026-10-03T05:53 and the newest at 2026-10-03T18:37, every one of them a
`push` event on `main`.

The decisive comparison is on the PR branch itself, because `H-branch` received the
pre-PR commit before the README commit:

| run | head SHA | event | branch | conclusion | failing step |
| --- | --- | --- | --- | --- | --- |
| 37189640001 | `8d0d47a1` | push | H-branch | failure | Frozen split files still say what they are supposed to say |
| 37189937376 | `41871b9f` | push | H-branch | failure | Frozen split files still say what they are supposed to say |
| 37190056787 | `41871b9f` | pull_request | H-branch | failure | Frozen split files still say what they are supposed to say |

`8d0d47a1` is the merge base, that is `main`'s HEAD before the README was touched.
`41871b9f` is the contributor's commit. Both fail, at the same step, with the same
error. The failure predates the PR and is independent of it.

All three runs emit the identical error:

```
ERROR test_the_frozen_family_split_matches_what_the_harness_derives: ModuleNotFoundError: No module named 'sklearn'
tests: 13, failures: 1
##[error]Process completed with exit code 1.
```

`ci / protocol` passes on all of them.

## Root cause

A missing dependency in the workflow, not a defect in the analysis code.

`.github/workflows/ci.yml` runs two jobs. The `protocol` job installs scikit-learn:

```
pip install "numpy>=1.26" "pandas>=2.2" "scipy>=1.13" "scikit-learn>=1.5" "matplotlib>=3.9"
```

The `pipeline` job does not:

```
pip install "numpy>=1.26" "pandas>=2.2" "requests>=2.31" "openpyxl>=3.1"
```

The `pipeline` job's seventh step runs `curation/test_splits.py`. Twelve of its
thirteen tests need only numpy and pandas, which is why the job gets as far as it
does before failing. The thirteenth,
`test_the_frozen_family_split_matches_what_the_harness_derives`
(`curation/test_splits.py:228`), imports the live harness in order to prove the frozen
split file still agrees with the partition `bench/protocol.py` derives at run time:

```python
sys.path.insert(0, str(REPO_ROOT / "bench"))
from protocol import load_dataset
```

`bench/protocol.py:43` imports `compute_cls` from `evaluation/evaluate.py`, and
`evaluation/evaluate.py:55` is:

```python
from sklearn.metrics import average_precision_score
```

So the import chain `test_splits.py` to `protocol.py` to `evaluate.py` reaches
scikit-learn, which the `pipeline` job never installed. The 20 to 50 second failure
time is consistent with this: the job fails at its seventh step, not at install.

This also explains why nobody noticed locally. Every test in the chain passes on a
developer machine, where scikit-learn is present. Confirmed in this review:

```
$ python curation/test_splits.py
pass test_the_frozen_family_split_matches_what_the_harness_derives
tests: 13, failures: 0
```

`requirements.txt` pins scikit-learn; only the workflow's inline install list omits it.

## Fix

One line in `.github/workflows/ci.yml`, adding `scikit-learn>=1.5` to the `pipeline`
job's install step so it matches the `protocol` job. This is a workflow
configuration change. **No analysis code, dataset, split definition, or result
artifact is touched**, and the test that was failing is not modified or skipped: it
is allowed to run, and it passes.

Committed separately from the documentation corrections, so the two are reviewable
apart from each other.

## What this was not

Worth recording, because each was checked and ruled out:

- Not caused by the PR. Proven above on the pre-PR commit.
- Not a Python version mismatch. Both jobs pin 3.12 and the install step succeeds.
- Not a missing data file. The step reached is a test that reads committed split
  files, and the preflight step that tolerates missing inputs
  (`check_inputs.py --allow-missing`) is never reached.
- Not a repository restructuring artifact. The import paths resolve correctly; only
  the dependency is absent.

---

# Second failure, revealed once the first was fixed

Added 2026-10-04, after pushing the scikit-learn fix.

The scikit-learn fix worked. `curation/test_splits.py` now passes in CI, and the
`pipeline` job advanced three steps further. It then failed at step 10, a step that
had never been reached before:

```
pipeline  Task A embedding files are aligned and the manifest is honest
  pass test_every_embedding_file_is_in_curated_row_order
  pass test_every_embedding_matrix_has_the_right_shape_and_dtype
  FAIL test_the_manifest_describes_the_files_that_exist: the manifest was written
       against a different curated.csv than the one on disk
  pass test_the_manifest_records_one_pooling_strategy_and_no_sweep
  tests: 4, failures: 1
```

Runs 37198657831 (push) and 37198660160 (pull_request). `ci / protocol` still passes.

## This is also pre-existing, and also unrelated to the PR

Proven from git, without needing a CI run, because neither file involved is touched by
this PR. At the pre-PR commit `8d0d47a`, which is `main`'s HEAD:

| quantity | value |
| --- | --- |
| `embeddings/MANIFEST_TASKA.json` field `curated_sha256` | `5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc` |
| SHA256 of the **committed bytes** of `tasks/taskA_crossfamily/curated.csv` | `5a93b70b5ccd84e9e1586f5c8f5eb8073c22617309a7bedbfbf70d26a5ea39b3` |
| SHA256 of the **Windows working-tree bytes** of the same file | `5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc` |

The mismatch is baked into commit `8d0d47a`. `git diff --name-only 8d0d47a..HEAD`
lists only `README.md`, `.github/workflows/ci.yml` and `review/`, so nothing in this
PR can have caused it.

It was previously invisible because the scikit-learn failure aborted the job at step 7,
and this is step 10. Fixing the first failure did not create the second one; it stopped
hiding it.

## Root cause: recorded checksums are of CRLF bytes, and a fresh checkout is LF

`embeddings/test_embeddings_taskA.py:94` asserts:

```python
assert data["curated_sha256"] == sha256_of(CURATED)
```

The repository has **no `.gitattributes`**. The author's machine is Windows with
`core.autocrlf` effectively converting on checkout, so:

- `curated.csv` in the author's working tree has 58 CRLF line endings and is 64876
  bytes, hashing to `5e159976...`, which is the value recorded in the manifest;
- the same file as committed, and therefore as checked out on the Linux runner, has LF
  endings and is 64818 bytes, hashing to `5a93b70b...`.

Normalizing the working-tree bytes to LF reproduces the committed hash exactly, which
confirms line endings as the whole of the difference and rules out any content change:

```
worktree bytes: 64876  sha256: 5e159976...  (58 CRLF, 0 bare LF)
blob bytes:     64818  sha256: 5a93b70b...  (0 CRLF)
LF-normalized:  64818  sha256: 5a93b70b...  identical to the blob
```

So the test passes on the machine that wrote the manifest and cannot pass anywhere
else. The same reasoning applies to every recorded SHA256 of a **text** artifact in
this repository, including the curated-dataset hash quoted in
`reports/FINAL_REPORT.md:8`. Binary artifacts (`.npz`, `.npy`) are unaffected, which is
why the two shape and row-order tests in the same file pass.

**The data is not corrupt and no result is wrong.** The sequences themselves are
verified by a different route, 57 of 57 byte-identical to Table S1
(`reports/reconciliation.md:102-106`). What is wrong is the recording convention: a
checksum of a text file was taken after platform line-ending translation, which makes
it a property of one machine rather than of the artifact.

## Why this is not fixed in this PR

Every available fix touches something a documentation PR must not touch:

| candidate fix | why it is out of scope here |
| --- | --- |
| Regenerate `MANIFEST_TASKA.json` with the LF hash | modifies a result artifact |
| Add `.gitattributes` with `* text eol=lf` | changes how every data file materialises in every checkout, and on its own does not fix the mismatch, because the recorded hash would still be the CRLF one |
| Normalize line endings inside `sha256_of` | modifies `schemas/task_schema.py`, which is validation code, and silently changes what every recorded checksum in the repository means |
| Skip or relax the assertion | removes an integrity check, which on this project is the worst of the four |

Per the review's Phase 3 rule, this is where the review stops rather than reaching into
the benchmark. **Reported as a separate issue, not fixed here.**

The recommended fix, for that issue rather than this PR, is to do both of the first two
together in one deliberate change: add a `.gitattributes` pinning data and text
artifacts to LF, re-checkout so the working tree matches the committed bytes, then
regenerate the affected manifests and re-record the hashes, and state in
`PROGRESS.md` that the recorded checksums changed because of line-ending
normalization and not because any content changed. That is a data-integrity change and
deserves its own commit, its own review, and the owner's judgement.

## Status of `ci / pipeline` at the merge gate

Still red, and the failure is proven pre-existing and unrelated by the git evidence
above. Net effect of the fix in this PR: the job advanced from failing at step 7 of 11
to failing at step 10 of 11, with three previously unreachable steps now passing and
`curation/test_splits.py` green in CI for the first time.

| | before this PR | after |
| --- | --- | --- |
| `ci / protocol` | pass | pass |
| `ci / pipeline` | fail at step 7, `ModuleNotFoundError: sklearn` | fail at step 10, manifest checksum mismatch |
| steps passing | 6 of 11 | 9 of 11 |
