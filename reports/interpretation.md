# Task A interpretation

Written by `bench/interpret_taskA.py`.

Source: `tasks/taskA_crossfamily/curated.csv`, SHA256
`5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc`.

## The gate

A representation is interpreted here only if it clears, at once, its own
dimensionality-matched Gaussian noise control and the search-capacity null at its
matched free-parameter count. Interpreting a model that loses to protein length is
interpreting noise, and a feature-importance plot of such a model is actively
misleading: it looks exactly like the plot of a model that works.

The search-capacity bar is a CLS of 0.4433, the p95 of what a one-free-parameter
search reaches on pure Gaussian noise.

| gate | metric | floor it must clear | representations clearing it |
| --- | --- | --- | --- |
| CLS | CLS | the larger of its noise control and the K=1 search-capacity null p95 of 0.4433 | 0 |
| PR-AUC, classification only | PR-AUC | the largest of its noise control, the positive prevalence of 0.3684, and its permuted-label p95 where measured | 1 |

The second gate exists because CLS is the harmonic mean of PR-AUC and a weighted
Spearman against `pe_efficiency_pct`. Per the Gate G2 ruling that column is a
digitization of Figure S1A, so a representation that separates actives well but
does not reproduce the digitized ordering scores a CLS of zero, the harmonic mean
flooring there. Failing the CLS gate for that reason is a statement about the
figure, not about the representation. There is no search-capacity null for PR-AUC,
because `bench/search_null.py` measures CLS; that gap is stated rather than filled
with the CLS bar, which would compare two different quantities.

## Representations that cleared a gate

| representation | head | metric | score | noise control | chance floor | permuted p95 | margin |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `kmer4` | classification | pr_auc | 0.6212 | 0.4458 | 0.3684 | 0.5398 | +0.0814 |

Feature attribution for a representation that clears a gate is the next step
and is deliberately not implemented in this script. Writing an attribution
path speculatively, for a case that might not arise, would mean shipping
untested code that produces a plot; and a plot is believed. The two things to
compute first are the contribution of length specifically and the contribution
of family-correlated dimensions, because those are the two confounds the
earlier phases measured directly.

Note what clearing the PR-AUC gate does and does not license. It licenses the
claim that the representation separates active from inactive enzymes above its
own noise control. It does not license a claim about predicting efficiency, and
it does not by itself rule out that the separation is lineage: a representation
that encodes family will separate actives in a panel where 12 of 18 retroviral
enzymes are active and 0 of 15 across three other families are. The
family-classification control in `reports/representation_diagnostics.md` is
what speaks to that, and it shows these representations classify family far
better than they classify activity.

## Attribution, for the representations that cleared the PR-AUC gate

The head is a logistic regression, so Shapley attributions are **exact** rather
than estimated: for a linear model the Shapley value of a feature is its
coefficient times its centred value, which is what a linear SHAP explainer
computes. Nothing here is sampled and no SHAP package is used.

Attributions are computed **out of fold**. For each held-out family the
configuration its own inner loop selected is refitted on the training families and
attributions are taken for the held-out rows only, so they describe the models the
benchmark actually scored rather than one fitted on all 57 labels.

### `kmer4`

| quantity | value | how to read it |
| --- | --- | --- |
| features | 20115 | against 57 rows |
| PR-AUC | 0.6212 | its noise control is 0.4458, margin +0.0814 |
| out-of-fold score against sequence length | Spearman +0.5212, p 3.23e-05 | **the row that matters.** A score strongly ranked by length is a length detector, and length is free |
| attribution mass in the top decile of family-explained features | 0.1638 | against a feature share of 0.1000. Far above means the model leans on lineage |
| attribution mass in the top 1 percent of features | 0.0656 | against a feature share of 0.0100. Low means the signal is spread thinly, so no individual feature is doing the work |
| per-feature importance against family-explained variance | Spearman +0.2055, p 1.05e-190 | positive means the fit preferentially used lineage dimensions |

Top 15 features by mean absolute out-of-fold attribution:

| rank | feature | mean absolute attribution | share of mass | family-explained variance |
| --- | --- | --- | --- | --- |
| 1 | `QKLL` | 0.01418 | 0.00079 | 0.2215 |
| 2 | `SAQK` | 0.01359 | 0.00076 | 0.2596 |
| 3 | `NLLS` | 0.01305 | 0.00073 | 0.2141 |
| 4 | `LKDA` | 0.01208 | 0.00067 | 0.2809 |
| 5 | `DGSS` | 0.01152 | 0.00064 | 0.5230 |
| 6 | `NSPT` | 0.01129 | 0.00063 | 0.5232 |
| 7 | `HRDL` | 0.01118 | 0.00062 | 0.1935 |
| 8 | `AELI` | 0.01015 | 0.00057 | 0.1777 |
| 9 | `DEAL` | 0.00928 | 0.00052 | 0.1767 |
| 10 | `AVAR` | 0.00924 | 0.00051 | 0.1562 |
| 11 | `RLAE` | 0.00883 | 0.00049 | 0.1027 |
| 12 | `DILI` | 0.00864 | 0.00048 | 0.0931 |
| 13 | `VLDL` | 0.00846 | 0.00047 | 0.3870 |
| 14 | `LERP` | 0.00836 | 0.00047 | 0.1440 |
| 15 | `DLKD` | 0.00824 | 0.00046 | 0.4802 |

**Read this ranking with care.** With 20115 features and 57 rows no individual
coefficient is estimable, so the ranking describes which directions a
regularized fit happened to use, not which features matter. The concentration
row above is the honest summary: mass spread thinly across thousands of
features is not a motif finding.

## Failure analysis

Run on `physicochemical`, the classification head's highest-scoring representation at a CLS of 0.3739.
Errors are expressed as a signed difference in rank percentile, predicted minus
true, so the scale is comparable across heads and the sign says whether an enzyme
was ranked too high or too low.

### Which families are predicted worst

| family | n | actives | mean absolute error | mean signed error |
| --- | --- | --- | --- | --- |
| CRISPR-associated | 5 | 0 | 0.5214 | +0.5214 |
| LTR_Retrotransposon | 11 | 2 | 0.4416 | -0.1104 |
| Unclassified | 1 | 0 | 0.4286 | +0.4286 |
| Other | 5 | 0 | 0.3893 | -0.2107 |
| Retroviral | 18 | 12 | 0.3522 | -0.1458 |
| Retron | 12 | 5 | 0.3348 | +0.2128 |
| Group_II_Intron | 5 | 2 | 0.2179 | -0.1393 |

### Do the errors track length, or novelty?

| predictor of absolute error | Spearman | p |
| --- | --- | --- |
| sequence length | +0.1200 | 0.3739 |
| distance from the panel centroid in representation space | +0.0499 | 0.7127 |

The second row is a proxy for how far a held-out enzyme sits from what the
training folds contained. It is a z-scored Euclidean distance from the panel
centroid, which is a crude measure: it treats every dimension as equally
informative and it is computed over the whole panel rather than per fold. A
stronger version would use the per-fold training centroid, and that is a stated
limitation rather than a result.

### The worst-ranked individual enzymes

| enzyme | family | active | true efficiency | predicted rank percentile | true rank percentile | signed error |
| --- | --- | --- | --- | --- | --- | --- |
| `Sau1-RT` | Retron | no | 0.0 | 0.893 | 0.071 | +0.821 |
| `HIVpol+MMLVRNaseH_RT` | Retroviral | no | 0.0 | 0.768 | 0.000 | +0.768 |
| `A.platensis-Cas1-RT` | CRISPR-associated | no | 0.0 | 0.857 | 0.107 | +0.750 |
| `Ty3-RT` | LTR_Retrotransposon | yes | 9.0 | 0.089 | 0.839 | -0.750 |
| `CRISPRRT2-RT` | CRISPR-associated | no | 0.0 | 0.964 | 0.268 | +0.696 |
| `MMTV-RT` | Retroviral | yes | 19.0 | 0.250 | 0.893 | -0.643 |
| `ROSE-CRISPR-RT` | CRISPR-associated | no | 0.0 | 0.982 | 0.339 | +0.643 |
| `Line1-RT` | LTR_Retrotransposon | no | 0.0 | 1.000 | 0.357 | +0.643 |
| `Vp96-RT` | Retron | yes | 8.0 | 0.196 | 0.821 | -0.625 |
| `ASLV-RT` | Retroviral | yes | 4.5 | 0.179 | 0.768 | -0.589 |

## Figures

| figure | what it shows |
| --- | --- |
| `figures/taskA_failure_by_family.png` | signed error by family, with the family median |
| `figures/taskA_error_vs_length.png` | absolute error against length and against distance from the panel centroid |

## What the failure analysis does and does not say

It describes where this particular model's errors fall. It does not diagnose why
the representations fail, because with 21 positives, a CLS-weighted effective
sample size of 11.338, and three of seven folds holding no active at all, the
panel cannot distinguish between the two live explanations: that the
representations carry no activity signal, and that they carry some but the panel
is too small and too confounded to detect it. Those are different conclusions with
different consequences, and this dataset does not separate them.

What the earlier phases did establish, and what the failure analysis is consistent
with, is that the representations encode lineage and length rather than function:
ESM-2 650M classifies family at 0.8197 against a majority baseline of 0.3214, and
its leading principal component tracks sequence length at Spearman -0.7681. A
representation that is mostly a lineage-and-length encoding has little left to
offer a family-held-out activity task, which is exactly what these results look
like.
