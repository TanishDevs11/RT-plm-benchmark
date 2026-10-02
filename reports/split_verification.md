# Task A split verification

Written by `curation/verify_splits_taskA.py`. The splits are frozen files, not
code that runs at model time, so that the partition is fixed before any model
exists and cannot be adjusted or re-derived once results start appearing. This
report is the check that each file says what it is supposed to say.

Curated table: `tasks/taskA_crossfamily/curated.csv`, SHA256
`5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc`.

| file | SHA256 |
| --- | --- |
| `leave_one_family_out.csv` | `bb941f55cad1c544ff4d1371e3b80ff70c73f667be365acc6da15d0210f6b381` |
| `leave_one_cluster_out_70.csv` | `08c309bf813343b4e10cab57f0de4dc76c1fd41b29e59fbe875ab89330e5e0ce` |
| `clusters_90.tsv` | `1897eb04104b1ba646b87212c437c82c558b6d51dfa6234ff6ff8a4ce12060f0` |
| `clusters_70.tsv` | `02c50c928820dbd4775c74759420f9d0c162404a49bff5844266dc44ed0a1db5` |
| `clusters_50.tsv` | `6ddd61d818309a2eda523cd28519dcc42205b92bdc7964d85d5842e87b97081f` |
| `clusters_30.tsv` | `79f9a29d6dc30c6bd2ba06f7a41f28c9ad4d13302cf6e8eabf3b17719b933ada` |

## leave-one-family-out, primary

| check | result | detail |
| --- | --- | --- |
| no id appears in both train and test, in any fold | PASS |  |
| every fold covers every row exactly once | PASS |  |
| every row is tested exactly once across the folds | PASS | tested 57 times against 57 rows |
| no sequence digest appears in both train and test | PASS |  |
| no family spans the split: each test set is exactly one family, absent from training | PASS |  |

#### Identity cluster containment

| threshold | clusters spanning train and test | holds | why |
| --- | --- | --- | --- |
| 90 percent | 0 | yes | every cluster at this threshold lies inside one fold |
| 70 percent | 0 | yes | every cluster at this threshold lies inside one fold |
| 50 percent | 0 | yes | every cluster at this threshold lies inside one fold |
| 30 percent | 6 | no | **a real limitation**: 6 folds leave a relative of the held-out set in training at this threshold |
| | | | `CRISPR-associated` shares cluster `Gs-RT`, `Tel4c-RT` |
| | | | `Group_II_Intron` shares cluster `Gs-RT`, `Tel4c-RT` |
| | | | `LTR_Retrotransposon` shares cluster `CaMV-RT` |
| | | | `Other` shares cluster `CaMV-RT`, `DRG2-RT` |
| | | | `Retron` shares cluster `Gs-RT` |
| | | | `Unclassified` shares cluster `DRG2-RT` |

### Fold properties

| quantity | value |
| --- | --- |
| folds | 7 |
| folds whose training set holds fewer than 2 actives | 0 |
| folds whose test set holds no active | 3 of 7 |

No fold has fewer than 2 actives in training, so the handling rule below does not fire for
this split. It is stated anyway, because it must not be invented later.

Folds whose test set is all negative, on which a ranking correlation is undefined:

- `CRISPR-associated`: 5 rows, 0 actives
- `Other`: 5 rows, 0 actives
- `Unclassified`: 1 row, 0 actives

## leave-one-cluster-out at 70 percent, secondary

| check | result | detail |
| --- | --- | --- |
| no id appears in both train and test, in any fold | PASS |  |
| every fold covers every row exactly once | PASS |  |
| every row is tested exactly once across the folds | PASS | tested 57 times against 57 rows |
| no sequence digest appears in both train and test | PASS |  |

#### Identity cluster containment

| threshold | clusters spanning train and test | holds | why |
| --- | --- | --- | --- |
| 90 percent | 0 | yes | every cluster at this threshold lies inside one fold |
| 70 percent | 0 | yes | every cluster at this threshold lies inside one fold |
| 50 percent | 8 | no | expected by construction: this split holds out a 70 percent cluster, which is a subset of a 50 percent cluster |
| 30 percent | 35 | no | expected by construction: this split holds out a 70 percent cluster, which is a subset of a 30 percent cluster |

### Fold properties

| quantity | value |
| --- | --- |
| folds | 49 |
| folds whose training set holds fewer than 2 actives | 0 |
| folds whose test set holds no active | 33 of 49 |

No fold has fewer than 2 actives in training, so the handling rule below does not fire for
this split. It is stated anyway, because it must not be invented later.

Folds whose test set is all negative, on which a ranking correlation is undefined:

- `cluster_A.platensis-Cas1-RT`: 1 row, 0 actives
- `cluster_AFY36037.1-RT`: 1 row, 0 actives
- `cluster_Abi-RT`: 1 row, 0 actives
- `cluster_BLV-RT`: 1 row, 0 actives
- `cluster_Bel-RT`: 1 row, 0 actives
- `cluster_CHLRE`: 1 row, 0 actives
- `cluster_CRISPRRT2-RT`: 1 row, 0 actives
- `cluster_CaMV-RT`: 1 row, 0 actives
- `cluster_DRG2-RT`: 1 row, 0 actives
- `cluster_Drg-RT`: 1 row, 0 actives
- and 23 more; the full assignment is in the split file

## The handling rules, stated once and applied uniformly

Two fold conditions need a rule. Both rules are stated here so that they are
fixed before any result exists, rather than chosen later when it is known which
choice flatters a number.

**Rule 1, a training set with fewer than 2 actives.** Such a fold cannot support a
classifier: with one positive there is nothing to separate. The fold is reported
as **undefined** and is excluded from the pooled prediction vector, with its
exclusion and its row count stated in the results table. It is never filled with
a constant, a prior, or a majority-class prediction, because each of those is an
invented prediction that would then be scored as though it were a measurement.

**Rule 2, a test set with no active.** Precision-recall area is undefined on an
all-negative test set and so is a ranking correlation against an all-zero target.
The fold's predictions still enter the pooled vector, because the pooled metric is
computed once over all 57 rows and those rows are genuine negatives that a model
must not rank highly. What is **not** done is computing a per-fold score for such
a fold and reporting it as zero, or dropping its rows from the pool. Scoring it as
zero invents a measurement; dropping it changes the denominator. Per-family
breakdowns therefore show `undefined` for these folds rather than a number.

This is why the primary split is scored by pooling predictions across folds and
computing the metric once, rather than by averaging per-fold metrics: 3 of the 7
families hold no active at all, and per-fold averaging has no defined value for
them.

## Compatibility with `bench/protocol.py`

`bench/protocol.py` does not read a split file. It loads the dataset and groups
by family inside `run_nested_lofo`, so the frozen primary split is only
compatible with the harness if it reproduces that grouping exactly. Asserting
that here is what stops the file and the harness drifting apart.

| check | result | detail |
| --- | --- | --- |
| the frozen test sets equal the partition the harness derives | PASS |  |

## Result

**All checks pass.**

What passing does not mean: the splits control sequence identity and family
membership, and nothing more. They do not remove the association between family
and activity, which is real in these data, so a model that predicts
"retroviral, therefore active" still scores well without knowing anything about
catalysis. That confound is addressed by the family-classification control in the
modelling phase, not by any split.

And as `reports/dataset_overview.md` records, the leave-one-cluster-out split at
70 percent does not clear remote homology either: four clusters cross a family
boundary at 30 percent identity, which no split defined at 70 percent can hold
out. That is a stated limitation of the panel.
