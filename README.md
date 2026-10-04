# Benchmarking Protein Language Models for Reverse Transcriptase Activity Prediction

A leakage-aware benchmark for evaluating whether protein language model
(PLM) representations improve reverse transcriptase (RT) activity
prediction across evolutionary families.

This project builds on our own earlier competition submission.
Rather than optimizing a leaderboard score, this repository focuses on a
stricter question: **do learned protein representations actually
generalize to unseen RT families better than simple sequence-derived
baselines?**

## Provenance

This repository is a methodological rebuild of
[TanishDevs11/RT-Activity-Predictor](https://github.com/TanishDevs11/RT-Activity-Predictor).
The original holds the submitted competition artifact and is **not modified by this
work**: no push, no branch, no tag, no pull request. It was cloned once at commit
`c1620706685d1a29e874031abd62d88a763d241e`, tagged here as `provenance`. Full record in
[ORIGIN.md](ORIGIN.md).

## Research Question

> Do protein language model representations provide better
> generalization for reverse transcriptase activity prediction than
> simple sequence and physicochemical representations?

The benchmark compares ESM-2 embeddings with sequence composition,
physicochemical features, structural information, and simple baselines
under family-held-out evaluation.

## Background

Reverse transcriptases are central to retroelements, retroviruses,
retrons, and several genome-engineering systems. Engineered RTs are also
key components of prime editors.

Predicting which RTs are functional in a prime-editing context is
difficult because available experimental datasets are small and strongly
structured by evolutionary family. Flexible modelling and
model-selection procedures can therefore produce apparently strong
scores without demonstrating genuine generalization.

This repository was developed to examine that problem explicitly.

## Status

Task A is complete and stands. Since 2026-09-30 the project is a multi-task
benchmark, so that a cross-family transfer task can be contrasted against a
within-protein variant effect task. Progress is in
[reports/progress_2026-09-30.md](reports/progress_2026-09-30.md).

| task | what it measures | assay | status |
| --- | --- | --- | --- |
| **A** cross-family | does a representation transfer across RT families | prime editing, percent precise edits, HEK293T | **complete**, 57 sequences from Table S1, endorsed through Gate G2; see [reports/FINAL_REPORT.md](reports/FINAL_REPORT.md) |
| **A2** evolved | transfer onto selected variants, evaluation only | prime editing, evolved editors in their own scaffolds | not acquired |
| **B** M-MLV DMS | within-protein variant effect | prime editing, normalized so wild type is zero | **blocked at acquisition**, splits and reference ready, labels never deposited. See [reports/taskB_mmlv_dms/FINAL_REPORT.md](reports/taskB_mmlv_dms/FINAL_REPORT.md) |
| **B** HIV-1 RT | drug susceptibility phenotype, surveyed as an alternative | fold resistance, clinical and laboratory isolates | **audited, not a DMS**; see [reports/taskB_hivrt/audit_report.md](reports/taskB_hivrt/audit_report.md) |
| C retron, C DGR, C retroviral | breadth of representation analysis | msDNA, mutagenic homing, in vitro kinetics | **blocked**, no usable panel found |

The scientific point of running A and B together is the contrast. Protein language
models are known to do well on within-protein variant effect prediction, and the audit
in this repository measured raw ESM-2 embeddings at CLS 0.3052 on the cross-family
task, below the 0.4416 that protein length alone achieves with no training.

## Dataset

### Task A: Cross-family RT activity

The completed benchmark uses a panel of:

-   **57 experimentally assayed reverse transcriptases**
-   **21 active RTs**
-   RTs spanning 7 evolutionary families: Retroviral 18, Retron 12,
    LTR_Retrotransposon 11, CRISPR-associated 5, Group_II_Intron 5,
    Other 5, Unclassified 1
-   full amino-acid sequences verified against the primary-source
    supplementary material, all 57 byte-identical by SHA256
-   binary activity as the primary reproducible target

**Which definition these counts use.** Both 57 and 21 are Table S1's counts, and both
differ from the article's prose, which says 59 enzymes and 20 actives. The gap is
inside the primary source, not introduced here: Table S1's assayed block holds 57 rows
indexed 1 to 57 without a gap, and its green activity fill marks 21. The prose's 20
excludes M-MLV RT, which is the PE1 comparator rather than a survey candidate. Both
pairs are correct under their own definition; this benchmark reports Table S1's,
because that is the definition attached to the sequences actually used. Full
reconciliation in [reports/reconciliation.md](reports/reconciliation.md).

A continuous `pe_efficiency_pct` target is retained for regression and
comparison with the inherited benchmark, but its provenance is treated
as a limitation because the per-enzyme numerical values were not
available as a published supplementary table. Table S1 carries no numeric cell
except the row index, and all six supplementary workbooks were scanned without
finding the per-enzyme efficiencies. The column is attributed to Figure S1A and
carries the word `UNVERIFIED_DIGITIZED` inside its own
`efficiency_source_column` value, so no downstream reader can treat it as sourced.

### Why assay labels are not merged

**There is no merged label column in this repository, and no code path that produces
one.**

Measurements from different RT experiments are not automatically
comparable. Prime-editing efficiency, retron activity, DGR activity, and
in-vitro retroviral RT kinetics represent different assays, units, and
biological contexts.

Assay type is also almost perfectly confounded with RT family, because each family was
characterised by a different subfield using its own readout. So if those numbers shared
a column, a leave-one-family-out split would silently become a leave-one-assay-out
split, and a model could score well by learning which publication a sequence came from
rather than anything about catalysis. That is not hypothetical: the audit already found
that mean-pooled embeddings on this panel carry lineage signal.

For this reason, this project does **not** combine heterogeneous RT
assays into a single activity label. Each assay must remain an
independent task.

**This is enforced mechanically, not by convention.** `schemas/task_schema.py` rejects
a table carrying two tasks, rejects inconsistent units inside a task, and refuses to
concatenate tables whose `label_units` or `label_assay` differ.
`schemas/test_task_schema.py` proves the refusal holds both through the helper and when
a merged frame is built by hand with plain pandas, and continuous integration runs it on
every push.

## Representations

The benchmark investigates several levels of protein representation.

### Simple baselines

-   Protein length
-   Amino-acid composition
-   Sequence k-mer composition

### Handcrafted biological features

-   Physicochemical properties
-   Sequence-derived descriptors
-   Structural descriptors where available. The structural block is 12 columns
    computed from the inherited models in `data/structures/`. 56 of 57 rows carry
    them; Line1-RT has no structure file, and its 12 columns are marked missing in
    the mask rather than zero-filled

### Protein language models

ESM-2 representations were evaluated across multiple model scales,
including:

-   ESM-2 8M
-   ESM-2 35M
-   ESM-2 150M
-   ESM-2 650M

Additional analyses investigated alternative pooling and representation
strategies, including catalytic-core-focused representations. None of them
fixed the lineage problem, and the two core-focused variants made it worse; see
[What the PLMs Learned](#what-the-plms-learned).

## Evaluation Protocol

The benchmark was designed to reduce evolutionary shortcut learning and
model-selection leakage.

Twelve representations, two model heads (regularized logistic regression for `active`
and ridge regression for `pe_efficiency_pct`, and nothing else), and one free
parameter, the regularization strength, taken from a grid of 6 values fixed a priori
and selected in the inner loop of a nested leave-one-family-out protocol. No other
model family appears anywhere. That single free parameter is what makes the
search-capacity null comparison below legitimate.

Key safeguards include:

-   **Leave-one-family-out evaluation**, 7 outer folds
-   Frozen evaluation splits, with a test that the frozen file still matches the
    partition the harness derives at run time
-   Out-of-fold predictions, pooled once over all 57 rows
-   Bootstrap confidence intervals, 10000 resamples
-   Dimensionality-matched Gaussian noise controls
-   Label-permutation controls
-   Search-capacity null experiments
-   Fixed random seeds
-   Dataset and artifact checksums
-   No selection decisions based on held-out family labels
-   A deliberate **peeking positive control** that the leakage check is required to
    reject, so a green suite cannot mean the check is inert

The objective is not simply to obtain the highest score, but to
determine whether an observed score contains evidence of generalizable
biological signal.

## The instrument

The contribution here is the **search-capacity null**: run a selection procedure,
unchanged, on K vectors of pure noise and record the score it reaches. That is how
much of a reported score the procedure can manufacture from nothing on this dataset
with this metric. Every score in this repository carries one, plus a bootstrap
interval. **A score that does not clear its null has reported nothing.**

![capacity curve](bench/figures/search_null_capacity.png)

## Main Result

> **Protein language model embeddings did not improve RT activity
> prediction over simpler representations under family-held-out
> evaluation on this dataset.**

For the primary binary activity benchmark. All figures are out-of-fold, pooled over
all 57 rows under the nested leave-one-family-out protocol.

| Representation | PR-AUC | Gaussian noise control | Permutation p95 | Survives permutation control |
| --- | --- | --- | --- | --- |
| 4-mer composition | **0.6212** | 0.4458 | 0.5398 | **Yes** |
| ESM-2 650M | 0.4220 | 0.2889 | 0.5217 | No |
| ESM-2 8M | 0.3706 | 0.2581 | 0.5676 | No |
| Physicochemical | 0.3623 | 0.2643 | 0.4254 | No |
| Protein length | 0.2599 | 0.2474 | 0.4111 | No |

The dataset prevalence is approximately **0.3684**, which is the
chance-level reference for PR-AUC.

Among the tested representations, the 4-mer representation was the only
one in the reported comparison to survive the permutation control. The permutation
test was run on 6 of the 12 representations, and the subset is stated rather than
silent.

However, this should **not** be interpreted as evidence that the model
discovered a catalytic sequence motif. The 4-mer predictions were
correlated with protein length and family-associated sequence structure,
while attribution was distributed across a very high-dimensional feature
space. Specifically: its out-of-fold score ranks with sequence length at Spearman
**+0.5212**, its top 1 percent of features carry only **6.6 percent** of the
attribution mass against a 1.0 percent feature share, and the top decile of
family-explained features carries 16.4 percent against a 10 percent share. The result
is therefore treated cautiously as a sequence-composition signal rather than a
mechanistic discovery. See [reports/interpretation.md](reports/interpretation.md).

### Nothing clears the composite metric, and the ordering above is not resolvable

**The table above is a PR-AUC table, and PR-AUC is one component of the metric this
benchmark actually reports.** On the composite CLS metric:

-   **No representation under either head clears the CLS gate.** The highest CLS,
    0.3739, sits below the search-capacity null p95 of **0.4433** at the one free
    parameter this benchmark uses, and every CLS bootstrap interval includes zero.
-   **The median minimum resolvable CLS difference is 0.4816**, which is larger than
    every CLS in the table. The CLS ordering is therefore not resolvable on this panel
    at all, and no pairwise difference between representations should be read as a win.

The dataset limits are the honest explanation for much of this: 57 enzymes, 21
positives, a Kish effective sample size of **11.34**, and three of seven
leave-one-family-out folds (CRISPR-associated, Other, Unclassified) containing no
active enzyme at all.

Detail in [reports/statistical_validation.md](reports/statistical_validation.md). The
auditable account by phase is [reports/FINAL_REPORT.md](reports/FINAL_REPORT.md), and
[reports/MANUSCRIPT_SUMMARY.md](reports/MANUSCRIPT_SUMMARY.md) reads it as a paper
would.

### The earlier single-task result, which stands

**No method tested beats using `protein_length_aa` as the score with no training at
all, and no method clears the score its own selection procedure reaches on pure
noise.**

| | CLS |
| --- | --- |
| 3-mer cosine to nearest training active, zero training | **0.4576** |
| `protein_length_aa`, zero training | **0.4416** |
| Best trained model (handcrafted + RandomForest) | 0.4284 |
| Best protein language model representation (ESM-2 150M) | 0.3052 |
| Minimum difference this benchmark can resolve at 80 percent power | **0.3419** |

The previously reported 0.9754 does not appear in this table. The reasons are in
[WRITEUP.md](WRITEUP.md), in the section titled "Why the previously reported 0.975 is
not a result", and are summarised below.

## What the PLMs Learned

The representation analysis showed an important distinction between
encoding biological structure and predicting the target phenotype.

ESM-2 embeddings strongly captured RT family information, but this did
not translate into reliable family-held-out activity prediction. All three parts of
this are now reproduced by scripts in this repository against the curated Task A
table, where previously two of them were published without code behind them:

-   ESM-2 embeddings classify RT **family** at **0.8197** five-fold accuracy against a
    **0.3214** majority baseline, and the accuracy rises monotonically with model
    scale: 0.7652 at 8M, 0.7833 at 35M, 0.8030 at 150M, 0.8197 at 650M.
-   Embedding **PC1 tracks sequence length** at Spearman **-0.7681**, reproducing the
    published figure exactly.
-   The same 650M representation that classifies family at 0.8197 predicts activity out
    of family at a PR-AUC of **0.4220**, which does not survive its own permuted
    labels.

That contrast is the finding: **the representation knows what an enzyme is related to,
and how long it is, and not what it does.**

This suggests that, on this small cross-family dataset, PLM
representations encode substantial evolutionary lineage information
while providing limited evidence of transferable RT activity signal.

Length residualization, family residualization, catalytic-core pooling and
attention-weighted pooling were all tried, and all failed to fix this. The two
core-focused variants became the **most** lineage-predictive of all, at 0.818 family
accuracy against 0.800 for the mean-pooled and residualized variants. See
[reports/representation_diagnostics.md](reports/representation_diagnostics.md).

## Leakage Audit of the Original Challenge Pipeline

This project grew from an earlier competition pipeline of my own.

### Why the previously reported 0.975 is not a result

**I optimized the competition metric directly against the labels it was scored on.**
`fast_opt.py` maximizes `compute_cls` over all 57 rows with 29 blend weights plus a
power exponent, and reseeds itself from its own previously fitted constants, so each
run resumes the prior hill climb. The commit history records 20 messages quoting a
CLS, climbing 0.4380 to 0.9754.

The final prediction layer therefore cannot be treated as an unbiased estimate of
generalization performance.

To quantify this, the project introduced **search-capacity null experiments**: the same
optimization procedure, unchanged, applied to vectors of pure Gaussian noise.

| Free parameters | CLS on noise (p95) |
| --- | --- |
| **29, the matched count** | **0.9340** |
| 50 | 0.9727 |

**Corrected 2026-10-03.** This section previously bolded the K=50 row and concluded
that the submitted score "sits within its own noise floor". That was an invalid
comparison: it compared a 29-parameter search against the noise ceiling of a
50-parameter one. The 62 fitted parameters quoted here belong to a different stored
artifact, which scored 0.8978, not to the submission.

At the **matched** count of 29 free parameters the p95 is 0.9340, so the submission's
0.9754 sits **above** its noise floor by +0.0414, not below it. The correct statement
is weaker in a different way: that margin is about half the **0.0794** bootstrap
interval width on the submitted vector, against a Kish effective sample size of
**11.34**, so the score is **not distinguishable** from what the procedure
manufactures from noise. It is not shown to be inside the null, and it is not shown to
be outside it either.

The leakage finding does not depend on this comparison. It rests on the static and
dynamic evidence in [audit/leakage_report.md](audit/leakage_report.md): the inherited
search optimises `compute_cls` directly against the test labels and reseeds itself from
its own previously fitted constants.

These experiments demonstrate that flexible searches over small
biological datasets can generate surprisingly high scores even when the
candidate predictors contain no biological signal.

The original challenge result is therefore preserved as project history,
while the current benchmark uses stricter evaluation and statistical
controls.

## Why Null Controls Matter

One of the central methodological findings of this project is that a
single noise control is not always sufficient.

Some ESM-2 representations exceeded dimensionality-matched Gaussian
noise controls but subsequently failed label-permutation tests. ESM-2 650M cleared its
noise control by +0.0535 and ESM-2 8M by +0.0022, and both then lost to their own
shuffled labels, at 0.4220 against a permuted p95 of 0.5217 and 0.3706 against 0.5676.
The noise control alone would have passed them, which is exactly why the permutation
test is not optional.

In other words:

> Beating random features does not necessarily mean that a
> representation predicts the biological target.

This motivates using multiple controls when benchmarking
high-dimensional biological representations on small datasets.

## Protocol integrity

`bench/test_protocol.py` corrupts every held-out label and requires the selected
configuration to be byte-identical, and includes a deliberate **peeking positive
control** that the check must reject. The control is the load-bearing test: a green
suite in which peeking also passed would mean the check is inert. Continuous
integration runs it on every push, alongside a self-check on the null instrument.

## Repository Structure

``` text
RT-plm-benchmark/
├── audit/                  # Leakage and historical-pipeline audit
├── bench/                  # Benchmarking and statistical evaluation
│   ├── protocol.py         #   The nested LOFO harness every experiment calls
│   ├── search_null.py      #   Search-capacity null, the central instrument
│   ├── names.py            #   Repairs an inherited RT-name join defect, fails loudly
│   └── results/            #   All measured results
├── curation/               # Identity clustering and the frozen split definitions
├── data/                   # Core inherited data and structures
├── data_acquisition/       # Source parsers, fetch checklist, reference resolver
├── embeddings/             # Protein language model representations, MANIFEST.json
├── evaluation/             # The competition metric, as inherited
├── features/               # Sequence and handcrafted representations
├── legacy_leaky/           # Quarantined inherited code. Not usable in any results table
├── legacy_submission/      # The submitted artifact, as the object of study
├── reports/                # Final reports and methodological analyses
├── schemas/                # The shared row schema and the merged-label validator
├── survey/                 # Dataset feasibility survey and acquisition log
├── tasks/                  # One per task: raw/, curated.csv, splits/, PROVENANCE.md
│   ├── taskA_crossfamily/  #   Completed cross-family RT benchmark
│   ├── taskA2_evolved/     #   Not acquired
│   ├── taskB_mmlv_dms/     #   Prepared variant-effect task, label-blocked
│   ├── taskB_hivrt/        #   HIV-1 RT phenotype, audited, not a DMS
│   └── taskC_*/            #   Blocked, no usable panel found
├── ORIGIN.md               # Provenance and the read-only guarantee
├── PROGRESS.md             # Dated execution record
├── WRITEUP.md              # Narrative writeup, including blocked experiments
├── NEXT_STEPS.md           # Remaining experiments and continuation context
└── reproduce.py            # Regenerates every result from data/
```

## Reproducibility

The benchmark emphasizes traceability and reproducibility.

The pipeline records:

-   fixed random seeds
-   source provenance
-   sequence checksums
-   artifact checksums
-   frozen splits
-   model and representation metadata
-   explicit missing or blocked experiments

```
python reproduce.py          # everything, several hours
python reproduce.py --quick  # skips the null sweep and embedding extraction
```

Retrains everything from `data/` to predictions and reads no stored result. Seed 42
throughout; every script prints its seed and library versions.

`make reproduce` runs the same sequence and there are also `make audit`, `make test`,
`make null`, `make bench` and `make scale` targets. The Makefile is provided
untested: `make` is not installed on the machine these results were produced on, so
`reproduce.py` is the entry point that has actually been exercised here. Run the heavy
stages one at a time; extraction loads a 650M parameter model, and on a memory
constrained machine parallel stages get terminated.

Environment for every number reported: Python 3.14.2 on Windows 11, numpy 2.4.2,
scipy 1.17.1, pandas 3.0.1, scikit-learn 1.8.0, matplotlib 3.10.8, torch 2.11.0+cpu
with zero CUDA devices, fair-esm 2.0.0.

See the reports and `NEXT_STEPS.md` for detailed implementation status
and known environment limitations.

## Limitations

This benchmark should be interpreted within the limits of the available
data.

The main limitations are:

-   only 57 experimentally assayed RTs are available for the
    cross-family task, with 21 positives and a Kish effective sample size of 11.34
-   evolutionary family structure is strong relative to sample size
-   three of the seven held-out families contain no positive examples at all
-   the continuous efficiency target has weaker provenance than the
    binary activity label
-   high-dimensional representations are difficult to evaluate reliably
    at this sample size
-   on the composite CLS metric nothing clears its search-capacity null, and the
    median minimum resolvable difference exceeds every CLS observed, so the CLS
    ordering is not resolvable on this panel
-   not every possible PLM architecture, layer, or pooling strategy was
    searched, deliberately avoiding another large model-selection search
-   the planned M-MLV RT variant-effect benchmark remains blocked
    because the required per-variant experimental labels were never deposited and
    cannot be computed from the public record

These limitations are part of the benchmark rather than being hidden
from the analysis.

## Blocked experiments

ProtT5-XL-U50, inverse-folding likelihoods, and zero-shot ESM-1v masked marginals are
marked **NOT RUN** with their exact blockers recorded in [WRITEUP.md](WRITEUP.md).
**None was given an estimated or literature-quoted score.**

## Future Work

A natural next step is a within-protein RT variant-effect benchmark.

A saturated M-MLV RT mutagenesis dataset would allow a complementary
question:

> Do protein language models predict the functional effects of mutations
> within a single RT better than traditional representations?

The sequence construction, reference resolution, and split design for
this task have been prepared, but modelling is intentionally paused
until the experimental per-variant labels can be obtained from a
verifiable source.

The obstacle is more general than one dataset. A feasibility survey of the two
standardized collections found **no reverse transcriptase deep mutational scan in
either**: 0 of ProteinGym v1.3's 217 substitution assays, and 0 of MaveDB's 2894
target genes. See [survey/DATASET_SURVEY.md](survey/DATASET_SURVEY.md).

Other future directions include:

-   additional experimentally measured RT datasets as they become
    available
-   zero-shot variant-effect prediction
-   structure-aware representations
-   inverse-folding models
-   larger and more diverse RT panels
-   improved evaluation metrics for very small biological datasets

## Reports

Detailed analyses are available in the `reports/` and `bench/results/`
directories, including:

-   [reports/MANUSCRIPT_SUMMARY.md](reports/MANUSCRIPT_SUMMARY.md), manuscript-style
    project summary
-   [reports/FINAL_REPORT.md](reports/FINAL_REPORT.md), the final benchmark report,
    phase by phase
-   [reports/statistical_validation.md](reports/statistical_validation.md), the nulls,
    intervals, permutations and resolvability
-   [reports/CROSS_TASK_COMPARISON.md](reports/CROSS_TASK_COMPARISON.md), what the pair
    of tasks does and does not establish
-   [reports/representation_diagnostics.md](reports/representation_diagnostics.md),
    representation comparison
-   [reports/interpretation.md](reports/interpretation.md), interpretation and
    attribution analysis
-   [reports/reconciliation.md](reports/reconciliation.md), dataset construction and
    provenance reconciliation
-   [reports/split_design.md](reports/split_design.md) and
    [reports/split_verification.md](reports/split_verification.md), split design and
    its verification

These reports contain the detailed evidence behind the README-level
conclusions.

## Contributors

-   **Tanish N.**: project design, data pipeline, modelling,
    benchmarking, statistical analysis, and interpretation
-   **Hemalakshmi P.**: documentation, README development, and
    project presentation

## Data source and citation

The Task A panel is derived from the supplementary material of:

> Doman JL, Pandey S, Neugebauer ME, An M, Davis JR, Randolph PB, et al.
> Phage-assisted evolution and protein engineering yield compact, efficient prime
> editors. *Cell* 2023, 186(18):3983-4002.e26.
> DOI [10.1016/j.cell.2023.07.039](https://doi.org/10.1016/j.cell.2023.07.039)

Those supplementary files are redistributed in this repository under the article's own
**CC BY 4.0** licence, which permits redistribution with attribution. Per-file
provenance is in
[tasks/taskA_crossfamily/PROVENANCE.md](tasks/taskA_crossfamily/PROVENANCE.md) and the
quoted source facts are in
[reports/doman2023_source_facts.md](reports/doman2023_source_facts.md).

## Acknowledgements

This project builds on work originally developed for a competition
submission, and on experimental reverse-transcriptase datasets produced
by the corresponding research groups.

We thank the authors of the underlying experimental studies and the
developers of the open-source protein modelling, bioinformatics, and
machine-learning tools used throughout this project.

## Project Status

**Task A: Complete**

The cross-family RT representation benchmark, leakage audit, statistical
controls, and final reports are complete.

**Task B: Prepared, data-blocked**

The M-MLV variant-effect task has its reference sequence and variant
construction framework prepared, but performance modelling is paused
until the required experimental labels are available from a verifiable
source.

The reference is resolved: 498 amino acids, read out of the parent plasmid Addgene
132775 and cross-checked against Addgene 174820 at 498 of 498 residues. All 1046
variant sequences are constructed and the splits are frozen. **The labels were never
deposited, no benchmark result exists, and none can be computed from the public
record**, across 30 acquisition attempts in six route families. No number has been
produced for this task and none will be invented for it.

## Licence

MIT. See [LICENSE](LICENSE) and [CITATION.cff](CITATION.cff). The redistributed source
data carries its own licence, recorded above.

------------------------------------------------------------------------

### Core takeaway

**On this 57-RT cross-family dataset, larger protein language models
encoded evolutionary lineage strongly but did not provide evidence of
better family-held-out RT activity prediction than simpler sequence
representations. Rigorous null and permutation controls were essential
to reaching that conclusion.**
