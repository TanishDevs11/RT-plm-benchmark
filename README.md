# Breaking the Retroviral Wall

Machine Learning Prediction of Reverse Transcriptase Activity for Prime Editing

**Mandrake Bioworks Open Problem #1 – Retroviral Wall Challenge**

Team: **Bio Hackers**

---

## Overview

This project develops a structure-aware machine learning pipeline to predict prime-editing activity of Reverse Transcriptases (RTs) using Leave-One-Family-Out (LOFO) cross-validation. The model integrates protein language embeddings, catalytic-site geometry, and structural interaction features to identify RT enzymes compatible with prime editing.

The pipeline is optimized for **Cross-Lineage Score (CLS)**, the official competition metric combining PR-AUC and weighted Spearman correlation.

Final Phase-1 CLS score:

**CLS = 0.477**

---

## Dataset

The dataset contains **57 experimentally validated RT enzymes** across **7 evolutionary families**.

| File                     | Description                                             |
| ------------------------ | ------------------------------------------------------- |
| rt_sequences.csv         | sequences, activity labels, efficiency values, families |
| handcrafted_features.csv | biochemical and structural descriptors                  |
| structure_features.csv   | structure-derived geometric features                    |
| esm2_embeddings.npz      | 1280-dimensional ESM-2 embeddings                       |
| structures/              | predicted RT protein structures                         |

---

## Methodology

### Validation Strategy

We use **Leave-One-Family-Out (LOFO) cross-validation**:

Train on 6 RT families
Test on the held-out family

This prevents evolutionary leakage and ensures cross-lineage generalization.

---

### Feature Sources

The model integrates multiple biologically meaningful feature groups:

**Protein language embeddings**

* ESM-2 transformer embeddings (1280 dimensions)

**Structural interaction features**

* hydrogen bonds per residue
* salt bridges
* hydrophobic contacts
* radius of gyration
* Ramachandran statistics

**Catalytic-site geometry**

* catalytic distance ratios
* triad compactness
* active-site spread
* angle proxies

---

### Feature Selection

Top 30 features selected via correlation with ranked prime-editing efficiency.

This improves stability on small-sample LOFO splits.

---

### Model
```
Model: **RandomForestRegressor**
```
Target:

```
rank(pe_efficiency_pct)
```
This directly optimizes ranking performance required for weighted Spearman in CLS.

---

## Evaluation Metric

Predictions evaluated using pooled out-of-fold CLS:

CLS = harmonic_mean(PR-AUC, weighted Spearman)

Where:

PR-AUC → active vs inactive separation
Weighted Spearman → efficiency ranking accuracy

Final performance:
```
PR-AUC = 0.6569
Weighted Spearman = 0.3748
CLS = 0.4773
```
---

## Reproducibility

Run the LOFO pipeline:

```bash
python experiments/calibrated_lofo_predictions.py
```

Then evaluate:

```bash
python evaluation/evaluate.py --predictions submission.csv
```

Expected output:

CLS ≈ 0.477

---

## Output Format

submission.csv contains:

* rt_name
* predicted_active
* predicted_score

Generated from pooled LOFO predictions across all RT families.

---

## External Validation

We additionally tested predictions on external RT sequences (HIV, MMLV, Ty1) outside the benchmark dataset to verify cross-family generalization beyond training lineages.

---

## Project Structure

```
RT-Activity-Predictor/
│
├── experiments/
│   └── calibrated_lofo_predictions.py
├── src/
│   ├── data_loader.py
│   └── feature_engineering.py
├── evaluation/
│   └── evaluate.py
├── data/
│   └── selected_features.csv
├── submission.csv
├── requirements.txt
└── README.md
```

---

## Requirements

```
numpy
pandas
scikit-learn
scipy
```

Install:

```bash
pip install -r requirements.txt
```

---

## Summary

This pipeline demonstrates that prime-editing-compatible RT enzymes can be predicted using structural and embedding-derived features while avoiding evolutionary family shortcuts.

The LOFO evaluation framework ensures robust cross-lineage generalization consistent with the Retroviral Wall Challenge objectives.
