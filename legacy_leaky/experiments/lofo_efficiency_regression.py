import sys
import os

print("LOFO Efficiency Regression")

import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import precision_recall_curve, auc
from scipy.stats import spearmanr


# -----------------------------
# Load dataset
# -----------------------------

features = pd.read_csv("data/handcrafted_features.csv")
seq = pd.read_csv("data/rt_sequences.csv")

df = features.merge(
    seq[["rt_name","active","rt_family","pe_efficiency_pct"]],
    on="rt_name"
)

# -----------------------------
# Feature matrix
# -----------------------------

X = df.drop(
    ["rt_name","active","rt_family","pe_efficiency_pct"],
    axis=1
)

y_binary = df["active"]
y_eff = df["pe_efficiency_pct"]
groups = df["rt_family"]

# -----------------------------
# Remove FoldSeek leakage
# -----------------------------

foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

print("Removed FoldSeek:",len(foldseek_cols))
print("Feature matrix:",X.shape)

# -----------------------------
# Clean features
# -----------------------------

X = X.replace([np.inf,-np.inf],np.nan)
X = X.fillna(X.median())

# -----------------------------
# Log transform efficiency
# -----------------------------

y_reg = np.log1p(y_eff)

# -----------------------------
# LOFO setup
# -----------------------------

logo = LeaveOneGroupOut()

all_scores = []
all_labels = []
all_eff = []
all_names = []

print("\nRunning LOFO regression...\n")

# -----------------------------
# LOFO loop
# -----------------------------

for train_idx, test_idx in logo.split(X,y_binary,groups):

    fam = groups.iloc[test_idx].unique()[0]
    print("Testing family:",fam)

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y_reg.iloc[train_idx]

    model = RandomForestRegressor(
        n_estimators=600,
        max_depth=12,
        random_state=42
    )

    model.fit(X_train,y_train)

    pred_log = model.predict(X_test)

    # convert back to efficiency
    pred_eff = np.expm1(pred_log)

    all_scores.extend(pred_eff)
    all_labels.extend(y_binary.iloc[test_idx])
    all_eff.extend(y_eff.iloc[test_idx])
    all_names.extend(df.iloc[test_idx]["rt_name"])


# convert arrays
all_scores = np.array(all_scores)
all_labels = np.array(all_labels)
all_eff = np.array(all_eff)

# -----------------------------
# PR-AUC
# -----------------------------

precision, recall, _ = precision_recall_curve(
    all_labels,
    all_scores
)

pr_auc = auc(recall,precision)

# -----------------------------
# Weighted Spearman
# -----------------------------

weights = all_eff + 0.1

corr,_ = spearmanr(all_scores * weights, all_eff * weights)

wspearman = max(corr,0)

# -----------------------------
# CLS
# -----------------------------

cls = 2*(pr_auc*wspearman)/(pr_auc+wspearman+1e-8)

print("\n==============================")
print("PR-AUC:",pr_auc)
print("Weighted Spearman:",wspearman)
print("CLS:",cls)
print("==============================")

# -----------------------------
# Convert to submission format
# -----------------------------

threshold = np.percentile(all_scores,70)

predicted_active = (all_scores > threshold).astype(int)

pred_df = pd.DataFrame({
    "rt_name":all_names,
    "predicted_active":predicted_active,
    "predicted_score":all_scores
})

os.makedirs("results",exist_ok=True)

pred_df.to_csv(
    "results/regression_predictions.csv",
    index=False
)

print("\nSaved â†’ results/regression_predictions.csv")
print("Finished")
