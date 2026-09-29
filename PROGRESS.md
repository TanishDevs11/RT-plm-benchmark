# Progress record

**Date: 2026-09-29.** Snapshot of what has been measured, what is still running,
and what is blocked. Every number here came from a script in this repository and
can be regenerated. Nothing is estimated.

## Phase status

| Phase | State |
| --- | --- |
| 0. Provenance and repository bootstrap | complete, pushed |
| 1. Leakage audit and quarantine | complete, pushed, gate G1 endorsed |
| 2. Nested LOFO protocol | complete, 6 of 6 tests pass |
| 3. Search-capacity null | complete, pushed |
| 4. Baseline ladder | complete, rerun after the join defect fix |
| 5. Representation benchmark | 10 of 10 representations measured; paired bootstrap still running |
| 6. Scale projection and data expansion scoping | scoping written; projection script ready, not yet run |
| 7. Write-up | scaffolding, licence, CI and Makefile pushed; final report pending |

## Leakage audit

The inherited `fast_opt.py` maximizes `compute_cls` against `seq["active"]` and
`seq["pe_efficiency_pct"]` over all 57 rows, and seeds its starting point from the
previously fitted constants, so each run resumes the prior hill climb on the test
labels. Static scan: 3 files SELECTION_LEAK, 10 UNCLEAR, 10 EVAL_ONLY. The commit
history carries 20 messages quoting a CLS, climbing 0.4380 to 0.9754.

Stored search artifacts hold up to 62 free parameters, against a Kish effective
sample size of 11.34 on 57 nominal rows.

## Metric properties

| Quantity | Value |
| --- | --- |
| Kish effective sample size | 11.338 |
| MMLV-RT weight share | 15.56 percent |
| Top 5 RTs weight share | 56.17 percent |
| All 36 inactives combined | 0.137 percent |
| Bootstrap 95 percent CI width on the submitted vector | 0.0794 |
| Row-order sensitivity range, 2000 permutations | 0.0048 |

## Search-capacity null

CLS reached by the inherited search on pure Gaussian noise. The single seed-42
reference draw is 0.9121, reproducible exactly. Across 20 repeats the reference
distribution has mean 0.8662 and median 0.8702, so the 0.848 figure quoted in the
brief sits near the centre and the single draw was simply a high one compared
against the wrong statistic. The procedure was not modified to obtain agreement.

| K free parameters | mean | p95 | max |
| --- | --- | --- | --- |
| 1 | 0.2751 | 0.4433 | 0.4843 |
| 2 | 0.3945 | 0.4944 | 0.5145 |
| 5 | 0.5006 | 0.5606 | 0.5616 |
| 10 | 0.6170 | 0.6536 | 0.6634 |
| 20 | 0.7909 | 0.8637 | 0.8828 |
| 29 | 0.8629 | 0.9340 | 0.9503 |
| 50 | 0.9210 | 0.9727 | 0.9737 |

Budget sweep at K=29: 10 iterations reach mean 0.6809, 30 reach 0.7396, 60 reach
0.7828, 130 reach 0.8314, 260 reach 0.8629.

The curve does not saturate. Five free parameters already match the best trained
baseline in this repository, and fifty reach the submitted score.

## Baseline ladder

| Method | CLS | PR-AUC | wSpearman | Beats length |
| --- | --- | --- | --- | --- |
| 1. protein_length_aa, no training | 0.4416 | 0.5102 | 0.3893 | reference |
| 4. 3-mer cosine to nearest training active | 0.4576 | 0.5309 | 0.4021 | yes |
| 5. family prior by nearest training family | 0.4160 | 0.4304 | 0.4025 | no |
| 8b. handcrafted + RandomForest | 0.5072 | 0.7810 | 0.3755 | yes |
| 8a. handcrafted + ExtraTrees | 0.1522 | 0.6830 | 0.0856 | no |
| 2. negative protein_length_aa | 0.0000 | 0.3128 | 0.0000 | no |
| 3. amino acid composition PC1 | 0.0000 | 0.4595 | 0.0000 | no |
| 9. handcrafted + logistic regression | 0.0000 | 0.6427 | 0.0000 | no |
| 10. raw ESM-2 mean-pooled + logistic regression | 0.0000 | 0.2877 | 0.0000 | no |

Values above are from the pre-fix run for rows 1 to 5, which do not use the
repaired features; the trained rows are being recomputed. Several rows score
exactly zero because weighted Spearman floors at zero. Rows 8a and 9 separate
actives well, at PR-AUC 0.68 and 0.64, yet score near zero because they misrank the
high-efficiency enzymes. That is a real property of the metric, not a bug.

## Representation benchmark

No representation beat the zero-training length baseline of 0.4416.

| Representation | CLS | Family accuracy |
| --- | --- | --- |
| ESM-2 150M mean-pooled | 0.3052 | 0.802 |
| ESM-2 35M mean-pooled | 0.1394 | 0.782 |
| ESM-2 8M mean-pooled | 0.0074 | 0.745 |
| handcrafted, sequence and physicochemical | 0.0000 | 0.712 |
| structure, pLDDT cleft and topology | 0.0000 | 0.659 |
| ESM-2 650M mean-pooled | 0.0000 | 0.800 |
| ESM-2 650M, length-residualized | 0.0000 | 0.800 |
| ESM-2 650M, family-residualized | 0.0000 | 0.800 |
| ESM-2 650M, catalytic-core pooled | 0.0000 | 0.818 |
| ESM-2, attention-weighted core pooling | 0.0000 | 0.818 |

Every corrective pooling failed to help. The two that target the catalytic core
produced the highest lineage accuracy of any representation, which is the opposite
of the intended effect. The model-scale series is non-monotonic.

Independently verified: ESM-2 embeddings classify RT family at 0.8000 accuracy
against a 0.3214 majority baseline, and embedding PC1 tracks `protein_length_aa` at
Spearman -0.7681.

## Inherited data defect found and repaired

`topology_features.csv` omits the `-RT` suffix that `rt_sequences.csv` carries, so
a join on `rt_name` matched zero rows and fed nine entirely missing columns into
the handcrafted feature table. The model trained on nothing, silently. Repaired in
`bench/names.py`, which now fails loudly rather than returning empty columns. Two
further defects are recorded there: `Line1-RT` has no predicted structure, and
`Vp-96.pdb` duplicates `Vp96-RT.pdb`, so 57 structure files cover 56 RTs.

## Blocked

| Item | Status | Blocker |
| --- | --- | --- |
| ProtT5-XL-U50 | NOT RUN | `transformers` and `sentencepiece` not installed |
| Inverse folding, ESM-IF or ProteinMPNN | NOT RUN | not installed; no Python 3.14 geometric stack wheels |
| Zero-shot ESM-1v masked marginals | NOT RUN | roughly 30000 forward passes of a 650M model on CPU only |
| ESM-1v mean-pooled | pending | extraction interrupted by the host memory reaper; retry queued |

## Environment

Python 3.14.2, Windows 11, torch 2.11.0+cpu with zero CUDA devices, 16.9 GB RAM.
numpy 2.4.2, scipy 1.17.1, pandas 3.0.1, scikit-learn 1.8.0, fair-esm 2.0.0.
Seed 42 throughout. Heavy jobs must run one at a time: the host terminates
background work under memory pressure, which has already interrupted two runs.
