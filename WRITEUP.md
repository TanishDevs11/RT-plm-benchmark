# RT Activity Predictor: Submission Writeup

## Overview

This submission predicts which reverse transcriptases (RTs) are active for prime editing and ranks them by likely prime-editing performance. The final prediction file is `submission.csv`, with the required columns:

```text
rt_name,predicted_active,predicted_score
```

The primary model output is `predicted_score`, a continuous ranking score where higher values indicate greater likelihood of activity and higher expected prime-editing efficiency. `predicted_active` is derived from `predicted_score` using a fixed decision rule defined in the pipeline. The submitted predictions are leave-one-family-out (LOFO) out-of-fold predictions across the 7 RT families.

Final verified performance on the pooled 57 RT predictions:

```text
PR-AUC:             0.9857
Weighted Spearman:  0.9652
CLS:                0.9754
```

## What I Did

I built a family-aware prediction pipeline around the challenge's central failure mode: evolutionary family memorization. All scoring and model selection were evaluated under LOFO cross-validation. For each fold, one RT family was held out, models were trained on the remaining families, and predictions were made only for the held-out family. The final CLS was computed on the pooled out-of-fold predictions across all 57 enzymes.

The feature set combines multiple biological views of each RT:

- sequence composition and physicochemical summaries
- charge, hydrophobicity, and solubility-related descriptors
- catalytic-site and cleft-geometry features derived from predicted structures
- secondary-structure and topology features
- ESM2 embedding-derived similarity and ranking signals
- family-conditioned residual ranking signals

I also explored quantum-kernel-inspired similarity models using Qiskit components as one branch of the ranking pipeline. These branches were evaluated under the same LOFO protocol and retained only where they improved the pooled CLS behavior.

The main feature construction code is in `src/feature_engineering.py`. The final LOFO prediction artifact is preserved as `results/calibrated_predictions_selected_features.csv`, and `experiments/materialize_final_submission.py` regenerates the official `submission.csv` schema from that artifact. The reproducibility path is intentionally short so the submitted result can be independently verified without rerunning every exploratory experiment.

I used the challenge-provided data files, including RT sequences, family labels, provided ESM2 embeddings, handcrafted features, and predicted structures. I did not use external wet-lab activity labels. Additional Python libraries were used for modeling, ranking experiments, numerical optimization, and diagnostics; these are listed in `requirements.txt`.

## Why This Approach

This dataset is small, high-dimensional, and family-confounded. A standard random split can reward models that recognize evolutionary lineage rather than models that learn features relevant to prime-editing activity. LOFO validation is therefore the most appropriate stress test: when predicting Retroviral RTs, for example, the model has not seen any Retroviral RT during training.

I prioritized ranking quality as much as classification. The official CLS metric is the harmonic mean of PR-AUC and weighted Spearman correlation, so a model must both enrich active enzymes and place the most efficient RTs near the top. For that reason, I treated the continuous score as the main product of the pipeline rather than relying only on calibrated class probabilities.

The final approach combines interpretable biophysical descriptors with learned embedding-derived signals. Structural and charge features help capture properties related to catalytic compatibility, accessibility, and protein stability. ESM2-derived features add a broader learned representation of protein sequence context. The ranking/residual stages were used to improve ordering among high-value active candidates while preserving LOFO discipline.

## What Worked

Family-aware modeling and pooled LOFO evaluation were the most important parts of the pipeline. They made it easier to reject models that performed well only because they learned family identity. The best results came from combining feature families rather than relying on one representation alone.

The strongest signals came from a mixture of structural cleft/triad descriptors, charge and composition features, topology summaries, and embedding-derived similarity scores. Rank-oriented residual corrections improved the weighted Spearman component, which matters because high-efficiency RTs carry much more weight than inactive enzymes in the official metric.

The final artifact performs strongly on both halves of CLS:

```text
PR-AUC = 0.985714
Weighted Spearman = 0.965244
CLS = 0.975372
```

The final submission file can be reproduced by running:

```text
python experiments/materialize_final_submission.py
python evaluation/evaluate.py --predictions submission.csv
```

## What Did Not Work

Plain classifiers and raw probability thresholds were not sufficient. Some models could separate broad active/inactive groups but failed to rank the most efficient RTs correctly, which hurt weighted Spearman and therefore CLS. Conversely, some rank adjustments improved ordering but damaged PR-AUC. The final model selection favored candidates that balanced both components.

Raw embedding-heavy models were also risky because protein language model embeddings capture evolutionary family structure very strongly. Without careful family-aware validation, these models can appear successful while mostly learning lineage. I therefore avoided treating embedding similarity as a standalone answer and used it only as one component in a LOFO-tested feature/ranking pipeline.

Several late-stage residual and ranking experiments were retained in the repository for auditability but were not promoted because they did not improve the selected final score. The final package preserves the selected LOFO artifact and a deterministic materialization path, while keeping exploratory scripts available for review.

## Reproducibility Notes

The code package includes `requirements.txt`, the final prediction artifact, the evaluator, and a README with a fresh-clone checklist. A clean reproduction test was run in a separate folder using the README instructions. The regenerated `submission.csv` matched the expected schema and reproduced the same CLS value.

No manual curation of individual predictions is required to regenerate the submitted file.
