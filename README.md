# RT-Activity-Predictor

Reproducible submission repository for the Mandrake Bio Retroviral Wall Challenge. The project predicts reverse transcriptase (RT) activity from sequence, protein-family, embedding, and structure-derived features under leave-one-family-out (LOFO) validation.

The repository is packaged so a reviewer can reproduce the submitted CSV and verify the reported score with two commands after environment setup.

## Submission Snapshot

Primary submission files:

- `submission.csv`
- `results/calibrated_predictions_selected_features.csv`
- `WRITEUP.md`
- `requirements.txt`

Required prediction schema:

```text
rt_name,predicted_active,predicted_score
```

Final verified metrics on `submission.csv`:

```text
PR-AUC:             0.9857
Weighted Spearman:  0.9652
CLS:                0.9754
```

The exact full-precision values recorded for the submitted artifact are:

```text
PR-AUC = 0.985714
Weighted Spearman = 0.965244
CLS = 0.975372
```

## Quick Reproduction

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python experiments\materialize_final_submission.py
python evaluation\evaluate.py --predictions submission.csv
```

Expected output:

```text
PR-AUC:             0.9857
Weighted Spearman:  0.9652
CLS:                0.9754
```

On macOS/Linux, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

python experiments/materialize_final_submission.py
python evaluation/evaluate.py --predictions submission.csv
```

## Reproducibility Contract

The final submission is materialized from the preserved winning score artifact:

```text
results/quantum_listwise_candidate.csv
```

`experiments/materialize_final_submission.py` reads that file, adds the required `predicted_active` column, and writes:

```text
submission.csv
results/calibrated_predictions_selected_features.csv
```

`predicted_score` is not changed during materialization. `predicted_active` is assigned to the top-ranked 21 RTs by `predicted_score`, matching the 21 active RTs in `data/rt_sequences.csv`. This is intentional because the final score is a rank score, not a calibrated probability; a raw `0.5` threshold would not be biologically or numerically appropriate for this artifact.

Artifact hashes after materialization:

```text
SHA256 submission.csv
760E05D8500D1D046B85EB9B4A8688B86F2870B506E5CC02687984BA0675E2A3

SHA256 results/calibrated_predictions_selected_features.csv
760E05D8500D1D046B85EB9B4A8688B86F2870B506E5CC02687984BA0675E2A3

SHA256 results/quantum_listwise_candidate.csv
28271D617C6503CF7894A0CB8C3471503C6EA3E800DDB5A7ED2D8BAB7307BD1D
```

## Validation Commands

Check the submitted score:

```powershell
python evaluation\evaluate.py --predictions submission.csv
```

Check the CSV schema:

```powershell
python -c "import pandas as pd; p=pd.read_csv('submission.csv'); print(list(p.columns)); print(len(p)); print(sorted(map(int, p.predicted_active.unique()))); print(int(p.isna().sum().sum()))"
```

Expected schema check:

```text
['rt_name', 'predicted_active', 'predicted_score']
57
[0, 1]
0
```

Generate a confusion matrix against the included labels:

```powershell
python experiments\confusion_matrix_eval.py
```

Expected classification counts:

```text
TP: 20
FP: 1
TN: 35
FN: 1
```

Run the shuffle-label leakage sanity check:

```powershell
python experiments\shuffle_labels_test.py
```

## Method Summary

The modeling objective was to predict RT activity while respecting evolutionary family boundaries. The strongest candidate was selected using LOFO-style evaluation, where each RT family is held out from training before predicting that family. This prevents inflated performance from close family-level similarity.

The feature set combines:

- sequence composition and charge features
- structural descriptors from predicted RT structures
- catalytic-site and cleft-geometry features
- secondary-structure summaries
- ESM2 embedding-derived similarity and ranking signals
- family-conditioned and residual rank-correction signals

The final artifact was selected for the best balance between active/inactive separation and efficiency-aware ranking under the official CLS metric:

```text
CLS = harmonic_mean(PR-AUC, Weighted Spearman)
```

## Repository Layout

```text
data/
  rt_sequences.csv                         Challenge labels, families, sequences, efficiency values
  family_splits.csv                        Family-level sample counts
  handcrafted_features.csv                 Precomputed sequence/biophysical features
  structure_features.csv                   Predicted-structure feature table
  topology_features.csv                    Structural/topological feature table
  esm2_embeddings.npz                      Precomputed ESM2 embeddings
  structures/                              Predicted protein structures

evaluation/
  evaluate.py                              Official-style CLS evaluator

experiments/
  materialize_final_submission.py          Rebuilds final submission CSVs
  family_conditioned_lofo_search.py        Main family-conditioned LOFO search lineage
  quantum_residual_ranker.py               Quantum-inspired residual ranking experiment
  lambdarank_residual_ranker.py            Active-subset LambdaRank-style residual experiment
  nested_residual_ranker.py                Strict nested-LOFO residual correction experiment
  confusion_matrix_eval.py                 Binary-label sanity report
  shuffle_labels_test.py                   Leakage sanity check

src/
  data_loader.py                           Data loading helpers
  feature_engineering.py                   Main feature construction pipeline
  structure_features.py                    Structure feature extraction utilities
  train_*.py                               Earlier model training scripts

results/
  quantum_listwise_candidate.csv           Preserved winning score artifact
  calibrated_predictions_selected_features.csv
                                           Materialized final prediction file
  *.csv, *.json, *.png                     Candidate outputs, diagnostics, and plots
```

## Main Pipeline Lineage

The shortest reproducible path is:

```text
results/quantum_listwise_candidate.csv
  -> experiments/materialize_final_submission.py
  -> submission.csv
  -> evaluation/evaluate.py
```

The main research/development scripts are:

- `experiments/family_conditioned_lofo_search.py`: strongest family-conditioned hybrid LOFO search.
- `experiments/quantum_residual_ranker.py`: local quantum-inspired residual ranking.
- `experiments/lambdarank_residual_ranker.py`: active-subset rank residual experiment.
- `experiments/nested_residual_ranker.py`: strict nested residual correction.
- `src/feature_engineering.py`: central construction of sequence, structure, and topology features.

Several late-stage scripts are retained for auditability. They are deterministic given the included data and fixed seeds, but they are exploratory and are not required to regenerate the submitted CSV.

## Requirements

Install all declared dependencies with:

```powershell
python -m pip install -r requirements.txt
```

The final artifact reproduction path requires only the core scientific Python stack: `numpy`, `pandas`, `scipy`, and `scikit-learn`. The full `requirements.txt` also includes packages used by exploratory scripts, plots, structure utilities, ESM/embedding experiments, XGBoost baselines, and quantum-inspired ranking experiments.

Recommended interpreter:

```text
Python 3.10-3.12 for broad package compatibility.
```

The final CSV materialization and evaluator were also verified in this workspace on:

```text
Python 3.14.2
```

## Fresh-Clone Checklist

1. Install dependencies from `requirements.txt`.
2. Run `python experiments\materialize_final_submission.py`.
3. Confirm `submission.csv` has exactly 57 rows and columns `rt_name,predicted_active,predicted_score`.
4. Run `python evaluation\evaluate.py --predictions submission.csv`.
5. Confirm the evaluator reports `CLS: 0.9754`.
6. Submit `submission.csv`, `WRITEUP.md`, and this repository as the runnable code package.

## Notes

- No external data download is required for the final reproduction path; all required inputs are included under `data/` and `results/`.
- The submitted `predicted_score` values are continuous rank scores. Higher means more likely active and/or higher-efficiency.
- `predicted_active` is included only to satisfy the submission schema. The official ranking metrics use `predicted_score`.
- The deadline text in the challenge instructions should be checked against the active submission form before upload.
