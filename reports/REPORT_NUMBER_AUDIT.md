# Number audit for the technical report

Written by `reports/build_pdf.py`, which is the only place a number enters
`RT_PLM_Benchmark_Technical_Report.pdf`. Nothing numeric is typed into
`reports/report.typ`; every figure is either computed from a result file at build
time or verified to occur, as an exact string, in the repository document named as
its source. *A value whose string cannot be found in its stated source aborts the
build*, so the PDF cannot be produced with an unsourced number in it.

Three kinds of entry appear below.

1. **Scalars quoted in the prose** (section 1), each with the result-file key path
   it was computed from, or the document whose text was verified to contain it.
2. **Every cell of every generated table** (section 2), one row per printed cell,
   with the key path that produced it.
3. **Numbers deliberately not carried into the report** (section 3), with the
   reason each was excluded.

Not audited here, and why. Section, figure, table and page numbers are generated
by the typesetter. Counts inside prose sentences that restate a table (for example
"four trained rows") are read off the table in the same section. Deliberately
rounded restatements of an audited value (for example "from about 0.86 to about
0.58" for the noise-null means of 0.8624 and 0.5794 in Table 14) are marked as
approximate in the text. The DOIs in the reference list are citation identifiers,
verified against the sources recorded in `reports/refs.yml`.

## 1. Scalars quoted in the prose

Rows: 194.

| what the report states | value as printed | source file | locator |
| --- | --- | --- | --- |
| baseline ladder: 3-mer cosine to nearest training active, no training (CLS, wSpearman, null p95, margin) | `0.4576, 0.4021, 0.3961, +0.0615` | `bench/results/baseline_ladder.json` | `rows[method='4. 3-mer cosine to nearest training active, no training'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: protein_length_aa, no training (CLS, wSpearman, null p95, margin) | `0.4416, 0.3893, 0.3961, +0.0455` | `bench/results/baseline_ladder.json` | `rows[method='1. protein_length_aa, no training'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: handcrafted + RandomForest (CLS, wSpearman, null p95, margin) | `0.4284, 0.2888, 0.4754, -0.0470` | `bench/results/baseline_ladder.json` | `rows[method='8b. handcrafted + RandomForest'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: family prior by nearest training family, no training (CLS, wSpearman, null p95, margin) | `0.4160, 0.4025, 0.3961, +0.0199` | `bench/results/baseline_ladder.json` | `rows[method='5. family prior by nearest training family, no training'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: handcrafted + ExtraTrees (CLS, wSpearman, null p95, margin) | `0.1802, 0.1036, 0.4754, -0.2951` | `bench/results/baseline_ladder.json` | `rows[method='8a. handcrafted + ExtraTrees'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: negative protein_length_aa, no training (CLS, wSpearman, null p95, margin) | `0.0000, 0.0000, 0.3961, -0.3961` | `bench/results/baseline_ladder.json` | `rows[method='2. negative protein_length_aa, no training'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: amino acid composition PC1, no training (CLS, wSpearman, null p95, margin) | `0.0000, 0.0000, 0.3961, -0.3961` | `bench/results/baseline_ladder.json` | `rows[method='3. amino acid composition PC1, no training'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: handcrafted + logistic regression (CLS, wSpearman, null p95, margin) | `0.0000, 0.0000, 0.4570, -0.4570` | `bench/results/baseline_ladder.json` | `rows[method='9. handcrafted + logistic regression'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| baseline ladder: raw ESM-2 mean-pooled + logistic regression (CLS, wSpearman, null p95, margin) | `0.0000, 0.0000, 0.4570, -0.4570` | `bench/results/baseline_ladder.json` | `rows[method='10. raw ESM-2 mean-pooled + logistic regression'].{cls,w_spearman,null_cls_p95,signal_margin}` |
| representation (CLS protocol): ESM-2 150M mean-pooled (CLS, wSpearman, null p95, margin, family acc.) | `0.3052, 0.2614, 0.4914, -0.1861, 0.802` | `bench/results/representations.json` | `rows[method='ESM-2 150M mean-pooled'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): ESM-2 35M mean-pooled (CLS, wSpearman, null p95, margin, family acc.) | `0.1394, 0.0909, 0.4914, -0.3520, 0.782` | `bench/results/representations.json` | `rows[method='ESM-2 35M mean-pooled'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): ESM-2 8M mean-pooled (CLS, wSpearman, null p95, margin, family acc.) | `0.0074, 0.0037, 0.4914, -0.4840, 0.745` | `bench/results/representations.json` | `rows[method='ESM-2 8M mean-pooled'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): handcrafted: sequence and physicochemical (CLS, wSpearman, null p95, margin, family acc.) | `0.0000, 0.0000, 0.4914, -0.4914, 0.712` | `bench/results/representations.json` | `rows[method='handcrafted: sequence and physicochemical'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): structure: pLDDT, cleft and topology (CLS, wSpearman, null p95, margin, family acc.) | `0.0000, 0.0000, 0.4914, -0.4914, 0.659` | `bench/results/representations.json` | `rows[method='structure: pLDDT, cleft and topology'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): ESM-2 650M mean-pooled (CLS, wSpearman, null p95, margin, family acc.) | `0.0000, 0.0000, 0.4914, -0.4914, 0.800` | `bench/results/representations.json` | `rows[method='ESM-2 650M mean-pooled'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): ESM-2 650M, length-residualized (CLS, wSpearman, null p95, margin, family acc.) | `0.0000, 0.0000, 0.4914, -0.4914, 0.800` | `bench/results/representations.json` | `rows[method='ESM-2 650M, length-residualized'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): ESM-2 650M, family-residualized (CLS, wSpearman, null p95, margin, family acc.) | `0.0000, 0.0000, 0.4914, -0.4914, 0.800` | `bench/results/representations.json` | `rows[method='ESM-2 650M, family-residualized'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): ESM-2 650M, catalytic-core pooled (CLS, wSpearman, null p95, margin, family acc.) | `0.0000, 0.0000, 0.4914, -0.4914, 0.818` | `bench/results/representations.json` | `rows[method='ESM-2 650M, catalytic-core pooled'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| representation (CLS protocol): ESM-2, attention-weighted core pooling (CLS, wSpearman, null p95, margin, family acc.) | `0.0000, 0.0000, 0.4914, -0.4914, 0.818` | `bench/results/representations.json` | `rows[method='ESM-2, attention-weighted core pooling'].{cls,w_spearman,null_cls_p95,signal_margin,family_accuracy}` |
| Task A kmer4: PR-AUC, 95% CI, noise control, permuted p95 | `0.6212, 0.4285–0.8325, 0.4458, 0.5398` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.kmer4.classification.pr_auc; intervals.kmer4.classification.pr_auc; noise.kmer4.classification.pr_auc; permutation.kmer4.classification.pr_auc_p95` |
| Task A esm2_650M: PR-AUC, 95% CI, noise control, permuted p95 | `0.4220, 0.2665–0.6492, 0.2889, 0.5217` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.esm2_650M.classification.pr_auc; intervals.esm2_650M.classification.pr_auc; noise.esm2_650M.classification.pr_auc; permutation.esm2_650M.classification.pr_auc_p95` |
| Task A esm2_8M: PR-AUC, 95% CI, noise control, permuted p95 | `0.3706, 0.2242–0.5710, 0.2581, 0.5676` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.esm2_8M.classification.pr_auc; intervals.esm2_8M.classification.pr_auc; noise.esm2_8M.classification.pr_auc; permutation.esm2_8M.classification.pr_auc_p95` |
| Task A physicochemical: PR-AUC, 95% CI, noise control, permuted p95 | `0.3623, 0.2457–0.5448, 0.2643, 0.4254` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.physicochemical.classification.pr_auc; intervals.physicochemical.classification.pr_auc; noise.physicochemical.classification.pr_auc; permutation.physicochemical.classification.pr_auc_p95` |
| Task A esm2_35M: PR-AUC, 95% CI, noise control, permuted p95 | `0.3162, 0.2066–0.4977, 0.2899, not tested` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.esm2_35M.classification.pr_auc; intervals.esm2_35M.classification.pr_auc; noise.esm2_35M.classification.pr_auc; permutation.esm2_35M.classification.pr_auc_p95` |
| Task A kmer3: PR-AUC, 95% CI, noise control, permuted p95 | `0.3137, 0.2085–0.4955, 0.3029, not tested` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.kmer3.classification.pr_auc; intervals.kmer3.classification.pr_auc; noise.kmer3.classification.pr_auc; permutation.kmer3.classification.pr_auc_p95` |
| Task A handcrafted_plus_esm2_650M: PR-AUC, 95% CI, noise control, permuted p95 | `0.3082, 0.2093–0.4748, 0.2970, not tested` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.handcrafted_plus_esm2_650M.classification.pr_auc; intervals.handcrafted_plus_esm2_650M.classification.pr_auc; noise.handcrafted_plus_esm2_650M.classification.pr_auc; permutation.handcrafted_plus_esm2_650M.classification.pr_auc_p95` |
| Task A dipeptide: PR-AUC, 95% CI, noise control, permuted p95 | `0.3081, 0.2090–0.4618, 0.3118, not tested` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.dipeptide.classification.pr_auc; intervals.dipeptide.classification.pr_auc; noise.dipeptide.classification.pr_auc; permutation.dipeptide.classification.pr_auc_p95` |
| Task A esm2_150M: PR-AUC, 95% CI, noise control, permuted p95 | `0.3056, 0.2052–0.4817, 0.2856, not tested` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.esm2_150M.classification.pr_auc; intervals.esm2_150M.classification.pr_auc; noise.esm2_150M.classification.pr_auc; permutation.esm2_150M.classification.pr_auc_p95` |
| Task A handcrafted: PR-AUC, 95% CI, noise control, permuted p95 | `0.2956, 0.2000–0.4475, 0.2675, 0.4891` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.handcrafted.classification.pr_auc; intervals.handcrafted.classification.pr_auc; noise.handcrafted.classification.pr_auc; permutation.handcrafted.classification.pr_auc_p95` |
| Task A aa_composition: PR-AUC, 95% CI, noise control, permuted p95 | `0.2781, 0.1889–0.4123, 0.3261, not tested` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.aa_composition.classification.pr_auc; intervals.aa_composition.classification.pr_auc; noise.aa_composition.classification.pr_auc; permutation.aa_composition.classification.pr_auc_p95` |
| Task A length: PR-AUC, 95% CI, noise control, permuted p95 | `0.2599, 0.1763–0.3923, 0.2474, 0.4111` | `bench/results/taskA_representations.json, bench/results/taskA_validation.json` | `results.length.classification.pr_auc; intervals.length.classification.pr_auc; noise.length.classification.pr_auc; permutation.length.classification.pr_auc_p95` |
| search-capacity null K=1: mean, sd, p95 | `0.2751, 0.1213, 0.4433` | `bench/results/search_null.json` | `k_sweep[k=1].{mean,std,p95}` |
| search-capacity null K=2: mean, sd, p95 | `0.3945, 0.0681, 0.4944` | `bench/results/search_null.json` | `k_sweep[k=2].{mean,std,p95}` |
| search-capacity null K=5: mean, sd, p95 | `0.5006, 0.0494, 0.5606` | `bench/results/search_null.json` | `k_sweep[k=5].{mean,std,p95}` |
| search-capacity null K=10: mean, sd, p95 | `0.6170, 0.0327, 0.6536` | `bench/results/search_null.json` | `k_sweep[k=10].{mean,std,p95}` |
| search-capacity null K=20: mean, sd, p95 | `0.7909, 0.0504, 0.8637` | `bench/results/search_null.json` | `k_sweep[k=20].{mean,std,p95}` |
| search-capacity null K=29: mean, sd, p95 | `0.8629, 0.0489, 0.9340` | `bench/results/search_null.json` | `k_sweep[k=29].{mean,std,p95}` |
| search-capacity null K=50: mean, sd, p95 | `0.9210, 0.0321, 0.9727` | `bench/results/search_null.json` | `k_sweep[k=50].{mean,std,p95}` |
| search-null budget sweep at K=29, 10 iterations: mean, p95 | `0.6809, 0.7340` | `bench/results/search_null.json` | `budget_sweep[budget=10].{mean,p95}` |
| search-null budget sweep at K=29, 30 iterations: mean, p95 | `0.7396, 0.7831` | `bench/results/search_null.json` | `budget_sweep[budget=30].{mean,p95}` |
| search-null budget sweep at K=29, 60 iterations: mean, p95 | `0.7828, 0.8441` | `bench/results/search_null.json` | `budget_sweep[budget=60].{mean,p95}` |
| search-null budget sweep at K=29, 130 iterations: mean, p95 | `0.8314, 0.8866` | `bench/results/search_null.json` | `budget_sweep[budget=130].{mean,p95}` |
| search-null budget sweep at K=29, 260 iterations: mean, p95 | `0.8629, 0.9340` | `bench/results/search_null.json` | `budget_sweep[budget=260].{mean,p95}` |
| scale projection n=57: Kish ESS, CI width, null mean, null p95 | `11.34, 0.2017, 0.8624, 0.9061` | `bench/results/scale_projection.json` | `rows[n=57].{kish_ess,ci_width,null_mean,null_p95}` |
| scale projection n=100: Kish ESS, CI width, null mean, null p95 | `24.89, 0.1269, 0.7192, 0.7621` | `bench/results/scale_projection.json` | `rows[n=100].{kish_ess,ci_width,null_mean,null_p95}` |
| scale projection n=200: Kish ESS, CI width, null mean, null p95 | `44.05, 0.0915, 0.5794, 0.6216` | `bench/results/scale_projection.json` | `rows[n=200].{kish_ess,ci_width,null_mean,null_p95}` |
| length-only baseline CLS | `0.4416` | `bench/results/baseline_ladder.json` | `length_baseline_cls` |
| 3-mer cosine baseline CLS | `0.4576` | `bench/results/baseline_ladder.json` | `rows[4].cls` |
| minimum resolvable CLS difference at 80% power | `0.3419` | `bench/results/representations.json` | `minimum_resolvable_difference` |
| CLS search-capacity null p95 used by the representation panel | `0.4914` | `bench/results/representations.json` | `rows[*].null_cls_p95` |
| search-capacity null p95 at K=1 | `0.4433` | `bench/results/taskA_validation.json` | `search_null_matched.p95` |
| search-capacity null mean at K=1 | `0.2751` | `bench/results/taskA_validation.json` | `search_null_matched.mean` |
| search-capacity null p95 at K=29, the matched count | `0.9340` | `bench/results/search_null.json` | `k_sweep[k=29].p95` |
| search-capacity null p95 at K=50 | `0.9727` | `bench/results/search_null.json` | `k_sweep[k=50].p95` |
| search-capacity null p95 at K=5 | `0.5606` | `bench/results/search_null.json` | `k_sweep[k=5].p95` |
| search-null mean at K=29 after ten DE iterations | `0.6809` | `bench/results/search_null.json` | `budget_sweep[budget=10].mean` |
| reference single draw at seed 42, K=29 | `0.9121` | `bench/results/search_null.json` | `reference.observed_single_draw` |
| value the brief expected for the K=29 null | `0.848` | `bench/results/search_null.json` | `reference.expected` |
| reference null mean over 20 repeats | `0.8662` | `bench/results/search_null.json` | `reference.distribution.mean` |
| reference null median over 20 repeats | `0.8702` | `bench/results/search_null.json` | `reference.distribution.median` |
| reference null repeats | `20` | `bench/results/search_null.json` | `reference.distribution.n_repeats` |
| self-check tolerance | `0.05` | `bench/results/search_null.json` | `reference.tolerance` |
| curated.csv SHA256 | `5e159976a37be07e797ad7048200a6a56fd1b0f396baff6e533f2c467e1b98dc` | `bench/results/taskA_representations.json` | `curated_sha256` |
| bootstrap draws | `10 000` | `bench/results/taskA_validation.json` | `n_bootstrap` |
| label permutation repeats | `20` | `bench/results/taskA_validation.json` | `n_permutations` |
| free parameters selected by the Task A inner loop | `1` | `bench/results/taskA_validation.json` | `free_parameters_used` |
| logistic regularization grid | `0.001, 0.01, 0.1, 1.0, 10.0, 100.0` | `bench/results/taskA_representations.json` | `logistic_C_grid` |
| ridge regularization grid | `0.01, 0.1, 1.0, 10.0, 100.0, 1000.0` | `bench/results/taskA_representations.json` | `ridge_alpha_grid` |
| kmer4 PR-AUC | `0.6212` | `bench/results/taskA_representations.json` | `results.kmer4.classification.pr_auc` |
| kmer4 noise control PR-AUC | `0.4458` | `bench/results/taskA_validation.json` | `noise.kmer4.classification.pr_auc` |
| kmer4 permuted PR-AUC p95 | `0.5398` | `bench/results/taskA_validation.json` | `permutation.kmer4.classification.pr_auc_p95` |
| kmer4 feature count | `20115` | `bench/results/taskA_representations.json` | `results.kmer4.n_features` |
| kmer4 CLS, classification head | `0.0000` | `bench/results/taskA_representations.json` | `results.kmer4.classification.cls` |
| ESM-2 650M PR-AUC | `0.4220` | `bench/results/taskA_representations.json` | `results.esm2_650M.classification.pr_auc` |
| ESM-2 650M noise control PR-AUC | `0.2889` | `bench/results/taskA_validation.json` | `noise.esm2_650M.classification.pr_auc` |
| ESM-2 650M permuted PR-AUC p95 | `0.5217` | `bench/results/taskA_validation.json` | `permutation.esm2_650M.classification.pr_auc_p95` |
| ESM-2 8M PR-AUC | `0.3706` | `bench/results/taskA_representations.json` | `results.esm2_8M.classification.pr_auc` |
| ESM-2 8M noise control PR-AUC | `0.2581` | `bench/results/taskA_validation.json` | `noise.esm2_8M.classification.pr_auc` |
| ESM-2 8M permuted PR-AUC p95 | `0.5676` | `bench/results/taskA_validation.json` | `permutation.esm2_8M.classification.pr_auc_p95` |
| physicochemical CLS, the highest observed under either head | `0.3739` | `bench/results/taskA_representations.json` | `results.physicochemical.classification.cls` |
| ESM-2 650M CLS, Task A classification head | `0.1061` | `bench/results/taskA_representations.json` | `results.esm2_650M.classification.cls` |
| ESM-2 150M CLS under the CLS protocol | `0.3052` | `bench/results/representations.json` | `rows[ESM-2 150M mean-pooled].cls` |
| ESM-2 35M CLS under the CLS protocol | `0.1394` | `bench/results/representations.json` | `rows[ESM-2 35M mean-pooled].cls` |
| ESM-2 8M CLS under the CLS protocol | `0.0074` | `bench/results/representations.json` | `rows[ESM-2 8M mean-pooled].cls` |
| ESM-2 650M CLS under the CLS protocol | `0.0000` | `bench/results/representations.json` | `rows[ESM-2 650M mean-pooled].cls` |
| ESM-2 650M family accuracy under the CLS-protocol measurement | `0.8000` | `bench/results/representations.json` | `rows[ESM-2 650M mean-pooled].family_accuracy` |
| family majority baseline | `0.3214` | `bench/results/representations.json` | `rows[*].family_majority` |
| catalytic-core pooled family accuracy | `0.818` | `bench/results/representations.json` | `rows[ESM-2 650M, catalytic-core pooled].family_accuracy` |
| handcrafted + RandomForest CLS after the join repair | `0.4284` | `bench/results/baseline_ladder.json` | `rows[8b. handcrafted + RandomForest].cls` |
| handcrafted + logistic regression PR-AUC | `0.6533` | `bench/results/baseline_ladder.json` | `rows[9. handcrafted + logistic regression].pr_auc` |
| principal components removed by family residualization | `6` | `bench/results/representations.json` | `rows[ESM-2 650M, family-residualized].transform_info.components_removed` |
| variance removed by family residualization | `0.6433` | `bench/results/representations.json` | `rows[ESM-2 650M, family-residualized].transform_info.variance_removed` |
| PR-AUC chance level, the positive prevalence | `0.3684` | `reports/FINAL_REPORT.md` | `prevalence chance level of 0.3684` |
| stated assumption of the scale projection | `Projections resample the observed 57 RTs with replacement, so they assume new data is drawn from the same family and efficiency distribution. A genuinely broader panel would be more heterogeneous, so these are best-case figures.` | `bench/results/scale_projection.json` | `note` |
| ESM-2 650M family accuracy, diagnostics measurement | `0.8197` | `reports/representation_diagnostics.md` | `verified present: '0.8197'` |
| ESM-2 8M family accuracy, diagnostics measurement | `0.7652` | `reports/representation_diagnostics.md` | `verified present: '0.7652'` |
| ESM-2 35M family accuracy, diagnostics measurement | `0.7833` | `reports/representation_diagnostics.md` | `verified present: '0.7833'` |
| ESM-2 150M family accuracy, diagnostics measurement | `0.8030` | `reports/representation_diagnostics.md` | `verified present: '0.8030'` |
| fold-to-fold SD of the ESM-2 650M family accuracy | `0.1450` | `reports/representation_diagnostics.md` | `verified present: '0.1450'` |
| best composition control family accuracy, 3-mer raw counts | `0.6621` | `reports/representation_diagnostics.md` | `verified present: '0.6621'` |
| length-only family accuracy | `0.5167` | `reports/representation_diagnostics.md` | `verified present: '0.5167'` |
| family majority baseline | `0.3214` | `reports/representation_diagnostics.md` | `verified present: '0.3214'` |
| Spearman of ESM-2 650M PC1 against sequence length | `-0.7681` | `reports/representation_diagnostics.md` | `verified present: '-0.7681'` |
| the same correlation on centred but unstandardized embeddings | `+0.6198` | `reports/representation_diagnostics.md` | `verified present: '+0.6198'` |
| rows retained by the at-least-five-members restriction | `56 of 57` | `reports/representation_diagnostics.md` | `verified present: '56 of 57'` |
| Kish effective sample size of the CLS weighting | `11.338` | `reports/dataset_overview.md` | `verified present: '11.338'` |
| Kish effective sample size, as the metric audit prints it | `11.34` | `audit/metric_report.md` | `verified present: '11.34'` |
| MMLV-RT share of total CLS weight, percent | `15.56` | `audit/metric_report.md` | `verified present: '15.56'` |
| top five RTs' share of total CLS weight, percent | `56.17` | `audit/metric_report.md` | `verified present: '56.17'` |
| all 36 inactives' combined share of total CLS weight, percent | `0.137` | `audit/metric_report.md` | `verified present: '0.137'` |
| bootstrap 95 percent CI width on the submitted prediction vector | `0.0794` | `audit/metric_report.md` | `verified present: '0.0794'` |
| point estimate of the submitted vector on the observed rows | `0.9754` | `audit/metric_report.md` | `verified present: '0.9754'` |
| 2.5th percentile of the bootstrap on the submitted vector | `0.9130` | `audit/metric_report.md` | `verified present: '0.9130'` |
| 97.5th percentile of the bootstrap on the submitted vector | `0.9924` | `audit/metric_report.md` | `verified present: '0.9924'` |
| bootstrap mean on the submitted vector | `0.9649` | `audit/metric_report.md` | `verified present: '0.9649'` |
| standard deviation of CLS over 2000 row permutations | `0.0008` | `audit/metric_report.md` | `verified present: '0.0008'` |
| range of CLS over 2000 row permutations | `0.0048` | `audit/metric_report.md` | `verified present: '0.0048'` |
| median minimum resolvable CLS difference across all pairs | `0.4816` | `reports/statistical_validation.md` | `verified present: '0.4816'` |
| smallest minimum resolvable difference, most similar pair | `0.1499` | `reports/statistical_validation.md` | `verified present: '0.1499'` |
| largest minimum resolvable difference, least similar pair | `0.9056` | `reports/statistical_validation.md` | `verified present: '0.9056'` |
| standard deviations needed for 80 percent power at alpha 0.05 | `2.8016` | `reports/statistical_validation.md` | `verified present: '2.8016'` |
| Spearman of kmer4 out-of-fold score against sequence length | `+0.5212` | `reports/interpretation.md` | `verified present: '+0.5212'` |
| p-value of that correlation | `3.23e-05` | `reports/interpretation.md` | `verified present: '3.23e-05'` |
| kmer4 attribution mass in the top decile of family-explained features | `0.1638` | `reports/interpretation.md` | `verified present: '0.1638'` |
| the feature share that decile represents | `0.1000` | `reports/interpretation.md` | `verified present: '0.1000'` |
| Spearman of per-feature importance against family-explained variance | `+0.2055` | `reports/interpretation.md` | `verified present: '+0.2055'` |
| p-value of the per-feature association | `1.05e-190` | `reports/interpretation.md` | `verified present: '1.05e-190'` |
| kmer4 attribution mass in the top 1 percent of features | `0.0656` | `reports/interpretation.md` | `verified present: '0.0656'` |
| the feature share the top 1 percent represents | `0.0100` | `reports/interpretation.md` | `verified present: '0.0100'` |
| kmer4 margin over its noise control | `+0.0814` | `reports/interpretation.md` | `verified present: '+0.0814'` |
| share of attribution mass carried by the top-ranked 4-mer | `0.00079` | `reports/interpretation.md` | `verified present: '0.00079'` |
| the previously reported CLS | `0.9754` | `WRITEUP.md` | `verified present: '0.9754'` |
| margin of 0.9754 over the matched K=29 noise p95 | `+0.0414` | `WRITEUP.md` | `verified present: '+0.0414'` |
| first CLS quoted in the commit ladder | `0.4380` | `audit/leakage_report.md` | `verified present: '0.4380'` |
| last CLS quoted in the commit ladder | `0.9754` | `audit/leakage_report.md` | `verified present: '0.9754'` |
| number of commit messages quoting a CLS | `20 commits` | `audit/leakage_report.md` | `verified present: '20 commits'` |
| CLS of the different stored artifact that holds 62 fitted parameters | `0.8978` | `WRITEUP.md` | `verified present: '0.8978'` |
| free parameters in de_best_weights.json | `62` | `audit/leakage_report.md` | `verified present: '62'` |
| components scored on their own against the 57 labels | `29` | `audit/leakage_report.md` | `verified present: '29'` |
| best single stored component | `0.6006` | `audit/leakage_report.md` | `verified present: '0.6006'` |
| mean single stored component | `0.4040` | `audit/leakage_report.md` | `verified present: '0.4040'` |
| handcrafted + RandomForest CLS before the join repair | `0.5072` | `WRITEUP.md` | `verified present: '0.5072'` |
| families on which the peeking positive control is detected | `5 of 7` | `WRITEUP.md` | `verified present: 'detects peeking on 5 of 7 families'` |
| structure files covering 56 enzymes | `57 structure` | `WRITEUP.md` | `verified present: '57 structure'` |
| enzymes in the panel | `57` | `reports/dataset_overview.md` | `verified present: '\| enzymes \| 57 \|'` |
| active enzymes | `21` | `reports/dataset_overview.md` | `verified present: '21 (36.8 percent)'` |
| inactive enzymes | `36` | `reports/dataset_overview.md` | `verified present: '\| inactive \| 36 \|'` |
| families | `7` | `reports/dataset_overview.md` | `verified present: '\| families \| 7 \|'` |
| families holding no active enzyme | `3 of 7` | `reports/dataset_overview.md` | `verified present: '3 of 7'` |
| informative leave-one-family-out folds | `4` | `reports/dataset_overview.md` | `verified present: 'Leave-one-family-out rests on 4 informative folds, not 7'` |
| accessions pinned exactly from sequence | `27 of 57` | `reports/FINAL_REPORT.md` | `verified present: '27 of 57'` |
| shortest sequence | `226` | `reports/dataset_overview.md` | `verified present: '\| min \| 226 \|'` |
| longest sequence | `824` | `reports/dataset_overview.md` | `verified present: '\| max \| 824 \|'` |
| median length | `523` | `reports/dataset_overview.md` | `verified present: '\| median \| 523 \|'` |
| mean length | `503.7` | `reports/dataset_overview.md` | `verified present: '503.7'` |
| length standard deviation | `149.9` | `reports/dataset_overview.md` | `verified present: '149.9'` |
| highest digitized efficiency | `41` | `reports/dataset_overview.md` | `verified present: '\| max \| 41 \|'` |
| lowest non-zero efficiency | `0.5` | `reports/dataset_overview.md` | `verified present: '\| min \| 0.5 \|'` |
| median efficiency among actives | `8` | `reports/dataset_overview.md` | `verified present: '\| median \| 8 \|'` |
| mean efficiency among actives | `12.524` | `reports/dataset_overview.md` | `verified present: '12.524'` |
| clusters crossing a family boundary at 30 percent identity | `4` | `reports/dataset_overview.md` | `verified present: '\| 30 percent \| 24 \|'` |
| enzymes the article's prose says were tested | `59` | `reports/doman2023_source_facts.md` | `verified present: 'tested 59 enzymes'` |
| actives the article's prose reports | `Twenty` | `reports/doman2023_source_facts.md` | `verified present: 'Twenty RTs from four different classes'` |
| Task B variants expected | `1045` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '1045'` |
| Task B variant identifiers frozen | `1046` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '1046'` |
| length of the resolved Task B reference | `498` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '498'` |
| residue positions at which the Task B reference was confirmed | `seven residue positions` | `reports/CROSS_TASK_COMPARISON.md` | `verified present: 'resolved and confirmed at seven'` |
| Task B split regimes written and verified | `4 split regimes` | `reports/CROSS_TASK_COMPARISON.md` | `verified present: 'split regimes written and verified'` |
| repository searches that returned nothing | `seven repository searches` | `reports/CROSS_TASK_COMPARISON.md` | `verified present: 'seven repository searches'` |
| the preprint version | `version 1` | `reports/CROSS_TASK_COMPARISON.md` | `verified present: 'still at version 1'` |
| how long version 1 has been current | `three months` | `reports/CROSS_TASK_COMPARISON.md` | `verified present: 'after three months'` |
| the resolving Task B DOI | `10.64898/2026.07.06.736660` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '10.64898/2026.07.06.736660'` |
| the non-resolving DOI the preprint's own header carries | `10.1101/2026.07.06.736660` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '10.1101/2026.07.06.736660'` |
| acquisition attempts logged | `30 attempts` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '30 attempts'` |
| median pairwise cosine similarity of 4-mer vectors across Task B variants | `0.983968` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '0.983968'` |
| median pairwise cosine similarity of physicochemical vectors | `0.999998` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '0.999998'` |
| the Task A source DOI | `10.1016/j.cell.2023.07.039` | `reports/doman2023_source_facts.md` | `verified present: '10.1016/j.cell.2023.07.039'` |
| the Task A source PMC accession | `PMC10482982` | `reports/doman2023_source_facts.md` | `verified present: 'PMC10482982'` |
| SHA256 of the source workbook mmc2.xlsx | `16cdb2109749210fb35acf5e511cbf6a2858982865e88b081ec2c514e88d931c` | `reports/reconciliation.md` | `verified present: '16cdb2109749210fb35acf5e511cbf6a2858982865e88b081ec2c514e88d931c'` |
| Python version of record | `3.14.2` | `WRITEUP.md` | `verified present: 'Python 3.14.2'` |
| numpy version of record | `2.4.2` | `WRITEUP.md` | `verified present: 'numpy 2.4.2'` |
| scipy version of record | `1.17.1` | `WRITEUP.md` | `verified present: 'scipy 1.17.1'` |
| pandas version of record | `3.0.1` | `WRITEUP.md` | `verified present: 'pandas 3.0.1'` |
| scikit-learn version of record | `1.8.0` | `WRITEUP.md` | `verified present: 'scikit-learn 1.8.0'` |
| matplotlib version of record | `3.10.8` | `WRITEUP.md` | `verified present: 'matplotlib 3.10.8'` |
| torch build of record, zero CUDA devices | `2.11.0+cpu` | `WRITEUP.md` | `verified present: 'torch 2.11.0+cpu'` |
| fair-esm version of record | `2.0.0` | `WRITEUP.md` | `verified present: 'fair-esm 2.0.0'` |
| MMseqs2 commit used for clustering | `8cc5ce36` | `reports/dataset_overview.md` | `verified present: '8cc5ce36'` |
| the baseline-ladder module that loads the inherited embedding file unconditionally | `bench/baselines.py` | `bench/baselines.py` | `verified present: 'esm2_embeddings.npz'` |
| the Makefile reproduce target, which does not invoke bench/search_null.py | `reproduce` | `Makefile` | `verified present: 'reproduce: test selfcheck audit embeddings'` |
| memory available at the ESM-1v retry | `2.1 GB` | `WRITEUP.md` | `verified present: '2.1 GB'` |
| total host memory at the ESM-1v retry | `16.9 GB` | `WRITEUP.md` | `verified present: '16.9 GB'` |
| nucleotide identity shared by the two Task B reading frames | `0.807` | `reports/taskB_mmlv_dms/FINAL_REPORT.md` | `verified present: '0.807'` |
| unassayed BLAST-hit entries in block 2 | `486` | `reports/FINAL_REPORT.md` | `verified present: "Block 2's 486 entries"` |

## 2. Every cell of every generated table
Tables: 14. Cells audited: 836.
Each table below is generated by `reports/build_pdf.py` directly from the named
result file and inserted into the PDF as data; the document source contains no
copy of these values. The locator column gives the key path for that exact cell.

### `t_ladder` — Baseline ladder, composite metric (body)

Source: `bench/results/baseline_ladder.json`. Rows: 9. Cells: 63.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| 3-mer cosine to nearest training active, no training | method | `3-mer cosine to nearest training active, no training` | `rows[3-mer cosine to nearest training active, no training].method` |
| 3-mer cosine to nearest training active, no training | selected | `none` | `rows[3-mer cosine to nearest training active, no training].kind / rows[3-mer cosine to nearest training active, no training].n_candidates` |
| 3-mer cosine to nearest training active, no training | CLS | `0.4576` | `rows[3-mer cosine to nearest training active, no training].cls` |
| 3-mer cosine to nearest training active, no training | wSpear. | `0.4021` | `rows[3-mer cosine to nearest training active, no training].w_spearman` |
| 3-mer cosine to nearest training active, no training | null p95 | `0.3961` | `rows[3-mer cosine to nearest training active, no training].null_cls_p95` |
| 3-mer cosine to nearest training active, no training | margin vs null | `+0.0615` | `rows[3-mer cosine to nearest training active, no training].signal_margin` |
| 3-mer cosine to nearest training active, no training | beats length | `yes` | `rows[3-mer cosine to nearest training active, no training].beats_length_baseline vs length_baseline_cls` |
| protein_length_aa, no training | method | `protein_length_aa, no training` | `rows[protein_length_aa, no training].method` |
| protein_length_aa, no training | selected | `none` | `rows[protein_length_aa, no training].kind / rows[protein_length_aa, no training].n_candidates` |
| protein_length_aa, no training | CLS | `0.4416` | `rows[protein_length_aa, no training].cls` |
| protein_length_aa, no training | wSpear. | `0.3893` | `rows[protein_length_aa, no training].w_spearman` |
| protein_length_aa, no training | null p95 | `0.3961` | `rows[protein_length_aa, no training].null_cls_p95` |
| protein_length_aa, no training | margin vs null | `+0.0455` | `rows[protein_length_aa, no training].signal_margin` |
| protein_length_aa, no training | beats length | `ref.` | `rows[protein_length_aa, no training].beats_length_baseline vs length_baseline_cls` |
| handcrafted + RandomForest | method | `handcrafted + RandomForest` | `rows[handcrafted + RandomForest].method` |
| handcrafted + RandomForest | selected | `6` | `rows[handcrafted + RandomForest].kind / rows[handcrafted + RandomForest].n_candidates` |
| handcrafted + RandomForest | CLS | `0.4284` | `rows[handcrafted + RandomForest].cls` |
| handcrafted + RandomForest | wSpear. | `0.2888` | `rows[handcrafted + RandomForest].w_spearman` |
| handcrafted + RandomForest | null p95 | `0.4754` | `rows[handcrafted + RandomForest].null_cls_p95` |
| handcrafted + RandomForest | margin vs null | `-0.0470` | `rows[handcrafted + RandomForest].signal_margin` |
| handcrafted + RandomForest | beats length | `no` | `rows[handcrafted + RandomForest].beats_length_baseline vs length_baseline_cls` |
| family prior by nearest training family, no training | method | `family prior by nearest training family, no training` | `rows[family prior by nearest training family, no training].method` |
| family prior by nearest training family, no training | selected | `none` | `rows[family prior by nearest training family, no training].kind / rows[family prior by nearest training family, no training].n_candidates` |
| family prior by nearest training family, no training | CLS | `0.4160` | `rows[family prior by nearest training family, no training].cls` |
| family prior by nearest training family, no training | wSpear. | `0.4025` | `rows[family prior by nearest training family, no training].w_spearman` |
| family prior by nearest training family, no training | null p95 | `0.3961` | `rows[family prior by nearest training family, no training].null_cls_p95` |
| family prior by nearest training family, no training | margin vs null | `+0.0199` | `rows[family prior by nearest training family, no training].signal_margin` |
| family prior by nearest training family, no training | beats length | `no` | `rows[family prior by nearest training family, no training].beats_length_baseline vs length_baseline_cls` |
| handcrafted + ExtraTrees | method | `handcrafted + ExtraTrees` | `rows[handcrafted + ExtraTrees].method` |
| handcrafted + ExtraTrees | selected | `6` | `rows[handcrafted + ExtraTrees].kind / rows[handcrafted + ExtraTrees].n_candidates` |
| handcrafted + ExtraTrees | CLS | `0.1802` | `rows[handcrafted + ExtraTrees].cls` |
| handcrafted + ExtraTrees | wSpear. | `0.1036` | `rows[handcrafted + ExtraTrees].w_spearman` |
| handcrafted + ExtraTrees | null p95 | `0.4754` | `rows[handcrafted + ExtraTrees].null_cls_p95` |
| handcrafted + ExtraTrees | margin vs null | `-0.2951` | `rows[handcrafted + ExtraTrees].signal_margin` |
| handcrafted + ExtraTrees | beats length | `no` | `rows[handcrafted + ExtraTrees].beats_length_baseline vs length_baseline_cls` |
| negative protein_length_aa, no training | method | `negative protein_length_aa, no training` | `rows[negative protein_length_aa, no training].method` |
| negative protein_length_aa, no training | selected | `none` | `rows[negative protein_length_aa, no training].kind / rows[negative protein_length_aa, no training].n_candidates` |
| negative protein_length_aa, no training | CLS | `0.0000` | `rows[negative protein_length_aa, no training].cls` |
| negative protein_length_aa, no training | wSpear. | `0.0000` | `rows[negative protein_length_aa, no training].w_spearman` |
| negative protein_length_aa, no training | null p95 | `0.3961` | `rows[negative protein_length_aa, no training].null_cls_p95` |
| negative protein_length_aa, no training | margin vs null | `-0.3961` | `rows[negative protein_length_aa, no training].signal_margin` |
| negative protein_length_aa, no training | beats length | `no` | `rows[negative protein_length_aa, no training].beats_length_baseline vs length_baseline_cls` |
| amino acid composition PC1, no training | method | `amino acid composition PC1, no training` | `rows[amino acid composition PC1, no training].method` |
| amino acid composition PC1, no training | selected | `none` | `rows[amino acid composition PC1, no training].kind / rows[amino acid composition PC1, no training].n_candidates` |
| amino acid composition PC1, no training | CLS | `0.0000` | `rows[amino acid composition PC1, no training].cls` |
| amino acid composition PC1, no training | wSpear. | `0.0000` | `rows[amino acid composition PC1, no training].w_spearman` |
| amino acid composition PC1, no training | null p95 | `0.3961` | `rows[amino acid composition PC1, no training].null_cls_p95` |
| amino acid composition PC1, no training | margin vs null | `-0.3961` | `rows[amino acid composition PC1, no training].signal_margin` |
| amino acid composition PC1, no training | beats length | `no` | `rows[amino acid composition PC1, no training].beats_length_baseline vs length_baseline_cls` |
| handcrafted + logistic regression | method | `handcrafted + logistic regression` | `rows[handcrafted + logistic regression].method` |
| handcrafted + logistic regression | selected | `4` | `rows[handcrafted + logistic regression].kind / rows[handcrafted + logistic regression].n_candidates` |
| handcrafted + logistic regression | CLS | `0.0000` | `rows[handcrafted + logistic regression].cls` |
| handcrafted + logistic regression | wSpear. | `0.0000` | `rows[handcrafted + logistic regression].w_spearman` |
| handcrafted + logistic regression | null p95 | `0.4570` | `rows[handcrafted + logistic regression].null_cls_p95` |
| handcrafted + logistic regression | margin vs null | `-0.4570` | `rows[handcrafted + logistic regression].signal_margin` |
| handcrafted + logistic regression | beats length | `no` | `rows[handcrafted + logistic regression].beats_length_baseline vs length_baseline_cls` |
| raw ESM-2 mean-pooled + logistic regression | method | `raw ESM-2 mean-pooled + logistic regression` | `rows[raw ESM-2 mean-pooled + logistic regression].method` |
| raw ESM-2 mean-pooled + logistic regression | selected | `4` | `rows[raw ESM-2 mean-pooled + logistic regression].kind / rows[raw ESM-2 mean-pooled + logistic regression].n_candidates` |
| raw ESM-2 mean-pooled + logistic regression | CLS | `0.0000` | `rows[raw ESM-2 mean-pooled + logistic regression].cls` |
| raw ESM-2 mean-pooled + logistic regression | wSpear. | `0.0000` | `rows[raw ESM-2 mean-pooled + logistic regression].w_spearman` |
| raw ESM-2 mean-pooled + logistic regression | null p95 | `0.4570` | `rows[raw ESM-2 mean-pooled + logistic regression].null_cls_p95` |
| raw ESM-2 mean-pooled + logistic regression | margin vs null | `-0.4570` | `rows[raw ESM-2 mean-pooled + logistic regression].signal_margin` |
| raw ESM-2 mean-pooled + logistic regression | beats length | `no` | `rows[raw ESM-2 mean-pooled + logistic regression].beats_length_baseline vs length_baseline_cls` |

### `t_ladder_cls` — Baseline ladder, composite metric (appendix)

Source: `bench/results/baseline_ladder.json`. Rows: 9. Cells: 63.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| 1. protein_length_aa, no training | method | `1. protein_length_aa, no training` | `rows[1. protein_length_aa, no training].method` |
| 1. protein_length_aa, no training | CLS | `0.4416` | `rows[1. protein_length_aa, no training].cls` |
| 1. protein_length_aa, no training | wSpear. | `0.3893` | `rows[1. protein_length_aa, no training].w_spearman` |
| 1. protein_length_aa, no training | CLS 95% CI | `0.0000–0.6555` | `rows[1. protein_length_aa, no training].ci_low / rows[1. protein_length_aa, no training].ci_high` |
| 1. protein_length_aa, no training | null mean | `0.1076` | `rows[1. protein_length_aa, no training].null_cls_mean` |
| 1. protein_length_aa, no training | null p95 | `0.3961` | `rows[1. protein_length_aa, no training].null_cls_p95` |
| 1. protein_length_aa, no training | margin | `+0.0455` | `rows[1. protein_length_aa, no training].signal_margin` |
| 2. negative protein_length_aa, no training | method | `2. negative protein_length_aa, no training` | `rows[2. negative protein_length_aa, no training].method` |
| 2. negative protein_length_aa, no training | CLS | `0.0000` | `rows[2. negative protein_length_aa, no training].cls` |
| 2. negative protein_length_aa, no training | wSpear. | `0.0000` | `rows[2. negative protein_length_aa, no training].w_spearman` |
| 2. negative protein_length_aa, no training | CLS 95% CI | `0.0000–0.1372` | `rows[2. negative protein_length_aa, no training].ci_low / rows[2. negative protein_length_aa, no training].ci_high` |
| 2. negative protein_length_aa, no training | null mean | `0.1076` | `rows[2. negative protein_length_aa, no training].null_cls_mean` |
| 2. negative protein_length_aa, no training | null p95 | `0.3961` | `rows[2. negative protein_length_aa, no training].null_cls_p95` |
| 2. negative protein_length_aa, no training | margin | `-0.3961` | `rows[2. negative protein_length_aa, no training].signal_margin` |
| 3. amino acid composition PC1, no training | method | `3. amino acid composition PC1, no training` | `rows[3. amino acid composition PC1, no training].method` |
| 3. amino acid composition PC1, no training | CLS | `0.0000` | `rows[3. amino acid composition PC1, no training].cls` |
| 3. amino acid composition PC1, no training | wSpear. | `0.0000` | `rows[3. amino acid composition PC1, no training].w_spearman` |
| 3. amino acid composition PC1, no training | CLS 95% CI | `0.0000–0.5282` | `rows[3. amino acid composition PC1, no training].ci_low / rows[3. amino acid composition PC1, no training].ci_high` |
| 3. amino acid composition PC1, no training | null mean | `0.1076` | `rows[3. amino acid composition PC1, no training].null_cls_mean` |
| 3. amino acid composition PC1, no training | null p95 | `0.3961` | `rows[3. amino acid composition PC1, no training].null_cls_p95` |
| 3. amino acid composition PC1, no training | margin | `-0.3961` | `rows[3. amino acid composition PC1, no training].signal_margin` |
| 4. 3-mer cosine to nearest training active, no training | method | `4. 3-mer cosine to nearest training active, no training` | `rows[4. 3-mer cosine to nearest training active, no training].method` |
| 4. 3-mer cosine to nearest training active, no training | CLS | `0.4576` | `rows[4. 3-mer cosine to nearest training active, no training].cls` |
| 4. 3-mer cosine to nearest training active, no training | wSpear. | `0.4021` | `rows[4. 3-mer cosine to nearest training active, no training].w_spearman` |
| 4. 3-mer cosine to nearest training active, no training | CLS 95% CI | `0.0000–0.6810` | `rows[4. 3-mer cosine to nearest training active, no training].ci_low / rows[4. 3-mer cosine to nearest training active, no training].ci_high` |
| 4. 3-mer cosine to nearest training active, no training | null mean | `0.1076` | `rows[4. 3-mer cosine to nearest training active, no training].null_cls_mean` |
| 4. 3-mer cosine to nearest training active, no training | null p95 | `0.3961` | `rows[4. 3-mer cosine to nearest training active, no training].null_cls_p95` |
| 4. 3-mer cosine to nearest training active, no training | margin | `+0.0615` | `rows[4. 3-mer cosine to nearest training active, no training].signal_margin` |
| 5. family prior by nearest training family, no training | method | `5. family prior by nearest training family, no training` | `rows[5. family prior by nearest training family, no training].method` |
| 5. family prior by nearest training family, no training | CLS | `0.4160` | `rows[5. family prior by nearest training family, no training].cls` |
| 5. family prior by nearest training family, no training | wSpear. | `0.4025` | `rows[5. family prior by nearest training family, no training].w_spearman` |
| 5. family prior by nearest training family, no training | CLS 95% CI | `0.0000–0.5783` | `rows[5. family prior by nearest training family, no training].ci_low / rows[5. family prior by nearest training family, no training].ci_high` |
| 5. family prior by nearest training family, no training | null mean | `0.1076` | `rows[5. family prior by nearest training family, no training].null_cls_mean` |
| 5. family prior by nearest training family, no training | null p95 | `0.3961` | `rows[5. family prior by nearest training family, no training].null_cls_p95` |
| 5. family prior by nearest training family, no training | margin | `+0.0199` | `rows[5. family prior by nearest training family, no training].signal_margin` |
| 8a. handcrafted + ExtraTrees | method | `8a. handcrafted + ExtraTrees` | `rows[8a. handcrafted + ExtraTrees].method` |
| 8a. handcrafted + ExtraTrees | CLS | `0.1802` | `rows[8a. handcrafted + ExtraTrees].cls` |
| 8a. handcrafted + ExtraTrees | wSpear. | `0.1036` | `rows[8a. handcrafted + ExtraTrees].w_spearman` |
| 8a. handcrafted + ExtraTrees | CLS 95% CI | `0.0000–0.6241` | `rows[8a. handcrafted + ExtraTrees].ci_low / rows[8a. handcrafted + ExtraTrees].ci_high` |
| 8a. handcrafted + ExtraTrees | null mean | `0.3305` | `rows[8a. handcrafted + ExtraTrees].null_cls_mean` |
| 8a. handcrafted + ExtraTrees | null p95 | `0.4754` | `rows[8a. handcrafted + ExtraTrees].null_cls_p95` |
| 8a. handcrafted + ExtraTrees | margin | `-0.2951` | `rows[8a. handcrafted + ExtraTrees].signal_margin` |
| 8b. handcrafted + RandomForest | method | `8b. handcrafted + RandomForest` | `rows[8b. handcrafted + RandomForest].method` |
| 8b. handcrafted + RandomForest | CLS | `0.4284` | `rows[8b. handcrafted + RandomForest].cls` |
| 8b. handcrafted + RandomForest | wSpear. | `0.2888` | `rows[8b. handcrafted + RandomForest].w_spearman` |
| 8b. handcrafted + RandomForest | CLS 95% CI | `0.0000–0.7390` | `rows[8b. handcrafted + RandomForest].ci_low / rows[8b. handcrafted + RandomForest].ci_high` |
| 8b. handcrafted + RandomForest | null mean | `0.3305` | `rows[8b. handcrafted + RandomForest].null_cls_mean` |
| 8b. handcrafted + RandomForest | null p95 | `0.4754` | `rows[8b. handcrafted + RandomForest].null_cls_p95` |
| 8b. handcrafted + RandomForest | margin | `-0.0470` | `rows[8b. handcrafted + RandomForest].signal_margin` |
| 9. handcrafted + logistic regression | method | `9. handcrafted + logistic regression` | `rows[9. handcrafted + logistic regression].method` |
| 9. handcrafted + logistic regression | CLS | `0.0000` | `rows[9. handcrafted + logistic regression].cls` |
| 9. handcrafted + logistic regression | wSpear. | `0.0000` | `rows[9. handcrafted + logistic regression].w_spearman` |
| 9. handcrafted + logistic regression | CLS 95% CI | `0.0000–0.4610` | `rows[9. handcrafted + logistic regression].ci_low / rows[9. handcrafted + logistic regression].ci_high` |
| 9. handcrafted + logistic regression | null mean | `0.2859` | `rows[9. handcrafted + logistic regression].null_cls_mean` |
| 9. handcrafted + logistic regression | null p95 | `0.4570` | `rows[9. handcrafted + logistic regression].null_cls_p95` |
| 9. handcrafted + logistic regression | margin | `-0.4570` | `rows[9. handcrafted + logistic regression].signal_margin` |
| 10. raw ESM-2 mean-pooled + logistic regression | method | `10. raw ESM-2 mean-pooled + logistic regression` | `rows[10. raw ESM-2 mean-pooled + logistic regression].method` |
| 10. raw ESM-2 mean-pooled + logistic regression | CLS | `0.0000` | `rows[10. raw ESM-2 mean-pooled + logistic regression].cls` |
| 10. raw ESM-2 mean-pooled + logistic regression | wSpear. | `0.0000` | `rows[10. raw ESM-2 mean-pooled + logistic regression].w_spearman` |
| 10. raw ESM-2 mean-pooled + logistic regression | CLS 95% CI | `0.0000–0.3248` | `rows[10. raw ESM-2 mean-pooled + logistic regression].ci_low / rows[10. raw ESM-2 mean-pooled + logistic regression].ci_high` |
| 10. raw ESM-2 mean-pooled + logistic regression | null mean | `0.2859` | `rows[10. raw ESM-2 mean-pooled + logistic regression].null_cls_mean` |
| 10. raw ESM-2 mean-pooled + logistic regression | null p95 | `0.4570` | `rows[10. raw ESM-2 mean-pooled + logistic regression].null_cls_p95` |
| 10. raw ESM-2 mean-pooled + logistic regression | margin | `-0.4570` | `rows[10. raw ESM-2 mean-pooled + logistic regression].signal_margin` |

### `t_ladder_pr` — Baseline ladder, precision-recall component (appendix)

Source: `bench/results/baseline_ladder.json`. Rows: 9. Cells: 45.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| 1. protein_length_aa, no training | method | `1. protein_length_aa, no training` | `rows[1. protein_length_aa, no training].method` |
| 1. protein_length_aa, no training | kind | `zero-parameter` | `rows[1. protein_length_aa, no training].kind` |
| 1. protein_length_aa, no training | selected | `none` | `rows[1. protein_length_aa, no training].n_candidates` |
| 1. protein_length_aa, no training | PR-AUC | `0.5102` | `rows[1. protein_length_aa, no training].pr_auc` |
| 1. protein_length_aa, no training | seconds | `5.28` | `rows[1. protein_length_aa, no training].seconds` |
| 2. negative protein_length_aa, no training | method | `2. negative protein_length_aa, no training` | `rows[2. negative protein_length_aa, no training].method` |
| 2. negative protein_length_aa, no training | kind | `zero-parameter` | `rows[2. negative protein_length_aa, no training].kind` |
| 2. negative protein_length_aa, no training | selected | `none` | `rows[2. negative protein_length_aa, no training].n_candidates` |
| 2. negative protein_length_aa, no training | PR-AUC | `0.3128` | `rows[2. negative protein_length_aa, no training].pr_auc` |
| 2. negative protein_length_aa, no training | seconds | `5.21` | `rows[2. negative protein_length_aa, no training].seconds` |
| 3. amino acid composition PC1, no training | method | `3. amino acid composition PC1, no training` | `rows[3. amino acid composition PC1, no training].method` |
| 3. amino acid composition PC1, no training | kind | `zero-parameter` | `rows[3. amino acid composition PC1, no training].kind` |
| 3. amino acid composition PC1, no training | selected | `none` | `rows[3. amino acid composition PC1, no training].n_candidates` |
| 3. amino acid composition PC1, no training | PR-AUC | `0.4595` | `rows[3. amino acid composition PC1, no training].pr_auc` |
| 3. amino acid composition PC1, no training | seconds | `5.74` | `rows[3. amino acid composition PC1, no training].seconds` |
| 4. 3-mer cosine to nearest training active, no training | method | `4. 3-mer cosine to nearest training active, no training` | `rows[4. 3-mer cosine to nearest training active, no training].method` |
| 4. 3-mer cosine to nearest training active, no training | kind | `zero-parameter` | `rows[4. 3-mer cosine to nearest training active, no training].kind` |
| 4. 3-mer cosine to nearest training active, no training | selected | `none` | `rows[4. 3-mer cosine to nearest training active, no training].n_candidates` |
| 4. 3-mer cosine to nearest training active, no training | PR-AUC | `0.5309` | `rows[4. 3-mer cosine to nearest training active, no training].pr_auc` |
| 4. 3-mer cosine to nearest training active, no training | seconds | `5.40` | `rows[4. 3-mer cosine to nearest training active, no training].seconds` |
| 5. family prior by nearest training family, no training | method | `5. family prior by nearest training family, no training` | `rows[5. family prior by nearest training family, no training].method` |
| 5. family prior by nearest training family, no training | kind | `zero-parameter` | `rows[5. family prior by nearest training family, no training].kind` |
| 5. family prior by nearest training family, no training | selected | `none` | `rows[5. family prior by nearest training family, no training].n_candidates` |
| 5. family prior by nearest training family, no training | PR-AUC | `0.4304` | `rows[5. family prior by nearest training family, no training].pr_auc` |
| 5. family prior by nearest training family, no training | seconds | `6.12` | `rows[5. family prior by nearest training family, no training].seconds` |
| 8a. handcrafted + ExtraTrees | method | `8a. handcrafted + ExtraTrees` | `rows[8a. handcrafted + ExtraTrees].method` |
| 8a. handcrafted + ExtraTrees | kind | `trained` | `rows[8a. handcrafted + ExtraTrees].kind` |
| 8a. handcrafted + ExtraTrees | selected | `6` | `rows[8a. handcrafted + ExtraTrees].n_candidates` |
| 8a. handcrafted + ExtraTrees | PR-AUC | `0.6948` | `rows[8a. handcrafted + ExtraTrees].pr_auc` |
| 8a. handcrafted + ExtraTrees | seconds | `56.75` | `rows[8a. handcrafted + ExtraTrees].seconds` |
| 8b. handcrafted + RandomForest | method | `8b. handcrafted + RandomForest` | `rows[8b. handcrafted + RandomForest].method` |
| 8b. handcrafted + RandomForest | kind | `trained` | `rows[8b. handcrafted + RandomForest].kind` |
| 8b. handcrafted + RandomForest | selected | `6` | `rows[8b. handcrafted + RandomForest].n_candidates` |
| 8b. handcrafted + RandomForest | PR-AUC | `0.8288` | `rows[8b. handcrafted + RandomForest].pr_auc` |
| 8b. handcrafted + RandomForest | seconds | `61.93` | `rows[8b. handcrafted + RandomForest].seconds` |
| 9. handcrafted + logistic regression | method | `9. handcrafted + logistic regression` | `rows[9. handcrafted + logistic regression].method` |
| 9. handcrafted + logistic regression | kind | `trained` | `rows[9. handcrafted + logistic regression].kind` |
| 9. handcrafted + logistic regression | selected | `4` | `rows[9. handcrafted + logistic regression].n_candidates` |
| 9. handcrafted + logistic regression | PR-AUC | `0.6533` | `rows[9. handcrafted + logistic regression].pr_auc` |
| 9. handcrafted + logistic regression | seconds | `4.06` | `rows[9. handcrafted + logistic regression].seconds` |
| 10. raw ESM-2 mean-pooled + logistic regression | method | `10. raw ESM-2 mean-pooled + logistic regression` | `rows[10. raw ESM-2 mean-pooled + logistic regression].method` |
| 10. raw ESM-2 mean-pooled + logistic regression | kind | `trained` | `rows[10. raw ESM-2 mean-pooled + logistic regression].kind` |
| 10. raw ESM-2 mean-pooled + logistic regression | selected | `4` | `rows[10. raw ESM-2 mean-pooled + logistic regression].n_candidates` |
| 10. raw ESM-2 mean-pooled + logistic regression | PR-AUC | `0.2877` | `rows[10. raw ESM-2 mean-pooled + logistic regression].pr_auc` |
| 10. raw ESM-2 mean-pooled + logistic regression | seconds | `5.20` | `rows[10. raw ESM-2 mean-pooled + logistic regression].seconds` |

### `t_reps` — Representations, composite metric (body)

Source: `bench/results/representations.json`. Rows: 10. Cells: 70.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| ESM-2 150M mean-pooled | representation | `ESM-2 150M mean-pooled` | `rows[ESM-2 150M mean-pooled].method` |
| ESM-2 150M mean-pooled | features | `640` | `rows[ESM-2 150M mean-pooled].n_features` |
| ESM-2 150M mean-pooled | CLS | `0.3052` | `rows[ESM-2 150M mean-pooled].cls` |
| ESM-2 150M mean-pooled | wSpear. | `0.2614` | `rows[ESM-2 150M mean-pooled].w_spearman` |
| ESM-2 150M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 150M mean-pooled].null_cls_p95` |
| ESM-2 150M mean-pooled | margin vs null | `-0.1861` | `rows[ESM-2 150M mean-pooled].signal_margin` |
| ESM-2 150M mean-pooled | family acc. | `0.802` | `rows[ESM-2 150M mean-pooled].family_accuracy` |
| ESM-2 35M mean-pooled | representation | `ESM-2 35M mean-pooled` | `rows[ESM-2 35M mean-pooled].method` |
| ESM-2 35M mean-pooled | features | `480` | `rows[ESM-2 35M mean-pooled].n_features` |
| ESM-2 35M mean-pooled | CLS | `0.1394` | `rows[ESM-2 35M mean-pooled].cls` |
| ESM-2 35M mean-pooled | wSpear. | `0.0909` | `rows[ESM-2 35M mean-pooled].w_spearman` |
| ESM-2 35M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 35M mean-pooled].null_cls_p95` |
| ESM-2 35M mean-pooled | margin vs null | `-0.3520` | `rows[ESM-2 35M mean-pooled].signal_margin` |
| ESM-2 35M mean-pooled | family acc. | `0.782` | `rows[ESM-2 35M mean-pooled].family_accuracy` |
| ESM-2 8M mean-pooled | representation | `ESM-2 8M mean-pooled` | `rows[ESM-2 8M mean-pooled].method` |
| ESM-2 8M mean-pooled | features | `320` | `rows[ESM-2 8M mean-pooled].n_features` |
| ESM-2 8M mean-pooled | CLS | `0.0074` | `rows[ESM-2 8M mean-pooled].cls` |
| ESM-2 8M mean-pooled | wSpear. | `0.0037` | `rows[ESM-2 8M mean-pooled].w_spearman` |
| ESM-2 8M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 8M mean-pooled].null_cls_p95` |
| ESM-2 8M mean-pooled | margin vs null | `-0.4840` | `rows[ESM-2 8M mean-pooled].signal_margin` |
| ESM-2 8M mean-pooled | family acc. | `0.745` | `rows[ESM-2 8M mean-pooled].family_accuracy` |
| handcrafted: sequence and physicochemical | representation | `handcrafted: sequence and physicochemical` | `rows[handcrafted: sequence and physicochemical].method` |
| handcrafted: sequence and physicochemical | features | `112` | `rows[handcrafted: sequence and physicochemical].n_features` |
| handcrafted: sequence and physicochemical | CLS | `0.0000` | `rows[handcrafted: sequence and physicochemical].cls` |
| handcrafted: sequence and physicochemical | wSpear. | `0.0000` | `rows[handcrafted: sequence and physicochemical].w_spearman` |
| handcrafted: sequence and physicochemical | null p95 | `0.4914` | `rows[handcrafted: sequence and physicochemical].null_cls_p95` |
| handcrafted: sequence and physicochemical | margin vs null | `-0.4914` | `rows[handcrafted: sequence and physicochemical].signal_margin` |
| handcrafted: sequence and physicochemical | family acc. | `0.712` | `rows[handcrafted: sequence and physicochemical].family_accuracy` |
| structure: pLDDT, cleft and topology | representation | `structure: pLDDT, cleft and topology` | `rows[structure: pLDDT, cleft and topology].method` |
| structure: pLDDT, cleft and topology | features | `18` | `rows[structure: pLDDT, cleft and topology].n_features` |
| structure: pLDDT, cleft and topology | CLS | `0.0000` | `rows[structure: pLDDT, cleft and topology].cls` |
| structure: pLDDT, cleft and topology | wSpear. | `0.0000` | `rows[structure: pLDDT, cleft and topology].w_spearman` |
| structure: pLDDT, cleft and topology | null p95 | `0.4914` | `rows[structure: pLDDT, cleft and topology].null_cls_p95` |
| structure: pLDDT, cleft and topology | margin vs null | `-0.4914` | `rows[structure: pLDDT, cleft and topology].signal_margin` |
| structure: pLDDT, cleft and topology | family acc. | `0.659` | `rows[structure: pLDDT, cleft and topology].family_accuracy` |
| ESM-2 650M mean-pooled | representation | `ESM-2 650M mean-pooled` | `rows[ESM-2 650M mean-pooled].method` |
| ESM-2 650M mean-pooled | features | `1280` | `rows[ESM-2 650M mean-pooled].n_features` |
| ESM-2 650M mean-pooled | CLS | `0.0000` | `rows[ESM-2 650M mean-pooled].cls` |
| ESM-2 650M mean-pooled | wSpear. | `0.0000` | `rows[ESM-2 650M mean-pooled].w_spearman` |
| ESM-2 650M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 650M mean-pooled].null_cls_p95` |
| ESM-2 650M mean-pooled | margin vs null | `-0.4914` | `rows[ESM-2 650M mean-pooled].signal_margin` |
| ESM-2 650M mean-pooled | family acc. | `0.800` | `rows[ESM-2 650M mean-pooled].family_accuracy` |
| ESM-2 650M, length-residualized | representation | `ESM-2 650M, length-residualized` | `rows[ESM-2 650M, length-residualized].method` |
| ESM-2 650M, length-residualized | features | `1280` | `rows[ESM-2 650M, length-residualized].n_features` |
| ESM-2 650M, length-residualized | CLS | `0.0000` | `rows[ESM-2 650M, length-residualized].cls` |
| ESM-2 650M, length-residualized | wSpear. | `0.0000` | `rows[ESM-2 650M, length-residualized].w_spearman` |
| ESM-2 650M, length-residualized | null p95 | `0.4914` | `rows[ESM-2 650M, length-residualized].null_cls_p95` |
| ESM-2 650M, length-residualized | margin vs null | `-0.4914` | `rows[ESM-2 650M, length-residualized].signal_margin` |
| ESM-2 650M, length-residualized | family acc. | `0.800` | `rows[ESM-2 650M, length-residualized].family_accuracy` |
| ESM-2 650M, family-residualized | representation | `ESM-2 650M, family-residualized` | `rows[ESM-2 650M, family-residualized].method` |
| ESM-2 650M, family-residualized | features | `1280` | `rows[ESM-2 650M, family-residualized].n_features` |
| ESM-2 650M, family-residualized | CLS | `0.0000` | `rows[ESM-2 650M, family-residualized].cls` |
| ESM-2 650M, family-residualized | wSpear. | `0.0000` | `rows[ESM-2 650M, family-residualized].w_spearman` |
| ESM-2 650M, family-residualized | null p95 | `0.4914` | `rows[ESM-2 650M, family-residualized].null_cls_p95` |
| ESM-2 650M, family-residualized | margin vs null | `-0.4914` | `rows[ESM-2 650M, family-residualized].signal_margin` |
| ESM-2 650M, family-residualized | family acc. | `0.800` | `rows[ESM-2 650M, family-residualized].family_accuracy` |
| ESM-2 650M, catalytic-core pooled | representation | `ESM-2 650M, catalytic-core pooled` | `rows[ESM-2 650M, catalytic-core pooled].method` |
| ESM-2 650M, catalytic-core pooled | features | `1280` | `rows[ESM-2 650M, catalytic-core pooled].n_features` |
| ESM-2 650M, catalytic-core pooled | CLS | `0.0000` | `rows[ESM-2 650M, catalytic-core pooled].cls` |
| ESM-2 650M, catalytic-core pooled | wSpear. | `0.0000` | `rows[ESM-2 650M, catalytic-core pooled].w_spearman` |
| ESM-2 650M, catalytic-core pooled | null p95 | `0.4914` | `rows[ESM-2 650M, catalytic-core pooled].null_cls_p95` |
| ESM-2 650M, catalytic-core pooled | margin vs null | `-0.4914` | `rows[ESM-2 650M, catalytic-core pooled].signal_margin` |
| ESM-2 650M, catalytic-core pooled | family acc. | `0.818` | `rows[ESM-2 650M, catalytic-core pooled].family_accuracy` |
| ESM-2, attention-weighted core pooling | representation | `ESM-2, attention-weighted core pooling` | `rows[ESM-2, attention-weighted core pooling].method` |
| ESM-2, attention-weighted core pooling | features | `1280` | `rows[ESM-2, attention-weighted core pooling].n_features` |
| ESM-2, attention-weighted core pooling | CLS | `0.0000` | `rows[ESM-2, attention-weighted core pooling].cls` |
| ESM-2, attention-weighted core pooling | wSpear. | `0.0000` | `rows[ESM-2, attention-weighted core pooling].w_spearman` |
| ESM-2, attention-weighted core pooling | null p95 | `0.4914` | `rows[ESM-2, attention-weighted core pooling].null_cls_p95` |
| ESM-2, attention-weighted core pooling | margin vs null | `-0.4914` | `rows[ESM-2, attention-weighted core pooling].signal_margin` |
| ESM-2, attention-weighted core pooling | family acc. | `0.818` | `rows[ESM-2, attention-weighted core pooling].family_accuracy` |

### `t_reps_cls` — Representations, composite metric (appendix)

Source: `bench/results/representations.json`. Rows: 10. Cells: 70.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| handcrafted: sequence and physicochemical | representation | `handcrafted: sequence and physicochemical` | `rows[handcrafted: sequence and physicochemical].method` |
| handcrafted: sequence and physicochemical | CLS | `0.0000` | `rows[handcrafted: sequence and physicochemical].cls` |
| handcrafted: sequence and physicochemical | wSpear. | `0.0000` | `rows[handcrafted: sequence and physicochemical].w_spearman` |
| handcrafted: sequence and physicochemical | CLS 95% CI | `0.0000–0.4585` | `rows[handcrafted: sequence and physicochemical].ci_low / rows[handcrafted: sequence and physicochemical].ci_high` |
| handcrafted: sequence and physicochemical | null p95 | `0.4914` | `rows[handcrafted: sequence and physicochemical].null_cls_p95` |
| handcrafted: sequence and physicochemical | margin | `-0.4914` | `rows[handcrafted: sequence and physicochemical].signal_margin` |
| handcrafted: sequence and physicochemical | fam. acc. | `0.712` | `rows[handcrafted: sequence and physicochemical].family_accuracy` |
| structure: pLDDT, cleft and topology | representation | `structure: pLDDT, cleft and topology` | `rows[structure: pLDDT, cleft and topology].method` |
| structure: pLDDT, cleft and topology | CLS | `0.0000` | `rows[structure: pLDDT, cleft and topology].cls` |
| structure: pLDDT, cleft and topology | wSpear. | `0.0000` | `rows[structure: pLDDT, cleft and topology].w_spearman` |
| structure: pLDDT, cleft and topology | CLS 95% CI | `0.0000–0.3516` | `rows[structure: pLDDT, cleft and topology].ci_low / rows[structure: pLDDT, cleft and topology].ci_high` |
| structure: pLDDT, cleft and topology | null p95 | `0.4914` | `rows[structure: pLDDT, cleft and topology].null_cls_p95` |
| structure: pLDDT, cleft and topology | margin | `-0.4914` | `rows[structure: pLDDT, cleft and topology].signal_margin` |
| structure: pLDDT, cleft and topology | fam. acc. | `0.659` | `rows[structure: pLDDT, cleft and topology].family_accuracy` |
| ESM-2 8M mean-pooled | representation | `ESM-2 8M mean-pooled` | `rows[ESM-2 8M mean-pooled].method` |
| ESM-2 8M mean-pooled | CLS | `0.0074` | `rows[ESM-2 8M mean-pooled].cls` |
| ESM-2 8M mean-pooled | wSpear. | `0.0037` | `rows[ESM-2 8M mean-pooled].w_spearman` |
| ESM-2 8M mean-pooled | CLS 95% CI | `0.0000–0.4545` | `rows[ESM-2 8M mean-pooled].ci_low / rows[ESM-2 8M mean-pooled].ci_high` |
| ESM-2 8M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 8M mean-pooled].null_cls_p95` |
| ESM-2 8M mean-pooled | margin | `-0.4840` | `rows[ESM-2 8M mean-pooled].signal_margin` |
| ESM-2 8M mean-pooled | fam. acc. | `0.745` | `rows[ESM-2 8M mean-pooled].family_accuracy` |
| ESM-2 35M mean-pooled | representation | `ESM-2 35M mean-pooled` | `rows[ESM-2 35M mean-pooled].method` |
| ESM-2 35M mean-pooled | CLS | `0.1394` | `rows[ESM-2 35M mean-pooled].cls` |
| ESM-2 35M mean-pooled | wSpear. | `0.0909` | `rows[ESM-2 35M mean-pooled].w_spearman` |
| ESM-2 35M mean-pooled | CLS 95% CI | `0.0000–0.4344` | `rows[ESM-2 35M mean-pooled].ci_low / rows[ESM-2 35M mean-pooled].ci_high` |
| ESM-2 35M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 35M mean-pooled].null_cls_p95` |
| ESM-2 35M mean-pooled | margin | `-0.3520` | `rows[ESM-2 35M mean-pooled].signal_margin` |
| ESM-2 35M mean-pooled | fam. acc. | `0.782` | `rows[ESM-2 35M mean-pooled].family_accuracy` |
| ESM-2 150M mean-pooled | representation | `ESM-2 150M mean-pooled` | `rows[ESM-2 150M mean-pooled].method` |
| ESM-2 150M mean-pooled | CLS | `0.3052` | `rows[ESM-2 150M mean-pooled].cls` |
| ESM-2 150M mean-pooled | wSpear. | `0.2614` | `rows[ESM-2 150M mean-pooled].w_spearman` |
| ESM-2 150M mean-pooled | CLS 95% CI | `0.0000–0.5294` | `rows[ESM-2 150M mean-pooled].ci_low / rows[ESM-2 150M mean-pooled].ci_high` |
| ESM-2 150M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 150M mean-pooled].null_cls_p95` |
| ESM-2 150M mean-pooled | margin | `-0.1861` | `rows[ESM-2 150M mean-pooled].signal_margin` |
| ESM-2 150M mean-pooled | fam. acc. | `0.802` | `rows[ESM-2 150M mean-pooled].family_accuracy` |
| ESM-2 650M mean-pooled | representation | `ESM-2 650M mean-pooled` | `rows[ESM-2 650M mean-pooled].method` |
| ESM-2 650M mean-pooled | CLS | `0.0000` | `rows[ESM-2 650M mean-pooled].cls` |
| ESM-2 650M mean-pooled | wSpear. | `0.0000` | `rows[ESM-2 650M mean-pooled].w_spearman` |
| ESM-2 650M mean-pooled | CLS 95% CI | `0.0000–0.3529` | `rows[ESM-2 650M mean-pooled].ci_low / rows[ESM-2 650M mean-pooled].ci_high` |
| ESM-2 650M mean-pooled | null p95 | `0.4914` | `rows[ESM-2 650M mean-pooled].null_cls_p95` |
| ESM-2 650M mean-pooled | margin | `-0.4914` | `rows[ESM-2 650M mean-pooled].signal_margin` |
| ESM-2 650M mean-pooled | fam. acc. | `0.800` | `rows[ESM-2 650M mean-pooled].family_accuracy` |
| ESM-2 650M, length-residualized | representation | `ESM-2 650M, length-residualized` | `rows[ESM-2 650M, length-residualized].method` |
| ESM-2 650M, length-residualized | CLS | `0.0000` | `rows[ESM-2 650M, length-residualized].cls` |
| ESM-2 650M, length-residualized | wSpear. | `0.0000` | `rows[ESM-2 650M, length-residualized].w_spearman` |
| ESM-2 650M, length-residualized | CLS 95% CI | `0.0000–0.2904` | `rows[ESM-2 650M, length-residualized].ci_low / rows[ESM-2 650M, length-residualized].ci_high` |
| ESM-2 650M, length-residualized | null p95 | `0.4914` | `rows[ESM-2 650M, length-residualized].null_cls_p95` |
| ESM-2 650M, length-residualized | margin | `-0.4914` | `rows[ESM-2 650M, length-residualized].signal_margin` |
| ESM-2 650M, length-residualized | fam. acc. | `0.800` | `rows[ESM-2 650M, length-residualized].family_accuracy` |
| ESM-2 650M, family-residualized | representation | `ESM-2 650M, family-residualized` | `rows[ESM-2 650M, family-residualized].method` |
| ESM-2 650M, family-residualized | CLS | `0.0000` | `rows[ESM-2 650M, family-residualized].cls` |
| ESM-2 650M, family-residualized | wSpear. | `0.0000` | `rows[ESM-2 650M, family-residualized].w_spearman` |
| ESM-2 650M, family-residualized | CLS 95% CI | `0.0000–0.1209` | `rows[ESM-2 650M, family-residualized].ci_low / rows[ESM-2 650M, family-residualized].ci_high` |
| ESM-2 650M, family-residualized | null p95 | `0.4914` | `rows[ESM-2 650M, family-residualized].null_cls_p95` |
| ESM-2 650M, family-residualized | margin | `-0.4914` | `rows[ESM-2 650M, family-residualized].signal_margin` |
| ESM-2 650M, family-residualized | fam. acc. | `0.800` | `rows[ESM-2 650M, family-residualized].family_accuracy` |
| ESM-2 650M, catalytic-core pooled | representation | `ESM-2 650M, catalytic-core pooled` | `rows[ESM-2 650M, catalytic-core pooled].method` |
| ESM-2 650M, catalytic-core pooled | CLS | `0.0000` | `rows[ESM-2 650M, catalytic-core pooled].cls` |
| ESM-2 650M, catalytic-core pooled | wSpear. | `0.0000` | `rows[ESM-2 650M, catalytic-core pooled].w_spearman` |
| ESM-2 650M, catalytic-core pooled | CLS 95% CI | `0.0000–0.2991` | `rows[ESM-2 650M, catalytic-core pooled].ci_low / rows[ESM-2 650M, catalytic-core pooled].ci_high` |
| ESM-2 650M, catalytic-core pooled | null p95 | `0.4914` | `rows[ESM-2 650M, catalytic-core pooled].null_cls_p95` |
| ESM-2 650M, catalytic-core pooled | margin | `-0.4914` | `rows[ESM-2 650M, catalytic-core pooled].signal_margin` |
| ESM-2 650M, catalytic-core pooled | fam. acc. | `0.818` | `rows[ESM-2 650M, catalytic-core pooled].family_accuracy` |
| ESM-2, attention-weighted core pooling | representation | `ESM-2, attention-weighted core pooling` | `rows[ESM-2, attention-weighted core pooling].method` |
| ESM-2, attention-weighted core pooling | CLS | `0.0000` | `rows[ESM-2, attention-weighted core pooling].cls` |
| ESM-2, attention-weighted core pooling | wSpear. | `0.0000` | `rows[ESM-2, attention-weighted core pooling].w_spearman` |
| ESM-2, attention-weighted core pooling | CLS 95% CI | `0.0000–0.2869` | `rows[ESM-2, attention-weighted core pooling].ci_low / rows[ESM-2, attention-weighted core pooling].ci_high` |
| ESM-2, attention-weighted core pooling | null p95 | `0.4914` | `rows[ESM-2, attention-weighted core pooling].null_cls_p95` |
| ESM-2, attention-weighted core pooling | margin | `-0.4914` | `rows[ESM-2, attention-weighted core pooling].signal_margin` |
| ESM-2, attention-weighted core pooling | fam. acc. | `0.818` | `rows[ESM-2, attention-weighted core pooling].family_accuracy` |

### `t_reps_pr` — Representations, precision-recall component (appendix)

Source: `bench/results/representations.json`. Rows: 10. Cells: 40.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| handcrafted: sequence and physicochemical | representation | `handcrafted: sequence and physicochemical` | `rows[handcrafted: sequence and physicochemical].method` |
| handcrafted: sequence and physicochemical | features | `112` | `rows[handcrafted: sequence and physicochemical].n_features` |
| handcrafted: sequence and physicochemical | PR-AUC | `0.6436` | `rows[handcrafted: sequence and physicochemical].pr_auc` |
| handcrafted: sequence and physicochemical | seconds | `15.49` | `rows[handcrafted: sequence and physicochemical].seconds` |
| structure: pLDDT, cleft and topology | representation | `structure: pLDDT, cleft and topology` | `rows[structure: pLDDT, cleft and topology].method` |
| structure: pLDDT, cleft and topology | features | `18` | `rows[structure: pLDDT, cleft and topology].n_features` |
| structure: pLDDT, cleft and topology | PR-AUC | `0.3391` | `rows[structure: pLDDT, cleft and topology].pr_auc` |
| structure: pLDDT, cleft and topology | seconds | `11.97` | `rows[structure: pLDDT, cleft and topology].seconds` |
| ESM-2 8M mean-pooled | representation | `ESM-2 8M mean-pooled` | `rows[ESM-2 8M mean-pooled].method` |
| ESM-2 8M mean-pooled | features | `320` | `rows[ESM-2 8M mean-pooled].n_features` |
| ESM-2 8M mean-pooled | PR-AUC | `0.3242` | `rows[ESM-2 8M mean-pooled].pr_auc` |
| ESM-2 8M mean-pooled | seconds | `30.34` | `rows[ESM-2 8M mean-pooled].seconds` |
| ESM-2 35M mean-pooled | representation | `ESM-2 35M mean-pooled` | `rows[ESM-2 35M mean-pooled].method` |
| ESM-2 35M mean-pooled | features | `480` | `rows[ESM-2 35M mean-pooled].n_features` |
| ESM-2 35M mean-pooled | PR-AUC | `0.2985` | `rows[ESM-2 35M mean-pooled].pr_auc` |
| ESM-2 35M mean-pooled | seconds | `38.63` | `rows[ESM-2 35M mean-pooled].seconds` |
| ESM-2 150M mean-pooled | representation | `ESM-2 150M mean-pooled` | `rows[ESM-2 150M mean-pooled].method` |
| ESM-2 150M mean-pooled | features | `640` | `rows[ESM-2 150M mean-pooled].n_features` |
| ESM-2 150M mean-pooled | PR-AUC | `0.3666` | `rows[ESM-2 150M mean-pooled].pr_auc` |
| ESM-2 150M mean-pooled | seconds | `45.13` | `rows[ESM-2 150M mean-pooled].seconds` |
| ESM-2 650M mean-pooled | representation | `ESM-2 650M mean-pooled` | `rows[ESM-2 650M mean-pooled].method` |
| ESM-2 650M mean-pooled | features | `1280` | `rows[ESM-2 650M mean-pooled].n_features` |
| ESM-2 650M mean-pooled | PR-AUC | `0.2870` | `rows[ESM-2 650M mean-pooled].pr_auc` |
| ESM-2 650M mean-pooled | seconds | `69.15` | `rows[ESM-2 650M mean-pooled].seconds` |
| ESM-2 650M, length-residualized | representation | `ESM-2 650M, length-residualized` | `rows[ESM-2 650M, length-residualized].method` |
| ESM-2 650M, length-residualized | features | `1280` | `rows[ESM-2 650M, length-residualized].n_features` |
| ESM-2 650M, length-residualized | PR-AUC | `0.3205` | `rows[ESM-2 650M, length-residualized].pr_auc` |
| ESM-2 650M, length-residualized | seconds | `68.19` | `rows[ESM-2 650M, length-residualized].seconds` |
| ESM-2 650M, family-residualized | representation | `ESM-2 650M, family-residualized` | `rows[ESM-2 650M, family-residualized].method` |
| ESM-2 650M, family-residualized | features | `1280` | `rows[ESM-2 650M, family-residualized].n_features` |
| ESM-2 650M, family-residualized | PR-AUC | `0.4016` | `rows[ESM-2 650M, family-residualized].pr_auc` |
| ESM-2 650M, family-residualized | seconds | `18.66` | `rows[ESM-2 650M, family-residualized].seconds` |
| ESM-2 650M, catalytic-core pooled | representation | `ESM-2 650M, catalytic-core pooled` | `rows[ESM-2 650M, catalytic-core pooled].method` |
| ESM-2 650M, catalytic-core pooled | features | `1280` | `rows[ESM-2 650M, catalytic-core pooled].n_features` |
| ESM-2 650M, catalytic-core pooled | PR-AUC | `0.2781` | `rows[ESM-2 650M, catalytic-core pooled].pr_auc` |
| ESM-2 650M, catalytic-core pooled | seconds | `68.48` | `rows[ESM-2 650M, catalytic-core pooled].seconds` |
| ESM-2, attention-weighted core pooling | representation | `ESM-2, attention-weighted core pooling` | `rows[ESM-2, attention-weighted core pooling].method` |
| ESM-2, attention-weighted core pooling | features | `1280` | `rows[ESM-2, attention-weighted core pooling].n_features` |
| ESM-2, attention-weighted core pooling | PR-AUC | `0.2808` | `rows[ESM-2, attention-weighted core pooling].pr_auc` |
| ESM-2, attention-weighted core pooling | seconds | `69.61` | `rows[ESM-2, attention-weighted core pooling].seconds` |

### `t_taskA` — Task A, three-control protocol, precision-recall area (body)

Source: `bench/results/taskA_representations.json + bench/results/taskA_validation.json`. Rows: 12. Cells: 84.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| kmer4 | representation | `kmer4` | `results.kmer4` |
| kmer4 | features | `20115` | `results.kmer4.n_features` |
| kmer4 | PR-AUC | `0.6212` | `results.kmer4.classification.pr_auc` |
| kmer4 | 95% CI | `0.4285–0.8325` | `intervals.kmer4.classification.pr_auc.ci_low / .ci_high` |
| kmer4 | noise control | `0.4458` | `noise.kmer4.classification.pr_auc` |
| kmer4 | permuted p95 | `0.5398` | `permutation.kmer4.classification.pr_auc_p95` |
| kmer4 | survives | `yes` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| esm2_650M | representation | `esm2_650M` | `results.esm2_650M` |
| esm2_650M | features | `1280` | `results.esm2_650M.n_features` |
| esm2_650M | PR-AUC | `0.4220` | `results.esm2_650M.classification.pr_auc` |
| esm2_650M | 95% CI | `0.2665–0.6492` | `intervals.esm2_650M.classification.pr_auc.ci_low / .ci_high` |
| esm2_650M | noise control | `0.2889` | `noise.esm2_650M.classification.pr_auc` |
| esm2_650M | permuted p95 | `0.5217` | `permutation.esm2_650M.classification.pr_auc_p95` |
| esm2_650M | survives | `no` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| esm2_8M | representation | `esm2_8M` | `results.esm2_8M` |
| esm2_8M | features | `320` | `results.esm2_8M.n_features` |
| esm2_8M | PR-AUC | `0.3706` | `results.esm2_8M.classification.pr_auc` |
| esm2_8M | 95% CI | `0.2242–0.5710` | `intervals.esm2_8M.classification.pr_auc.ci_low / .ci_high` |
| esm2_8M | noise control | `0.2581` | `noise.esm2_8M.classification.pr_auc` |
| esm2_8M | permuted p95 | `0.5676` | `permutation.esm2_8M.classification.pr_auc_p95` |
| esm2_8M | survives | `no` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| physicochemical | representation | `physicochemical` | `results.physicochemical` |
| physicochemical | features | `13` | `results.physicochemical.n_features` |
| physicochemical | PR-AUC | `0.3623` | `results.physicochemical.classification.pr_auc` |
| physicochemical | 95% CI | `0.2457–0.5448` | `intervals.physicochemical.classification.pr_auc.ci_low / .ci_high` |
| physicochemical | noise control | `0.2643` | `noise.physicochemical.classification.pr_auc` |
| physicochemical | permuted p95 | `0.4254` | `permutation.physicochemical.classification.pr_auc_p95` |
| physicochemical | survives | `no` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| esm2_35M | representation | `esm2_35M` | `results.esm2_35M` |
| esm2_35M | features | `480` | `results.esm2_35M.n_features` |
| esm2_35M | PR-AUC | `0.3162` | `results.esm2_35M.classification.pr_auc` |
| esm2_35M | 95% CI | `0.2066–0.4977` | `intervals.esm2_35M.classification.pr_auc.ci_low / .ci_high` |
| esm2_35M | noise control | `0.2899` | `noise.esm2_35M.classification.pr_auc` |
| esm2_35M | permuted p95 | `not tested` | `permutation.esm2_35M.classification.pr_auc_p95` |
| esm2_35M | survives | `n/a` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| kmer3 | representation | `kmer3` | `results.kmer3` |
| kmer3 | features | `6256` | `results.kmer3.n_features` |
| kmer3 | PR-AUC | `0.3137` | `results.kmer3.classification.pr_auc` |
| kmer3 | 95% CI | `0.2085–0.4955` | `intervals.kmer3.classification.pr_auc.ci_low / .ci_high` |
| kmer3 | noise control | `0.3029` | `noise.kmer3.classification.pr_auc` |
| kmer3 | permuted p95 | `not tested` | `permutation.kmer3.classification.pr_auc_p95` |
| kmer3 | survives | `n/a` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| handcrafted_plus_esm2_650M | representation | `handcrafted_plus_esm2_650M` | `results.handcrafted_plus_esm2_650M` |
| handcrafted_plus_esm2_650M | features | `2069` | `results.handcrafted_plus_esm2_650M.n_features` |
| handcrafted_plus_esm2_650M | PR-AUC | `0.3082` | `results.handcrafted_plus_esm2_650M.classification.pr_auc` |
| handcrafted_plus_esm2_650M | 95% CI | `0.2093–0.4748` | `intervals.handcrafted_plus_esm2_650M.classification.pr_auc.ci_low / .ci_high` |
| handcrafted_plus_esm2_650M | noise control | `0.2970` | `noise.handcrafted_plus_esm2_650M.classification.pr_auc` |
| handcrafted_plus_esm2_650M | permuted p95 | `not tested` | `permutation.handcrafted_plus_esm2_650M.classification.pr_auc_p95` |
| handcrafted_plus_esm2_650M | survives | `n/a` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| dipeptide | representation | `dipeptide` | `results.dipeptide` |
| dipeptide | features | `400` | `results.dipeptide.n_features` |
| dipeptide | PR-AUC | `0.3081` | `results.dipeptide.classification.pr_auc` |
| dipeptide | 95% CI | `0.2090–0.4618` | `intervals.dipeptide.classification.pr_auc.ci_low / .ci_high` |
| dipeptide | noise control | `0.3118` | `noise.dipeptide.classification.pr_auc` |
| dipeptide | permuted p95 | `not tested` | `permutation.dipeptide.classification.pr_auc_p95` |
| dipeptide | survives | `n/a` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| esm2_150M | representation | `esm2_150M` | `results.esm2_150M` |
| esm2_150M | features | `640` | `results.esm2_150M.n_features` |
| esm2_150M | PR-AUC | `0.3056` | `results.esm2_150M.classification.pr_auc` |
| esm2_150M | 95% CI | `0.2052–0.4817` | `intervals.esm2_150M.classification.pr_auc.ci_low / .ci_high` |
| esm2_150M | noise control | `0.2856` | `noise.esm2_150M.classification.pr_auc` |
| esm2_150M | permuted p95 | `not tested` | `permutation.esm2_150M.classification.pr_auc_p95` |
| esm2_150M | survives | `n/a` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| handcrafted | representation | `handcrafted` | `results.handcrafted` |
| handcrafted | features | `789` | `results.handcrafted.n_features` |
| handcrafted | PR-AUC | `0.2956` | `results.handcrafted.classification.pr_auc` |
| handcrafted | 95% CI | `0.2000–0.4475` | `intervals.handcrafted.classification.pr_auc.ci_low / .ci_high` |
| handcrafted | noise control | `0.2675` | `noise.handcrafted.classification.pr_auc` |
| handcrafted | permuted p95 | `0.4891` | `permutation.handcrafted.classification.pr_auc_p95` |
| handcrafted | survives | `no` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| aa_composition | representation | `aa_composition` | `results.aa_composition` |
| aa_composition | features | `20` | `results.aa_composition.n_features` |
| aa_composition | PR-AUC | `0.2781` | `results.aa_composition.classification.pr_auc` |
| aa_composition | 95% CI | `0.1889–0.4123` | `intervals.aa_composition.classification.pr_auc.ci_low / .ci_high` |
| aa_composition | noise control | `0.3261` | `noise.aa_composition.classification.pr_auc` |
| aa_composition | permuted p95 | `not tested` | `permutation.aa_composition.classification.pr_auc_p95` |
| aa_composition | survives | `n/a` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |
| length | representation | `length` | `results.length` |
| length | features | `1` | `results.length.n_features` |
| length | PR-AUC | `0.2599` | `results.length.classification.pr_auc` |
| length | 95% CI | `0.1763–0.3923` | `intervals.length.classification.pr_auc.ci_low / .ci_high` |
| length | noise control | `0.2474` | `noise.length.classification.pr_auc` |
| length | permuted p95 | `0.4111` | `permutation.length.classification.pr_auc_p95` |
| length | survives | `no` | `derived: PR-AUC exceeds noise, prevalence 0.3684 and permuted p95` |

### `t_cls_class` — Task A composite, classification head (appendix)

Source: `bench/results/taskA_representations.json + bench/results/taskA_validation.json`. Rows: 12. Cells: 72.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| physicochemical | representation | `physicochemical` | `results.physicochemical` |
| physicochemical | CLS | `0.3739` | `results.physicochemical.classification.cls` |
| physicochemical | 95% CI | `0.0000–0.5258` | `intervals.physicochemical.classification.cls.ci_low / .ci_high` |
| physicochemical | noise CLS | `0.0000` | `noise.physicochemical.classification.cls` |
| physicochemical | search null p95 | `0.4433` | `search_null_matched.p95` |
| physicochemical | margin | `-0.0694` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| handcrafted_plus_esm2_650M | representation | `handcrafted_plus_esm2_650M` | `results.handcrafted_plus_esm2_650M` |
| handcrafted_plus_esm2_650M | CLS | `0.3449` | `results.handcrafted_plus_esm2_650M.classification.cls` |
| handcrafted_plus_esm2_650M | 95% CI | `0.0000–0.5136` | `intervals.handcrafted_plus_esm2_650M.classification.cls.ci_low / .ci_high` |
| handcrafted_plus_esm2_650M | noise CLS | `0.0000` | `noise.handcrafted_plus_esm2_650M.classification.cls` |
| handcrafted_plus_esm2_650M | search null p95 | `0.4433` | `search_null_matched.p95` |
| handcrafted_plus_esm2_650M | margin | `-0.0984` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| kmer3 | representation | `kmer3` | `results.kmer3` |
| kmer3 | CLS | `0.3249` | `results.kmer3.classification.cls` |
| kmer3 | 95% CI | `0.0000–0.4864` | `intervals.kmer3.classification.cls.ci_low / .ci_high` |
| kmer3 | noise CLS | `0.0000` | `noise.kmer3.classification.cls` |
| kmer3 | search null p95 | `0.4433` | `search_null_matched.p95` |
| kmer3 | margin | `-0.1184` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| handcrafted | representation | `handcrafted` | `results.handcrafted` |
| handcrafted | CLS | `0.2805` | `results.handcrafted.classification.cls` |
| handcrafted | 95% CI | `0.0000–0.4643` | `intervals.handcrafted.classification.cls.ci_low / .ci_high` |
| handcrafted | noise CLS | `0.0471` | `noise.handcrafted.classification.cls` |
| handcrafted | search null p95 | `0.4433` | `search_null_matched.p95` |
| handcrafted | margin | `-0.1628` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_35M | representation | `esm2_35M` | `results.esm2_35M` |
| esm2_35M | CLS | `0.2412` | `results.esm2_35M.classification.cls` |
| esm2_35M | 95% CI | `0.0000–0.4690` | `intervals.esm2_35M.classification.cls.ci_low / .ci_high` |
| esm2_35M | noise CLS | `0.2460` | `noise.esm2_35M.classification.cls` |
| esm2_35M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_35M | margin | `-0.2020` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_150M | representation | `esm2_150M` | `results.esm2_150M` |
| esm2_150M | CLS | `0.2187` | `results.esm2_150M.classification.cls` |
| esm2_150M | 95% CI | `0.0000–0.4871` | `intervals.esm2_150M.classification.cls.ci_low / .ci_high` |
| esm2_150M | noise CLS | `0.2506` | `noise.esm2_150M.classification.cls` |
| esm2_150M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_150M | margin | `-0.2246` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| aa_composition | representation | `aa_composition` | `results.aa_composition` |
| aa_composition | CLS | `0.1142` | `results.aa_composition.classification.cls` |
| aa_composition | 95% CI | `0.0000–0.4177` | `intervals.aa_composition.classification.cls.ci_low / .ci_high` |
| aa_composition | noise CLS | `0.0000` | `noise.aa_composition.classification.cls` |
| aa_composition | search null p95 | `0.4433` | `search_null_matched.p95` |
| aa_composition | margin | `-0.3291` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| length | representation | `length` | `results.length` |
| length | CLS | `0.1100` | `results.length.classification.cls` |
| length | 95% CI | `0.0000–0.3758` | `intervals.length.classification.cls.ci_low / .ci_high` |
| length | noise CLS | `0.0645` | `noise.length.classification.cls` |
| length | search null p95 | `0.4433` | `search_null_matched.p95` |
| length | margin | `-0.3333` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_650M | representation | `esm2_650M` | `results.esm2_650M` |
| esm2_650M | CLS | `0.1061` | `results.esm2_650M.classification.cls` |
| esm2_650M | 95% CI | `0.0000–0.4614` | `intervals.esm2_650M.classification.cls.ci_low / .ci_high` |
| esm2_650M | noise CLS | `0.0357` | `noise.esm2_650M.classification.cls` |
| esm2_650M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_650M | margin | `-0.3372` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| dipeptide | representation | `dipeptide` | `results.dipeptide` |
| dipeptide | CLS | `0.0000` | `results.dipeptide.classification.cls` |
| dipeptide | 95% CI | `0.0000–0.3600` | `intervals.dipeptide.classification.cls.ci_low / .ci_high` |
| dipeptide | noise CLS | `0.0241` | `noise.dipeptide.classification.cls` |
| dipeptide | search null p95 | `0.4433` | `search_null_matched.p95` |
| dipeptide | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_8M | representation | `esm2_8M` | `results.esm2_8M` |
| esm2_8M | CLS | `0.0000` | `results.esm2_8M.classification.cls` |
| esm2_8M | 95% CI | `0.0000–0.3965` | `intervals.esm2_8M.classification.cls.ci_low / .ci_high` |
| esm2_8M | noise CLS | `0.0000` | `noise.esm2_8M.classification.cls` |
| esm2_8M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_8M | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| kmer4 | representation | `kmer4` | `results.kmer4` |
| kmer4 | CLS | `0.0000` | `results.kmer4.classification.cls` |
| kmer4 | 95% CI | `0.0000–0.5671` | `intervals.kmer4.classification.cls.ci_low / .ci_high` |
| kmer4 | noise CLS | `0.0000` | `noise.kmer4.classification.cls` |
| kmer4 | search null p95 | `0.4433` | `search_null_matched.p95` |
| kmer4 | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |

### `t_cls_reg` — Task A composite, regression head (appendix)

Source: `bench/results/taskA_representations.json + bench/results/taskA_validation.json`. Rows: 12. Cells: 72.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| length | representation | `length` | `results.length` |
| length | CLS | `0.3576` | `results.length.regression.cls` |
| length | 95% CI | `0.0000–0.4992` | `intervals.length.regression.cls.ci_low / .ci_high` |
| length | noise CLS | `0.1192` | `noise.length.regression.cls` |
| length | search null p95 | `0.4433` | `search_null_matched.p95` |
| length | margin | `-0.0857` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_8M | representation | `esm2_8M` | `results.esm2_8M` |
| esm2_8M | CLS | `0.2840` | `results.esm2_8M.regression.cls` |
| esm2_8M | 95% CI | `0.0000–0.4625` | `intervals.esm2_8M.regression.cls.ci_low / .ci_high` |
| esm2_8M | noise CLS | `0.0000` | `noise.esm2_8M.regression.cls` |
| esm2_8M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_8M | margin | `-0.1593` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_35M | representation | `esm2_35M` | `results.esm2_35M` |
| esm2_35M | CLS | `0.2785` | `results.esm2_35M.regression.cls` |
| esm2_35M | 95% CI | `0.0000–0.5043` | `intervals.esm2_35M.regression.cls.ci_low / .ci_high` |
| esm2_35M | noise CLS | `0.0000` | `noise.esm2_35M.regression.cls` |
| esm2_35M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_35M | margin | `-0.1648` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| handcrafted | representation | `handcrafted` | `results.handcrafted` |
| handcrafted | CLS | `0.2646` | `results.handcrafted.regression.cls` |
| handcrafted | 95% CI | `0.0000–0.4431` | `intervals.handcrafted.regression.cls.ci_low / .ci_high` |
| handcrafted | noise CLS | `0.0000` | `noise.handcrafted.regression.cls` |
| handcrafted | search null p95 | `0.4433` | `search_null_matched.p95` |
| handcrafted | margin | `-0.1786` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| physicochemical | representation | `physicochemical` | `results.physicochemical` |
| physicochemical | CLS | `0.0821` | `results.physicochemical.regression.cls` |
| physicochemical | 95% CI | `0.0000–0.4170` | `intervals.physicochemical.regression.cls.ci_low / .ci_high` |
| physicochemical | noise CLS | `0.0000` | `noise.physicochemical.regression.cls` |
| physicochemical | search null p95 | `0.4433` | `search_null_matched.p95` |
| physicochemical | margin | `-0.3612` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| aa_composition | representation | `aa_composition` | `results.aa_composition` |
| aa_composition | CLS | `0.0159` | `results.aa_composition.regression.cls` |
| aa_composition | 95% CI | `0.0000–0.3744` | `intervals.aa_composition.regression.cls.ci_low / .ci_high` |
| aa_composition | noise CLS | `0.0000` | `noise.aa_composition.regression.cls` |
| aa_composition | search null p95 | `0.4433` | `search_null_matched.p95` |
| aa_composition | margin | `-0.4274` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| dipeptide | representation | `dipeptide` | `results.dipeptide` |
| dipeptide | CLS | `0.0000` | `results.dipeptide.regression.cls` |
| dipeptide | 95% CI | `0.0000–0.3304` | `intervals.dipeptide.regression.cls.ci_low / .ci_high` |
| dipeptide | noise CLS | `0.0000` | `noise.dipeptide.regression.cls` |
| dipeptide | search null p95 | `0.4433` | `search_null_matched.p95` |
| dipeptide | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_150M | representation | `esm2_150M` | `results.esm2_150M` |
| esm2_150M | CLS | `0.0000` | `results.esm2_150M.regression.cls` |
| esm2_150M | 95% CI | `0.0000–0.1888` | `intervals.esm2_150M.regression.cls.ci_low / .ci_high` |
| esm2_150M | noise CLS | `0.2774` | `noise.esm2_150M.regression.cls` |
| esm2_150M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_150M | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| esm2_650M | representation | `esm2_650M` | `results.esm2_650M` |
| esm2_650M | CLS | `0.0000` | `results.esm2_650M.regression.cls` |
| esm2_650M | 95% CI | `0.0000–0.3762` | `intervals.esm2_650M.regression.cls.ci_low / .ci_high` |
| esm2_650M | noise CLS | `0.0000` | `noise.esm2_650M.regression.cls` |
| esm2_650M | search null p95 | `0.4433` | `search_null_matched.p95` |
| esm2_650M | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| handcrafted_plus_esm2_650M | representation | `handcrafted_plus_esm2_650M` | `results.handcrafted_plus_esm2_650M` |
| handcrafted_plus_esm2_650M | CLS | `0.0000` | `results.handcrafted_plus_esm2_650M.regression.cls` |
| handcrafted_plus_esm2_650M | 95% CI | `0.0000–0.3767` | `intervals.handcrafted_plus_esm2_650M.regression.cls.ci_low / .ci_high` |
| handcrafted_plus_esm2_650M | noise CLS | `0.0000` | `noise.handcrafted_plus_esm2_650M.regression.cls` |
| handcrafted_plus_esm2_650M | search null p95 | `0.4433` | `search_null_matched.p95` |
| handcrafted_plus_esm2_650M | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| kmer3 | representation | `kmer3` | `results.kmer3` |
| kmer3 | CLS | `0.0000` | `results.kmer3.regression.cls` |
| kmer3 | 95% CI | `0.0000–0.3767` | `intervals.kmer3.regression.cls.ci_low / .ci_high` |
| kmer3 | noise CLS | `0.0000` | `noise.kmer3.regression.cls` |
| kmer3 | search null p95 | `0.4433` | `search_null_matched.p95` |
| kmer3 | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |
| kmer4 | representation | `kmer4` | `results.kmer4` |
| kmer4 | CLS | `0.0000` | `results.kmer4.regression.cls` |
| kmer4 | 95% CI | `0.0000–0.1684` | `intervals.kmer4.regression.cls.ci_low / .ci_high` |
| kmer4 | noise CLS | `0.0000` | `noise.kmer4.regression.cls` |
| kmer4 | search null p95 | `0.4433` | `search_null_matched.p95` |
| kmer4 | margin | `-0.4433` | `derived: cls minus max(noise cls, search_null_matched.p95)` |

### `t_ksweep` — Search-capacity null, K sweep

Source: `bench/results/search_null.json`. Rows: 7. Cells: 49.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| 1 | K | `1` | `k_sweep[k=1].k` |
| 1 | repeats | `10` | `k_sweep[k=1].n_repeats` |
| 1 | mean | `0.2751` | `k_sweep[k=1].mean` |
| 1 | sd | `0.1213` | `k_sweep[k=1].std` |
| 1 | p95 | `0.4433` | `k_sweep[k=1].p95` |
| 1 | min | `0.1113` | `k_sweep[k=1].min` |
| 1 | max | `0.4843` | `k_sweep[k=1].max` |
| 2 | K | `2` | `k_sweep[k=2].k` |
| 2 | repeats | `10` | `k_sweep[k=2].n_repeats` |
| 2 | mean | `0.3945` | `k_sweep[k=2].mean` |
| 2 | sd | `0.0681` | `k_sweep[k=2].std` |
| 2 | p95 | `0.4944` | `k_sweep[k=2].p95` |
| 2 | min | `0.3160` | `k_sweep[k=2].min` |
| 2 | max | `0.5145` | `k_sweep[k=2].max` |
| 5 | K | `5` | `k_sweep[k=5].k` |
| 5 | repeats | `10` | `k_sweep[k=5].n_repeats` |
| 5 | mean | `0.5006` | `k_sweep[k=5].mean` |
| 5 | sd | `0.0494` | `k_sweep[k=5].std` |
| 5 | p95 | `0.5606` | `k_sweep[k=5].p95` |
| 5 | min | `0.4430` | `k_sweep[k=5].min` |
| 5 | max | `0.5616` | `k_sweep[k=5].max` |
| 10 | K | `10` | `k_sweep[k=10].k` |
| 10 | repeats | `10` | `k_sweep[k=10].n_repeats` |
| 10 | mean | `0.6170` | `k_sweep[k=10].mean` |
| 10 | sd | `0.0327` | `k_sweep[k=10].std` |
| 10 | p95 | `0.6536` | `k_sweep[k=10].p95` |
| 10 | min | `0.5536` | `k_sweep[k=10].min` |
| 10 | max | `0.6634` | `k_sweep[k=10].max` |
| 20 | K | `20` | `k_sweep[k=20].k` |
| 20 | repeats | `10` | `k_sweep[k=20].n_repeats` |
| 20 | mean | `0.7909` | `k_sweep[k=20].mean` |
| 20 | sd | `0.0504` | `k_sweep[k=20].std` |
| 20 | p95 | `0.8637` | `k_sweep[k=20].p95` |
| 20 | min | `0.7011` | `k_sweep[k=20].min` |
| 20 | max | `0.8828` | `k_sweep[k=20].max` |
| 29 | K | `29` | `k_sweep[k=29].k` |
| 29 | repeats | `10` | `k_sweep[k=29].n_repeats` |
| 29 | mean | `0.8629` | `k_sweep[k=29].mean` |
| 29 | sd | `0.0489` | `k_sweep[k=29].std` |
| 29 | p95 | `0.9340` | `k_sweep[k=29].p95` |
| 29 | min | `0.7996` | `k_sweep[k=29].min` |
| 29 | max | `0.9503` | `k_sweep[k=29].max` |
| 50 | K | `50` | `k_sweep[k=50].k` |
| 50 | repeats | `10` | `k_sweep[k=50].n_repeats` |
| 50 | mean | `0.9210` | `k_sweep[k=50].mean` |
| 50 | sd | `0.0321` | `k_sweep[k=50].std` |
| 50 | p95 | `0.9727` | `k_sweep[k=50].p95` |
| 50 | min | `0.8759` | `k_sweep[k=50].min` |
| 50 | max | `0.9737` | `k_sweep[k=50].max` |

### `t_budget` — Search-capacity null, budget sweep at K=29

Source: `bench/results/search_null.json`. Rows: 5. Cells: 25.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| 10 | iterations | `10` | `budget_sweep[budget=10].budget` |
| 10 | repeats | `10` | `budget_sweep[budget=10].n_repeats` |
| 10 | mean | `0.6809` | `budget_sweep[budget=10].mean` |
| 10 | sd | `0.0478` | `budget_sweep[budget=10].std` |
| 10 | p95 | `0.7340` | `budget_sweep[budget=10].p95` |
| 30 | iterations | `30` | `budget_sweep[budget=30].budget` |
| 30 | repeats | `10` | `budget_sweep[budget=30].n_repeats` |
| 30 | mean | `0.7396` | `budget_sweep[budget=30].mean` |
| 30 | sd | `0.0378` | `budget_sweep[budget=30].std` |
| 30 | p95 | `0.7831` | `budget_sweep[budget=30].p95` |
| 60 | iterations | `60` | `budget_sweep[budget=60].budget` |
| 60 | repeats | `10` | `budget_sweep[budget=60].n_repeats` |
| 60 | mean | `0.7828` | `budget_sweep[budget=60].mean` |
| 60 | sd | `0.0495` | `budget_sweep[budget=60].std` |
| 60 | p95 | `0.8441` | `budget_sweep[budget=60].p95` |
| 130 | iterations | `130` | `budget_sweep[budget=130].budget` |
| 130 | repeats | `10` | `budget_sweep[budget=130].n_repeats` |
| 130 | mean | `0.8314` | `budget_sweep[budget=130].mean` |
| 130 | sd | `0.0421` | `budget_sweep[budget=130].std` |
| 130 | p95 | `0.8866` | `budget_sweep[budget=130].p95` |
| 260 | iterations | `260` | `budget_sweep[budget=260].budget` |
| 260 | repeats | `10` | `budget_sweep[budget=260].n_repeats` |
| 260 | mean | `0.8629` | `budget_sweep[budget=260].mean` |
| 260 | sd | `0.0489` | `budget_sweep[budget=260].std` |
| 260 | p95 | `0.9340` | `budget_sweep[budget=260].p95` |

### `t_scale` — Scale projection

Source: `bench/results/scale_projection.json`. Rows: 3. Cells: 15.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| 57 | n | `57` | `rows[n=57].n` |
| 57 | Kish ESS | `11.34` | `rows[n=57].kish_ess` |
| 57 | bootstrap CI width | `0.2017` | `rows[n=57].ci_width` |
| 57 | noise null mean | `0.8624` | `rows[n=57].null_mean` |
| 57 | noise null p95 | `0.9061` | `rows[n=57].null_p95` |
| 100 | n | `100` | `rows[n=100].n` |
| 100 | Kish ESS | `24.89` | `rows[n=100].kish_ess` |
| 100 | bootstrap CI width | `0.1269` | `rows[n=100].ci_width` |
| 100 | noise null mean | `0.7192` | `rows[n=100].null_mean` |
| 100 | noise null p95 | `0.7621` | `rows[n=100].null_p95` |
| 200 | n | `200` | `rows[n=200].n` |
| 200 | Kish ESS | `44.05` | `rows[n=200].kish_ess` |
| 200 | bootstrap CI width | `0.0915` | `rows[n=200].ci_width` |
| 200 | noise null mean | `0.5794` | `rows[n=200].null_mean` |
| 200 | noise null p95 | `0.6216` | `rows[n=200].null_p95` |

### `t_perm_cls` — Label permutation, composite metric

Source: `bench/results/taskA_representations.json + bench/results/taskA_validation.json`. Rows: 12. Cells: 84.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| esm2_650M | representation | `esm2_650M` | `permutation.esm2_650M` |
| esm2_650M | head | `classification` | `the head named in this cell` |
| esm2_650M | permuted mean | `0.1051` | `permutation.esm2_650M.<head>.mean` |
| esm2_650M | permuted p95 | `0.3700` | `permutation.esm2_650M.<head>.p95` |
| esm2_650M | permuted max | `0.3851` | `permutation.esm2_650M.<head>.max` |
| esm2_650M | observed | `0.1061` | `results.esm2_650M.<head>.cls` |
| esm2_650M | above p95 | `no` | `derived: observed exceeds permuted p95` |
| esm2_650M | representation | `esm2_650M` | `permutation.esm2_650M` |
| esm2_650M | head | `regression` | `the head named in this cell` |
| esm2_650M | permuted mean | `0.1047` | `permutation.esm2_650M.<head>.mean` |
| esm2_650M | permuted p95 | `0.3529` | `permutation.esm2_650M.<head>.p95` |
| esm2_650M | permuted max | `0.4012` | `permutation.esm2_650M.<head>.max` |
| esm2_650M | observed | `0.0000` | `results.esm2_650M.<head>.cls` |
| esm2_650M | above p95 | `no` | `derived: observed exceeds permuted p95` |
| esm2_8M | representation | `esm2_8M` | `permutation.esm2_8M` |
| esm2_8M | head | `classification` | `the head named in this cell` |
| esm2_8M | permuted mean | `0.1410` | `permutation.esm2_8M.<head>.mean` |
| esm2_8M | permuted p95 | `0.3537` | `permutation.esm2_8M.<head>.p95` |
| esm2_8M | permuted max | `0.4019` | `permutation.esm2_8M.<head>.max` |
| esm2_8M | observed | `0.0000` | `results.esm2_8M.<head>.cls` |
| esm2_8M | above p95 | `no` | `derived: observed exceeds permuted p95` |
| esm2_8M | representation | `esm2_8M` | `permutation.esm2_8M` |
| esm2_8M | head | `regression` | `the head named in this cell` |
| esm2_8M | permuted mean | `0.0736` | `permutation.esm2_8M.<head>.mean` |
| esm2_8M | permuted p95 | `0.2530` | `permutation.esm2_8M.<head>.p95` |
| esm2_8M | permuted max | `0.4578` | `permutation.esm2_8M.<head>.max` |
| esm2_8M | observed | `0.2840` | `results.esm2_8M.<head>.cls` |
| esm2_8M | above p95 | `yes` | `derived: observed exceeds permuted p95` |
| handcrafted | representation | `handcrafted` | `permutation.handcrafted` |
| handcrafted | head | `classification` | `the head named in this cell` |
| handcrafted | permuted mean | `0.1548` | `permutation.handcrafted.<head>.mean` |
| handcrafted | permuted p95 | `0.3644` | `permutation.handcrafted.<head>.p95` |
| handcrafted | permuted max | `0.5400` | `permutation.handcrafted.<head>.max` |
| handcrafted | observed | `0.2805` | `results.handcrafted.<head>.cls` |
| handcrafted | above p95 | `no` | `derived: observed exceeds permuted p95` |
| handcrafted | representation | `handcrafted` | `permutation.handcrafted` |
| handcrafted | head | `regression` | `the head named in this cell` |
| handcrafted | permuted mean | `0.1215` | `permutation.handcrafted.<head>.mean` |
| handcrafted | permuted p95 | `0.3072` | `permutation.handcrafted.<head>.p95` |
| handcrafted | permuted max | `0.4551` | `permutation.handcrafted.<head>.max` |
| handcrafted | observed | `0.2646` | `results.handcrafted.<head>.cls` |
| handcrafted | above p95 | `no` | `derived: observed exceeds permuted p95` |
| kmer4 | representation | `kmer4` | `permutation.kmer4` |
| kmer4 | head | `classification` | `the head named in this cell` |
| kmer4 | permuted mean | `0.1916` | `permutation.kmer4.<head>.mean` |
| kmer4 | permuted p95 | `0.4371` | `permutation.kmer4.<head>.p95` |
| kmer4 | permuted max | `0.4671` | `permutation.kmer4.<head>.max` |
| kmer4 | observed | `0.0000` | `results.kmer4.<head>.cls` |
| kmer4 | above p95 | `no` | `derived: observed exceeds permuted p95` |
| kmer4 | representation | `kmer4` | `permutation.kmer4` |
| kmer4 | head | `regression` | `the head named in this cell` |
| kmer4 | permuted mean | `0.0393` | `permutation.kmer4.<head>.mean` |
| kmer4 | permuted p95 | `0.2622` | `permutation.kmer4.<head>.p95` |
| kmer4 | permuted max | `0.3019` | `permutation.kmer4.<head>.max` |
| kmer4 | observed | `0.0000` | `results.kmer4.<head>.cls` |
| kmer4 | above p95 | `no` | `derived: observed exceeds permuted p95` |
| length | representation | `length` | `permutation.length` |
| length | head | `classification` | `the head named in this cell` |
| length | permuted mean | `0.1266` | `permutation.length.<head>.mean` |
| length | permuted p95 | `0.3418` | `permutation.length.<head>.p95` |
| length | permuted max | `0.4153` | `permutation.length.<head>.max` |
| length | observed | `0.1100` | `results.length.<head>.cls` |
| length | above p95 | `no` | `derived: observed exceeds permuted p95` |
| length | representation | `length` | `permutation.length` |
| length | head | `regression` | `the head named in this cell` |
| length | permuted mean | `0.0264` | `permutation.length.<head>.mean` |
| length | permuted p95 | `0.1406` | `permutation.length.<head>.p95` |
| length | permuted max | `0.1426` | `permutation.length.<head>.max` |
| length | observed | `0.3576` | `results.length.<head>.cls` |
| length | above p95 | `yes` | `derived: observed exceeds permuted p95` |
| physicochemical | representation | `physicochemical` | `permutation.physicochemical` |
| physicochemical | head | `classification` | `the head named in this cell` |
| physicochemical | permuted mean | `0.1076` | `permutation.physicochemical.<head>.mean` |
| physicochemical | permuted p95 | `0.3786` | `permutation.physicochemical.<head>.p95` |
| physicochemical | permuted max | `0.3801` | `permutation.physicochemical.<head>.max` |
| physicochemical | observed | `0.3739` | `results.physicochemical.<head>.cls` |
| physicochemical | above p95 | `no` | `derived: observed exceeds permuted p95` |
| physicochemical | representation | `physicochemical` | `permutation.physicochemical` |
| physicochemical | head | `regression` | `the head named in this cell` |
| physicochemical | permuted mean | `0.0598` | `permutation.physicochemical.<head>.mean` |
| physicochemical | permuted p95 | `0.3099` | `permutation.physicochemical.<head>.p95` |
| physicochemical | permuted max | `0.3589` | `permutation.physicochemical.<head>.max` |
| physicochemical | observed | `0.0821` | `results.physicochemical.<head>.cls` |
| physicochemical | above p95 | `no` | `derived: observed exceeds permuted p95` |

### `t_perm_pr` — Label permutation, precision-recall area

Source: `bench/results/taskA_representations.json + bench/results/taskA_validation.json`. Rows: 12. Cells: 84.

| row | column | value as printed | locator |
| --- | --- | --- | --- |
| esm2_650M | representation | `esm2_650M` | `permutation.esm2_650M` |
| esm2_650M | head | `classification` | `the head named in this cell` |
| esm2_650M | permuted mean | `0.3969` | `permutation.esm2_650M.<head>.pr_auc_mean` |
| esm2_650M | permuted p95 | `0.5217` | `permutation.esm2_650M.<head>.pr_auc_p95` |
| esm2_650M | permuted max | `0.5275` | `permutation.esm2_650M.<head>.pr_auc_max` |
| esm2_650M | observed | `0.4220` | `results.esm2_650M.<head>.pr_auc` |
| esm2_650M | above p95 | `no` | `derived: observed exceeds permuted p95` |
| esm2_650M | representation | `esm2_650M` | `permutation.esm2_650M` |
| esm2_650M | head | `regression` | `the head named in this cell` |
| esm2_650M | permuted mean | `0.4021` | `permutation.esm2_650M.<head>.pr_auc_mean` |
| esm2_650M | permuted p95 | `0.5042` | `permutation.esm2_650M.<head>.pr_auc_p95` |
| esm2_650M | permuted max | `0.5378` | `permutation.esm2_650M.<head>.pr_auc_max` |
| esm2_650M | observed | `0.4067` | `results.esm2_650M.<head>.pr_auc` |
| esm2_650M | above p95 | `no` | `derived: observed exceeds permuted p95` |
| esm2_8M | representation | `esm2_8M` | `permutation.esm2_8M` |
| esm2_8M | head | `classification` | `the head named in this cell` |
| esm2_8M | permuted mean | `0.3976` | `permutation.esm2_8M.<head>.pr_auc_mean` |
| esm2_8M | permuted p95 | `0.5676` | `permutation.esm2_8M.<head>.pr_auc_p95` |
| esm2_8M | permuted max | `0.5688` | `permutation.esm2_8M.<head>.pr_auc_max` |
| esm2_8M | observed | `0.3706` | `results.esm2_8M.<head>.pr_auc` |
| esm2_8M | above p95 | `no` | `derived: observed exceeds permuted p95` |
| esm2_8M | representation | `esm2_8M` | `permutation.esm2_8M` |
| esm2_8M | head | `regression` | `the head named in this cell` |
| esm2_8M | permuted mean | `0.4189` | `permutation.esm2_8M.<head>.pr_auc_mean` |
| esm2_8M | permuted p95 | `0.5650` | `permutation.esm2_8M.<head>.pr_auc_p95` |
| esm2_8M | permuted max | `0.5753` | `permutation.esm2_8M.<head>.pr_auc_max` |
| esm2_8M | observed | `0.3269` | `results.esm2_8M.<head>.pr_auc` |
| esm2_8M | above p95 | `no` | `derived: observed exceeds permuted p95` |
| handcrafted | representation | `handcrafted` | `permutation.handcrafted` |
| handcrafted | head | `classification` | `the head named in this cell` |
| handcrafted | permuted mean | `0.3769` | `permutation.handcrafted.<head>.pr_auc_mean` |
| handcrafted | permuted p95 | `0.4891` | `permutation.handcrafted.<head>.pr_auc_p95` |
| handcrafted | permuted max | `0.5025` | `permutation.handcrafted.<head>.pr_auc_max` |
| handcrafted | observed | `0.2956` | `results.handcrafted.<head>.pr_auc` |
| handcrafted | above p95 | `no` | `derived: observed exceeds permuted p95` |
| handcrafted | representation | `handcrafted` | `permutation.handcrafted` |
| handcrafted | head | `regression` | `the head named in this cell` |
| handcrafted | permuted mean | `0.3813` | `permutation.handcrafted.<head>.pr_auc_mean` |
| handcrafted | permuted p95 | `0.4830` | `permutation.handcrafted.<head>.pr_auc_p95` |
| handcrafted | permuted max | `0.4978` | `permutation.handcrafted.<head>.pr_auc_max` |
| handcrafted | observed | `0.3050` | `results.handcrafted.<head>.pr_auc` |
| handcrafted | above p95 | `no` | `derived: observed exceeds permuted p95` |
| kmer4 | representation | `kmer4` | `permutation.kmer4` |
| kmer4 | head | `classification` | `the head named in this cell` |
| kmer4 | permuted mean | `0.3839` | `permutation.kmer4.<head>.pr_auc_mean` |
| kmer4 | permuted p95 | `0.5398` | `permutation.kmer4.<head>.pr_auc_p95` |
| kmer4 | permuted max | `0.5504` | `permutation.kmer4.<head>.pr_auc_max` |
| kmer4 | observed | `0.6212` | `results.kmer4.<head>.pr_auc` |
| kmer4 | above p95 | `yes` | `derived: observed exceeds permuted p95` |
| kmer4 | representation | `kmer4` | `permutation.kmer4` |
| kmer4 | head | `regression` | `the head named in this cell` |
| kmer4 | permuted mean | `0.3571` | `permutation.kmer4.<head>.pr_auc_mean` |
| kmer4 | permuted p95 | `0.4492` | `permutation.kmer4.<head>.pr_auc_p95` |
| kmer4 | permuted max | `0.4603` | `permutation.kmer4.<head>.pr_auc_max` |
| kmer4 | observed | `0.2954` | `results.kmer4.<head>.pr_auc` |
| kmer4 | above p95 | `no` | `derived: observed exceeds permuted p95` |
| length | representation | `length` | `permutation.length` |
| length | head | `classification` | `the head named in this cell` |
| length | permuted mean | `0.3225` | `permutation.length.<head>.pr_auc_mean` |
| length | permuted p95 | `0.4111` | `permutation.length.<head>.pr_auc_p95` |
| length | permuted max | `0.4200` | `permutation.length.<head>.pr_auc_max` |
| length | observed | `0.2599` | `results.length.<head>.pr_auc` |
| length | above p95 | `no` | `derived: observed exceeds permuted p95` |
| length | representation | `length` | `permutation.length` |
| length | head | `regression` | `the head named in this cell` |
| length | permuted mean | `0.3662` | `permutation.length.<head>.pr_auc_mean` |
| length | permuted p95 | `0.4807` | `permutation.length.<head>.pr_auc_p95` |
| length | permuted max | `0.4827` | `permutation.length.<head>.pr_auc_max` |
| length | observed | `0.3318` | `results.length.<head>.pr_auc` |
| length | above p95 | `no` | `derived: observed exceeds permuted p95` |
| physicochemical | representation | `physicochemical` | `permutation.physicochemical` |
| physicochemical | head | `classification` | `the head named in this cell` |
| physicochemical | permuted mean | `0.3450` | `permutation.physicochemical.<head>.pr_auc_mean` |
| physicochemical | permuted p95 | `0.4254` | `permutation.physicochemical.<head>.pr_auc_p95` |
| physicochemical | permuted max | `0.5364` | `permutation.physicochemical.<head>.pr_auc_max` |
| physicochemical | observed | `0.3623` | `results.physicochemical.<head>.pr_auc` |
| physicochemical | above p95 | `no` | `derived: observed exceeds permuted p95` |
| physicochemical | representation | `physicochemical` | `permutation.physicochemical` |
| physicochemical | head | `regression` | `the head named in this cell` |
| physicochemical | permuted mean | `0.3878` | `permutation.physicochemical.<head>.pr_auc_mean` |
| physicochemical | permuted p95 | `0.5344` | `permutation.physicochemical.<head>.pr_auc_p95` |
| physicochemical | permuted max | `0.5433` | `permutation.physicochemical.<head>.pr_auc_max` |
| physicochemical | observed | `0.3698` | `results.physicochemical.<head>.pr_auc` |
| physicochemical | above p95 | `no` | `derived: observed exceeds permuted p95` |

## 3. Numbers deliberately not carried into the report

| number | where it appears | why it was not used |
| --- | --- | --- |
| PR-AUC 0.7810 and weighted Spearman 0.3755 for handcrafted + RandomForest | `WRITEUP.md`, `PROGRESS.md` | pre-join-repair values printed beside a post-repair composite. `bench/results/baseline_ladder.json` gives 0.8288 and 0.2888, whose harmonic mean is the reported composite. The report uses the result file and records the defect in section 7. |
| PR-AUC 0.6830 and weighted Spearman 0.0856 for handcrafted + ExtraTrees | `WRITEUP.md`, `PROGRESS.md` | same defect; the result file gives 0.6948 and 0.1036. |
| PR-AUC 0.6427 for handcrafted + logistic regression | `WRITEUP.md` | same defect; the result file gives 0.6533, which the report uses and flags in section 3.4. |
| the frequency-normalized 3-mer family accuracy of 0.6803 | `reports/representation_diagnostics.md` | reported there as one of two encodings of a control the repository never specified. The report states that both encodings exist and quotes only the raw-counts figure of 0.6621 as the stated control, rather than choosing the encoding that suits the conclusion. |
| any score for ProtT5-XL-U50, ESM-IF or ProteinMPNN, zero-shot ESM-1v masked marginals, or ESM-1v mean-pooled | nowhere | the experiments were blocked and no value exists. No estimate, interpolation or literature-quoted figure was substituted. See Table 17. |
| any Task B benchmark score | nowhere | Task B produced no measurement; the per-variant activity values were never deposited. |
| any combined or cross-task score, and any sentence comparing a Task A number with a Task B number | nowhere | forbidden by `reports/CROSS_TASK_COMPARISON.md` and blocked in code by `schemas/task_schema.py`. |
| a maximum elementwise difference between the two ESM-2 650M embedding files | nowhere | the two builds were compared while preparing section 5.7 and agree to within float16 storage precision, but no repository file records that comparison, so the report states the dtype difference rather than quoting a magnitude it cannot source. |
| a precision-recall search-capacity null | nowhere | `bench/search_null.py` measures the composite, not precision-recall area. The gap is stated in the report rather than filled with the composite bar, which would compare two different quantities. |

