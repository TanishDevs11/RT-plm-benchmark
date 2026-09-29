# Representation benchmark

Seed: 42. One nested protocol, one pair of inner-selected heads, only the representation varies.

## Power statement

With 21 positives and a weighted-Spearman effective sample size of 11.3, the minimum CLS difference this benchmark can resolve at 80 percent power is **0.342**. Any gap smaller than that is reported below as not resolvable at this sample size, and is not a win for either side. This threshold is computed from the bootstrap standard deviation of the paired difference, not assumed.

## Results

| Representation | Dims | CLS | PR-AUC | wSpearman | 95% CI | null p95 | Margin | Family acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ESM-2 150M mean-pooled | 640 | 0.3052 | 0.3666 | 0.2614 | [0.000, 0.529] | 0.4914 | -0.1861 | 0.802 |
| ESM-2 35M mean-pooled | 480 | 0.1394 | 0.2985 | 0.0909 | [0.000, 0.434] | 0.4914 | -0.3520 | 0.782 |
| ESM-2 8M mean-pooled | 320 | 0.0074 | 0.3242 | 0.0037 | [0.000, 0.455] | 0.4914 | -0.4840 | 0.745 |
| handcrafted: sequence and physicochemical | 112 | 0.0000 | 0.6436 | 0.0000 | [0.000, 0.458] | 0.4914 | -0.4914 | 0.712 |
| structure: pLDDT, cleft and topology | 18 | 0.0000 | 0.3391 | 0.0000 | [0.000, 0.352] | 0.4914 | -0.4914 | 0.659 |
| ESM-2 650M mean-pooled | 1280 | 0.0000 | 0.2870 | 0.0000 | [0.000, 0.353] | 0.4914 | -0.4914 | 0.800 |
| ESM-2 650M, length-residualized | 1280 | 0.0000 | 0.3205 | 0.0000 | [0.000, 0.290] | 0.4914 | -0.4914 | 0.800 |
| ESM-2 650M, family-residualized | 1280 | 0.0000 | 0.4016 | 0.0000 | [0.000, 0.121] | 0.4914 | -0.4914 | 0.800 |
| ESM-2 650M, catalytic-core pooled | 1280 | 0.0000 | 0.2781 | 0.0000 | [0.000, 0.299] | 0.4914 | -0.4914 | 0.818 |
| ESM-2, attention-weighted core pooling | 1280 | 0.0000 | 0.2808 | 0.0000 | [0.000, 0.287] | 0.4914 | -0.4914 | 0.818 |

YXDD motif not found in 7 RTs, handled explicitly by falling back to full-length pooling for those rows: FuRT-Cas1-RT, ROSE-CRISPR-RT, CHLRE, Line1-RT, Ngaro-RT, Ty1B-RT, Ec48-RT.

## Pairwise comparisons

Paired bootstrap over the same 57 RTs. `P(A beats B)` is the fraction of resamples in which A scored higher, not a point difference.

| A | B | P(A beats B) | Mean diff | Resolvable |
| --- | --- | --- | --- | --- |
| ESM-2 150M mean-pooled | ESM-2 35M mean-pooled | 0.942 | +0.2159 | NOT RESOLVABLE |
| ESM-2 150M mean-pooled | ESM-2 8M mean-pooled | 0.940 | +0.2387 | NOT RESOLVABLE |
| ESM-2 150M mean-pooled | handcrafted: sequence and physicochemical | 0.927 | +0.2823 | NOT RESOLVABLE |
| ESM-2 150M mean-pooled | structure: pLDDT, cleft and topology | 0.930 | +0.2868 | NOT RESOLVABLE |
| ESM-2 150M mean-pooled | ESM-2 650M mean-pooled | 0.963 | +0.2834 | NOT RESOLVABLE |
| ESM-2 150M mean-pooled | ESM-2 650M, length-residualized | 0.966 | +0.3208 | NOT RESOLVABLE |
| ESM-2 150M mean-pooled | ESM-2 650M, family-residualized | 0.959 | +0.3467 | yes |
| ESM-2 150M mean-pooled | ESM-2 650M, catalytic-core pooled | 0.967 | +0.3157 | NOT RESOLVABLE |
| ESM-2 150M mean-pooled | ESM-2, attention-weighted core pooling | 0.968 | +0.3206 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | ESM-2 8M mean-pooled | 0.376 | +0.0228 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | handcrafted: sequence and physicochemical | 0.464 | +0.0665 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | structure: pLDDT, cleft and topology | 0.508 | +0.0710 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | ESM-2 650M mean-pooled | 0.525 | +0.0676 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | ESM-2 650M, length-residualized | 0.552 | +0.1049 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | ESM-2 650M, family-residualized | 0.558 | +0.1309 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | ESM-2 650M, catalytic-core pooled | 0.556 | +0.0999 | NOT RESOLVABLE |
| ESM-2 35M mean-pooled | ESM-2, attention-weighted core pooling | 0.557 | +0.1047 | NOT RESOLVABLE |
| ESM-2 8M mean-pooled | handcrafted: sequence and physicochemical | 0.354 | +0.0437 | NOT RESOLVABLE |
| ESM-2 8M mean-pooled | structure: pLDDT, cleft and topology | 0.411 | +0.0482 | NOT RESOLVABLE |
| ESM-2 8M mean-pooled | ESM-2 650M mean-pooled | 0.393 | +0.0448 | NOT RESOLVABLE |
| ESM-2 8M mean-pooled | ESM-2 650M, length-residualized | 0.438 | +0.0821 | NOT RESOLVABLE |
| ESM-2 8M mean-pooled | ESM-2 650M, family-residualized | 0.454 | +0.1081 | NOT RESOLVABLE |
| ESM-2 8M mean-pooled | ESM-2 650M, catalytic-core pooled | 0.445 | +0.0771 | NOT RESOLVABLE |
| ESM-2 8M mean-pooled | ESM-2, attention-weighted core pooling | 0.446 | +0.0820 | NOT RESOLVABLE |
| handcrafted: sequence and physicochemical | structure: pLDDT, cleft and topology | 0.286 | +0.0045 | NOT RESOLVABLE |
| handcrafted: sequence and physicochemical | ESM-2 650M mean-pooled | 0.204 | +0.0011 | NOT RESOLVABLE |
| handcrafted: sequence and physicochemical | ESM-2 650M, length-residualized | 0.281 | +0.0384 | NOT RESOLVABLE |
| handcrafted: sequence and physicochemical | ESM-2 650M, family-residualized | 0.309 | +0.0644 | NOT RESOLVABLE |
| handcrafted: sequence and physicochemical | ESM-2 650M, catalytic-core pooled | 0.276 | +0.0334 | NOT RESOLVABLE |
| handcrafted: sequence and physicochemical | ESM-2, attention-weighted core pooling | 0.285 | +0.0383 | NOT RESOLVABLE |
| structure: pLDDT, cleft and topology | ESM-2 650M mean-pooled | 0.321 | -0.0034 | NOT RESOLVABLE |
| structure: pLDDT, cleft and topology | ESM-2 650M, length-residualized | 0.344 | +0.0339 | NOT RESOLVABLE |
| structure: pLDDT, cleft and topology | ESM-2 650M, family-residualized | 0.344 | +0.0599 | NOT RESOLVABLE |
| structure: pLDDT, cleft and topology | ESM-2 650M, catalytic-core pooled | 0.337 | +0.0289 | NOT RESOLVABLE |
| structure: pLDDT, cleft and topology | ESM-2, attention-weighted core pooling | 0.340 | +0.0338 | NOT RESOLVABLE |
| ESM-2 650M mean-pooled | ESM-2 650M, length-residualized | 0.360 | +0.0373 | NOT RESOLVABLE |
| ESM-2 650M mean-pooled | ESM-2 650M, family-residualized | 0.365 | +0.0633 | NOT RESOLVABLE |
| ESM-2 650M mean-pooled | ESM-2 650M, catalytic-core pooled | 0.358 | +0.0323 | NOT RESOLVABLE |
| ESM-2 650M mean-pooled | ESM-2, attention-weighted core pooling | 0.360 | +0.0372 | NOT RESOLVABLE |
| ESM-2 650M, length-residualized | ESM-2 650M, family-residualized | 0.191 | +0.0260 | NOT RESOLVABLE |
| ESM-2 650M, length-residualized | ESM-2 650M, catalytic-core pooled | 0.095 | -0.0050 | NOT RESOLVABLE |
| ESM-2 650M, length-residualized | ESM-2, attention-weighted core pooling | 0.116 | -0.0001 | NOT RESOLVABLE |
| ESM-2 650M, family-residualized | ESM-2 650M, catalytic-core pooled | 0.046 | -0.0310 | NOT RESOLVABLE |
| ESM-2 650M, family-residualized | ESM-2, attention-weighted core pooling | 0.047 | -0.0261 | NOT RESOLVABLE |
| ESM-2 650M, catalytic-core pooled | ESM-2, attention-weighted core pooling | 0.175 | +0.0049 | NOT RESOLVABLE |

## Blocked

| Representation | Status | Blocker |
| --- | --- | --- |
| ESM-1v mean-pooled | NOT RUN | embedding cache bench/cache/pooled_esm1v.npz not produced |
| ProtT5-XL-U50 mean-pooled | NOT RUN | transformers and sentencepiece are not installed and could not be installed in this environment |
| inverse-folding likelihood, ESM-IF or ProteinMPNN | NOT RUN | neither package is installed; ESM-IF needs a geometric deep learning stack with no Python 3.14 wheels on this platform |
