# Task A representation benchmark

Written by `bench/representations_taskA.py`. Nested leave-one-family-out through
`bench/protocol.py`, whose inner loop receives training families only and whose
deliberate-peeking positive control passes.

Two heads and nothing else: regularized logistic regression for `active`, ridge
regression for `pe_efficiency_pct`. The only selected quantity is the
regularization strength, from a grid of 6 values fixed a priori, chosen in the
inner loop. No other model family appears anywhere.

Per the Gate G2 ruling, **classification is the primary result**: the binary label
is read from Table S1's fill and is reproducible from the file, while
`pe_efficiency_pct` is a digitization of Figure S1A at roughly half a percentage
point of resolution. Every regression and weighted-Spearman number below inherits
that limitation.

## Classification of `active`, the primary result

| representation | features | CLS | PR-AUC | wSpearman | 95 percent CI | search capacity |
| --- | --- | --- | --- | --- | --- | --- |
| `kmer4` | 20115 | 0.0000 | 0.6212 | 0.0000 | 0.0000 to 0.5671 | 6 |
| `esm2_650M` | 1280 | 0.1061 | 0.4220 | 0.0607 | 0.0000 to 0.4614 | 6 |
| `esm2_8M` | 320 | 0.0000 | 0.3706 | 0.0000 | 0.0000 to 0.3965 | 6 |
| `physicochemical` | 13 | 0.3739 | 0.3623 | 0.3862 | 0.0000 to 0.5258 | 6 |
| `esm2_35M` | 480 | 0.2412 | 0.3162 | 0.1950 | 0.0000 to 0.4690 | 6 |
| `kmer3` | 6256 | 0.3249 | 0.3137 | 0.3369 | 0.0000 to 0.4864 | 6 |
| `handcrafted_plus_esm2_650M` | 2069 | 0.3449 | 0.3082 | 0.3914 | 0.0000 to 0.5136 | 6 |
| `dipeptide` | 400 | 0.0000 | 0.3081 | 0.0000 | 0.0000 to 0.3600 | 6 |
| `esm2_150M` | 640 | 0.2187 | 0.3056 | 0.1702 | 0.0000 to 0.4871 | 6 |
| `handcrafted` | 789 | 0.2805 | 0.2956 | 0.2668 | 0.0000 to 0.4643 | 6 |
| `aa_composition` | 20 | 0.1142 | 0.2781 | 0.0718 | 0.0000 to 0.4177 | 6 |
| `length` | 1 | 0.1100 | 0.2599 | 0.0697 | 0.0000 to 0.3758 | 6 |

## Regression of `pe_efficiency_pct`

Ordered by weighted Spearman, the component this head contributes.

| representation | features | CLS | PR-AUC | wSpearman | 95 percent CI | search capacity |
| --- | --- | --- | --- | --- | --- | --- |
| `length` | 1 | 0.3576 | 0.3318 | 0.3878 | 0.0000 to 0.4992 | 6 |
| `esm2_8M` | 320 | 0.2840 | 0.3269 | 0.2510 | 0.0000 to 0.4625 | 6 |
| `handcrafted` | 789 | 0.2646 | 0.3050 | 0.2337 | 0.0000 to 0.4431 | 6 |
| `esm2_35M` | 480 | 0.2785 | 0.3923 | 0.2158 | 0.0000 to 0.5043 | 6 |
| `physicochemical` | 13 | 0.0821 | 0.3698 | 0.0462 | 0.0000 to 0.4170 | 6 |
| `aa_composition` | 20 | 0.0159 | 0.3311 | 0.0081 | 0.0000 to 0.3744 | 6 |
| `dipeptide` | 400 | 0.0000 | 0.3205 | 0.0000 | 0.0000 to 0.3304 | 6 |
| `kmer3` | 6256 | 0.0000 | 0.2937 | 0.0000 | 0.0000 to 0.3767 | 6 |
| `kmer4` | 20115 | 0.0000 | 0.2954 | 0.0000 | 0.0000 to 0.1684 | 6 |
| `esm2_150M` | 640 | 0.0000 | 0.3391 | 0.0000 | 0.0000 to 0.1888 | 6 |
| `esm2_650M` | 1280 | 0.0000 | 0.4067 | 0.0000 | 0.0000 to 0.3762 | 6 |
| `handcrafted_plus_esm2_650M` | 2069 | 0.0000 | 0.3516 | 0.0000 | 0.0000 to 0.3767 | 6 |

## Two-head CLS

CLS is the harmonic mean of a separation term and a ranking term. With two
heads the natural construction takes PR-AUC from the classifier and weighted
Spearman from the regressor, which is what this column is. Each head's own
single-vector CLS is in the tables above, for comparability with the earlier
audit, which scored one vector on both components.

| representation | classifier PR-AUC | regressor wSpearman | two-head CLS |
| --- | --- | --- | --- |
| `length` | 0.2599 | 0.3878 | 0.3112 |
| `esm2_8M` | 0.3706 | 0.2510 | 0.2993 |
| `handcrafted` | 0.2956 | 0.2337 | 0.2611 |
| `esm2_35M` | 0.3162 | 0.2158 | 0.2566 |
| `physicochemical` | 0.3623 | 0.0462 | 0.0819 |
| `aa_composition` | 0.2781 | 0.0081 | 0.0158 |
| `dipeptide` | 0.3081 | 0.0000 | 0.0000 |
| `kmer3` | 0.3137 | 0.0000 | 0.0000 |
| `kmer4` | 0.6212 | 0.0000 | 0.0000 |
| `esm2_150M` | 0.3056 | 0.0000 | 0.0000 |
| `esm2_650M` | 0.4220 | 0.0000 | 0.0000 |
| `handcrafted_plus_esm2_650M` | 0.3082 | 0.0000 | 0.0000 |

## Per-family breakdown

Three families hold no active enzyme, so PR-AUC is undefined within them and a
ranking correlation is undefined against an all-zero target. Those folds are
marked `undefined` rather than scored as zero, per the handling rule in
`reports/split_verification.md`. Their predictions still enter the pooled vector,
because the pooled metric is computed once over all 57 rows and those rows are
genuine negatives a model must not rank highly.

| representation | head | family | n | actives | mean predicted score | per-family metric |
| --- | --- | --- | --- | --- | --- | --- |
| `aa_composition` | classification | CRISPR-associated | 5 | 0 | 0.6803 | undefined, no active |
| `aa_composition` | classification | Group_II_Intron | 5 | 2 | 0.0540 | defined |
| `aa_composition` | classification | LTR_Retrotransposon | 11 | 2 | 0.4108 | defined |
| `aa_composition` | classification | Other | 5 | 0 | 0.2479 | undefined, no active |
| `aa_composition` | classification | Retron | 12 | 5 | 0.2261 | defined |
| `aa_composition` | classification | Retroviral | 18 | 12 | 0.1647 | defined |
| `aa_composition` | classification | Unclassified | 1 | 0 | 0.1761 | undefined, no active |
| `aa_composition` | regression | CRISPR-associated | 5 | 0 | 7.7953 | undefined, no active |
| `aa_composition` | regression | Group_II_Intron | 5 | 2 | -1.3649 | defined |
| `aa_composition` | regression | LTR_Retrotransposon | 11 | 2 | 0.4161 | defined |
| `aa_composition` | regression | Other | 5 | 0 | 4.8014 | undefined, no active |
| `aa_composition` | regression | Retron | 12 | 5 | 4.9829 | defined |
| `aa_composition` | regression | Retroviral | 18 | 12 | 4.4901 | defined |
| `aa_composition` | regression | Unclassified | 1 | 0 | -1.5725 | undefined, no active |
| `dipeptide` | classification | CRISPR-associated | 5 | 0 | 0.3998 | undefined, no active |
| `dipeptide` | classification | Group_II_Intron | 5 | 2 | 0.3261 | defined |
| `dipeptide` | classification | LTR_Retrotransposon | 11 | 2 | 0.0328 | defined |
| `dipeptide` | classification | Other | 5 | 0 | 0.3865 | undefined, no active |
| `dipeptide` | classification | Retron | 12 | 5 | 0.0632 | defined |
| `dipeptide` | classification | Retroviral | 18 | 12 | 0.2216 | defined |
| `dipeptide` | classification | Unclassified | 1 | 0 | 0.3641 | undefined, no active |
| `dipeptide` | regression | CRISPR-associated | 5 | 0 | 6.2438 | undefined, no active |
| `dipeptide` | regression | Group_II_Intron | 5 | 2 | 4.7408 | defined |
| `dipeptide` | regression | LTR_Retrotransposon | 11 | 2 | -0.6474 | defined |
| `dipeptide` | regression | Other | 5 | 0 | 0.5522 | undefined, no active |
| `dipeptide` | regression | Retron | 12 | 5 | -0.2481 | defined |
| `dipeptide` | regression | Retroviral | 18 | 12 | 0.8780 | defined |
| `dipeptide` | regression | Unclassified | 1 | 0 | 11.7648 | undefined, no active |
| `esm2_150M` | classification | CRISPR-associated | 5 | 0 | 0.3374 | undefined, no active |
| `esm2_150M` | classification | Group_II_Intron | 5 | 2 | 0.2722 | defined |
| `esm2_150M` | classification | LTR_Retrotransposon | 11 | 2 | 0.3979 | defined |
| `esm2_150M` | classification | Other | 5 | 0 | 0.2840 | undefined, no active |
| `esm2_150M` | classification | Retron | 12 | 5 | 0.0793 | defined |
| `esm2_150M` | classification | Retroviral | 18 | 12 | 0.1732 | defined |
| `esm2_150M` | classification | Unclassified | 1 | 0 | 0.3011 | undefined, no active |
| `esm2_150M` | regression | CRISPR-associated | 5 | 0 | 0.7159 | undefined, no active |
| `esm2_150M` | regression | Group_II_Intron | 5 | 2 | 28.0750 | defined |
| `esm2_150M` | regression | LTR_Retrotransposon | 11 | 2 | -10.9409 | defined |
| `esm2_150M` | regression | Other | 5 | 0 | 2.8743 | undefined, no active |
| `esm2_150M` | regression | Retron | 12 | 5 | 0.3588 | defined |
| `esm2_150M` | regression | Retroviral | 18 | 12 | -4.4473 | defined |
| `esm2_150M` | regression | Unclassified | 1 | 0 | 0.6353 | undefined, no active |
| `esm2_35M` | classification | CRISPR-associated | 5 | 0 | 0.3717 | undefined, no active |
| `esm2_35M` | classification | Group_II_Intron | 5 | 2 | 0.1146 | defined |
| `esm2_35M` | classification | LTR_Retrotransposon | 11 | 2 | 0.4685 | defined |
| `esm2_35M` | classification | Other | 5 | 0 | 0.2859 | undefined, no active |
| `esm2_35M` | classification | Retron | 12 | 5 | 0.0047 | defined |
| `esm2_35M` | classification | Retroviral | 18 | 12 | 0.0091 | defined |
| `esm2_35M` | classification | Unclassified | 1 | 0 | 0.4570 | undefined, no active |
| `esm2_35M` | regression | CRISPR-associated | 5 | 0 | 8.0986 | undefined, no active |
| `esm2_35M` | regression | Group_II_Intron | 5 | 2 | -1.2873 | defined |
| `esm2_35M` | regression | LTR_Retrotransposon | 11 | 2 | 6.2395 | defined |
| `esm2_35M` | regression | Other | 5 | 0 | 1.7514 | undefined, no active |
| `esm2_35M` | regression | Retron | 12 | 5 | -3.1789 | defined |
| `esm2_35M` | regression | Retroviral | 18 | 12 | -0.0008 | defined |
| `esm2_35M` | regression | Unclassified | 1 | 0 | 1.5668 | undefined, no active |
| `esm2_650M` | classification | CRISPR-associated | 5 | 0 | 0.2786 | undefined, no active |
| `esm2_650M` | classification | Group_II_Intron | 5 | 2 | 0.2462 | defined |
| `esm2_650M` | classification | LTR_Retrotransposon | 11 | 2 | 0.3113 | defined |
| `esm2_650M` | classification | Other | 5 | 0 | 0.2779 | undefined, no active |
| `esm2_650M` | classification | Retron | 12 | 5 | 0.0361 | defined |
| `esm2_650M` | classification | Retroviral | 18 | 12 | 0.3397 | defined |
| `esm2_650M` | classification | Unclassified | 1 | 0 | 0.1701 | undefined, no active |
| `esm2_650M` | regression | CRISPR-associated | 5 | 0 | 0.7069 | undefined, no active |
| `esm2_650M` | regression | Group_II_Intron | 5 | 2 | 6.1524 | defined |
| `esm2_650M` | regression | LTR_Retrotransposon | 11 | 2 | -10.6562 | defined |
| `esm2_650M` | regression | Other | 5 | 0 | 2.3921 | undefined, no active |
| `esm2_650M` | regression | Retron | 12 | 5 | -0.3876 | defined |
| `esm2_650M` | regression | Retroviral | 18 | 12 | 0.7128 | defined |
| `esm2_650M` | regression | Unclassified | 1 | 0 | -2.6256 | undefined, no active |
| `esm2_8M` | classification | CRISPR-associated | 5 | 0 | 0.3827 | undefined, no active |
| `esm2_8M` | classification | Group_II_Intron | 5 | 2 | 0.2026 | defined |
| `esm2_8M` | classification | LTR_Retrotransposon | 11 | 2 | 0.4375 | defined |
| `esm2_8M` | classification | Other | 5 | 0 | 0.2554 | undefined, no active |
| `esm2_8M` | classification | Retron | 12 | 5 | 0.5604 | defined |
| `esm2_8M` | classification | Retroviral | 18 | 12 | 0.0001 | defined |
| `esm2_8M` | classification | Unclassified | 1 | 0 | 0.3851 | undefined, no active |
| `esm2_8M` | regression | CRISPR-associated | 5 | 0 | 15.8272 | undefined, no active |
| `esm2_8M` | regression | Group_II_Intron | 5 | 2 | -1.3381 | defined |
| `esm2_8M` | regression | LTR_Retrotransposon | 11 | 2 | 11.4500 | defined |
| `esm2_8M` | regression | Other | 5 | 0 | -4.8521 | undefined, no active |
| `esm2_8M` | regression | Retron | 12 | 5 | 3.0004 | defined |
| `esm2_8M` | regression | Retroviral | 18 | 12 | 1.3542 | defined |
| `esm2_8M` | regression | Unclassified | 1 | 0 | -8.6186 | undefined, no active |
| `handcrafted` | classification | CRISPR-associated | 5 | 0 | 0.3989 | undefined, no active |
| `handcrafted` | classification | Group_II_Intron | 5 | 2 | 0.0457 | defined |
| `handcrafted` | classification | LTR_Retrotransposon | 11 | 2 | 0.3817 | defined |
| `handcrafted` | classification | Other | 5 | 0 | 0.1827 | undefined, no active |
| `handcrafted` | classification | Retron | 12 | 5 | 0.0384 | defined |
| `handcrafted` | classification | Retroviral | 18 | 12 | 0.2125 | defined |
| `handcrafted` | classification | Unclassified | 1 | 0 | 0.3487 | undefined, no active |
| `handcrafted` | regression | CRISPR-associated | 5 | 0 | 4.9364 | undefined, no active |
| `handcrafted` | regression | Group_II_Intron | 5 | 2 | 3.3462 | defined |
| `handcrafted` | regression | LTR_Retrotransposon | 11 | 2 | 0.4278 | defined |
| `handcrafted` | regression | Other | 5 | 0 | 1.5750 | undefined, no active |
| `handcrafted` | regression | Retron | 12 | 5 | 1.4960 | defined |
| `handcrafted` | regression | Retroviral | 18 | 12 | 1.3413 | defined |
| `handcrafted` | regression | Unclassified | 1 | 0 | 11.5379 | undefined, no active |
| `handcrafted_plus_esm2_650M` | classification | CRISPR-associated | 5 | 0 | 0.2897 | undefined, no active |
| `handcrafted_plus_esm2_650M` | classification | Group_II_Intron | 5 | 2 | 0.2383 | defined |
| `handcrafted_plus_esm2_650M` | classification | LTR_Retrotransposon | 11 | 2 | 0.2994 | defined |
| `handcrafted_plus_esm2_650M` | classification | Other | 5 | 0 | 0.3299 | undefined, no active |
| `handcrafted_plus_esm2_650M` | classification | Retron | 12 | 5 | 0.0123 | defined |
| `handcrafted_plus_esm2_650M` | classification | Retroviral | 18 | 12 | 0.1721 | defined |
| `handcrafted_plus_esm2_650M` | classification | Unclassified | 1 | 0 | 0.2558 | undefined, no active |
| `handcrafted_plus_esm2_650M` | regression | CRISPR-associated | 5 | 0 | 1.1285 | undefined, no active |
| `handcrafted_plus_esm2_650M` | regression | Group_II_Intron | 5 | 2 | 5.7948 | defined |
| `handcrafted_plus_esm2_650M` | regression | LTR_Retrotransposon | 11 | 2 | -1.3808 | defined |
| `handcrafted_plus_esm2_650M` | regression | Other | 5 | 0 | 2.3735 | undefined, no active |
| `handcrafted_plus_esm2_650M` | regression | Retron | 12 | 5 | -0.5881 | defined |
| `handcrafted_plus_esm2_650M` | regression | Retroviral | 18 | 12 | 0.4344 | defined |
| `handcrafted_plus_esm2_650M` | regression | Unclassified | 1 | 0 | 0.7799 | undefined, no active |
| `kmer3` | classification | CRISPR-associated | 5 | 0 | 0.2170 | undefined, no active |
| `kmer3` | classification | Group_II_Intron | 5 | 2 | 0.0175 | defined |
| `kmer3` | classification | LTR_Retrotransposon | 11 | 2 | 0.1735 | defined |
| `kmer3` | classification | Other | 5 | 0 | 0.1475 | undefined, no active |
| `kmer3` | classification | Retron | 12 | 5 | 0.0230 | defined |
| `kmer3` | classification | Retroviral | 18 | 12 | 0.1869 | defined |
| `kmer3` | classification | Unclassified | 1 | 0 | 0.1267 | undefined, no active |
| `kmer3` | regression | CRISPR-associated | 5 | 0 | 4.2059 | undefined, no active |
| `kmer3` | regression | Group_II_Intron | 5 | 2 | 2.2944 | defined |
| `kmer3` | regression | LTR_Retrotransposon | 11 | 2 | 3.3908 | defined |
| `kmer3` | regression | Other | 5 | 0 | 4.1389 | undefined, no active |
| `kmer3` | regression | Retron | 12 | 5 | 3.3404 | defined |
| `kmer3` | regression | Retroviral | 18 | 12 | 1.3851 | defined |
| `kmer3` | regression | Unclassified | 1 | 0 | -0.6725 | undefined, no active |
| `kmer4` | classification | CRISPR-associated | 5 | 0 | 0.1113 | undefined, no active |
| `kmer4` | classification | Group_II_Intron | 5 | 2 | 0.2408 | defined |
| `kmer4` | classification | LTR_Retrotransposon | 11 | 2 | 0.0969 | defined |
| `kmer4` | classification | Other | 5 | 0 | 0.1501 | undefined, no active |
| `kmer4` | classification | Retron | 12 | 5 | 0.2196 | defined |
| `kmer4` | classification | Retroviral | 18 | 12 | 0.4538 | defined |
| `kmer4` | classification | Unclassified | 1 | 0 | 0.0611 | undefined, no active |
| `kmer4` | regression | CRISPR-associated | 5 | 0 | 3.8160 | undefined, no active |
| `kmer4` | regression | Group_II_Intron | 5 | 2 | 3.4045 | defined |
| `kmer4` | regression | LTR_Retrotransposon | 11 | 2 | 3.6614 | defined |
| `kmer4` | regression | Other | 5 | 0 | 4.2190 | undefined, no active |
| `kmer4` | regression | Retron | 12 | 5 | 4.2265 | defined |
| `kmer4` | regression | Retroviral | 18 | 12 | 1.6025 | defined |
| `kmer4` | regression | Unclassified | 1 | 0 | 3.3327 | undefined, no active |
| `length` | classification | CRISPR-associated | 5 | 0 | 0.4027 | undefined, no active |
| `length` | classification | Group_II_Intron | 5 | 2 | 0.3237 | defined |
| `length` | classification | LTR_Retrotransposon | 11 | 2 | 0.4134 | defined |
| `length` | classification | Other | 5 | 0 | 0.3671 | undefined, no active |
| `length` | classification | Retron | 12 | 5 | 0.2095 | defined |
| `length` | classification | Retroviral | 18 | 12 | 0.1516 | defined |
| `length` | classification | Unclassified | 1 | 0 | 0.2068 | undefined, no active |
| `length` | regression | CRISPR-associated | 5 | 0 | 0.6416 | undefined, no active |
| `length` | regression | Group_II_Intron | 5 | 2 | 3.7630 | defined |
| `length` | regression | LTR_Retrotransposon | 11 | 2 | 5.7894 | defined |
| `length` | regression | Other | 5 | 0 | 3.7719 | undefined, no active |
| `length` | regression | Retron | 12 | 5 | 2.6038 | defined |
| `length` | regression | Retroviral | 18 | 12 | 2.0133 | defined |
| `length` | regression | Unclassified | 1 | 0 | -1.5758 | undefined, no active |
| `physicochemical` | classification | CRISPR-associated | 5 | 0 | 0.4871 | undefined, no active |
| `physicochemical` | classification | Group_II_Intron | 5 | 2 | 0.1488 | defined |
| `physicochemical` | classification | LTR_Retrotransposon | 11 | 2 | 0.2485 | defined |
| `physicochemical` | classification | Other | 5 | 0 | 0.1023 | undefined, no active |
| `physicochemical` | classification | Retron | 12 | 5 | 0.3178 | defined |
| `physicochemical` | classification | Retroviral | 18 | 12 | 0.1828 | defined |
| `physicochemical` | classification | Unclassified | 1 | 0 | 0.4069 | undefined, no active |
| `physicochemical` | regression | CRISPR-associated | 5 | 0 | 4.9411 | undefined, no active |
| `physicochemical` | regression | Group_II_Intron | 5 | 2 | 1.4302 | defined |
| `physicochemical` | regression | LTR_Retrotransposon | 11 | 2 | 1.8659 | defined |
| `physicochemical` | regression | Other | 5 | 0 | 1.7463 | undefined, no active |
| `physicochemical` | regression | Retron | 12 | 5 | 4.6905 | defined |
| `physicochemical` | regression | Retroviral | 18 | 12 | 3.1506 | defined |
| `physicochemical` | regression | Unclassified | 1 | 0 | 4.9648 | undefined, no active |

## What this table is not

It is not yet a finding. No score here has been compared against a
dimensionality-matched noise control, a search-capacity null at matched free
parameter count, or a label permutation, and no pairwise difference has been
tested against the smallest difference this sample size can resolve. Those are
Phase 7, in `reports/statistical_validation.md`, and until they are run the only
honest reading of this table is as a set of raw numbers.
