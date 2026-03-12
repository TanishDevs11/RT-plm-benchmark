# Breaking the Retroviral Wall  

## Machine Learning Prediction of Reverse Transcriptase Activity for Prime Editing

This project develops a machine learning framework to predict whether a **Reverse Transcriptase (RT)** enzyme is compatible with **Prime Editing**. The model uses **sequence-derived, structural, and biophysical features** to identify active RT candidates while avoiding shortcuts based purely on evolutionary family membership.

The work was developed as part of **Mandrake Bioworks Open Problem #1 – The Retroviral Wall Challenge**. By BioHackers Team 

---

# Project Motivation

Prime editing is one of the most precise genome editing technologies currently available. It enables targeted DNA modifications **without creating double-strand breaks**.

At the core of prime editing is a **reverse transcriptase enzyme** that copies genetic information from an RNA template into DNA. However, only a **small subset of naturally occurring RT enzymes are compatible with prime editing**.

Experimentally screening RT enzymes is expensive and time-consuming.

A computational model that predicts RT activity could:
```
- accelerate enzyme discovery
- reduce experimental costs
- identify novel RT candidates for genome editing applications
```
A major challenge is **avoiding evolutionary shortcuts**.

Many models achieve high accuracy simply by learning that certain **RT families are usually active**, which fails when predicting enzymes from **new evolutionary families**.

This project instead focuses on **learning generalizable biophysical signals that determine RT activity**.

---

# Dataset

The dataset contains **57 experimentally characterized RT enzymes** spanning **7 evolutionary families**.
```
| File | Description |
|-----|-------------|
| `rt_sequences.csv` | RT sequences, activity labels, efficiency values, and family annotations |
| `handcrafted_features.csv` | 98 structural and biochemical features |
| `esm2_embeddings.npz` | 1280-dimensional protein language model embeddings |
| `structures/` | Predicted 3D protein structures (PDB format) |
| `feature_dictionary.csv` | Description of engineered features |
```
---

# Project Goals

### Primary Objective

Predict whether an RT enzyme is **active or inactive for prime editing**.

### Secondary Objectives

- Identify **biophysical determinants** of RT activity  
- Avoid **evolutionary family shortcuts**  
- Achieve strong performance under **Leave-One-Family-Out validation**  
- Build a **fully reproducible ML pipeline**

---

# Key Challenges

## Small Dataset

Only **57 proteins** are available, which increases the risk of overfitting.
## Family Confounding

Activity is strongly correlated with evolutionary family.

Models must avoid learning:
```
Retroviral RT → active
Other families → inactive

Instead, they must detect **biophysical and structural signals**.
```
## High-Dimensional Embeddings

Protein language model embeddings contain **1280 dimensions**, requiring dimensionality reduction to avoid overfitting.

---

# Methodology

The computational pipeline consists of several stages.

---

# 1. Data Exploration

Initial dataset analysis included:
```
- class balance inspection
- family distribution analysis
- missing value detection
- correlation analysis
```
Special attention was given to **family bias in activity labels**.

---

# 2. Feature Engineering

Features were derived from multiple biological sources.

### Biophysical descriptors

Examples include:

- hydrogen bonds per residue
- hydrophobic contact counts
- salt bridge counts
- aromaticity
- protein compactness

### Structural features

Extracted from predicted 3D structures:

- solvent accessible surface area
- radius of gyration
- Ramachandran statistics
- secondary structure proportions

### Active-site geometry

Additional catalytic features were engineered:

- catalytic triad spread
- triad compactness
- catalytic distance ratios
- active-site angle proxies

These features capture **spatial organization of catalytic residues**.

---

# 3. Protein Language Model Features

Each RT protein is represented by a **1280-dimensional embedding** generated using the **ESM-2 protein language model**.

These embeddings encode:

- evolutionary signals
- structural motifs
- functional patterns

---

# 4. Dimensionality Reduction

To avoid overfitting from high-dimensional embeddings:

- **Principal Component Analysis (PCA)** was applied
- embeddings were reduced to **20 principal components**

This preserves functional signal while reducing noise.

---

# 5. Feature Selection

Feature importance was estimated using **Random Forest importance scores**.

The **top 50 most informative features** were selected to reduce dimensionality and improve model stability.

Important features included:
```
- hydrogen bonding density
- hydrophobic pocket properties
- Ramachandran statistics
- structural compactness
- embedding principal components
```
---

# 6. Model Training
```
Several machine learning models were evaluated:

| Model | Description |
|------|-------------|
| Random Forest | Nonlinear ensemble classifier |
| XGBoost | Gradient boosting tree model |
| Logistic Regression | Regularized linear classifier |
| Hybrid models | Combined handcrafted + embedding features |
```
---

# 7. Model Evaluation

Two validation strategies were used.

## Leave-One-Family-Out (LOFO)

Train on six RT families and test on the seventh.

This tests whether the model can **generalize to completely unseen evolutionary families**.

## Leave-One-Out (LOO)

Evaluates prediction performance within the full dataset.

---

## Evaluation Metrics

Primary metric:
```
**LOFO Macro F1 Score**
```
Additional metrics:
```
- Precision and Recall
- ROC-AUC
- Spearman correlation with prime editing efficiency
- Kendall rank correlation
Additional metrics:

- Precision
- Recall
- ROC-AUC
- Spearman correlation with editing efficiency
- Kendall rank correlation
```
---

# Experimental Results
```
| Model | LOFO F1 |
|------|---------|
| Random Forest (handcrafted features) | ~0.55 |
| Random Forest (ESM embeddings) | ~0.63 |
| Hybrid Model | ~0.63 |
| **Logistic Regression** | **~0.70 (best)** |

The best performing model was a **regularized logistic regression classifier**, suggesting that RT activity signals are **linearly separable in embedding space**.
```
---

# Model Interpretation

To understand model predictions, **SHAP (SHapley Additive Explanations)** analysis was performed.

SHAP revealed that the most important predictors include:
```
- hydrogen bonding density
- hydrophobic contacts
- catalytic pocket hydrophobicity
- Ramachandran structural quality
- protein embedding components
```
---

# Visualization

Two major visualization techniques were used.

### UMAP Embedding Visualization

UMAP was used to project high-dimensional feature space into two dimensions to visualize clustering of RT enzymes.
<img width="1536" height="754" alt="umap-" src="https://github.com/user-attachments/assets/5327ac22-b3ad-4477-a654-e02a05894a21" />

```
This helped reveal:

- family clustering patterns
- activity separability
- overlapping families

```
### SHAP Feature Importance

Global SHAP analysis provided interpretable insights into which features drive predictions.

<img width="2400" height="2850" alt="shap_summary_plot" src="https://github.com/user-attachments/assets/a397762c-e477-4e8f-b31d-5d47dd609ead" />

# Current Best Model:
```
Model: Logistic Regression
Features: engineered biochemical + embedding features
Validation: Leave-One-Family-Out
Performance: LOFO F1 ≈ 0.70
```
---
```
## Project Structure
RT-Activity-Predictor
│
├── data/
│ ├── rt_sequences.csv
│ ├── handcrafted_features.csv
│ ├── esm2_embeddings.npz
│ └── structures/
│
├── src/
│ ├── data_loader.py
│ ├── feature_engineering.py
│ ├── feature_selection.py
│ ├── train_lofo_model.py
│ ├── experiment_agent.py
│ ├── shap_analysis.py
│ ├── train_linear_model.py
│ ├── train_esm_model.py
│ └── train_hybrid_model.py
│
├── results/
│
├── notebooks/
│
├── requirements.txt
└── README.md
```
<img width="736" height="1408" alt="image" src="https://github.com/user-attachments/assets/69822c11-9c3d-4494-9923-c7d1a96a5ce6" />

