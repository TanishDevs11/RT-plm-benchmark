# Breaking the Retroviral Wall
## Machine Learning Prediction of Reverse Transcriptase Activity for Prime Editing

This project aims to build a machine learning model that predicts whether a **Reverse Transcriptase (RT)** enzyme can function in **Prime Editing**. The goal is to identify active RT candidates using sequence, structural, and biophysical features while avoiding shortcuts based on evolutionary family membership.

This project is developed as part of the **Mandrake Bioworks Open Problem #1: The Retroviral Wall Challenge**.

---

## Project Motivation

Prime editing is one of the most precise genome editing technologies currently available. It can introduce targeted DNA modifications without creating double-strand breaks.

At the core of prime editing is a **reverse transcriptase enzyme** that copies information from an RNA template into DNA. However, only a small subset of naturally occurring RT enzymes are compatible with prime editing.

Experimentally screening RT enzymes is slow and expensive. A computational model that can predict RT activity would significantly accelerate enzyme discovery.

The key challenge is avoiding **family memorization**. Many models achieve good accuracy simply by learning that certain evolutionary families (e.g., retroviral RTs) are more likely to be active. Such models fail when predicting enzymes from unseen families.

This project focuses on learning **generalizable biophysical signals** that determine RT activity.

---

## Dataset

The dataset contains **57 experimentally tested RT enzymes** across **7 evolutionary families**.

### Data Files

| File | Description |
|-----|-------------|
| `rt_sequences.csv` | RT sequences, activity labels, efficiency values, and family annotations |
| `handcrafted_features.csv` | 98 biophysical and structural features |
| `esm2_embeddings.npz` | 1280-dimensional protein language model embeddings |
| `structures/` | Predicted 3D structures (PDB format) for all RT enzymes |
| `feature_dictionary.csv` | Explanation of all engineered features |

---

## Project Goals

Primary objective:

- Predict whether an RT enzyme is **active or inactive for prime editing**

Secondary objectives:

- Identify **biophysical determinants of RT activity**
- Avoid **evolutionary family shortcuts**
- Achieve strong performance under **Leave-One-Family-Out (LOFO) validation**
- Maintain a **reproducible computational pipeline**

---

## Key Challenges

### Small Dataset

The dataset contains only **57 samples**, making the problem susceptible to overfitting.

### Family Confounding

Activity is strongly correlated with evolutionary family. Models must avoid simply learning these relationships.

### High Dimensional Features

ESM embeddings contain **1280 dimensions**, which must be compressed to prevent overfitting.

---

## Methodology

The modeling pipeline follows several stages.

### 1. Data Exploration

- Analyze class distribution
- Identify missing values
- Examine family bias in activity labels

### 2. Feature Engineering

Feature sources include:

- biophysical descriptors
- protein language model embeddings
- structural features extracted from PDB files

Additional structural features may include:

- catalytic residue geometry
- solvent accessible surface area
- structural compactness

### 3. Dimensionality Reduction

High-dimensional embeddings are reduced using techniques such as:

- PCA
- UMAP

This helps remove evolutionary noise while preserving functional signals.

### 4. Model Training

Candidate models include:

- Random Forest
- XGBoost
- Logistic Regression with regularization
- Ensemble models

### 5. Model Evaluation

Two validation strategies are used.

**Leave-One-Family-Out (LOFO)**  
Train on six families and test on the seventh to evaluate cross-family generalization.

**Leave-One-Out (LOO)**  
Evaluate within-distribution predictive performance.

---

## Evaluation Metrics

Primary metric:

- **LOFO Macro F1 Score**

Additional metrics:

- Precision and Recall
- ROC-AUC
- Spearman correlation with prime editing efficiency
- Kendall rank correlation

---

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
│ ├── structure_parser.py
│ ├── model_training.py
│ └── evaluation.py
│
├── notebooks/
├── results/
│
├── train_model.py
├── predict.py
├── requirements.txt
└── README.md
