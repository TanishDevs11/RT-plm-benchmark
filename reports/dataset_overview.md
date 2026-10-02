# Task A dataset overview

Written by `curation/dataset_overview_taskA.py`. Descriptive only: nothing here
is fitted, selected or predicted, and no model has been trained.

Source: `tasks/taskA_crossfamily/curated.csv`, SHA256
`5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc`.

## What this dataset can resolve, before any result

These three numbers bound every claim the benchmark can make, so they come first.

| quantity | value | consequence |
| --- | --- | --- |
| families holding no active enzyme | 3 of 7 (CRISPR-associated, Other, Unclassified) | when one of these is the held-out fold the test set is all negative, so a ranking correlation is undefined on it. Leave-one-family-out rests on 4 informative folds, not 7 |
| families holding a single enzyme | 1 (Unclassified) | a fold of one. Nothing about variance within that family is estimable |
| Kish effective sample size of the CLS weighting | 11.338 | the weighted half of CLS is worth about 11.3 independent observations, not 57 |

The effective sample size is low because the CLS weights are the efficiency plus
0.01, and the efficiencies span 0 to 41. `MMLV-RT` alone carries 15.56 percent of the
total weight, the top five carry 56.17 percent, and all 36 inactive enzymes together
carry 0.137 percent. A weighted Spearman over this panel is close to a statement
about the ordering of a handful of enzymes.

## Composition

| quantity | value |
| --- | --- |
| enzymes | 57 |
| families | 7 |
| active | 21 (36.8 percent) |
| inactive | 36 |

| family | enzymes | active | inactive | shortest | median | longest |
| --- | --- | --- | --- | --- | --- | --- |
| Retroviral | 18 | 12 | 6 | 571 | 654 | 693 |
| Retron | 12 | 5 | 7 | 292 | 370 | 604 |
| LTR_Retrotransposon | 11 | 2 | 9 | 367 | 505 | 824 |
| Group_II_Intron | 5 | 2 | 3 | 306 | 426 | 598 |
| CRISPR-associated | 5 | 0 | 5 | 240 | 311 | 446 |
| Other | 5 | 0 | 5 | 315 | 336 | 682 |
| Unclassified | 1 | 0 | 1 | 226 | 226 | 226 |

The panel is dominated by two families. Retroviral holds 18 of the 57 enzymes and
12 of the 21 actives; Retron holds 12 and 5. Between them they are 30 rows
and 17 of the actives, so a model that learns only the retroviral family will score well
on the pooled metric while having learned one clade.

## Length

| statistic | all enzymes |
| --- | --- |
| n | 57 |
| min | 226 |
| q1 | 336 |
| median | 523 |
| q3 | 626 |
| max | 824 |
| mean | 503.7 |
| sd | 149.9 |

Length is not independent of family. The bacterial families sit near 300 to 500
residues and the retroviral family near 570 to 700, so any model with access to
length has partial access to lineage. That is the confound the earlier audit
measured as embedding PC1 tracking length at Spearman -0.77, and it is why the
length-only baseline is the one every representation has to beat.

## Efficiency among the actives

Only the 21 active enzymes have a non-zero efficiency; all 36 inactives are
exactly 0.0.

| statistic | value |
| --- | --- |
| n | 21 |
| min | 0.5 |
| q1 | 2.5 |
| median | 8 |
| q3 | 21 |
| max | 41 |
| mean | 12.524 |
| sd | 11.892 |

Every one of these values is an exact multiple of 0.5, which is the signature of
a figure read by eye rather than a table transcribed. The provenance is set out in
`reports/reconciliation.md` section 4. Per the Gate G2 ruling, classification on
the binary label is the primary result and every number derived from this column
carries that digitization as a stated limitation.

## Identity clustering

MMseqs2 `easy-cluster`, commit `8cc5ce36`, at four thresholds with parameters
fixed a priori: `--cov-mode 1 -c 0.8 -s 7.5`. Coverage is measured over the
target rather than bidirectionally, because these are excised domains with
different boundaries and containment is what redundancy between them looks like.

| threshold | clusters | size distribution | clusters spanning two families | clusters with mixed activity |
| --- | --- | --- | --- | --- |
| 90 percent | 53 | 49 of size 1, 4 of size 2 | 0 | 2 |
| 70 percent | 49 | 44 of size 1, 3 of size 2, 1 of size 3, 1 of size 4 | 0 | 2 |
| 50 percent | 44 | 39 of size 1, 3 of size 2, 1 of size 4, 1 of size 8 | 0 | 2 |
| 30 percent | 24 | 14 of size 1, 2 of size 2, 4 of size 3, 1 of size 4, 1 of size 5, 1 of size 8, 1 of size 10 | 4 | 7 |

### Clusters crossing a family boundary at 30 percent

- CaMV-RT (Other), Tf1-RT (LTR_Retrotransposon), Ty3-RT (LTR_Retrotransposon)
- AFY36037.1-RT (Unclassified), DRG2-RT (Other), Drg-RT (Other)
- A.platensis-Cas1-RT (CRISPR-associated), FuRT-Cas1-RT (CRISPR-associated), Gs-RT (Group_II_Intron), Med-CasRT (CRISPR-associated), Rs-RT (Retron)
- CRISPRRT2-RT (CRISPR-associated), Er-RT (Group_II_Intron), GroupII_CLA-RT (Group_II_Intron), Tel4c-RT (Group_II_Intron)

### What the 30 percent threshold changes

At 90, 70 and 50 percent identity no cluster crosses a family boundary, which is
what an earlier version of `reports/split_design.md` reported as holding at every
threshold. Adding 30 percent shows that claim was threshold-limited: four clusters
cross a family boundary there. The correction matters because it is the only
threshold at which the claim fails, and 30 percent is the conventional line below
which two proteins are not assumed homologous.

So leave-one-family-out does **not** hold out an identity cluster at 30 percent.
For the families involved, holding out the family still leaves relatives above 30
percent identity in the training set. Three of the four crossing clusters join
bacterial families to each other, which is consistent with CRISPR-associated RTs
being derived from group II intron RTs rather than with a labelling error; the
fourth joins `CaMV-RT`, labelled Other, to the two LTR retrotransposon RTs, which
is consistent with caulimovirus being a pararetrovirus. In other words these look
like genuine phylogenetic signal that the 7-way labelling coarsens away, not like
mislabelled rows. Either way they are flagged, and the leave-one-cluster-out split
at 70 percent exists as the stricter control.

### Clusters holding both an active and an inactive enzyme

These are the pairs no similarity-based method can get fully right, because the
members are near-identical and carry opposite labels.

- at 90 percent identity: BAEMV-RT (active), FENV1-RT (inactive)
- at 90 percent identity: ASLV-RT (active), RSVSB-RT (inactive)

Either activity turns on a few residues or one of the calls is noise. 21
positives cannot separate those two readings, and that is a limit of the dataset
rather than of any particular model.

## Figures

| figure | what it shows |
| --- | --- |
| `figures/taskA_family_composition.png` | enzymes per family |
| `figures/taskA_activity_by_family.png` | actives against inactives per family |
| `figures/taskA_length_by_family.png` | length spread per family, with the family median |
| `figures/taskA_efficiency_among_actives.png` | the 21 non-zero efficiencies, sorted |

Every figure's underlying numbers are in the tables above, so the report is
readable without the images.
