# Leakage audit of the inherited tree

Seed: 42

Library versions: python 3.14.2, numpy 2.4.2, pandas 3.0.1, scipy 1.17.1, scikit-learn 1.8.0, matplotlib 3.10.8

This report characterizes inherited work. Nothing in it is a benchmark result, and no number here may be carried into a results table.

## 1. Static scan

Files that both use the competition metric and touch the label columns. SELECTION_LEAK means the metric value is fed back into a search or selection construct in the same file, so held-out labels inform a choice.

| File | Verdict | Lines where labels enter scoring | Search markers |
| --- | --- | --- | --- |
| `legacy_leaky/experiments/family_conditioned_lofo_search.py` | SELECTION_LEAK | 1300, 1319 | differential_evolution, minimize( |
| `legacy_leaky/experiments/midband_zone_repair_search.py` | SELECTION_LEAK | 157, 228 | differential_evolution, best_cls, best_score |
| `legacy_leaky/fast_opt.py` | SELECTION_LEAK | 61, 66 | differential_evolution, best_cls |
| `legacy_leaky/experiments/delta_residual_ranker.py` | UNCLEAR | 300, 343, 354 | best_cls |
| `legacy_leaky/experiments/history_meta_stack.py` | UNCLEAR | 143 | best_score |
| `legacy_leaky/experiments/lambdarank_residual_ranker.py` | UNCLEAR | 286, 346, 357 | best_cls |
| `legacy_leaky/experiments/master_pipeline.py` | UNCLEAR | 249, 332, 343 | best_cls |
| `legacy_leaky/experiments/master_pipeline_residual.py` | UNCLEAR | 58, 144, 155 | best_cls |
| `legacy_leaky/experiments/midband_repair_search.py` | UNCLEAR | 280 | best_cls, best_score |
| `legacy_leaky/experiments/nested_residual_ranker.py` | UNCLEAR | 187, 230, 241 | best_cls |
| `legacy_leaky/experiments/quantum_residual_ranker.py` | UNCLEAR | 263, 313, 324 | best_cls |
| `legacy_leaky/experiments/quantum_residual_ranker_supervised.py` | UNCLEAR | 307, 373, 385 | best_cls |
| `legacy_leaky/experiments/two_stage_objective_ranker.py` | UNCLEAR | 457, 484, 490 | best_cls |
| `evaluation/evaluate.py` | EVAL_ONLY | 110, 125, 167, 191 | none |
| `legacy_leaky/experiments/calibrated_lofo_predictions.py` | EVAL_ONLY | 792 | none |
| `legacy_leaky/experiments/clean_calibrated.py` | EVAL_ONLY | 391 | none |
| `legacy_leaky/experiments/clean_calibrated_utf8.py` | EVAL_ONLY | 391 | none |
| `legacy_leaky/experiments/foldsafe_top_region_repair.py` | EVAL_ONLY | 212, 250 | none |
| `legacy_leaky/experiments/nested_lofo_rank_repair.py` | EVAL_ONLY | 277, 320 | none |
| `legacy_leaky/experiments/quantum_branch_search.py` | EVAL_ONLY | 421 | none |
| `legacy_leaky/experiments/shuffle_labels_test.py` | EVAL_ONLY | 99 | none |
| `src/compute_cls_score.py` | EVAL_ONLY | 85 | none |
| `src/improve_weighted_spearman.py` | EVAL_ONLY | 83 | none |

Totals: EVAL_ONLY 10, SELECTION_LEAK 3, UNCLEAR 10

## 2. Free parameters fitted against the 57 labels

| Artifact | Status | Free parameters | Note |
| --- | --- | --- | --- |
| `fast_opt.py` | present | n_components + 1 | bounds vector: one weight per component plus one power exponent |
| `results/cls_search_log.json` | present | 44 | list entries |
| `results/best_weights.json` | present | 11 | loose scalar fields |
| `results/de_best_weights.json` | present | 62 | 61 weights plus 1 scalar(s): power |
| `results/component_weight_search_best.json` | absent | n/a |  |
| `results/blend_search_best.json` | absent | n/a |  |
| `temp_artifacts/results_scratch/component_weight_search_best.json` | absent | n/a |  |
| `temp_artifacts/results_scratch/blend_search_best.json` | absent | n/a |  |
| `legacy_leaky/fast_opt.py` | present | n_components + 1 | bounds vector: one weight per component plus one power exponent |

## 3. Commit ladder

20 commits carry a CLS value in the subject line. First 0.4380, last 0.9754.

| Commit index | SHA | CLS | Subject |
| --- | --- | --- | --- |
| 13 | `839f70d` | 0.4380 | 839f70d Major model improvement: feature selection + calibrated LOFO pipeline + CLS 0.438 + sanity tests |
| 25 | `1633ecd` | 0.4850 | 1633ecd CLS - 0.485 |
| 26 | `7d7e965` | 0.4900 | 7d7e965 CLS: 0.490 |
| 27 | `4f3887b` | 0.5020 | 4f3887b CLS: 0.502 |
| 28 | `f576944` | 0.5280 | f576944 CLS: 0.528 |
| 29 | `3bad349` | 0.5380 | 3bad349 CLS: 0.538 |
| 32 | `1200411` | 0.6526 | 1200411 CLS: 0.6526 |
| 33 | `4a7e72e` | 0.6528 | 4a7e72e cls:0.652790 |
| 34 | `a2269ca` | 0.6576 | a2269ca  CLS: 0.6576 with agentscope addition (failed) |
| 37 | `f46416e` | 0.8234 | f46416e CLS -  0.8234 |
| 38 | `d83b59e` | 0.8907 | d83b59e CLS - 0.8907 |
| 39 | `935e17a` | 0.9118 | 935e17a  CLS = 0.911812 |
| 40 | `0d1bb95` | 0.9256 | 0d1bb95  CLS - 0.9256 |
| 42 | `07a9351` | 0.9620 | 07a9351  CLS = 0.962015 |
| 43 | `d782d74` | 0.9660 | d782d74 CLS - 0.965997 |
| 44 | `3787941` | 0.9728 | 3787941 CLS - 0.972765 |
| 45 | `44f75d0` | 0.9737 | 44f75d0 CLS = 0.973738 |
| 46 | `1696d30` | 0.9741 | 1696d30 CLS = 0.974063 |
| 47 | `b729961` | 0.9753 | b729961 CLS - 0.975314 |
| 48 | `248a1d2` | 0.9754 | 248a1d2 CLS - 0.975372 |

Figure: `audit/figures/cls_ladder.png`

## 4. Per-component scores

Each of the stored blend components, scored on its own against the same 57 labels. These are not generalization estimates: the components were produced by pipelines already tuned on this dataset. They are shown to size the gap between any one component and the blended figure.

Components scored: 29. Best 0.6006, mean 0.4040, worst 0.0000.

| Component | CLS | PR-AUC | Weighted Spearman |
| --- | --- | --- | --- |
| `et_full_038` | 0.6006 | 0.6247 | 0.5784 |
| `esm_ratio_contrast` | 0.5900 | 0.5163 | 0.6883 |
| `esm_delta_contrast` | 0.5890 | 0.5149 | 0.6880 |
| `globalmm_l2` | 0.5888 | 0.6164 | 0.5635 |
| `proto_posneg` | 0.5856 | 0.5137 | 0.6810 |
| `both_zsig_l1` | 0.5776 | 0.6028 | 0.5544 |
| `both_zsig_l2` | 0.5753 | 0.6300 | 0.5294 |
| `esm_synth_reg` | 0.5691 | 0.5281 | 0.6170 |
| `esm_proto_density_mul` | 0.5453 | 0.4750 | 0.6401 |
| `esm_block_svc` | 0.5416 | 0.4758 | 0.6284 |
| `current605_l1` | 0.5349 | 0.6161 | 0.4726 |
| `safe_pct_l2` | 0.5319 | 0.6305 | 0.4599 |
| `hand_et_085` | 0.5155 | 0.5994 | 0.4521 |
| `svc_mi64` | 0.5028 | 0.6249 | 0.4206 |
| `stack_ridge` | 0.4929 | 0.6307 | 0.4045 |
| `safe_pct_l1` | 0.4907 | 0.6012 | 0.4145 |
| `svc_esm_interact` | 0.4661 | 0.3924 | 0.5739 |
| `baseline` | 0.4428 | 0.4841 | 0.4080 |
| `binary_manifold` | 0.4374 | 0.5282 | 0.3733 |
| `svc_hand32` | 0.4016 | 0.8699 | 0.2611 |
| `svc_hand64` | 0.3808 | 0.7625 | 0.2538 |
| `esm_active_density` | 0.2928 | 0.3550 | 0.2492 |
| `clf_only_etl2` | 0.2810 | 0.6920 | 0.1763 |
| `qsvc_hand4` | 0.1823 | 0.3684 | 0.1211 |
| `esm_interact_sim` | 0.0000 | 0.3005 | 0.0000 |
| `esm_curvature` | 0.0000 | 0.3755 | 0.0000 |
| `esm_subcluster` | 0.0000 | 0.3272 | 0.0000 |
| `esm_proto_curv_mul` | 0.0000 | 0.3378 | 0.0000 |
| `esm_proto_curv_div` | 0.0000 | 0.4385 | 0.0000 |

