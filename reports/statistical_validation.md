# Task A statistical validation

Written by `bench/validate_taskA.py`. Every score in
`bench/results/taskA_representations.md` is reported here with its interval, its
dimensionality-matched noise control, and the search-capacity null at matched
free-parameter count. A score without those is not a result.

Source: `tasks/taskA_crossfamily/curated.csv`, SHA256
`5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc`. Seed 42.

## The search-capacity null, at matched K

This benchmark's inner loop selects exactly **one** free parameter, the
regularization strength, from a grid of 6 values fixed a priori. So the matched
search-capacity null is K equals 1.

| K | repeats | mean | sd | p95 | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 10 | 0.2751 | 0.1213 | 0.4433 | 0.1113 | 0.4843 |

**The bar every score below has to clear is a CLS of 0.4433**, the p95 of what
a one-free-parameter search reaches on pure Gaussian noise.

### An invalid comparison in this repository, and its correction

The inherited result of 0.9754 was produced by a search holding up to 62 free
parameters, and `bench/results/search_null.json` records that a 29-parameter
search reaches a mean of 0.8662 and a p95 of 0.9340 on noise. Comparing a
62-parameter result against a null computed at any smaller K understates the
null, and comparing a 1-parameter result against the K equals 29 null
overstates it. Each score must be compared against the null at its own K.

The correction that matters for this report: the scores below are
one-parameter scores, so 0.4433 is their bar, not 0.9340. That is a much lower
bar, and most of them still do not clear it.

## The primary test: PR-AUC against its own noise control

CLS is the harmonic mean of a separation term, PR-AUC, and a ranking term,
weighted Spearman against `pe_efficiency_pct`. Per the Gate G2 ruling that
column is a digitization of Figure S1A at roughly half a percentage point of
resolution, so a representation that separates actives from inactives well but
does not reproduce the digitized ordering scores a CLS of zero, because the
harmonic mean floors there.

For the primary claim, which is classification of the reproducible binary
label, the honest test is therefore PR-AUC against a dimensionality-matched
noise control. The chance level for PR-AUC is the positive prevalence, 0.3684.

No search-capacity null exists for PR-AUC: `bench/search_null.py` measures what
a search reaches on CLS, not on PR-AUC. That gap is stated rather than papered
over with the CLS bar, which would be a comparison between two different
quantities.

| representation | PR-AUC | 95 percent CI | noise control PR-AUC | prevalence | margin over the larger | clears both |
| --- | --- | --- | --- | --- | --- | --- |
| `kmer4` | 0.6212 | 0.4285 to 0.8325 | 0.4458 | 0.3684 | +0.1754 | **yes** |
| `esm2_650M` | 0.4220 | 0.2665 to 0.6492 | 0.2889 | 0.3684 | +0.0535 | **yes** |
| `esm2_8M` | 0.3706 | 0.2242 to 0.5710 | 0.2581 | 0.3684 | +0.0022 | **yes** |
| `physicochemical` | 0.3623 | 0.2457 to 0.5448 | 0.2643 | 0.3684 | -0.0061 | no |
| `esm2_35M` | 0.3162 | 0.2066 to 0.4977 | 0.2899 | 0.3684 | -0.0522 | no |
| `kmer3` | 0.3137 | 0.2085 to 0.4955 | 0.3029 | 0.3684 | -0.0547 | no |
| `handcrafted_plus_esm2_650M` | 0.3082 | 0.2093 to 0.4748 | 0.2970 | 0.3684 | -0.0602 | no |
| `dipeptide` | 0.3081 | 0.2090 to 0.4618 | 0.3118 | 0.3684 | -0.0604 | no |
| `esm2_150M` | 0.3056 | 0.2052 to 0.4817 | 0.2856 | 0.3684 | -0.0628 | no |
| `handcrafted` | 0.2956 | 0.2000 to 0.4475 | 0.2675 | 0.3684 | -0.0728 | no |
| `aa_composition` | 0.2781 | 0.1889 to 0.4123 | 0.3261 | 0.3684 | -0.0903 | no |
| `length` | 0.2599 | 0.1763 to 0.3923 | 0.2474 | 0.3684 | -0.1085 | no |

## CLS results table, classification head

`signal margin` is the score minus the larger of its two nulls, so a
non-positive margin means the representation has not been shown to carry
anything.

| representation | CLS | 95 percent CI | noise control CLS | search null p95 | signal margin | clears both |
| --- | --- | --- | --- | --- | --- | --- |
| `physicochemical` | 0.3739 | 0.0000 to 0.5258 | 0.0000 | 0.4433 | -0.0694 | no |
| `handcrafted_plus_esm2_650M` | 0.3449 | 0.0000 to 0.5136 | 0.0000 | 0.4433 | -0.0984 | no |
| `kmer3` | 0.3249 | 0.0000 to 0.4864 | 0.0000 | 0.4433 | -0.1184 | no |
| `handcrafted` | 0.2805 | 0.0000 to 0.4643 | 0.0471 | 0.4433 | -0.1628 | no |
| `esm2_35M` | 0.2412 | 0.0000 to 0.4690 | 0.2460 | 0.4433 | -0.2020 | no |
| `esm2_150M` | 0.2187 | 0.0000 to 0.4871 | 0.2506 | 0.4433 | -0.2246 | no |
| `aa_composition` | 0.1142 | 0.0000 to 0.4177 | 0.0000 | 0.4433 | -0.3291 | no |
| `length` | 0.1100 | 0.0000 to 0.3758 | 0.0645 | 0.4433 | -0.3333 | no |
| `esm2_650M` | 0.1061 | 0.0000 to 0.4614 | 0.0357 | 0.4433 | -0.3372 | no |
| `dipeptide` | 0.0000 | 0.0000 to 0.3600 | 0.0241 | 0.4433 | -0.4433 | no |
| `esm2_8M` | 0.0000 | 0.0000 to 0.3965 | 0.0000 | 0.4433 | -0.4433 | no |
| `kmer4` | 0.0000 | 0.0000 to 0.5671 | 0.0000 | 0.4433 | -0.4433 | no |

## CLS results table, regression head

`signal margin` is the score minus the larger of its two nulls, so a
non-positive margin means the representation has not been shown to carry
anything.

| representation | CLS | 95 percent CI | noise control CLS | search null p95 | signal margin | clears both |
| --- | --- | --- | --- | --- | --- | --- |
| `length` | 0.3576 | 0.0000 to 0.4992 | 0.1192 | 0.4433 | -0.0857 | no |
| `esm2_8M` | 0.2840 | 0.0000 to 0.4625 | 0.0000 | 0.4433 | -0.1593 | no |
| `esm2_35M` | 0.2785 | 0.0000 to 0.5043 | 0.0000 | 0.4433 | -0.1648 | no |
| `handcrafted` | 0.2646 | 0.0000 to 0.4431 | 0.0000 | 0.4433 | -0.1786 | no |
| `physicochemical` | 0.0821 | 0.0000 to 0.4170 | 0.0000 | 0.4433 | -0.3612 | no |
| `aa_composition` | 0.0159 | 0.0000 to 0.3744 | 0.0000 | 0.4433 | -0.4274 | no |
| `dipeptide` | 0.0000 | 0.0000 to 0.3304 | 0.0000 | 0.4433 | -0.4433 | no |
| `esm2_150M` | 0.0000 | 0.0000 to 0.1888 | 0.2774 | 0.4433 | -0.4433 | no |
| `esm2_650M` | 0.0000 | 0.0000 to 0.3762 | 0.0000 | 0.4433 | -0.4433 | no |
| `handcrafted_plus_esm2_650M` | 0.0000 | 0.0000 to 0.3767 | 0.0000 | 0.4433 | -0.4433 | no |
| `kmer3` | 0.0000 | 0.0000 to 0.3767 | 0.0000 | 0.4433 | -0.4433 | no |
| `kmer4` | 0.0000 | 0.0000 to 0.1684 | 0.0000 | 0.4433 | -0.4433 | no |

## Label permutation

`active` and `pe_efficiency_pct` are permuted together inside the protocol, so
their pairing with each other survives and only their pairing with the
sequences is broken. 20 repeats. This catches leakage the noise control
misses: a leak through the protocol's structure survives random features but
not a permuted label.

Run on `length`, `handcrafted`, `physicochemical`, `kmer4`, `esm2_8M`, `esm2_650M`, which span the trained length baseline, the
best handcrafted block and the largest language model. All twelve
representations would be 480 protocol runs; the subset is stated rather than
silent.

| representation | head | metric | permuted mean | permuted p95 | permuted max | observed | above the permuted p95 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `esm2_650M` | classification | CLS | 0.1051 | 0.3700 | 0.3851 | 0.1061 | **no** |
| `esm2_650M` | classification | PR-AUC | 0.3969 | 0.5217 | 0.5275 | 0.4220 | **no** |
| `esm2_650M` | regression | CLS | 0.1047 | 0.3529 | 0.4012 | 0.0000 | **no** |
| `esm2_650M` | regression | PR-AUC | 0.4021 | 0.5042 | 0.5378 | 0.4067 | **no** |
| `handcrafted` | classification | CLS | 0.1548 | 0.3644 | 0.5400 | 0.2805 | **no** |
| `handcrafted` | classification | PR-AUC | 0.3769 | 0.4891 | 0.5025 | 0.2956 | **no** |
| `handcrafted` | regression | CLS | 0.1215 | 0.3072 | 0.4551 | 0.2646 | **no** |
| `handcrafted` | regression | PR-AUC | 0.3813 | 0.4830 | 0.4978 | 0.3050 | **no** |
| `kmer4` | classification | CLS | 0.1916 | 0.4371 | 0.4671 | 0.0000 | **no** |
| `kmer4` | classification | PR-AUC | 0.3839 | 0.5398 | 0.5504 | 0.6212 | yes |
| `kmer4` | regression | CLS | 0.0393 | 0.2622 | 0.3019 | 0.0000 | **no** |
| `kmer4` | regression | PR-AUC | 0.3571 | 0.4492 | 0.4603 | 0.2954 | **no** |
| `length` | classification | CLS | 0.1266 | 0.3418 | 0.4153 | 0.1100 | **no** |
| `length` | classification | PR-AUC | 0.3225 | 0.4111 | 0.4200 | 0.2599 | **no** |
| `length` | regression | CLS | 0.0264 | 0.1406 | 0.1426 | 0.3576 | yes |
| `length` | regression | PR-AUC | 0.3662 | 0.4807 | 0.4827 | 0.3318 | **no** |
| `physicochemical` | classification | CLS | 0.1076 | 0.3786 | 0.3801 | 0.3739 | **no** |
| `physicochemical` | classification | PR-AUC | 0.3450 | 0.4254 | 0.5364 | 0.3623 | **no** |
| `physicochemical` | regression | CLS | 0.0598 | 0.3099 | 0.3589 | 0.0821 | **no** |
| `physicochemical` | regression | PR-AUC | 0.3878 | 0.5344 | 0.5433 | 0.3698 | **no** |
| `esm2_8M` | classification | CLS | 0.1410 | 0.3537 | 0.4019 | 0.0000 | **no** |
| `esm2_8M` | classification | PR-AUC | 0.3976 | 0.5676 | 0.5688 | 0.3706 | **no** |
| `esm2_8M` | regression | CLS | 0.0736 | 0.2530 | 0.4578 | 0.2840 | yes |
| `esm2_8M` | regression | PR-AUC | 0.4189 | 0.5650 | 0.5753 | 0.3269 | **no** |

## Minimum resolvable difference

Estimated from the paired bootstrap rather than assumed from a formula. For
each comparison the paired bootstrap gives the standard deviation of the CLS
difference under resampling of the enzymes; a two-sided test at alpha 0.05
with 80 percent power needs a true difference of about 2.8016 of those
standard deviations.

| quantity | CLS |
| --- | --- |
| median minimum resolvable difference across all pairs | 0.4816 |
| smallest, for the most similar pair | 0.1499 |
| largest, for the least similar pair | 0.9056 |

**A median MRD of 0.4816 CLS on a panel of 57 enzymes with 21 positives and a**
**CLS-weighted effective sample size of 11.338 is the central limitation of this**
**benchmark.** Most of the gaps between representations are smaller than this,
and every such gap is reported below as not resolvable rather than as a win.

## Pairwise comparisons

Every pair, by paired bootstrap on the same resamples, reporting the
probability that A scores above B rather than a bare point difference. A gap
smaller than that pair's own MRD is marked not resolvable.

| head | A | B | CLS A minus B | 95 percent CI of the difference | P(A beats B) | pair MRD | resolvable |
| --- | --- | --- | --- | --- | --- | --- | --- |
| regression | `kmer4` | `length` | -0.3076 | -0.4864 to +0.0000 | 0.000 | 0.3474 | **not resolvable** |
| regression | `esm2_150M` | `length` | -0.3054 | -0.4931 to +0.0000 | 0.009 | 0.3697 | **not resolvable** |
| regression | `dipeptide` | `length` | -0.2648 | -0.4746 to +0.0000 | 0.022 | 0.3958 | **not resolvable** |
| classification | `dipeptide` | `physicochemical` | -0.2617 | -0.5132 to +0.1573 | 0.069 | 0.5030 | **not resolvable** |
| classification | `dipeptide` | `handcrafted_plus_esm2_650M` | -0.2573 | -0.5123 to +0.1907 | 0.098 | 0.5191 | **not resolvable** |
| classification | `esm2_8M` | `physicochemical` | -0.2543 | -0.5244 to +0.3035 | 0.135 | 0.6203 | **not resolvable** |
| regression | `esm2_650M` | `length` | -0.2537 | -0.4980 to +0.2496 | 0.117 | 0.5541 | **not resolvable** |
| classification | `esm2_8M` | `handcrafted_plus_esm2_650M` | -0.2499 | -0.4550 to +0.0000 | 0.010 | 0.3590 | **not resolvable** |
| regression | `kmer3` | `length` | -0.2338 | -0.4476 to +0.0000 | 0.014 | 0.3673 | **not resolvable** |
| regression | `handcrafted_plus_esm2_650M` | `length` | -0.2336 | -0.4810 to +0.1765 | 0.099 | 0.4954 | **not resolvable** |
| regression | `esm2_8M` | `kmer4` | +0.2282 | +0.0000 to +0.4503 | 0.836 | 0.4019 | **not resolvable** |
| regression | `esm2_150M` | `esm2_8M` | -0.2261 | -0.4558 to +0.0000 | 0.021 | 0.4268 | **not resolvable** |
| regression | `esm2_35M` | `kmer4` | +0.2243 | +0.0000 to +0.4804 | 0.790 | 0.4422 | **not resolvable** |
| regression | `esm2_150M` | `esm2_35M` | -0.2221 | -0.4967 to +0.0000 | 0.022 | 0.4742 | **not resolvable** |
| regression | `aa_composition` | `length` | -0.2180 | -0.4901 to +0.2204 | 0.125 | 0.5277 | **not resolvable** |
| classification | `dipeptide` | `kmer3` | -0.2154 | -0.4835 to +0.3134 | 0.144 | 0.6029 | **not resolvable** |
| classification | `esm2_8M` | `kmer3` | -0.2080 | -0.4745 to +0.1606 | 0.106 | 0.5106 | **not resolvable** |
| classification | `length` | `physicochemical` | -0.2069 | -0.5194 to +0.3085 | 0.179 | 0.6317 | **not resolvable** |
| classification | `handcrafted_plus_esm2_650M` | `length` | +0.2025 | +0.0000 to +0.4181 | 0.945 | 0.3187 | **not resolvable** |
| regression | `handcrafted` | `kmer4` | +0.2022 | +0.0000 to +0.4282 | 0.786 | 0.3969 | **not resolvable** |
| regression | `esm2_150M` | `handcrafted` | -0.2000 | -0.4345 to +0.0000 | 0.011 | 0.4096 | **not resolvable** |
| regression | `length` | `physicochemical` | +0.1878 | -0.2954 to +0.4923 | 0.785 | 0.6016 | **not resolvable** |
| classification | `aa_composition` | `physicochemical` | -0.1860 | -0.5153 to +0.3168 | 0.217 | 0.6504 | **not resolvable** |
| regression | `dipeptide` | `esm2_8M` | -0.1854 | -0.4287 to +0.0177 | 0.032 | 0.3984 | **not resolvable** |
| classification | `dipeptide` | `handcrafted` | -0.1827 | -0.4600 to +0.2165 | 0.137 | 0.5162 | **not resolvable** |
| classification | `aa_composition` | `handcrafted_plus_esm2_650M` | -0.1816 | -0.4053 to +0.0000 | 0.024 | 0.3412 | **not resolvable** |
| regression | `dipeptide` | `esm2_35M` | -0.1814 | -0.4681 to +0.1662 | 0.076 | 0.4829 | **not resolvable** |
| classification | `kmer4` | `physicochemical` | -0.1792 | -0.4993 to +0.3984 | 0.221 | 0.6842 | **not resolvable** |
| classification | `esm2_8M` | `handcrafted` | -0.1753 | -0.4144 to +0.0397 | 0.050 | 0.3871 | **not resolvable** |
| classification | `handcrafted_plus_esm2_650M` | `kmer4` | +0.1748 | -0.4496 to +0.5125 | 0.706 | 0.7914 | **not resolvable** |
| regression | `esm2_650M` | `esm2_8M` | -0.1743 | -0.4620 to +0.3213 | 0.181 | 0.6021 | **not resolvable** |
| classification | `esm2_650M` | `physicochemical` | -0.1728 | -0.4860 to +0.2642 | 0.172 | 0.5564 | **not resolvable** |
| regression | `esm2_35M` | `esm2_650M` | +0.1703 | -0.3655 to +0.5043 | 0.718 | 0.6885 | **not resolvable** |
| classification | `esm2_650M` | `handcrafted_plus_esm2_650M` | -0.1684 | -0.4800 to +0.3147 | 0.214 | 0.6015 | **not resolvable** |
| classification | `kmer3` | `length` | +0.1606 | -0.1862 to +0.4534 | 0.758 | 0.4804 | **not resolvable** |
| regression | `dipeptide` | `handcrafted` | -0.1594 | -0.3843 to +0.0000 | 0.016 | 0.3572 | **not resolvable** |
| regression | `esm2_8M` | `kmer3` | +0.1544 | -0.1080 to +0.4107 | 0.778 | 0.4060 | **not resolvable** |
| regression | `esm2_8M` | `handcrafted_plus_esm2_650M` | +0.1543 | -0.3001 to +0.4453 | 0.738 | 0.5472 | **not resolvable** |
| regression | `esm2_35M` | `kmer3` | +0.1505 | -0.0201 to +0.4107 | 0.763 | 0.3703 | **not resolvable** |
| regression | `esm2_35M` | `handcrafted_plus_esm2_650M` | +0.1503 | -0.3451 to +0.4933 | 0.692 | 0.6581 | **not resolvable** |
| regression | `esm2_650M` | `handcrafted` | -0.1483 | -0.4427 to +0.3491 | 0.205 | 0.6112 | **not resolvable** |
| classification | `aa_composition` | `kmer3` | -0.1397 | -0.4693 to +0.3344 | 0.263 | 0.6328 | **not resolvable** |
| regression | `aa_composition` | `esm2_8M` | -0.1386 | -0.4470 to +0.2767 | 0.202 | 0.5427 | **not resolvable** |
| regression | `aa_composition` | `esm2_35M` | -0.1347 | -0.4958 to +0.3247 | 0.249 | 0.6376 | **not resolvable** |
| classification | `dipeptide` | `esm2_35M` | -0.1340 | -0.4690 to +0.3322 | 0.239 | 0.6353 | **not resolvable** |
| classification | `esm2_150M` | `physicochemical` | -0.1334 | -0.5161 to +0.4023 | 0.308 | 0.7285 | **not resolvable** |
| classification | `kmer3` | `kmer4` | +0.1329 | -0.5090 to +0.4769 | 0.663 | 0.8093 | **not resolvable** |
| classification | `esm2_150M` | `handcrafted_plus_esm2_650M` | -0.1290 | -0.3617 to +0.0173 | 0.056 | 0.3068 | **not resolvable** |
| regression | `handcrafted` | `kmer3` | +0.1284 | -0.0499 to +0.3752 | 0.740 | 0.3528 | **not resolvable** |
| regression | `handcrafted` | `handcrafted_plus_esm2_650M` | +0.1283 | -0.2769 to +0.4187 | 0.677 | 0.5176 | **not resolvable** |
| classification | `dipeptide` | `esm2_150M` | -0.1283 | -0.4871 to +0.3107 | 0.235 | 0.6300 | **not resolvable** |
| classification | `handcrafted` | `length` | +0.1279 | -0.0839 to +0.3842 | 0.789 | 0.3577 | **not resolvable** |
| classification | `esm2_35M` | `physicochemical` | -0.1276 | -0.5049 to +0.3892 | 0.292 | 0.6831 | **not resolvable** |
| classification | `esm2_35M` | `esm2_8M` | +0.1266 | +0.0000 to +0.3697 | 0.712 | 0.3335 | **not resolvable** |
| classification | `esm2_650M` | `kmer3` | -0.1265 | -0.3762 to +0.0534 | 0.097 | 0.3525 | **not resolvable** |
| classification | `esm2_35M` | `handcrafted_plus_esm2_650M` | -0.1232 | -0.3607 to +0.0180 | 0.053 | 0.2988 | **not resolvable** |
| classification | `esm2_150M` | `esm2_8M` | +0.1208 | +0.0000 to +0.3821 | 0.666 | 0.3430 | **not resolvable** |
| regression | `kmer4` | `physicochemical` | -0.1198 | -0.4170 to +0.1636 | 0.058 | 0.4391 | **not resolvable** |
| regression | `esm2_150M` | `physicochemical` | -0.1177 | -0.4149 to +0.1287 | 0.051 | 0.4282 | **not resolvable** |
| regression | `aa_composition` | `handcrafted` | -0.1126 | -0.4283 to +0.2904 | 0.235 | 0.5430 | **not resolvable** |
| regression | `esm2_8M` | `physicochemical` | +0.1084 | -0.2908 to +0.4450 | 0.643 | 0.5557 | **not resolvable** |
| classification | `aa_composition` | `handcrafted` | -0.1070 | -0.3229 to +0.0110 | 0.038 | 0.2778 | **not resolvable** |
| regression | `handcrafted` | `length` | -0.1054 | -0.3895 to +0.2296 | 0.189 | 0.4207 | **not resolvable** |
| regression | `esm2_35M` | `physicochemical` | +0.1044 | -0.3838 to +0.4996 | 0.622 | 0.7279 | **not resolvable** |
| classification | `handcrafted` | `kmer4` | +0.1002 | -0.4280 to +0.4615 | 0.608 | 0.7549 | **not resolvable** |
| classification | `esm2_650M` | `handcrafted` | -0.0938 | -0.4431 to +0.3977 | 0.315 | 0.6479 | **not resolvable** |
| regression | `aa_composition` | `kmer4` | +0.0896 | -0.1619 to +0.3744 | 0.493 | 0.3863 | **not resolvable** |
| classification | `dipeptide` | `esm2_650M` | -0.0889 | -0.4580 to +0.3534 | 0.233 | 0.6268 | **not resolvable** |
| regression | `aa_composition` | `esm2_150M` | +0.0874 | -0.1664 to +0.3744 | 0.486 | 0.3865 | **not resolvable** |
| classification | `esm2_150M` | `kmer3` | -0.0871 | -0.4534 to +0.3578 | 0.345 | 0.6249 | **not resolvable** |
| regression | `esm2_35M` | `length` | -0.0833 | -0.3859 to +0.2450 | 0.295 | 0.4466 | **not resolvable** |
| classification | `dipeptide` | `kmer4` | -0.0825 | -0.4492 to +0.0567 | 0.045 | 0.3939 | **not resolvable** |
| regression | `handcrafted` | `physicochemical` | +0.0824 | -0.3764 to +0.4369 | 0.598 | 0.6513 | **not resolvable** |
| classification | `esm2_650M` | `esm2_8M` | +0.0815 | -0.2926 to +0.4478 | 0.472 | 0.5411 | **not resolvable** |
| classification | `esm2_35M` | `kmer3` | -0.0813 | -0.4350 to +0.3084 | 0.328 | 0.5478 | **not resolvable** |
| regression | `esm2_8M` | `length` | -0.0794 | -0.3905 to +0.2734 | 0.265 | 0.4396 | **not resolvable** |
| classification | `esm2_35M` | `length` | +0.0793 | -0.0496 to +0.2829 | 0.685 | 0.2501 | **not resolvable** |
| classification | `handcrafted` | `physicochemical` | -0.0790 | -0.4913 to +0.3821 | 0.361 | 0.6512 | **not resolvable** |
| regression | `dipeptide` | `physicochemical` | -0.0770 | -0.4072 to +0.3126 | 0.199 | 0.5194 | **not resolvable** |
| classification | `aa_composition` | `dipeptide` | +0.0757 | -0.3272 to +0.4158 | 0.502 | 0.5676 | **not resolvable** |
| classification | `esm2_8M` | `kmer4` | -0.0751 | -0.5671 to +0.3965 | 0.321 | 0.7764 | **not resolvable** |
| classification | `handcrafted` | `handcrafted_plus_esm2_650M` | -0.0746 | -0.3271 to +0.1475 | 0.175 | 0.3109 | **not resolvable** |
| regression | `handcrafted_plus_esm2_650M` | `kmer4` | +0.0740 | -0.1284 to +0.3742 | 0.407 | 0.3640 | **not resolvable** |
| regression | `kmer3` | `kmer4` | +0.0738 | +0.0000 to +0.3289 | 0.404 | 0.3034 | **not resolvable** |
| classification | `esm2_150M` | `length` | +0.0735 | -0.0655 to +0.3007 | 0.630 | 0.2605 | **not resolvable** |
| regression | `esm2_150M` | `handcrafted_plus_esm2_650M` | -0.0718 | -0.3511 to +0.0000 | 0.017 | 0.3166 | **not resolvable** |
| regression | `esm2_150M` | `kmer3` | -0.0716 | -0.3598 to +0.0606 | 0.036 | 0.3427 | **not resolvable** |
| classification | `aa_composition` | `esm2_8M` | +0.0682 | -0.1075 to +0.3480 | 0.473 | 0.3315 | **not resolvable** |
| regression | `esm2_650M` | `physicochemical` | -0.0659 | -0.3453 to +0.1697 | 0.123 | 0.3555 | **not resolvable** |
| classification | `aa_composition` | `esm2_35M` | -0.0584 | -0.2899 to +0.2097 | 0.174 | 0.3254 | **not resolvable** |
| classification | `dipeptide` | `length` | -0.0548 | -0.3758 to +0.3560 | 0.272 | 0.5782 | **not resolvable** |
| classification | `esm2_150M` | `handcrafted` | -0.0544 | -0.3112 to +0.1221 | 0.291 | 0.3115 | **not resolvable** |
| regression | `esm2_650M` | `kmer4` | +0.0539 | -0.1679 to +0.3762 | 0.305 | 0.3590 | **not resolvable** |
| classification | `aa_composition` | `esm2_150M` | -0.0526 | -0.2607 to +0.1562 | 0.133 | 0.2686 | **not resolvable** |
| regression | `esm2_150M` | `esm2_650M` | -0.0517 | -0.3688 to +0.1335 | 0.054 | 0.3402 | **not resolvable** |
| classification | `esm2_35M` | `kmer4` | +0.0515 | -0.5408 to +0.4690 | 0.594 | 0.9056 | **not resolvable** |
| classification | `esm2_35M` | `handcrafted` | -0.0487 | -0.3354 to +0.2002 | 0.329 | 0.3675 | **not resolvable** |
| classification | `esm2_8M` | `length` | -0.0473 | -0.2686 to +0.0811 | 0.119 | 0.2523 | **not resolvable** |
| regression | `aa_composition` | `dipeptide` | +0.0467 | -0.2939 to +0.3600 | 0.428 | 0.4394 | **not resolvable** |
| classification | `kmer3` | `physicochemical` | -0.0463 | -0.4277 to +0.3647 | 0.375 | 0.5350 | **not resolvable** |
| regression | `kmer3` | `physicochemical` | -0.0460 | -0.4145 to +0.3727 | 0.323 | 0.6194 | **not resolvable** |
| regression | `handcrafted_plus_esm2_650M` | `physicochemical` | -0.0459 | -0.3755 to +0.3032 | 0.245 | 0.4621 | **not resolvable** |
| classification | `esm2_150M` | `kmer4` | +0.0457 | -0.5347 to +0.4871 | 0.560 | 0.9006 | **not resolvable** |
| classification | `esm2_35M` | `esm2_650M` | +0.0452 | -0.3900 to +0.4047 | 0.512 | 0.5886 | **not resolvable** |
| regression | `dipeptide` | `kmer4` | +0.0428 | -0.0596 to +0.3175 | 0.266 | 0.2808 | **not resolvable** |
| classification | `handcrafted_plus_esm2_650M` | `kmer3` | +0.0419 | -0.3671 to +0.4266 | 0.575 | 0.5507 | **not resolvable** |
| regression | `dipeptide` | `esm2_150M` | +0.0407 | -0.1146 to +0.3185 | 0.264 | 0.2890 | **not resolvable** |
| classification | `esm2_150M` | `esm2_650M` | +0.0394 | -0.4220 to +0.4341 | 0.497 | 0.6614 | **not resolvable** |
| regression | `aa_composition` | `esm2_650M` | +0.0357 | -0.3250 to +0.3609 | 0.405 | 0.4572 | **not resolvable** |
| classification | `esm2_650M` | `length` | +0.0341 | -0.3053 to +0.4093 | 0.431 | 0.5113 | **not resolvable** |
| classification | `handcrafted` | `kmer3` | -0.0327 | -0.4263 to +0.3909 | 0.407 | 0.5952 | **not resolvable** |
| regression | `dipeptide` | `handcrafted_plus_esm2_650M` | -0.0311 | -0.3513 to +0.2784 | 0.190 | 0.3981 | **not resolvable** |
| regression | `dipeptide` | `kmer3` | -0.0310 | -0.3093 to +0.2369 | 0.158 | 0.3343 | **not resolvable** |
| regression | `aa_composition` | `physicochemical` | -0.0303 | -0.3641 to +0.3152 | 0.296 | 0.4698 | **not resolvable** |
| classification | `kmer4` | `length` | +0.0278 | -0.3758 to +0.5645 | 0.388 | 0.8454 | **not resolvable** |
| regression | `esm2_8M` | `handcrafted` | +0.0260 | -0.2968 to +0.3312 | 0.552 | 0.4184 | **not resolvable** |
| regression | `esm2_35M` | `handcrafted` | +0.0220 | -0.2982 to +0.3338 | 0.551 | 0.4254 | **not resolvable** |
| classification | `aa_composition` | `length` | +0.0209 | -0.2116 to +0.3020 | 0.399 | 0.3267 | **not resolvable** |
| regression | `esm2_650M` | `handcrafted_plus_esm2_650M` | -0.0200 | -0.3049 to +0.2403 | 0.199 | 0.3365 | **not resolvable** |
| regression | `esm2_650M` | `kmer3` | -0.0199 | -0.3767 to +0.3754 | 0.290 | 0.5461 | **not resolvable** |
| regression | `aa_composition` | `kmer3` | +0.0158 | -0.3704 to +0.3723 | 0.425 | 0.5558 | **not resolvable** |
| regression | `aa_composition` | `handcrafted_plus_esm2_650M` | +0.0156 | -0.3453 to +0.3598 | 0.392 | 0.4999 | **not resolvable** |
| classification | `aa_composition` | `esm2_650M` | -0.0132 | -0.4457 to +0.3896 | 0.407 | 0.6628 | **not resolvable** |
| regression | `dipeptide` | `esm2_650M` | -0.0111 | -0.3717 to +0.3279 | 0.248 | 0.4615 | **not resolvable** |
| classification | `dipeptide` | `esm2_8M` | -0.0074 | -0.3965 to +0.3597 | 0.293 | 0.5332 | **not resolvable** |
| classification | `aa_composition` | `kmer4` | -0.0069 | -0.5344 to +0.4161 | 0.461 | 0.8116 | **not resolvable** |
| classification | `esm2_650M` | `kmer4` | +0.0064 | -0.5584 to +0.4555 | 0.477 | 0.8484 | **not resolvable** |
| classification | `esm2_150M` | `esm2_35M` | -0.0058 | -0.2057 to +0.1770 | 0.376 | 0.2336 | **not resolvable** |
| classification | `handcrafted_plus_esm2_650M` | `physicochemical` | -0.0044 | -0.4377 to +0.4264 | 0.468 | 0.5907 | **not resolvable** |
| regression | `esm2_35M` | `esm2_8M` | -0.0040 | -0.3676 to +0.3732 | 0.487 | 0.5266 | **not resolvable** |
| regression | `esm2_150M` | `kmer4` | +0.0022 | -0.1228 to +0.1595 | 0.065 | 0.1499 | **not resolvable** |
| regression | `handcrafted_plus_esm2_650M` | `kmer3` | +0.0002 | -0.3476 to +0.3609 | 0.330 | 0.4918 | **not resolvable** |

## How to read all of this

A representation has been shown to carry activity signal only if it clears, at
once: its own dimensionality-matched noise control, the search-capacity null at
its own free-parameter count, and the permuted-label distribution. Clearing a
majority baseline is not evidence of anything, and neither is beating another
representation by less than the minimum resolvable difference.

Per the Gate G2 ruling, the classification head carries the headline claim
because its label is reproducible from Table S1, while every regression and
weighted-Spearman number inherits the Figure S1A digitization described in
`reports/reconciliation.md` section 4.
