# Scoping additional labelled RT activity data

## Why this document exists

The audit and the search-capacity null both point at the same conclusion: the
limiting factor here is not the model, it is n. The weighted Spearman term has a
Kish effective sample size of 11.3 against a nominal 57 rows, the bootstrap
interval on a fixed prediction vector spans roughly 0.08 CLS, and the reference
noise search reaches a CLS far above what any honest method achieves. No modelling
choice fixes any of that. More labelled RTs would.

This is a scoping document only. Nothing described here has been downloaded,
harmonized, or merged into `data/`, and nothing should be without an explicit human
decision, as the brief requires.

## Verification status, stated plainly

The candidate sources below are named from domain knowledge. **The quantitative
fields (n, exact assay readout, licence terms) have not been verified against the
primary sources in this session, and are marked `UNVERIFIED` wherever that is the
case.** Writing plausible sample sizes into this table would be exactly the kind of
invented number the rest of this project exists to refuse, so they are left
unfilled rather than guessed. Each row states what must be checked before use.

## Candidate sources

### 1. Prime editing RT variant screens (PE2 lineage)

- **What**: Engineered MMLV-RT pentamutant and related variants characterized
  during the original prime editor development, plus the RT-domain variants tested
  in subsequent prime editor generations.
- **Assay**: Prime editing efficiency as percent precise edits at defined genomic
  targets, read out by amplicon sequencing.
- **Comparability to `pe_efficiency_pct`**: Potentially high, because the readout
  is the same class of quantity. The hazard is that efficiency is strongly target
  site and cell line dependent, so values are only comparable within a fixed target
  and delivery context. Cross-study pooling without a shared reference construct
  would introduce a batch effect larger than the biological signal.
- **n**: UNVERIFIED.
- **Licence**: UNVERIFIED; typically supplementary tables under journal terms.
- **Harmonization required**: Identify a shared anchor construct present in both
  the existing 57 and the new set, and rescale to it. Without an anchor, merge as a
  separate cohort with a cohort indicator, never as extra rows in one pool.

### 2. Evolved compact prime editor RT panels (PE6 lineage)

- **What**: RT variants produced by phage-assisted continuous evolution toward
  compact and more efficient prime editors.
- **Assay**: Prime editing efficiency, same class of readout as above.
- **Comparability**: Moderate to high, with the same target-dependence caveat.
  These are additionally a biased sample: they were selected for activity, so a
  panel of evolved variants is enriched for actives and does not resemble the
  family-diverse natural panel in `data/`. Pooling them would shift the class
  balance and make the out-of-family framing incoherent.
- **n**: UNVERIFIED.
- **Licence**: UNVERIFIED.
- **Harmonization required**: Treat as a distinct evaluation cohort for transfer
  testing, not as additional rows for leave-one-family-out. Their value is as a
  held-out generalization check, not as training mass.

### 3. Retron RT activity sets

- **What**: Retron reverse transcriptases characterized for msDNA production and,
  in engineering contexts, for editing or recombineering activity.
- **Assay**: Frequently msDNA yield or recombineering efficiency, **not** prime
  editing efficiency.
- **Comparability**: Low on the continuous axis. A retron msDNA yield is not
  convertible into `pe_efficiency_pct`. It may still be usable for the binary
  active or inactive label, which would help PR-AUC but not the weighted Spearman
  term, and the weighted Spearman term is the half of CLS that is currently
  resolution limited.
- **n**: UNVERIFIED.
- **Licence**: UNVERIFIED.
- **Harmonization required**: Binary label only, with the efficiency field left
  missing rather than imputed. Any imputation here would be inventing the exact
  quantity the benchmark measures.

### 4. Diversity-generating retroelement RTs

- **What**: DGR reverse transcriptases, which perform adenine-mutagenic
  cDNA synthesis.
- **Assay**: Mutagenesis frequency or retrohoming activity.
- **Comparability**: Low, for the same reason as retrons, and arguably lower: DGR
  RTs are selected for infidelity, which is close to the opposite of the property
  a prime editor RT is selected for. They are useful as negative or
  distribution-shift examples, not as additional positives.
- **n**: UNVERIFIED.
- **Licence**: UNVERIFIED.
- **Harmonization required**: Treat as an out-of-distribution probe set.

### 5. Deep mutational scan of MMLV-RT

- **What**: A saturating or near-saturating variant-effect map of MMLV-RT.
- **Status**: **Existence not confirmed in this session.** A DMS of MMLV-RT at
  prime-editing readout may or may not be published. This row is retained because
  the brief asked for it, but it must be treated as a literature search task with
  an uncertain answer rather than as a known asset.
- **Why it would matter if it exists**: It would be the single most valuable
  addition, not as extra rows for the out-of-family task, but as transfer
  pretraining. A dense local map around one RT teaches a representation what
  changes matter catalytically, which is precisely the signal mean-pooled
  embeddings currently lack. The assay would almost certainly differ, so it would
  be used for pretraining a representation, never merged into the evaluation set.

## The structural warning

Every source above shares one hazard, and it is worth stating separately because it
is the mistake most likely to be made in good faith. Adding rows whose activity was
measured under a different assay will inflate apparent performance, because a model
can learn to predict the assay rather than the enzyme. Cohort identity would be
almost perfectly predictable from sequence family, so a model that learns cohort
learns lineage, which is exactly the confound this benchmark already found in
mean-pooled embeddings. Any merge must therefore carry a cohort indicator, and the
protocol must hold out whole cohorts, not just families.

## Projected value of more data

Computed by `bench/scale_projection.py`, which resamples the observed 57 RTs up to
the target size and recomputes both limiting quantities. The numbers are in
`bench/results/scale_projection.json`. They assume new RTs are drawn from the same
family and efficiency distribution as the current ones, which is optimistic, so
they are a best case rather than a forecast.

The two quantities to read are the bootstrap interval width, which is the smallest
difference the benchmark could ever resolve, and the search-capacity null, which is
the score a 30-parameter search reaches on pure noise. Data collection is worth
doing to the extent that it narrows the first and lowers the second. If the null at
n = 200 is still high, then the honest conclusion is that this metric, not this
dataset, is the problem, and the metric should be replaced rather than the panel
enlarged.
