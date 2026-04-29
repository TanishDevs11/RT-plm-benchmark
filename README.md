# RT-Activity-Predictor

Reproducible submission repo for the Mandrake Bio Retroviral Wall Challenge.

This repository contains the exact final submitted prediction artifact, the evaluation utilities used to verify it, and the main experiment scripts used during LOFO model development.

## Final submitted result

Submitted prediction files:
- `submission.csv`
- `results/calibrated_predictions_selected_features.csv`

Both files use the required challenge schema:

```text
rt_name,predicted_active,predicted_score
```

Winning artifact source:
- `results/quantum_listwise_candidate.csv`

Verified score on the submitted file:
- `PR-AUC = 0.985714`
- `Weighted Spearman = 0.965244`
- `CLS = 0.975372`

## Repository layout

- `data/`
  - challenge input files
  - ESM2 embeddings
  - predicted structures
- `src/`
  - feature engineering and helper modules
- `evaluation/`
  - official CLS evaluator
- `experiments/`
  - LOFO search scripts and late-stage refinement experiments
- `results/`
  - candidate OOF prediction files and the final submitted artifact

## Environment setup

Create and activate a Python environment, then install requirements:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Minimal reproduction of the final submission

This is the shortest path a reviewer can run to reproduce the exact final submitted files from the preserved winning artifact:

```powershell
python experiments\materialize_final_submission.py
python evaluation\evaluate.py --predictions results\calibrated_predictions_selected_features.csv
```

Expected evaluator output:

```text
PR-AUC:             0.9857
Weighted Spearman:  0.9652
CLS:                0.9754
```

## Sanity checks

Shuffle-label leakage sanity check:

```powershell
python experiments\shuffle_labels_test.py
```

Confusion matrix on the final selected file:

```powershell
python experiments\confusion_matrix_eval.py
```

## Main modeling scripts

The repository includes many exploratory scripts. The most important ones for understanding the final pipeline lineage are:

- `experiments/family_conditioned_lofo_search.py`
  - main LOFO search script for the strongest family-conditioned hybrid ensemble
- `experiments/quantum_residual_ranker.py`
  - local quantum-inspired residual ranking experiment
- `experiments/lambdarank_residual_ranker.py`
  - active-subset LambdaRank-style residual experiment
- `experiments/nested_residual_ranker.py`
  - strict nested-LOFO residual correction experiment

## Notes on reproducibility

- The final submitted predictions are preserved exactly in `results/quantum_listwise_candidate.csv`.
- `experiments/materialize_final_submission.py` copies that winning artifact into the canonical output locations:
  - `results/calibrated_predictions_selected_features.csv`
  - `submission.csv`
- `predicted_active` is derived from the top-ranked 21 RTs by `predicted_score`, matching the known active prevalence in `data/rt_sequences.csv`; `predicted_score` is unchanged from the winning artifact and is the column used by the official ranking metrics.
- All evaluation commands above are deterministic on the preserved artifact.
- The late-stage experiment scripts are also deterministic given the included data and fixed random seeds, but many of them are exploratory and were not promoted because they did not beat the protected floor.

## Submission artifact

Canonical final output paths:

- `results/calibrated_predictions_selected_features.csv`
- `submission.csv`

Writeup:

- `WRITEUP.md`

If you need to restore them from the winning artifact:

```powershell
python experiments\materialize_final_submission.py
```
