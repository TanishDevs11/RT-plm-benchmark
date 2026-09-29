# Inherited competition submission

`submission.csv` and `WRITEUP.md` are the artifacts submitted to the RT Prime
Editing Activity Prediction Challenge. They are kept here unmodified, as the object
of study for this rebuild. They are not inputs to any measurement made here, and no
number in them may be carried into a results table.

`submission.csv` is the vector that scores CLS 0.9754 on the 57 labels. The audit in
`audit/metric_report.md` uses it only as a fixed prediction vector for two
measurements that are properties of the metric rather than of the model: how much
the score moves under arbitrary tie-breaking of the 36 zero-efficiency rows, and how
wide a bootstrap interval on 57 rows is. Both of those would give the same
qualitative answer for any vector.

## A note on `data/`

The rebuild brief asked for `data/` to be kept here alongside the submission. It has
deliberately been left at the repository root instead, because the rest of the brief
requires `make reproduce` to run the pipeline from `data/` to predictions on a fresh
clone, and Phases 4 and 5 read `data/handcrafted_features.csv`,
`data/structure_features.csv`, `data/topology_features.csv`, and `data/structures/`
as raw inputs. Moving `data/` under a directory marked as not-an-input would
contradict that. The deviation is recorded here rather than made silently.

Two files inside `data/` do need treating with the same suspicion as the quarantined
code, because they are label-derived rather than raw:

- `selected_features.csv` records a feature subset chosen using all 57 labels.
- `hyperparameter_results.csv` records hyperparameters chosen the same way.

Using either as an input would import a selection made on held-out labels into the
rebuild, which is exactly the failure being corrected. The nested protocol therefore
performs its own feature selection and hyperparameter selection inside each training
fold, and ignores both files.

`data/esm2_embeddings.npz` is a third case. It is present and 1280 dimensional,
consistent with ESM-2 650M, but the script that generated it has not been located in
the inherited tree. Until that is resolved it is treated as an artifact of unknown
provenance, and `make reproduce` cannot claim to regenerate it.
