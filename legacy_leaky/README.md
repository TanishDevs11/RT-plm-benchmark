# Quarantined inherited code and artifacts

Nothing in this directory may be used to produce, support, or calibrate any number
in any results table in this repository. These files are retained as evidence, not
as tools. They are the object of the leakage audit in `audit/`, and deleting them
would destroy the record of what actually happened.

## Why these files are here

The inherited pipeline optimized the competition metric directly against the same
57 labels it was scored on. The clearest instance is `fast_opt.py`, which builds an
objective returning the negation of `compute_cls(seq["active"], y_score,
seq["pe_efficiency_pct"])` over all 57 rows and hands it to
`scipy.optimize.differential_evolution` with 29 blend weights plus one power
exponent. It also seeds its starting point by parsing the previously fitted
constants back out of `experiments/calibrated_lofo_predictions.py`, so each run
begins from the previous run's optimum. That is a hill climb on the test labels,
and its output is the value of an objective rather than an estimate of
generalization.

`calibrated_lofo_predictions.py` carries the result of that climb frozen into
source as `RANK_POWER` and a 29 entry `RANK_BLEND_WEIGHTS` dictionary at 16
significant figures. A constant specified to 16 digits was not chosen, it was
fitted, and it encodes the held-out labels it was fitted against.

`history_meta_stack.py` stacks prediction vectors recovered from earlier git
commits, each of which had itself been tuned against the same 57 labels, so the
stacking compounds the problem rather than averaging it away.

`materialize_final_submission.py` retrains nothing. It reads a stored CSV and
applies a fixed score threshold.

`shuffle_labels_test.py` shuffles labels inside the base RandomForest only. It
cannot detect leakage introduced by the downstream blend weight search, because
that search sits outside the code path it perturbs. It is a real test of the wrong
thing.

## Scope of the quarantine

The whole of the inherited `experiments/` and `results/` directories was moved
here, rather than only the files matching the known leaky patterns. None of this
code is an input to the rebuild, so a superset is safer than a pattern match, and
moving everything avoids the risk that a file with an innocuous name quietly
carries a fitted constant. The audit classification of each file is recorded in
`audit/leakage_report.md`.

## What was deleted rather than quarantined

`temp_artifacts/` was deleted, along with a committed `.pyc` file. These were
scratch outputs and build residue with no evidentiary value. They remain
recoverable from the inherited git history, which is preserved in full, so nothing
is actually lost.
