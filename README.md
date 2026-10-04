# Benchmarking Protein Language Models for Reverse Transcriptase Activity Prediction

A leakage-aware benchmark for evaluating whether protein language model
(PLM) representations improve reverse transcriptase (RT) activity
prediction across evolutionary families.

This project builds on our work for the Mandrake Bio Open Challenge.
Rather than optimizing a leaderboard score, this repository focuses on a
stricter question: **do learned protein representations actually
generalize to unseen RT families better than simple sequence-derived
baselines?**

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

## Dataset

### Task A: Cross-family RT activity

The completed benchmark uses a panel of:

-   **57 experimentally assayed reverse transcriptases**
-   **21 active RTs**
-   RTs spanning multiple evolutionary families
-   full amino-acid sequences verified against the primary-source
    supplementary material
-   binary activity as the primary reproducible target

A continuous `pe_efficiency_pct` target is retained for regression and
comparison with the inherited benchmark, but its provenance is treated
as a limitation because the per-enzyme numerical values were not
available as a published supplementary table.

### Why assay labels are not merged

Measurements from different RT experiments are not automatically
comparable. Prime-editing efficiency, retron activity, DGR activity, and
in-vitro retroviral RT kinetics represent different assays, units, and
biological contexts.

For this reason, this project does **not** combine heterogeneous RT
assays into a single activity label. Each assay must remain an
independent task.

## Representations

The benchmark investigates several levels of protein representation.

### Simple baselines

-   Protein length
-   Amino-acid composition
-   Sequence k-mer composition

### Handcrafted biological features

-   Physicochemical properties
-   Sequence-derived descriptors
-   Structural descriptors where available

### Protein language models

ESM-2 representations were evaluated across multiple model scales,
including:

-   ESM-2 8M
-   ESM-2 35M
-   ESM-2 150M
-   ESM-2 650M

Additional analyses investigated alternative pooling and representation
strategies, including catalytic-core-focused representations.

## Evaluation Protocol

The benchmark was designed to reduce evolutionary shortcut learning and
model-selection leakage.

Key safeguards include:

-   **Leave-one-family-out evaluation**
-   Frozen evaluation splits
-   Out-of-fold predictions
-   Bootstrap confidence intervals
-   Dimensionality-matched Gaussian noise controls
-   Label-permutation controls
-   Search-capacity null experiments
-   Fixed random seeds
-   Dataset and artifact checksums
-   No selection decisions based on held-out family labels

The objective is not simply to obtain the highest score, but to
determine whether an observed score contains evidence of generalizable
biological signal.

## Main Result

> **Protein language model embeddings did not improve RT activity
> prediction over simpler representations under family-held-out
> evaluation on this dataset.**

For the primary binary activity benchmark:

  ----------------------------------------------------------------------------
  Representation               PR-AUC   Permutation p95  Survives permutation
                                                               control
  ----------------- ----------------- ----------------- ----------------------
  4-mer composition        **0.6212**            0.5398          Yes

  ESM-2 650M                   0.4220            0.5217           No

  ESM-2 8M                     0.3706            0.5676           No

  Physicochemical              0.3623            0.4254           No

  Protein length               0.2599            0.4111           No
  ----------------------------------------------------------------------------

The dataset prevalence is approximately **0.3684**, which is the
chance-level reference for PR-AUC.

Among the tested representations, the 4-mer representation was the only
one in the reported comparison to survive the permutation control.

However, this should **not** be interpreted as evidence that the model
discovered a catalytic sequence motif. The 4-mer predictions were
correlated with protein length and family-associated sequence structure,
while attribution was distributed across a very high-dimensional feature
space. The result is therefore treated cautiously as a
sequence-composition signal rather than a mechanistic discovery.

## What the PLMs Learned

The representation analysis showed an important distinction between
encoding biological structure and predicting the target phenotype.

ESM-2 embeddings strongly captured RT family information, but this did
not translate into reliable family-held-out activity prediction.

This suggests that, on this small cross-family dataset, PLM
representations encode substantial evolutionary lineage information
while providing limited evidence of transferable RT activity signal.

## Leakage Audit of the Original Challenge Pipeline

This project grew from an earlier Mandrake Bio Open Challenge pipeline.

A retrospective audit found that the original high-scoring ensemble
involved extensive optimization against the available labels. The final
prediction layer therefore could not be treated as an unbiased estimate
of generalization performance.

To quantify this problem, the project introduced **search-capacity null
experiments**: the same optimization procedure was applied to
noise-generated prediction vectors.

These experiments demonstrated that flexible searches over small
biological datasets can generate surprisingly high scores even when the
candidate predictors contain no biological signal.

The original challenge result is therefore preserved as project history,
while the current benchmark uses stricter evaluation and statistical
controls.

## Why Null Controls Matter

One of the central methodological findings of this project is that a
single noise control is not always sufficient.

Some ESM-2 representations exceeded dimensionality-matched Gaussian
noise controls but subsequently failed label-permutation tests.

In other words:

> Beating random features does not necessarily mean that a
> representation predicts the biological target.

This motivates using multiple controls when benchmarking
high-dimensional biological representations on small datasets.

## Repository Structure

``` text
RT-plm-benchmark/
├── audit/                  # Leakage and historical-pipeline audit
├── bench/                  # Benchmarking and statistical evaluation
├── data/                   # Core inherited data and structures
├── tasks/
│   ├── taskA_crossfamily/  # Completed cross-family RT benchmark
│   └── taskB_mmlv_dms/     # Prepared variant-effect task, currently label-blocked
├── features/               # Sequence and handcrafted representations
├── embeddings/             # Protein language model representations
├── reports/                # Final reports and methodological analyses
├── schemas/                # Dataset validation rules
├── legacy_leaky/           # Quarantined historical leakage-related components
├── legacy_submission/      # Original challenge submission artifacts
└── NEXT_STEPS.md           # Remaining experiments and continuation context
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

The Task A pipeline can be reproduced using the repository's provided
reproduction workflow. Individual benchmark stages have also been
validated independently.

See the reports and `NEXT_STEPS.md` for detailed implementation status
and known environment limitations.

## Limitations

This benchmark should be interpreted within the limits of the available
data.

The main limitations are:

-   only 57 experimentally assayed RTs are available for the
    cross-family task
-   evolutionary family structure is strong relative to sample size
-   some held-out families contain few or no positive examples
-   the continuous efficiency target has weaker provenance than the
    binary activity label
-   high-dimensional representations are difficult to evaluate reliably
    at this sample size
-   not every possible PLM architecture, layer, or pooling strategy was
    searched, deliberately avoiding another large model-selection search
-   the planned M-MLV RT variant-effect benchmark remains blocked
    because the required per-variant experimental labels were not
    publicly available during data acquisition

These limitations are part of the benchmark rather than being hidden
from the analysis.

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

-   manuscript-style project summary
-   final benchmark report
-   statistical validation
-   representation comparison
-   interpretation and attribution analysis
-   dataset construction and provenance documentation
-   split-design documentation

These reports contain the detailed evidence behind the README-level
conclusions.

## Contributors

-   **Tanish N.**: project design, data pipeline, modelling,
    benchmarking, statistical analysis, and interpretation
-   **Hemalakshmi P.**: documentation, README development, and
    project presentation

## Acknowledgements

This project builds on work originally developed for the **Mandrake Bio
Open Challenge** and on experimental reverse-transcriptase datasets
produced by the corresponding research groups.

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

------------------------------------------------------------------------

### Core takeaway

**On this 57-RT cross-family dataset, larger protein language models
encoded evolutionary lineage strongly but did not provide evidence of
better family-held-out RT activity prediction than simpler sequence
representations. Rigorous null and permutation controls were essential
to reaching that conclusion.**
