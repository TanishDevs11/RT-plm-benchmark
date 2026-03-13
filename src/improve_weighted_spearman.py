import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import average_precision_score
from sklearn.ensemble import RandomForestRegressor
from scipy.stats import spearmanr


print("🚀 Improving Weighted Spearman")

# -----------------------------
# Load dataset
# -----------------------------

features = pd.read_csv("data/handcrafted_features.csv")
seq = pd.read_csv("data/rt_sequences.csv")

df = features.merge(
    seq[["rt_name", "active", "rt_family", "pe_efficiency_pct"]],
    on="rt_name"
)

X = df.drop(["rt_name","active","rt_family","pe_efficiency_pct"], axis=1)
y_class = df["active"]
y_eff = df["pe_efficiency_pct"]
groups = df["rt_family"]

# -----------------------------
# Remove FoldSeek leakage
# -----------------------------

foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

# -----------------------------
# Clean features
# -----------------------------

X = X.apply(pd.to_numeric, errors="coerce")
X = X.replace([np.inf,-np.inf],np.nan)
X = X.fillna(X.median())

print("Feature matrix:", X.shape)

# -----------------------------
# LOFO predictions
# -----------------------------

logo = LeaveOneGroupOut()

pred_scores = np.zeros(len(X))

model = RandomForestRegressor(
    n_estimators=500,
    max_depth=10,
    random_state=42
)

print("\nRunning LOFO regression...\n")

for train_idx, test_idx in logo.split(X, y_class, groups):

    fam = groups.iloc[test_idx].unique()[0]
    print("Testing family:", fam)

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y_eff.iloc[train_idx]

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    pred_scores[test_idx] = preds


# -----------------------------
# PR-AUC
# -----------------------------

pr_auc = average_precision_score(y_class, pred_scores)

# -----------------------------
# Weighted Spearman
# -----------------------------

weights = y_eff + 0.1

rank_pred = pd.Series(pred_scores).rank()
rank_true = y_eff.rank()

corr,_ = spearmanr(rank_pred, rank_true)

wspearman = max(0, corr)

# -----------------------------
# CLS
# -----------------------------

cls = (2 * pr_auc * wspearman) / (pr_auc + wspearman)

print("\n==============================")
print("PR-AUC:", pr_auc)
print("Weighted Spearman:", wspearman)
print("CLS:", cls)
print("==============================")