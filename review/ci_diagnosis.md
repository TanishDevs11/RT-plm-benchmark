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
