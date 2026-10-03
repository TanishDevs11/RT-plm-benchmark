# Do protein language models improve reverse transcriptase activity prediction?

Task A final report. Written by `reports/build_final_report.py`, which reads every
number from the artifact that produced it.

| field | value |
| --- | --- |
| curated dataset | `tasks/taskA_crossfamily/curated.csv`, SHA256 `5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc` |
| enzymes | 57 |
| active | 21 |
| families | 7 |
| source | Doman et al., Cell 2023, `10.1016/j.cell.2023.07.039`, Supplementary Table S1 |

## The direct answer

**No.** On this 57-enzyme cross-family panel, under family-held-out evaluation with
a fixed model head, protein language model representations do not improve reverse
transcriptase activity prediction over simpler biological representations, and
neither they nor the simpler representations are distinguishable from their own
noise controls on the composite metric.

The longer version, which the rest of this report supports:

- The best ESM-2 classification PR-AUC is 0.4220 and the best non-language-model PR-AUC is 0.6212,
  so the language models are **behind** on the primary metric before any null is applied.
- Every bootstrap interval on CLS includes zero, and **no representation under
  either head clears the CLS gate**: the highest CLS is 0.3739 against a
  search-capacity null p95 of 0.4433 at the one free parameter this benchmark uses.
- On the primary classification metric, exactly **one** representation survives all
  three controls, and it is not a language model: `kmer4`. Its signal is
  **strongly associated with sequence length and family structure rather than with
  any specific biological motif**, which section 6 establishes directly.
- **Every ESM-2 size fails the label permutation test.** 650M reaches PR-AUC 0.4220
  against a permuted p95 of 0.5217, 8M reaches 0.3706 against 0.5676. Both clear
  their Gaussian noise controls, and both lose to their own shuffled labels, which
  is why the permutation test is not optional.
- The median minimum resolvable CLS difference on this panel is 0.4816, which is larger
  than **every** CLS actually observed, so the ordering of the CLS column is not
  resolvable at this sample size at all.

## 1. Dataset construction and the reconciliation findings

Supplementary Table S1 was acquired from the Europe PMC supplementary files
endpoint for PMC10482982 and is committed as `raw/mmc2.xlsx`; the article is CC BY
4.0. Its layout was not what the brief anticipated: one sheet, two
caption-delimited FASTA blocks under a single running index, with activity encoded
as a green cell fill rather than a column. Block 1, rows 6 to 118, holds 57 assayed
enzymes of which 21 carry the fill. Block 2's 486 entries are UniProt BLAST hits,
never assayed, and are excluded from the benchmark entirely. Full inventory in
`reports/tableS1_inventory.md`, ruled on at Gate G1.

### The 57 against 59 and 21 against 20 discrepancies

Both are **internal to the primary source**, between the article's prose and its own
supplementary table, not between this repository and the paper.

The 57 names in Table S1 are exactly the 57 in the inherited `data/rt_sequences.csv`
as sets, and the 21 filled entries are exactly the 21 rows marked active. The prose
says 59 enzymes were tested and twenty showed detectable activity.

For the activity count the responsible enzyme is identified. The Figure S1A caption
breaks the actives into 11 retroviral, 2 LTR retrotransposon and 7 bacterial, which
is 20, and the filled set matches in every class except retroviral, where it is 12.
The caption says those 11 are "closely related to the M-MLV RT" and separately
marks wild-type M-MLV RT as the PE1 system's enzyme. So the prose excludes the PE1
comparator and the table includes it. Both counts are correct under their own
definition; the benchmark uses the table's, with the other documented.

For the row count nothing in the published record names the missing two. Documented
as a source discrepancy, not corrected. **The panel must be described as the 57
enzymes Table S1 lists, not as the 59 the paper says were tested.**

### Sequence integrity

All 57 inherited sequences are byte-identical by SHA256 to Table S1, and the
inherited length column agrees with `len(sequence)` on every row. This check had
never been run on this dataset. It is the one inherited claim this work strengthens
rather than qualifies.

### The regression target has no verifiable source

**Table S1 contains no efficiency values.** There is no numeric cell in the sheet
except the row index, and all six supplementary workbooks were scanned without
finding the per-enzyme survey values. The column is attributed to Figure S1A, the
only panel giving one value per enzyme for every enzyme including the inactives,
assayed as HEK293T, HEK3 +5 G to T, mean of n = 3. Every one of the 21 non-zero
values is an exact multiple of 0.5 and every inactive is exactly 0.0, which is the
signature of a figure digitized by eye rather than a table transcribed.

This is the most consequential finding in the dataset work. The weighted Spearman
half of CLS is computed against a plot read at roughly half a percentage point of
resolution, and the CLS weighting concentrates on exactly the high-efficiency rows
where a digitization error is largest in absolute terms. Per the Gate G2 ruling the
binary label carries the primary claim and every regression number inherits this
limitation.

### Accessions and classes

Table S1 gives no accession for any assayed enzyme and the article's full text
contains no protein accession of any form. 27 of 57 were pinned exactly from
sequence against UniProt. Of the remaining 30: 6 are exact substrings blocked only
by ambiguity, 13 are near matches differing at 1 to 4 residues, and 11 have no
candidate in the local cache. The near-match group has a mechanism: 7 of the 13
differ at position 1, 4 of those to methionine, which is a start codon on an excised
domain. M-MLV RT is P03355 residues 660 to 1336 with one difference, H8Y. None of
this was written into the accession column, because a near match is evidence for an
identification, not an identification.

No class labels exist in the table; the paper's 14 classes are in the Figure 1B tree
image only. The benchmark's 7-way family labelling is inherited and **cannot be
verified against the paper**.

## 2. Benchmark design: what the splits do and do not control for

Primary split: leave-one-family-out, 7 folds, frozen in
`tasks/taskA_crossfamily/splits/leave_one_family_out.csv` and asserted to reproduce
the partition `bench/protocol.py` derives at run time, so the file and the harness
cannot drift apart. Secondary: leave-one-cluster-out at 70 percent identity, 49
folds.

| the split controls | the split does not control |
| --- | --- |
| same-family train-test pairs | the association between family and activity, which is real in these data |
| identity above 50 percent across a fold boundary | remote homology: 4 clusters cross a family boundary at 30 percent identity, and 6 of the 7 family folds leave a relative of the held-out family in training at that threshold |
| duplicate sequences across the boundary | length, which is confounded with family |

**A correction to this repository's earlier claim.** `reports/split_design.md` and
`reports/data_pipeline_report.md` both stated that no identity cluster crosses a
family boundary "at any threshold". That was written when only 90, 70 and 50
percent had been computed, and it is false at 30 percent, which is the conventional
line below which two proteins are not assumed homologous. Both documents are
corrected in place with the original wording quoted.

## 3. Representation comparison, the main table

Twelve representations, two heads, nested leave-one-family-out, one free parameter
selected in the inner loop. Ordered by classification PR-AUC against a prevalence
chance level of 0.3684.

| representation | features | PR-AUC | noise PR-AUC | CLS | CLS 95 percent CI | noise CLS |
| --- | --- | --- | --- | --- | --- | --- |
| `kmer4` | 20115 | 0.6212 | 0.4458 | 0.0000 | 0.0000 to 0.5671 | 0.0000 |
| `esm2_650M` | 1280 | 0.4220 | 0.2889 | 0.1061 | 0.0000 to 0.4614 | 0.0357 |
| `esm2_8M` | 320 | 0.3706 | 0.2581 | 0.0000 | 0.0000 to 0.3965 | 0.0000 |
| `physicochemical` | 13 | 0.3623 | 0.2643 | 0.3739 | 0.0000 to 0.5258 | 0.0000 |
| `esm2_35M` | 480 | 0.3162 | 0.2899 | 0.2412 | 0.0000 to 0.4690 | 0.2460 |
| `kmer3` | 6256 | 0.3137 | 0.3029 | 0.3249 | 0.0000 to 0.4864 | 0.0000 |
| `handcrafted_plus_esm2_650M` | 2069 | 0.3082 | 0.2970 | 0.3449 | 0.0000 to 0.5136 | 0.0000 |
| `dipeptide` | 400 | 0.3081 | 0.3118 | 0.0000 | 0.0000 to 0.3600 | 0.0241 |
| `esm2_150M` | 640 | 0.3056 | 0.2856 | 0.2187 | 0.0000 to 0.4871 | 0.2506 |
| `handcrafted` | 789 | 0.2956 | 0.2675 | 0.2805 | 0.0000 to 0.4643 | 0.0471 |
| `aa_composition` | 20 | 0.2781 | 0.3261 | 0.1142 | 0.0000 to 0.4177 | 0.0000 |
| `length` | 1 | 0.2599 | 0.2474 | 0.1100 | 0.0000 to 0.3758 | 0.0645 |

Full tables including the regression head and the per-family breakdown are in
`bench/results/taskA_representations.md`.

### Why PR-AUC is the primary column

CLS is the harmonic mean of PR-AUC and a weighted Spearman against the digitized
efficiency column, and a harmonic mean floors at zero when either term does. kmer4
reaches a PR-AUC of 0.6212 while scoring a CLS of exactly zero, because it separates
actives from inactives but does not reproduce the digitized ordering. CLS cannot
distinguish that from a representation that does nothing. So the primary test is
PR-AUC against a dimensionality-matched noise control, on the label that is
reproducible from the source file.

## 4. Statistical validation, including every null

Detail in `reports/statistical_validation.md`.

### The search-capacity null at matched K

This benchmark selects one free parameter, so the matched null is K equals 1.

| K | repeats | mean | sd | p95 | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | 0.2751 | 0.1213 | 0.4433 | 0.1113 | 0.4843 |

### A correction to the inherited headline comparison

The inherited result of 0.9754 is compared in `README.md`, `WRITEUP.md` and
`PROGRESS.md` against the K equals 50 noise p95 of 0.9727, and the conclusion drawn
is that the score "sits within its own noise floor". **That is an invalid
comparison, and correcting it does not favour this repository's existing framing.**

`README.md` describes the search that produced it as 29 weights plus a power
exponent. The matched null is therefore K equals 29, whose p95 is 0.9340, and the 62
fitted parameters quoted nearby belong to a different stored artifact scoring
0.8978. At matched K the margin is +0.0414, which is positive: the score does **not**
sit inside its noise floor.

What is true, and is the correct statement, is weaker in a different way: that
margin of 0.0414 is far smaller than the 0.0794 bootstrap interval width on the
submitted vector, so the score is **not distinguishable from what the procedure
manufactures from noise** at this sample size. The leakage finding stands on the
evidence in `audit/leakage_report.md`, which does not depend on this comparison.

### Noise controls, permutation, and resolvability

| control | result |
| --- | --- |
| representations clearing the CLS gate, noise control and K=1 search null | 0 of 24 |
| representations clearing the PR-AUC gate, noise control and prevalence | 1 of 12 |
| CLS bootstrap intervals excluding zero | 0 |
| median minimum resolvable CLS difference | 0.4816 |

Every representation that clears the noise control and chance on PR-AUC, with
the permuted-label p95 shown alongside. The permutation is the decisive column:
a representation whose shuffled labels reproduce its score has not been shown to
use the real ones.

| representation | PR-AUC | noise control | prevalence | permuted p95 | survives all three |
| --- | --- | --- | --- | --- | --- |
| `kmer4` | 0.6212 | 0.4458 | 0.3684 | 0.5398 | **yes** |
| `esm2_650M` | 0.4220 | 0.2889 | 0.3684 | 0.5217 | no |
| `esm2_8M` | 0.3706 | 0.2581 | 0.3684 | 0.5676 | no |

**`kmer4` is the only representation that survives all three controls.**

Every ESM-2 size fails the permutation test. ESM-2 650M reaches a PR-AUC of
0.4220 against a permuted p95 of 0.5217, and ESM-2 8M reaches 0.3706 against
0.5676: in both cases shuffled labels reproduce the observed score more than 5
percent of the time. The noise control alone would have passed 650M, which is
precisely why the permutation test is not optional.

Label permutation, 20 repeats, on `length`, `handcrafted`, `physicochemical`, `kmer4`, `esm2_8M`, `esm2_650M`:

| representation | head | permuted mean CLS | permuted p95 | observed | above the permuted p95 |
| --- | --- | --- | --- | --- | --- |
| `esm2_650M` | classification | 0.1051 | 0.3700 | 0.1061 | **no** |
| `esm2_650M` | regression | 0.1047 | 0.3529 | 0.0000 | **no** |
| `esm2_8M` | classification | 0.1410 | 0.3537 | 0.0000 | **no** |
| `esm2_8M` | regression | 0.0736 | 0.2530 | 0.2840 | yes |
| `handcrafted` | classification | 0.1548 | 0.3644 | 0.2805 | **no** |
| `handcrafted` | regression | 0.1215 | 0.3072 | 0.2646 | **no** |
| `kmer4` | classification | 0.1916 | 0.4371 | 0.0000 | **no** |
| `kmer4` | regression | 0.0393 | 0.2622 | 0.0000 | **no** |
| `length` | classification | 0.1266 | 0.3418 | 0.1100 | **no** |
| `length` | regression | 0.0264 | 0.1406 | 0.3576 | yes |
| `physicochemical` | classification | 0.1076 | 0.3786 | 0.3739 | **no** |
| `physicochemical` | regression | 0.0598 | 0.3099 | 0.0821 | **no** |

## 5. Representation analysis: lineage against length against activity

Detail in `reports/representation_diagnostics.md`. No activity label is used in
either measurement.

| what the representation predicts | ESM-2 650M | best simple control | majority or chance |
| --- | --- | --- | --- |
| family, 5-fold accuracy | 0.8197 | 0.6621, 3-mer raw counts | 0.3214 |
| activity, PR-AUC out of family | 0.4220 | 0.6212 | 0.3684 |

That contrast is the finding of this report. **The same representation that
classifies evolutionary family at 0.82 predicts activity at barely above chance.**
Its leading principal component tracks sequence length at Spearman -0.7681, which
reproduces the published figure exactly and is now computed by a script in this
repository rather than being an orphan number.

So ESM-2 mean-pooled embeddings of these sequences encode what the protein is
related to, and how long it is, and little that transfers to whether it works as a
prime editor across a family boundary.

## 6. Interpretation, or the failure analysis

Detail in `reports/interpretation.md`. The gate is that a representation is
interpreted only if it clears both its noise control and the matched search-capacity
null, because a feature-importance plot of a model that loses to protein length
looks exactly like one of a model that works.

`kmer4` cleared the PR-AUC gate, so it is the only representation analyzed.
Attribution is exact rather than estimated: the head is linear, so a Shapley
value is the coefficient times the centred feature value, computed out of fold
by refitting each family's selected configuration on its own training folds.

### What `kmer4`'s surviving signal actually is

Three measurements, and they point the same way.

| measurement | value | what it means |
| --- | --- | --- |
| out-of-fold score against sequence length | Spearman **+0.5212**, p 3.23e-05 | half the ordering it produces is length, and length is free |
| attribution mass in the top decile of family-explained features | **0.1638** against a 0.1000 feature share | the fit leans on dimensions that family explains, by about 64 percent more than their share |
| per-feature importance against family-explained variance | Spearman **+0.2055** | the association is systematic across all 20115 features, not an artifact of a few |
| attribution mass in the top 1 percent of features | **0.0656** against a 0.0100 feature share | the signal is diffuse: no small set of 4-mers carries it |

**So `kmer4` survives the controls, and what it has survived them with is
sequence length and family structure, not a specific biological motif.** The
top-ranked 4-mers carry 0.08 percent of the attribution mass each; with 20115
features and 57 rows no individual coefficient is estimable, and the diffuse
mass confirms there is nothing motif-like to report. A reader looking for a
catalytic signature in that ranking would be reading noise.

This matters for how the one positive result in this benchmark should be cited.
`kmer4` clearing its noise control, chance, and its own permuted labels is a
real and reproducible property of the data. It is **not** evidence that 4-mer
composition captures reverse transcriptase catalysis, and it does not rescue
the headline: the thing that separates actives here is substantially the same
lineage-and-length confound that the representation diagnostics measured
directly, reached by a different route.

## 7. Limitations, in full

| limitation | value |
| --- | --- |
| enzymes | 57 |
| positives | 21 |
| Kish effective sample size of the CLS weighting | 11.338 |
| families with zero actives | 3 of 7: CRISPR-associated, Other, Unclassified |
| families with a single member | 1, Unclassified |
| informative leave-one-family-out folds | 4, not 7 |
| median minimum resolvable CLS difference | 0.4816 |
| regression target provenance | a digitization of Figure S1A, roughly 0.5 percentage point resolution, no error bars recoverable |
| family labels | inherited 7-way, not verifiable against the paper's 14 classes |
| remote homology | 4 identity clusters cross a family boundary at 30 percent; no split here removes it |
| accessions | 27 of 57 pinned exactly |

Three further limitations that are about what was not done rather than about the
panel:

- Only mean pooling of the final layer was used. No layer or pooling sweep was run,
  deliberately, because a sweep is a selection decision; it is possible that a
  different layer carries function better, and this benchmark does not test that.
- Only two model heads were used, deliberately. A more flexible head might extract
  more, and would also be able to manufacture more from noise, which is why the
  restriction is the design rather than a shortcut.
- The label permutation covers 6 of the 12 representations, stated rather
  than silent, because all twelve would be 480 protocol runs.

## 8. The answer, in one sentence

**No: on this 57-enzyme panel, protein language model representations do not
improve reverse transcriptase activity prediction over simpler biological
representations under family-held-out evaluation, and the honest reason is as much
that the panel cannot resolve a difference of the size in question as that the
embeddings encode lineage and length rather than function.**

Those two explanations are different, and this dataset does not separate them. With
21 positives, an effective sample size of 11.3, three of seven folds holding no active at
all, and a median resolvable difference of 0.4816 CLS, a real improvement smaller than
that would be invisible here. What can be said positively is narrower and better
supported: these representations demonstrably encode family and length, and
demonstrably do not convert that into cross-family activity prediction.

## Figures

| figure | what it shows |
| --- | --- |
| `figures/taskA_representation_comparison.png` | PR-AUC per representation with its 95 percent bootstrap interval, against chance |
| `figures/taskA_null_comparison.png` | **the result in one picture.** Observed against the Gaussian noise control and the permuted-label p95 |
| `figures/taskA_family_composition.png` | enzymes per family |
| `figures/taskA_activity_by_family.png` | actives against inactives per family |
| `figures/taskA_length_by_family.png` | length spread per family |
| `figures/taskA_efficiency_among_actives.png` | the 21 digitized efficiencies |
| `figures/taskA_embedding_by_length.png` | PCA and UMAP coloured by length, plus PC1 against length |
| `figures/taskA_embedding_by_family.png` | small multiples, one panel per family |
| `figures/taskA_embedding_by_activity.png` | the same projections coloured by activity |
| `figures/taskA_pc_length_correlation.png` | PC1 to PC4 against length, per model size |
| `figures/taskA_failure_by_family.png` | signed prediction error by family |
| `figures/taskA_error_vs_length.png` | absolute error against length and against novelty |

## Reproducing this

```
make pipeline-taskA-source      # fetch Table S1, inventory every sheet
make pipeline-taskA-parse       # parse the assayed block, reconcile, curate
make pipeline-clusters          # identity clustering at 90, 70, 50, 30
make pipeline-taskA-overview    # descriptive statistics and figures
make pipeline-splits            # freeze and verify the splits
make pipeline-features          # handcrafted features and the mask
make pipeline-taskA-embeddings  # ESM-2 at four sizes, then the diagnostics
python bench/representations_taskA.py
python bench/validate_taskA.py --stage all
python bench/interpret_taskA.py
python reports/build_final_report.py
```

Seed 42 throughout. Every reported number is read
from a result file by the generator of this report, not typed in.
