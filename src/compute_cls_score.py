import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import average_precision_score
from sklearn.ensemble import RandomForestClassifier
from scipy.stats import spearmanr


print("🚀 Computing Mandrake CLS Score")

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
y = df["active"]
groups = df["rt_family"]
eff = df["pe_efficiency_pct"]

# -----------------------------
# Remove FoldSeek leakage
# -----------------------------

foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

print("Removed FoldSeek:", len(foldseek_cols))

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

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=8,
    random_state=42
)

print("\nRunning LOFO predictions...\n")

for train_idx, test_idx in logo.split(X, y, groups):

    fam = groups.iloc[test_idx].unique()[0]
    print("Testing family:", fam)

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]

    model.fit(X_train, y_train)

    probs = model.predict_proba(X_test)[:,1]

    pred_scores[test_idx] = probs


# -----------------------------
# PR-AUC
# -----------------------------

pr_auc = average_precision_score(y, pred_scores)

print("\nPR-AUC:", pr_auc)


# -----------------------------
# Weighted Spearman
# -----------------------------

weights = eff + 0.1

rank_pred = pd.Series(pred_scores).rank()
rank_true = eff.rank()

corr,_ = spearmanr(rank_pred, rank_true)

wspearman = corr

if wspearman < 0:
    wspearman = 0

print("Weighted Spearman:", wspearman)


# -----------------------------
# CLS Score
# -----------------------------

cls = (2 * pr_auc * wspearman) / (pr_auc + wspearman)

print("\n==============================")
print("CLS SCORE:", cls)
print("==============================")
