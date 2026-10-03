# Task B HIV-1 RT split verification

Written by `curation/verify_splits_hivrt.py`. The splits are frozen files, not
code that runs at model time.

Primary dataset: `filtered`, 4116 class-qualified isolates carrying 16325 phenotype results.

Chosen identity threshold: **99 percent**, by the rule recorded in
`tasks/taskB_hivrt/splits/split_summary.json`.

| file | SHA256 |
| --- | --- |
| `identity_cluster.csv` | `9346c3d18ee7b5261d6eab19c435b9e9f7b34df64c897f46511d91c80c2ddcba` |
| `drm_pattern_held_out.csv` | `31e730dfcea71b9dc11270328304690b97ff1024e73c38c147a5d3dd7cfc3229` |
| `subtype_held_out.csv` | `866bf3d2e62cb70282134702b29aa2bc2beba96fa420b585ff8d473abb994375` |
| `random_LEAKY_DO_NOT_REPORT.csv` | `9d07a4da2747989b386f468efbdffa52841ae965ae9809d2e7aece8647eb90ac` |

## identity_cluster, primary

| check | result | detail |
| --- | --- | --- |
| no isolate appears in both train and test | PASS |  |
| every fold covers every isolate exactly once | PASS |  |
| no fold has an empty test set | PASS |  |

### Identity cluster containment

| threshold | folds whose test cluster also appears in training | holds | why |
| --- | --- | --- | --- |
| 99 percent | 0 of 5 | yes | every cluster at this threshold lies inside one fold |
| 98 percent | 5 of 5 | no | expected by construction: this split holds out 99 percent clusters, and at 98 percent the largest single cluster already holds 13.3 percent of the panel, so no split can hold it out |
| 95 percent | 5 of 5 | no | expected by construction: this split holds out 99 percent clusters, and at 95 percent the largest single cluster already holds 50.0 percent of the panel, so no split can hold it out |
| 90 percent | 5 of 5 | no | expected by construction: this split holds out 99 percent clusters, and at 90 percent the largest single cluster already holds 84.9 percent of the panel, so no split can hold it out |

### Label distribution across test folds

| fold | isolates in test | phenotype results | median log10 fold |
| --- | --- | --- | --- |
| `cluster_fold_0` | 868 | 3265 | 0.2788 |
| `cluster_fold_1` | 802 | 3265 | 0.2304 |
| `cluster_fold_2` | 800 | 3265 | 0.1761 |
| `cluster_fold_3` | 842 | 3265 | 0.2304 |
| `cluster_fold_4` | 804 | 3265 | 0.2041 |

Spread of the fold medians: 0.1027 log10 units, a factor of 1.27 in fold resistance.

Label distribution across folds is comparable.

## drm_pattern_held_out

| check | result | detail |
| --- | --- | --- |
| no isolate appears in both train and test | PASS |  |
| every fold covers every isolate exactly once | PASS |  |
| no fold has an empty test set | PASS |  |

### Identity cluster containment

| threshold | folds whose test cluster also appears in training | holds | why |
| --- | --- | --- | --- |
| 99 percent | 4 of 4 | no | **a real limitation** at this threshold |
| 98 percent | 4 of 4 | no | **a real limitation** at this threshold |
| 95 percent | 4 of 4 | no | **a real limitation** at this threshold |
| 90 percent | 4 of 4 | no | **a real limitation** at this threshold |

### Label distribution across test folds

| fold | isolates in test | phenotype results | median log10 fold |
| --- | --- | --- | --- |
| `held_out_K65R` | 126 | 533 | 0.4771 |
| `held_out_M184V` | 1826 | 7281 | 0.4150 |
| `held_out_TAM1` | 892 | 3561 | 0.6335 |
| `held_out_TAM2` | 188 | 757 | 0.5563 |

Spread of the fold medians: 0.2185 log10 units, a factor of 1.65 in fold resistance.

## subtype_held_out

| check | result | detail |
| --- | --- | --- |
| no isolate appears in both train and test | PASS |  |
| every fold covers every isolate exactly once | PASS |  |
| no fold has an empty test set | PASS |  |

### Identity cluster containment

| threshold | folds whose test cluster also appears in training | holds | why |
| --- | --- | --- | --- |
| 99 percent | 2 of 3 | no | **a real limitation** at this threshold |
| 98 percent | 2 of 3 | no | **a real limitation** at this threshold |
| 95 percent | 3 of 3 | no | **a real limitation** at this threshold |
| 90 percent | 3 of 3 | no | **a real limitation** at this threshold |

### Label distribution across test folds

| fold | isolates in test | phenotype results | median log10 fold |
| --- | --- | --- | --- |
| `held_out_subtype_A` | 35 | 76 | 0.3323 |
| `held_out_subtype_B` | 3975 | 15884 | 0.2304 |
| `held_out_subtype_G` | 30 | 109 | -0.0969 |

Spread of the fold medians: 0.4292 log10 units, a factor of 2.69 in fold resistance.

## random, LEAKY reference only

| check | result | detail |
| --- | --- | --- |
| no isolate appears in both train and test | PASS |  |
| every fold covers every isolate exactly once | PASS |  |
| no fold has an empty test set | PASS |  |

### Identity cluster containment

| threshold | folds whose test cluster also appears in training | holds | why |
| --- | --- | --- | --- |
| 99 percent | 5 of 5 | no | **this is the leak the random split exists to demonstrate** |
| 98 percent | 5 of 5 | no | **this is the leak the random split exists to demonstrate** |
| 95 percent | 5 of 5 | no | **this is the leak the random split exists to demonstrate** |
| 90 percent | 5 of 5 | no | **this is the leak the random split exists to demonstrate** |

### Label distribution across test folds

| fold | isolates in test | phenotype results | median log10 fold |
| --- | --- | --- | --- |
| `random_fold_0` | 824 | 3242 | 0.2173 |
| `random_fold_1` | 823 | 3261 | 0.1761 |
| `random_fold_2` | 823 | 3268 | 0.2553 |
| `random_fold_3` | 823 | 3285 | 0.2041 |
| `random_fold_4` | 823 | 3269 | 0.2553 |

Spread of the fold medians: 0.0792 log10 units, a factor of 1.20 in fold resistance.

Label distribution across folds is comparable.

## The clustering sweep, and why 99 percent

These are variants of one gene in one virus, so pairwise identity is high
throughout and the thresholds that work for a cross-family panel do not partition
this set at all. The sweep shows that directly.

| threshold | clusters | largest cluster | share of the panel in it | singletons |
| --- | --- | --- | --- | --- |
| 99 percent | 3323 | 176 | 4.3 percent | 3060 |
| 98 percent | 2216 | 548 | 13.3 percent | 1722 |
| 95 percent | 130 | 2057 | 50.0 percent | 38 |
| 90 percent | 7 | 3496 | 84.9 percent | 2 |

**At 95 percent identity half the panel is one cluster, and at 90 percent 85
percent of it is.** Those thresholds cannot produce folds: a single cluster would
have to be either entirely in training or entirely in test, and either way one
fold is almost the whole dataset.

Selection rule, fixed before looking at any result: the tightest threshold whose largest cluster holds less than 10 percent of all isolates, which is half of one fold, and which yields at least 10 clusters.

That gives **99 percent**, with 3323 clusters whose largest holds
4.3 percent of the panel. It is a weaker control than a cross-family identity
split, and it is the strongest one this data admits. The shape of that curve, from
3323 clusters at 99 percent to 7 at 90, is the material for the leakage analysis.

## What these splits control and what they do not

| regime | controls | does not control |
| --- | --- | --- |
| `identity_cluster` | isolates, and identity clusters at 99 percent | relatedness below 99 percent, which is most of the panel; patient identity, which the filtered sets do not record |
| `drm_pattern_held_out` | the named resistance package, entirely absent from training | other resistance packages that co-occur with it; the held-out set is not a random sample, so its label distribution differs by construction |
| `subtype_held_out` | the named subtype | almost nothing, because the panel is 96.6 percent subtype B; the non-B test sets are tiny |
| `random` | **isolate identity only** | everything else; it is a leaky reference and is labelled so in its filename and on every row |

**Patient-level grouping is the control this task most wants and cannot have in its
primary analysis.** The filtered sets carry no `PtID`. The unfiltered sets do, and
the source's own filtering removes only same-patient viruses that share a major
resistance pattern, so patient structure survives into the filtered sets
unmeasured. Any result here is therefore an upper bound relative to what a
patient-held-out split would give.

## Result

**All enforced checks pass.**

