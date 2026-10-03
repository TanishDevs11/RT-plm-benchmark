# Task B HIV-1 RT split design

Written 2026-10-03. The frozen split files are in `tasks/taskB_hivrt/splits/`, and the
checks against them are in `reports/taskB_hivrt/split_verification.md`.

## The one non-negotiable: isolate-level grouping

Each isolate carries up to 7.63 phenotype results, one per drug assayed on it. A split
that works at the row level would put an isolate's 3TC measurement in training and its AZT
measurement in test, sharing a 560-residue sequence across the boundary. That is leakage
with no interpretation under which it is acceptable.

Every regime here is therefore keyed on the class-qualified isolate rather than the row.
The class qualification matters: an isolate id can appear in both the NRTI and the NNRTI
dataset with a different reconstructed sequence, because the two files report different
position ranges, so `NRTI:12345` and `NNRTI:12345` are distinct units.

## Why standard identity thresholds do not work, measured

These are variants of one gene in one virus. The clustering sweep shows what that does:

| threshold | clusters | largest cluster | share of the panel in it | singletons |
| --- | --- | --- | --- | --- |
| 99 percent | 3323 | 176 | 4.3 percent | 3060 |
| 98 percent | 2216 | 548 | 13.3 percent | 1722 |
| 95 percent | 130 | 2057 | **50.0 percent** | 38 |
| 90 percent | 7 | 3496 | **84.9 percent** | 2 |

**At 95 percent identity half the panel is a single cluster; at 90 percent, 85 percent of
it is.** Those thresholds cannot produce folds at all: one cluster would have to go
entirely into training or entirely into test, and either way one fold is almost the whole
dataset.

This is the opposite failure from the M-MLV task, where every variant collapsed into one
cluster at any threshold and clustering was undefined. Here clustering is defined but only
at the very tight end, and the threshold has to be chosen rather than taken from
convention.

**Selection rule, fixed before any result was looked at:** the tightest threshold whose
largest cluster holds less than 10 percent of all isolates, which is half of one fold, and
which yields at least 10 clusters. That selects **99 percent**.

MMseqs2 `easy-cluster`, commit `8cc5ce36`, `-c 0.8 --cov-mode 0 -s 7.5`. Bidirectional
coverage is used here, unlike the Task A cross-family panel, because these are all the
same gene at the same length and containment is not the redundancy of interest.

## The four regimes

### 1. `identity_cluster.csv`, primary

5 folds, whole 99 percent identity clusters assigned to folds by greedy largest-first
balancing so the folds stay comparable in size. Verified: 3265 phenotype results in every
fold, and fold median log10 fold resistance spanning 0.1027, a factor of 1.27.

**Controls:** isolate identity, and sequence identity at 99 percent.

**Does not control:** relatedness below 99 percent, which is most of the panel. The
verification reports this explicitly rather than claiming a control that does not exist:
at 98, 95 and 90 percent every fold shares a cluster with training, and that is
unavoidable rather than a defect, because at those thresholds a single cluster already
exceeds a fold.

### 2. `drm_pattern_held_out.csv`

One fold per named resistance package, holding out every isolate that carries the complete
package.

| pattern | mutations | isolates held out |
| --- | --- | --- |
| TAM1 | M41L, L210W, T215Y | 892 |
| TAM2 | D67N, K70R, T215F, K219Q | 188 |
| M184V | M184V | 1826 |
| K65R | K65R | 126 |

**This is the clinically meaningful question.** Thymidine analogue mutations travel
together under treatment selection, so a model can learn the package without learning any
causal contribution. Holding one out asks whether it generalises to a resistance mechanism
it has not seen.

**Does not control:** other packages that co-occur with the held-out one. And the held-out
set is not a random sample, so its label distribution differs from training by
construction; that is the point of the regime and it means the score is not comparable to
a cluster-split score without saying so.

### 3. `subtype_held_out.csv`

One fold per subtype with at least 20 isolates.

| subtype | isolates |
| --- | --- |
| B | 3975 |
| A | 35 |
| G | 30 |
| C | 17 |
| CRF02_AG | 16 |
| Unknown | 15 |

**The panel is 96.6 percent subtype B.** That is itself the finding: this regime cannot
support a claim about cross-subtype generalization, because every non-B test set is tiny.
It is included because the brief asks for a realistic distribution shift where the metadata
supports one, and because the subtype composition bounds every generalization claim the
task can make. Holding out B leaves 141 isolates to train on, which is a different and
much harder problem than the others and must not be compared with them directly.

Subtype comes from the unfiltered sets; the filtered sets carry no subtype column, so the
annotation is joined by isolate id.

### 4. `random_LEAKY_DO_NOT_REPORT.csv`, a leaky reference only

5 folds, isolates shuffled with `GLOBAL_SEED`. **Labelled leaky in the filename and in two
columns on every row**, `leaky = yes` and a `never_report` column naming the leak.

**Controls:** isolate identity, and nothing else.

**Does not control:** identity clusters. Verification confirms all 5 folds share a 99
percent cluster between training and test, which is exactly the leak the regime exists to
demonstrate.

Most published results on this dataset use something close to this split. The gap between
it and `identity_cluster` is the quantity the leakage analysis exists to measure, and it is
the contribution this task offers, because the predictive numbers themselves are two
decades old.

## What no regime here controls

**Patient identity.** The filtered sets carry no `PtID`. The unfiltered sets do, and the
source's own filtering removes only same-patient viruses that share a major resistance
mutation pattern, so patient structure survives into the filtered sets unmeasured.

Patient grouping is the control this task most wants and cannot have in its primary
analysis. Every result on the filtered sets is therefore an **upper bound** relative to
what a patient-held-out split would give, and that has to be stated wherever a number from
this task is reported.

## What the splits are not

They are partitions, not results. No model has been trained under any of them at the time
of writing.
