# Task B audit: HIV-1 RT drug susceptibility phenotype

Written by `curation/audit_hivrt.py`. Descriptive only: nothing here is fitted,
selected or predicted.

Source: `tasks/taskB_hivrt/curated.csv`, SHA256 `556b48aaeadebd230910134636888bd56a185894b349eac49d2d47807bf08caf`.

**This dataset is not a deep mutational scan.** Each row is a clinical or
laboratory isolate carrying many substitutions at once, and correlation here is
not causal attribution of effect to individual mutations.

## What bounds every later claim

Three numbers, first because they are the constraints rather than the results.

| quantity | value | consequence |
| --- | --- | --- |
| assay reproducibility ceiling, Spearman between repeated measurements of the same sequence | **0.8622** over 292 replicate pairs | no model may be credited for a correlation above this; it is the assay's own agreement with itself |
| mean absolute difference between replicates | 0.2648 log10 units | a predicted value closer than this to a measurement is inside the noise |
| phenotype results per isolate, worst case | 7.63 in unfiltered/NRTI | rows greatly outnumber independent sequences, so **every split must group at isolate level**; a row-level split leaks outright |

## 1. Counts per drug

`n` is the number of non-missing phenotype results. The three susceptibility bands
use fold resistance cutoffs of 3 and 10, stated here once and used throughout.

| dataset | class | drug | n | median log10 | median fold | max fold | below 3x | 3x to 10x | at or above 10x |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| filtered | NNRTI | `DOR` | 130 | 0.681 | 4.80 | 210.8 | 46 | 35 | 49 |
| filtered | NNRTI | `EFV` | 2168 | 0.255 | 1.80 | 1500.0 | 1170 | 210 | 788 |
| filtered | NNRTI | `ETR` | 998 | 0.041 | 1.10 | 100.0 | 715 | 156 | 127 |
| filtered | NNRTI | `NVP` | 2052 | 0.550 | 3.55 | 200.0 | 999 | 86 | 967 |
| filtered | NNRTI | `RPV` | 311 | 0.301 | 2.00 | 200.0 | 193 | 55 | 63 |
| filtered | NRTI | `3TC` | 1839 | 1.079 | 12.00 | 200.0 | 675 | 225 | 939 |
| filtered | NRTI | `ABC` | 1731 | 0.519 | 3.30 | 100.0 | 804 | 797 | 130 |
| filtered | NRTI | `AZT` | 1853 | 0.230 | 1.70 | 2400.0 | 1019 | 226 | 608 |
| filtered | NRTI | `D4T` | 1846 | 0.114 | 1.30 | 100.0 | 1508 | 296 | 42 |
| filtered | NRTI | `DDI` | 1849 | 0.176 | 1.50 | 100.0 | 1686 | 135 | 28 |
| filtered | NRTI | `TDF` | 1548 | 0.000 | 1.00 | 51.0 | 1376 | 150 | 22 |
| unfiltered | NNRTI | `DOR` | 322 | 0.756 | 5.70 | 50000.0 | 105 | 79 | 138 |
| unfiltered | NNRTI | `EFV` | 4222 | 0.602 | 4.00 | 24630.3 | 1964 | 499 | 1759 |
| unfiltered | NNRTI | `ETR` | 2002 | 0.176 | 1.50 | 7381.9 | 1263 | 389 | 350 |
| unfiltered | NNRTI | `NVP` | 4170 | 1.220 | 16.60 | 6659.0 | 1689 | 302 | 2179 |
| unfiltered | NNRTI | `RPV` | 829 | 0.398 | 2.50 | 90090.0 | 449 | 189 | 191 |
| unfiltered | NRTI | `3TC` | 5161 | 1.579 | 37.90 | 5000.0 | 1406 | 648 | 3107 |
| unfiltered | NRTI | `ABC` | 4878 | 0.491 | 3.10 | 200.0 | 2362 | 2088 | 428 |
| unfiltered | NRTI | `AZT` | 5104 | 0.415 | 2.60 | 6666.0 | 2617 | 995 | 1492 |
| unfiltered | NRTI | `D4T` | 4993 | 0.114 | 1.30 | 382.0 | 4152 | 696 | 145 |
| unfiltered | NRTI | `DDI` | 5041 | 0.176 | 1.50 | 200.0 | 4290 | 590 | 161 |
| unfiltered | NRTI | `TDF` | 4328 | 0.000 | 1.00 | 120.0 | 3769 | 497 | 62 |

Fold resistance is approximately log-normal, so **log10 fold resistance is the
modelling scale** and every score in this task is computed on it.

## 2. Isolates against phenotype results

| dataset and class | results | isolates | results per isolate |
| --- | --- | --- | --- |
| filtered/NNRTI | 5659 | 2272 | 2.49 |
| filtered/NRTI | 10666 | 1844 | 5.78 |
| unfiltered/NNRTI | 11545 | 4804 | 2.40 |
| unfiltered/NRTI | 29505 | 3867 | 7.63 |

This ratio is the reason **isolate-level grouping is mandatory in every split**.
A split that puts an isolate's 3TC row in training and its AZT row in test shares
a sequence across the boundary, which is leakage with no redeeming interpretation.

## 3. Mutations per isolate

| dataset | n | min | median | q3 | max | isolates with exactly one mutation |
| --- | --- | --- | --- | --- | --- | --- |
| filtered | 4139 | 0 | 15 | 20 | 45 | 106 |
| unfiltered | 10282 | 0 | 16 | 21 | 55 | 263 |

**This is the single clearest way to see that the task is not variant effect
prediction.** A mutagenesis library would have every row at exactly one mutation.
Here the median isolate carries many, and single-mutant isolates are a small
minority, so no model here estimates the effect of a mutation in isolation.

Unknown positions per isolate, which are positions encoded as `X` because they
were not sequenced, carried a mixture, or were otherwise indeterminate:

| dataset | median unknown positions | max |
| --- | --- | --- |
| filtered | 7 | 168 |
| unfiltered | 258 | 410 |

## 4. Censoring, which is present and was nearly missed

**No label in any file carries a `>` or `<` marker: 0 found. That is not the same as**
**no censoring, and the first version of this audit drew the wrong conclusion from**
**it.**

The filtered datasets are **right-censored at a fold resistance of 100**, and the
truncation is reported as a point value rather than as a bound. It is visible only
distributionally: the filtered maximum is exactly 100.0 for five of the eleven
drugs, while the unfiltered sets for the same drugs reach 5000, 6659 and 24630.

| dataset and drug | n | censored at 100 | share | recovered | unrecovered |
| --- | --- | --- | --- | --- | --- |
| filtered/3TC | 1839 | 831 | 45.19 percent | 822 | 9 |
| filtered/AZT | 1853 | 253 | 13.65 percent | 252 | 1 |
| filtered/DOR | 130 | 26 | 20.00 percent | 24 | 2 |
| filtered/EFV | 2168 | 370 | 17.07 percent | 366 | 4 |
| filtered/NVP | 2052 | 678 | 33.04 percent | 675 | 3 |
| filtered/RPV | 311 | 12 | 3.86 percent | 12 | 0 |

**45.19 percent of filtered 3TC values sit exactly on the bound.** Treating those
as point measurements would bias every number computed from that drug, which is
precisely the error this dataset is known for.

### The evidence that this is truncation and not a real mode

Of the 2196 isolate-drug pairs whose filtered value is exactly 100.0 and which also
appear in the unfiltered set, **2176 have an unfiltered value above 100**, with a
median of 200 and a maximum of 2400. Only 16 are genuinely 100. Where neither is
capped the two datasets agree exactly 98.5 percent of the time, so these are the
same measurements reported at different precision.

### The handling rule, stated once and applied uniformly

1. A value equal to its dataset-and-drug maximum, where that maximum carries at
   least 2 percent of the mass, is flagged `censored`. Both conditions are
   required: the mass condition alone produced a false positive on unfiltered DOR,
   which has 5.9 percent of values at exactly 100 but a maximum of 50000, so 100
   there is a round number rather than a bound.
2. Where the same isolate and drug has a higher value in the unfiltered set, that
   value is **recovered** and the row is flagged `censoring_recovered`. 2151 of
   2170 censored values were recovered this way.
3. A censored value that cannot be recovered is **retained** for rank-based metrics,
   which tolerate ties, and **excluded** from RMSE and MAE, where squaring the
   distance to a bound is meaningless.

Nothing is dropped and nothing is imputed. `curated.csv` carries `censored`,
`censoring_recovered` and `fold_original` so every downstream consumer can see
exactly which values were adjusted and to what.

## 5. Sequence lengths and duplicates

| length | isolate rows |
| --- | --- |
| 560 | 14421 |

Every reconstructed sequence is the same length as the reference, as substitutions
require. Any deviation would be an error rather than an indel to accommodate, and
insertions are recorded as their own category rather than lengthening a sequence.

| dataset | distinct sequences carried by more than one isolate id |
| --- | --- |
| filtered | 52 |
| unfiltered | 268 |

Those duplicate groups are what makes the reproducibility ceiling estimable, and
they are also a redundancy the splits have to control: two isolate ids with an
identical sequence are not two independent observations.

## 6. The reproducibility ceiling, in detail

Where two different isolate ids carry an identical reconstructed sequence and both
were measured for the same drug, the two measurements are effectively replicates.
Their agreement is an upper bound on any model's achievable correlation.

| drug | replicate pairs | Spearman | Pearson | mean absolute difference, log10 |
| --- | --- | --- | --- | --- |
| `3TC` | 26 | 0.9264 | 0.8953 | 0.2060 |
| `ABC` | 17 | 0.9202 | 0.9301 | 0.1527 |
| `AZT` | 27 | 0.8645 | 0.8743 | 0.2926 |
| `D4T` | 9 | 0.8573 | 0.7626 | 0.0527 |
| `DDI` | 13 | 0.8152 | 0.7667 | 0.2233 |
| `DOR` | 23 | 0.7892 | 0.7852 | 0.5094 |
| `EFV` | 47 | 0.8077 | 0.7371 | 0.2545 |
| `ETR` | 54 | 0.8769 | 0.8958 | 0.1891 |
| `NVP` | 29 | 0.9318 | 0.9565 | 0.1798 |
| `RPV` | 29 | 0.6985 | 0.6885 | 0.4918 |
| `TDF` | 18 | 0.4723 | 0.6150 | 0.2625 |
| **pooled** | **292** | **0.8622** | **0.8443** | **0.2648** |

**This ceiling must be drawn on every comparison figure in this task.** A model
reported as reaching a Spearman above it has not beaten the assay; it has
overfitted something, or the evaluation is leaking.

A mean absolute difference of 0.2648 log10 units between replicates is a factor of
about 1.84 in fold resistance. Two measurements of the same virus routinely disagree by
that much, which is the practical resolution of the label.

### How this estimate was constrained, and why it matters

Two decisions were forced by what a naive version produced, and both are stated
because the difference between them is large.

**Only fully sequenced isolates count.** The reconstruction encodes unsequenced
positions and mixtures as `X`, and the median unfiltered isolate carries 258
such positions out of 560. Two isolates differing only at `X` positions collapse
to the same string without being the same virus.

**One pair per distinct sequence.** A group of n identical sequences contributes
n(n-1)/2 pairs, so a few large groups would otherwise dominate.

The first version of this estimate did neither, and reported a ceiling of
**0.9761 over 306759 pairs**. Almost all of those pairs came from five groups of
isolates that were more than half unsequenced, the largest containing 256
isolates. That is not replicate agreement; it is the agreement of different
viruses that happen to be indistinguishable at low sequencing coverage. The
corrected figure is far lower, and using the inflated one would have set a
ceiling no model could be measured against.

Sensitivity to the sequencing-quality threshold, one pair per group throughout:

| maximum unknown positions allowed | groups with a replicate | Spearman | mean absolute difference |
| --- | --- | --- | --- |
| 0 **(adopted)** | 292 | 0.8622 | 0.2648 |
| 20 | 332 | 0.8769 | 0.2473 |
| 50 | 338 | 0.8811 | 0.2429 |
| 100 | 344 | 0.8849 | 0.2387 |
| 560 | 6249 | 0.9604 | 0.0633 |

And for completeness, the naive estimate this replaces: all pairs, no quality
filter, 306759 pairs, Spearman 0.9761. **Not used.**

## 7. Composition, from the unfiltered sets

The filtered sets carry no metadata beyond the sequence and the labels, so
everything in this section comes from the unfiltered files.

| quantity | value |
| --- | --- |
| isolates | 5277 |
| distinct patient identifiers | 3539 |

**Patient is a stronger grouping than isolate, and it is available here.** Multiple
isolates come from one patient. The source's own filtering removes same-patient
viruses that share a major drug resistance mutation pattern, which is partial:
patient structure survives it. This is taken up in the split design.

| subtype | isolates |
| --- | --- |
| B | 9701 |
| C | 153 |
| CRF02_AG | 89 |
| Unknown | 81 |
| A | 60 |
| G | 53 |
| D | 40 |
| F | 19 |
| CRF12_BF | 17 |
| CRF06_cpx | 12 |
| CRF11_cpx | 9 |
| CRF01_AE | 9 |
| CRF45_cpx | 6 |
| U | 5 |
| A1 | 4 |

Subtype composition bounds any generalization claim: a benchmark dominated by one
subtype says little about the others.

| phenotype method | isolates |
| --- | --- |
| PhenoSense | 5989 |
| Antivirogram | 3348 |
| PBMC | 135 |
| Plaque reduction | 128 |
| Subtype C Pseudovirus | 124 |
| TZM-bl | 102 |
| Phenoscript | 71 |
| MT2/MT4 reporter gene | 71 |
| TZM-Sienna | 51 |
| HeLa-CD4 reporter gene | 43 |
| Gilead-MT2-Reporter | 42 |
| Merck | 42 |
| Cell line | 36 |
| NCI | 32 |
| TZM-McGill | 29 |
| MAGIC-5A single-cycle | 16 |
| Cell protection | 13 |
| Biochemical | 10 |

The unfiltered sets mix assay methods, which pools measurement scales. That is why
the filtered sets, PhenoSense only, are the primary analysis.

| isolate type | isolates |
| --- | --- |
| Clinical | 8949 |
| Lab | 1333 |

Laboratory isolates are site-directed mutants or in vitro passage products, so they
are not clinical samples and do not carry the same phylogenetic structure.

## 8. What the filtering removes

Comparing the unfiltered results whose isolate survives into the filtered set
against those that do not.

| class | kept results | removed results | kept median log10 | removed median log10 | difference |
| --- | --- | --- | --- | --- | --- |
| NNRTI | 5974 | 5566 | 0.2553 | 0.8228 | -0.5675 |
| NRTI | 14819 | 14683 | 0.2041 | 0.3010 | -0.0969 |

**The filtering is not neutral with respect to resistance level.** For NNRTI the
removed results have a median log10 fold of 0.8228 against 0.2553 for those kept, a
difference of 0.5675 log10 units, which is a factor of 3.69 in fold resistance.

So the filtered set is **enriched for less resistant isolates**, which follows
from the source's own exclusion rule: it removes viruses carrying mixtures at
major drug resistance positions, and mixtures at those positions are commoner in
treatment-experienced, more resistant viruses. The filtered set's label
distribution is therefore not a random subsample of the unfiltered one, and any
result on it describes a population shifted toward susceptibility. That has to
be stated wherever a filtered result is reported.

## Figures

| figure | what it shows |
| --- | --- |
| `figures/hivrt_label_distribution.png` | log10 fold resistance per drug, filtered sets, with the 10-fold line |
| `figures/hivrt_mutation_counts.png` | mutations per isolate; the clearest view of why this is not a mutagenesis library |
