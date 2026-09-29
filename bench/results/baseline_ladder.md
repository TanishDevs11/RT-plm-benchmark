# Baseline ladder

Seed: 42. Every row runs through the nested protocol in `bench/protocol.py`.

`null p95` is the 95th percentile of the CLS reached by the same selection procedure applied to pure noise, and `margin` is the score minus that null. A row whose margin is not clearly positive has not demonstrated signal, however high its raw CLS looks.

| Method | Kind | CLS | PR-AUC | wSpearman | 95% CI | Cands | null p95 | Margin | Beats length |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. protein_length_aa, no training | zero-parameter | 0.4416 | 0.5102 | 0.3893 | [0.000, 0.656] | 1 | 0.3961 | +0.0455 | reference |
| 2. negative protein_length_aa, no training | zero-parameter | 0.0000 | 0.3128 | 0.0000 | [0.000, 0.137] | 1 | 0.3961 | -0.3961 | NO |
| 3. amino acid composition PC1, no training | zero-parameter | 0.0000 | 0.4595 | 0.0000 | [0.000, 0.528] | 1 | 0.3961 | -0.3961 | NO |
| 4. 3-mer cosine to nearest training active, no training | zero-parameter | 0.4576 | 0.5309 | 0.4021 | [0.000, 0.681] | 1 | 0.3961 | +0.0615 | yes |
| 5. family prior by nearest training family, no training | zero-parameter | 0.4160 | 0.4304 | 0.4025 | [0.000, 0.578] | 1 | 0.3961 | +0.0199 | NO |
| 8a. handcrafted + ExtraTrees | trained | 0.1802 | 0.6948 | 0.1036 | [0.000, 0.624] | 6 | 0.4754 | -0.2951 | NO |
| 8b. handcrafted + RandomForest | trained | 0.4284 | 0.8288 | 0.2888 | [0.000, 0.739] | 6 | 0.4754 | -0.0470 | NO |
| 9. handcrafted + logistic regression | trained | 0.0000 | 0.6533 | 0.0000 | [0.000, 0.461] | 4 | 0.4570 | -0.4570 | NO |
| 10. raw ESM-2 mean-pooled + logistic regression | trained | 0.0000 | 0.2877 | 0.0000 | [0.000, 0.325] | 4 | 0.4570 | -0.4570 | NO |

## Not run

| Baseline | Status | Blocker |
| --- | --- | --- |
| 6. zero-shot ESM-1v masked-marginal pseudo-likelihood | NOT RUN | Masked marginals need one forward pass per residue per sequence. At 57 RTs of median length 523 that is roughly 30000 forward passes of a 650M parameter model, and the probe found torch 2.11.0+cpu with zero CUDA devices. This is a wall-clock blocker, not a missing dependency. |
| 7. inverse-folding log-likelihood, ESM-IF or ProteinMPNN | NOT RUN | Neither package is installed. ESM-IF additionally requires a geometric deep learning stack (torch-geometric, torch-sparse) with no prebuilt wheels for Python 3.14 on this platform. |

## Reading this table

The reference line is baseline 1, `protein_length_aa` used directly as the score with no training whatsoever, at CLS 0.4416. Any trained model below that line is not learning function; it is learning something weaker than a single number that was already in the input file.

The bootstrap intervals are wide because the dataset is small and the weighted Spearman term has a Kish effective sample size of 11.3. Two rows whose intervals overlap heavily have not been separated by this benchmark, and the paired comparison in the representation phase is the only place where a difference is claimed.
