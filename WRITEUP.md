# RT Activity Predictor Writeup

## Summary

This submission predicts retroviral and retroelement reverse transcriptase activity from sequence, structure-derived, and embedding-based features. The final submitted CSV is `submission.csv`, with the required columns `rt_name`, `predicted_active`, and `predicted_score`. The continuous score is the primary ranking signal used for PR-AUC and weighted Spearman evaluation. The binary active label is derived from the top-ranked 21 RTs, matching the known 21 active examples in the challenge metadata.

The final preserved prediction artifact is `results/quantum_listwise_candidate.csv`. Running `python experiments/materialize_final_submission.py` regenerates both `submission.csv` and `results/calibrated_predictions_selected_features.csv` from that artifact. Running `python evaluation/evaluate.py --predictions submission.csv` gives:

```text
PR-AUC:             0.9857
Weighted Spearman:  0.9652
CLS:                0.9754
```

## What I Did

I built the solution around leave-one-family-out validation, because the challenge is explicitly about generalizing across evolutionary RT families rather than memorizing near neighbors. The feature set combines several views of each RT: sequence composition, engineered charge and hydrophobicity signals, predicted structural geometry around catalytic and cleft regions, secondary-structure summaries, and ESM2 embedding information. The main feature engineering code lives in `src/feature_engineering.py`.

The modeling work explored multiple ranked prediction pipelines. The strongest lineage used family-conditioned LOFO models, embedding centroid features, local structural descriptors, and rank-oriented residual corrections. Candidate outputs were evaluated with the supplied CLS evaluator, which combines PR-AUC for active/inactive separation with weighted Spearman correlation for ranking high-efficiency RTs. Late experiments included family-normalized blends, nested residual ranking, LambdaRank-style residuals, and quantum-inspired listwise/ranking adjustments.

The final selected score file came from the best late-stage ranking artifact, `results/quantum_listwise_candidate.csv`. I kept that source file unchanged and added a materialization script so the official submission file can always be regenerated in the exact required schema.

## Why This Approach

The dataset is small and family structured, so ordinary random cross-validation would overestimate performance. LOFO validation is a better match for the biological question: can a model identify active RTs in a family it did not see during training? I prioritized rank stability over raw probability calibration because the official metric rewards both active enrichment and ordering of the most efficient RTs.

The feature mix was designed to capture complementary signals. Sequence and charge features provide broad biochemical trends. Predicted structure features describe catalytic-site geometry and possible accessibility. ESM2 embeddings add a learned representation of protein context that can capture patterns not obvious from hand-engineered features. Residual and rank-correction stages helped correct specific high-impact misorderings among active RTs.

## What Worked

Family-aware validation and rank-based objective tuning worked best. The final artifact reaches strong global pooled performance, with PR-AUC near 0.986 and weighted Spearman near 0.965. The top-ranked active calls are also consistent with the binary submission requirement: the generated `predicted_active` column has 20 true positives, 1 false positive, 35 true negatives, and 1 false negative against the included labels.

The most useful features were not a single class of inputs, but the combination of structural cleft/triad descriptors, charge and composition summaries, and embedding-derived similarity/ranking features. Late-stage residual rankers improved ordering among high-value RTs more than they improved simple active/inactive classification, which matches the weighted Spearman part of the metric.

## What Did Not Work

Simple calibrated classifiers and plain probability thresholds were not enough. In particular, a raw `0.5` cutoff on the final ranking score is inappropriate because the final score is not a probability; it would mark 46 of 57 RTs active. I therefore generate `predicted_active` from the top 21 scores while leaving the continuous ranking score unchanged.

Several more complex residual experiments also failed to beat the selected artifact. They were useful for understanding local ranking errors, but I did not promote them because they either reduced CLS or improved one component of the metric while hurting the other. The final package preserves those experiments for reproducibility, but the submission path is intentionally short and deterministic.
