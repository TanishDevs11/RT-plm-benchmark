import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve, auc
from scipy.stats import spearmanr

print("ðŸš€ Ranking Adjustment Model")

# -------------------------
# Load data
# -------------------------

features = pd.read_csv("data/handcrafted_features.csv")
seq = pd.read_csv("data/rt_sequences.csv")

df = features.merge(
    seq[["rt_name", "active", "rt_family", "pe_efficiency_pct"]],
    on="rt_name"
)

X = df.drop(["rt_name","active","rt_family","pe_efficiency_pct"], axis=1)
y = df["active"]
groups = df["rt_family"]

# -------------------------
# Remove FoldSeek leakage
# -------------------------

foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

print("Removed FoldSeek:", len(foldseek_cols))
print("Feature matrix:", X.shape)

# -------------------------
# Selected ranking features
# -------------------------

ranking_features = [
    "t75_raw",
    "hydrophobic_per_res",
    "g_factor_overall",
    "yxdd_mean_hydrophobicity",
    "pct_H"
]

ranking_features = [f for f in ranking_features if f in X.columns]

print("Ranking features used:", ranking_features)

# normalize ranking features
rank_signal = X[ranking_features].copy()

rank_signal = (rank_signal - rank_signal.mean()) / rank_signal.std()

rank_signal = rank_signal.mean(axis=1)

# -------------------------
# LOFO validation
# -------------------------

logo = LeaveOneGroupOut()

all_scores = []
all_labels = []
all_eff = []
all_preds = []
all_names = []

print("\nRunning LOFO evaluation...\n")

for train_idx, test_idx in logo.split(X, y, groups):

    fam = groups.iloc[test_idx].unique()[0]
    print("Testing family:", fam)

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        random_state=42
    )

    model.fit(X_train, y_train)

    prob = model.predict_proba(X_test)[:,1]

    # ranking adjustment
    adjustment = rank_signal.iloc[test_idx].values

    final_score = prob * (1 + 0.3 * adjustment)

    pred = (final_score > 0.5).astype(int)

    all_scores.extend(final_score)
    all_labels.extend(y_test)
    all_eff.extend(df.iloc[test_idx]["pe_efficiency_pct"])
    all_preds.extend(pred)
    all_names.extend(df.iloc[test_idx]["rt_name"])

# -------------------------
# Metrics
# -------------------------

all_scores = np.array(all_scores)
all_labels = np.array(all_labels)
all_eff = np.array(all_eff)

precision, recall, _ = precision_recall_curve(all_labels, all_scores)
pr_auc = auc(recall, precision)

corr, _ = spearmanr(all_scores, all_eff)
wspearman = max(corr, 0)

cls = 2 * (pr_auc * wspearman) / (pr_auc + wspearman + 1e-8)

print("\n==============================")
print("PR-AUC:", pr_auc)
print("Weighted Spearman:", wspearman)
print("CLS:", cls)
print("==============================")

# -------------------------
# Save predictions
# -------------------------

pred_df = pd.DataFrame({
    "rt_name": all_names,
    "predicted_active": all_preds,
    "predicted_score": all_scores
})

import os
os.makedirs("results", exist_ok=True)

pred_df.to_csv(
    "results/ranking_adjusted_predictions.csv",
    index=False
)

print("\nSaved â†’ results/ranking_adjusted_predictions.csv")
print("Finished")
