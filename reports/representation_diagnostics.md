# Task A representation diagnostics

Written by `embeddings/representation_diagnostics_taskA.py`. **No activity label
is used anywhere in the two measurements below.** Activity appears only as a
colour in one figure.

Source: `tasks/taskA_crossfamily/curated.csv`, SHA256
`5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc`.

Representations are ESM-2 at four sizes, final transformer block, mean pooled over
residue positions excluding the BOS and EOS tokens. No layer or pooling sweep: see
`embeddings/MANIFEST_TASKA.json`.

## 1. Family classification: do the representations encode lineage?

Stratified 5-fold logistic regression predicting family, `random_state=0`,
`max_iter=5000`, restricted to families with at least 5 members. That keeps 56 of 57 rows
and drops the singleton `Unclassified` family.

**Two preprocessing variants are reported because the choice is contested.**
`in-fold` standardizes inside each training fold through a pipeline, which is what
the no-fitting-outside-a-fold rule requires. `global` standardizes once over all
rows, which is how the prior figures in this repository were produced. The second
column is the one to compare against the prior numbers; the first is the one to
believe.

| representation | in-fold accuracy | fold-to-fold SD | global accuracy | prior | deviation from prior |
| --- | --- | --- | --- | --- | --- |
| ESM2-8M | 0.7652 | 0.1540 | 0.7652 | none | no prior published |
| ESM2-35M | 0.7833 | 0.1240 | 0.7833 | none | no prior published |
| ESM2-150M | 0.8030 | 0.1355 | 0.8030 | none | no prior published |
| ESM2-650M | 0.8197 | 0.1450 | 0.8197 | 0.821 | -0.0013 within the fold SD |
| length only | 0.5167 | 0.1414 | 0.5167 | 0.520 | -0.0033 within the fold SD |
| 3-mer composition, frequencies | 0.5364 | 0.0674 | 0.6803 | 0.571 | +0.1093 **beyond the fold SD** |
| 3-mer composition, raw counts | 0.6621 | 0.0633 | 0.5894 | 0.571 | +0.0184 within the fold SD |
| majority baseline | 0.3214 | 0 | 0.3214 | 0.321 | +0.0004 |

### How to read a deviation

A deviation beyond the fold-to-fold standard deviation would mean the dataset
changed during reconciliation. It did not: the 57 sequences are byte-identical to
Table S1 and to the inherited table, which `reports/reconciliation.md` section 3
establishes by SHA256 on every row. So a deviation here can only come from
preprocessing or from the embeddings having been recomputed, and both of those are
stated rather than inferred.

The 3-mer control is reported in two encodings deliberately. The earlier review
found the prior figure of 0.571 is reproduced by raw counts standardized, while
frequency-normalized standardized gives a materially higher number, and the
repository specifies no encoding for this control. Reporting one encoding would be
choosing the comparison that suits the conclusion.

## 2. Length correlation: is the leading structure just protein length?

Spearman correlation of principal components 1 to 4 against sequence length, on
standardized embeddings with `PCA(random_state=0)`.

| model | PC1 | PC2 | PC3 | PC4 |
| --- | --- | --- | --- | --- |
| ESM-2 8M | -0.5156 | +0.5143 | +0.3921 | -0.3135 |
| ESM-2 35M | +0.7368 | -0.0683 | -0.1667 | -0.2706 |
| ESM-2 150M | -0.7380 | -0.1623 | +0.1190 | -0.2081 |
| ESM-2 650M | -0.7681 | -0.1000 | -0.0738 | +0.1022 |

The same, on centred but **not** standardized embeddings, because the earlier
review found this choice flips the sign and changes the magnitude:

| model | PC1 | PC2 | PC3 | PC4 |
| --- | --- | --- | --- | --- |
| ESM-2 8M | +0.1495 | +0.5839 | -0.5963 | -0.1856 |
| ESM-2 35M | -0.4894 | +0.6296 | -0.0923 | +0.1959 |
| ESM-2 150M | -0.5951 | +0.5361 | +0.1101 | +0.2482 |
| ESM-2 650M | +0.6198 | -0.6384 | -0.2178 | -0.0266 |

Prior published figure, on standardized 650M embeddings: PC1 against length at
Spearman -0.77. Measured here: -0.7681.

The sign is a PCA convention and carries no meaning; the magnitude is what
matters. A leading component this strongly tied to length means the embedding's
dominant axis of variation is substantially a length axis, and length is a
feature any model can compute for free. That is why the length-only baseline is
the one every representation has to clear in Phase 6, and why clearing the
majority baseline is not evidence of anything.

## 3. What the space looks like

| figure | what it shows |
| --- | --- |
| `figures/taskA_embedding_by_length.png` | **the important one.** PCA and UMAP coloured by length, plus PC1 against length directly |
| `figures/taskA_embedding_by_activity.png` | the same projections coloured by activity |
| `figures/taskA_embedding_by_family.png` | small multiples, one panel per family |
| `figures/taskA_pc_length_correlation.png` | PC1 to PC4 against length, per model size |

Projections use ESM-2 650M, the largest available.

Two notes on reading these. The family figure uses small multiples rather than
seven colours because seven categorical hues cannot be distinguished reliably in a
scatter: on this project's reference palette the worst all-pairs separation is a
colour-vision-deficiency delta E of 3.2 and a normal-vision delta E of 12.9, both
below the floors, and no re-ordering fixes it because a scatter puts every pair on
screen at once. And the UMAP projection of 57 points with `n_neighbors=10` should
be read as a sketch, not as structure: UMAP on a sample this small will produce
apparent clusters from noise.

## What these diagnostics do and do not establish

They establish that the representations carry lineage and carry length, both
without reference to activity. In a panel where family and activity are strongly
associated, 12 of 18 retroviral enzymes active against 0 of 15 across the three
families with no actives, that is precisely the confound to be worried about: a
representation can score well on activity by encoding clade.

They do not establish anything about activity prediction. That is Phase 6, and the
comparison that matters there is against the length-only baseline rather than
against chance.
