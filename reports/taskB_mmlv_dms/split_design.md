# Task B split design

Written 2026-10-03. Covers the four frozen split regimes for the M-MLV RT saturated
mutagenesis task, and the one family of regimes that is deliberately absent.

The split files exist and are verified. **The activity values do not**, so no result has
been computed under any of them; see `tasks/taskB_mmlv_dms/PROVENANCE.md`. The splits are
written now because they are fully determined by the library design, which the preprint
states exactly, and freezing them before any label arrives is the point of freezing them
at all.

## Why identity and cluster splits are undefined here, not merely difficult

**There is no MMseqs2 clustering anywhere in Task B, and there must never be.**

Every row is a single amino acid substitution in the same 498-residue protein. Two
variants therefore differ at no more than two positions, so pairwise identity is at least
496 of 498, which is 99.6 percent, and a variant against the wild type is 497 of 498, or
99.8 percent. At any threshold a sequence-identity clustering tool can express, all 1046
rows collapse into one cluster.

That makes the regime undefined rather than hard. A leave-one-cluster-out split over one
cluster has one fold whose training set is empty. A 90, 70, 50 or 30 percent identity
threshold does not partition this set at all. Reporting "no cluster spans the split" here
would be true and completely vacuous, and reporting an identity-controlled result would
imply a control that does not exist.

This matters because Task A **does** use identity clustering, and its
`curation/cluster_redundancy.py` is a short import away. The failure mode to prevent is a
later contributor, reasonably, adding Task B to `TASK_SOURCES` in that script for
consistency. The reason it must not happen is recorded here and in the task's provenance.

What replaces it: the three structural regimes below. Redundancy in this dataset is not
sequence identity, it is **position identity**, and that is what the splits control.

## The regimes

### 1. `position_held_out.csv`, primary

5 folds over 55 positions, assigned round robin within each stretch so every fold draws
from both libraries and the folds stay balanced. All variants at a position go to the same
fold.

**Prevents:** learning a position's mean effect from its other 18 substitutions and then
being scored on the 19th. That is the dominant leak in variant effect prediction, and it
is what the random split below exists to quantify.

**Does not prevent:** learning from the immediate structural neighbours of a held-out
position. A stricter variant would hold out contiguous blocks of positions, which also
withholds the neighbours. That is a harder regime; it is noted here rather than used,
because the brief asks for one position-held-out regime and round robin is the standard
grouped form of it.

### 2. `stretch_held_out.csv`, the headline generalization test

2 folds. Train on Library Stretch 1 (S60 to Q84, 475 variants), test on Stretch 2 (N95 to
D124, 570 variants), then the reverse.

**Prevents:** everything the position regime prevents, plus any transfer from the
immediate sequence neighbourhood, since the two stretches are separated by ten residues
and are different regions of the Fingers domain.

**Does not prevent, and this is a real caveat:** the two libraries were screened
separately, and the preprint does not say whether the scaling to the interval from -1 to 1
was computed within each library or across both. If it was computed within each, then a
model trained on one stretch and tested on the other is also crossing two normalizations,
and part of any error is a scale difference rather than a prediction failure. This must be
stated wherever the stretch-held-out result is reported, and it is one of the three
questions in `data_acquisition/AUTHOR_REQUEST.md`.

### 3. `aa_held_out.csv`, secondary

20 folds, one per target residue. All substitutions **to** a given amino acid are held out
together.

**Prevents:** learning the chemistry of a substitution type from other examples of it.
A model that has never seen any variant mutated to tryptophan must predict those from
substitution chemistry rather than from memorised examples.

**Does not prevent:** position identity. Each fold's test set spans both stretches and
many positions, and the training set contains other substitutions at those same positions.
That is deliberate: the point is to isolate substitution chemistry from position identity,
not to confound the two. Fold test sizes run from 49 to 55 variants.

### 4. `random_variant_LEAKY_DO_NOT_REPORT.csv`, a leaky reference only

5 folds, variants shuffled with `GLOBAL_SEED`.

**This split is labelled leaky in its filename and in two columns on every one of its 5230
rows**, `leaky = yes` and a `never_report` column naming the leak. It exists to quantify
how much optimism a naive split buys, and for nothing else.

**Prevents:** nothing. Variants at the same position appear in both training and test, so
a model can learn each position's mean effect from its other substitutions and be scored
on the remainder.

The gap between this and `position_held_out` is a reportable finding in its own right, and
the clearest available demonstration of why the random split is unusable. The
position-mean baseline makes the same point more sharply: predicting each variant as the
mean of the other variants at its position should score very highly here and is
**undefined** under `position_held_out`, because there are no other variants at that
position in training. Reporting both outcomes side by side is the intended use.

## Verification

Every regime was checked after writing:

| regime | rows | identifiers | folds | every row tested exactly once |
| --- | --- | --- | --- | --- |
| `position_held_out` | 5230 | 1046 | 5 | yes |
| `stretch_held_out` | 2092 | 1046 | 2 | yes |
| `aa_held_out` | 20920 | 1046 | 20 | yes |
| `random_variant_LEAKY_DO_NOT_REPORT` | 5230 | 1046 | 5 | yes |

`curation/test_splits.py` asserts the structural properties of the first two and the leak
in the fourth, and asserts that the identifier set matches the one derived from the
reference frame.

## The identifier set, and one open count

1046 identifiers: 1045 variants plus one wild type. The 1045 is exact and derived rather
than assumed. The preprint states the stretches as S60-Q84 and N95-D124, which is 25 and
30 positions, and 19 non-wild-type substitutions per position gives 475 and 570, which are
the two counts the preprint itself reports.

**One count is open.** The figure legend reads "Library Stretch 1 (475 variants + WT) and
Library Stretch 2 (570 variants + WT)", which admits a wild-type measurement per library
rather than one shared. The split files carry a single `B_wt`. If the tables arrive with
one wild type per library the total is 1047 and each regime needs one row added. Recorded
so the discrepancy is noticed at parse time rather than absorbed.

## What these splits are not

They are partitions, not results. No model has been trained under any of them, because the
per-variant activity values were not deposited with the preprint and are not available
from any of the eleven routes tried. The splits will become usable the moment Tables S6
and S7 exist, and the parser will reconcile whatever arrives against the frozen identifier
set, logging any variant in one and not the other.
