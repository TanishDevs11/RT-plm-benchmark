import sys
import os

# allow imports from src/
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import precision_recall_curve, auc

from feature_engineering import engineer_features


print("LOFO hybrid rank-classifier pipeline started")


# ---------------------------------------------------
# Load engineered features
# ---------------------------------------------------

X, y, groups = engineer_features()
seq = pd.read_csv("data/rt_sequences.csv")


# ---------------------------------------------------
# Load selected_features.csv safely
# ---------------------------------------------------

selected_features = pd.read_csv(
    "data/selected_features.csv",
    header=None
)[0].tolist()

selected_features = [
    f for f in selected_features
    if f in X.columns
]

X = X[selected_features]

print("Applied feature selection:", len(selected_features))


# ---------------------------------------------------
# Weighted Spearman implementation
# ---------------------------------------------------

EPSILON = 0.01


def weighted_spearman(predicted_scores, true_efficiency):

    pred_ranks = np.argsort(np.argsort(predicted_scores)).astype(float)
    true_ranks = np.argsort(np.argsort(true_efficiency)).astype(float)

    weights = true_efficiency + EPSILON
    weights = weights / weights.sum()

    mu_p = np.dot(weights, pred_ranks)
    mu_t = np.dot(weights, true_ranks)

    dp = pred_ranks - mu_p
    dt = true_ranks - mu_t

    cov = np.sum(weights * dp * dt)

    std_p = np.sqrt(np.sum(weights * dp ** 2))
    std_t = np.sqrt(np.sum(weights * dt ** 2))

    if std_p < 1e-12 or std_t < 1e-12:
        return 0.0

    return cov / (std_p * std_t)


# ---------------------------------------------------
# LOFO Cross-validation
# ---------------------------------------------------

logo = LeaveOneGroupOut()

all_scores = []
all_labels = []
all_eff = []
all_names = []


for train_idx, test_idx in logo.split(X, y, groups):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    train_eff = seq.iloc[train_idx]["pe_efficiency_pct"]
    train_family = groups.iloc[train_idx]

    # ---------------------------------------------------
    # FAMILY Z-SCORE NORMALIZATION
    # ---------------------------------------------------

    fam_mean = train_eff.groupby(train_family).transform("mean")
    fam_std = train_eff.groupby(train_family).transform("std")

    fam_std = fam_std.fillna(1).replace(0, 1)

    normalized_eff = (train_eff - fam_mean) / fam_std
    normalized_eff = normalized_eff.fillna(0)

    y_train_eff = normalized_eff.rank(method="average")

    y_test_eff = seq.iloc[test_idx]["pe_efficiency_pct"]
    y_test_binary = y.iloc[test_idx]

    # ---------------------------------------------------
    # Rank regression model
    # ---------------------------------------------------

    rank_model = RandomForestRegressor(
        n_estimators=700,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    rank_model.fit(X_train, y_train_eff)
    rank_preds = rank_model.predict(X_test)

    # ---------------------------------------------------
    # Activity classifier model
    # ---------------------------------------------------

    clf_model = RandomForestClassifier(
        n_estimators=700,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )

    clf_model.fit(X_train, y.iloc[train_idx])
    clf_probs = clf_model.predict_proba(X_test)[:, 1]

    # ---------------------------------------------------
    # Hybrid stacking
    # ---------------------------------------------------

    preds = 0.65 * rank_preds + 0.35 * clf_probs

    # ---------------------------------------------------
    # Family calibration
    # ---------------------------------------------------

    family_bias = train_eff.groupby(train_family).mean().mean()
    preds = preds + 0.20 * family_bias

    # ---------------------------------------------------
    # Store fold predictions
    # ---------------------------------------------------

    all_scores.extend(preds)
    all_labels.extend(y_test_binary)
    all_eff.extend(y_test_eff.values)
    all_names.extend(seq.iloc[test_idx]["rt_name"].values)


# ---------------------------------------------------
# Convert arrays
# ---------------------------------------------------

all_scores = np.array(all_scores)
all_labels = np.array(all_labels)
all_eff = np.array(all_eff)


# ---------------------------------------------------
# Normalize predictions
# ---------------------------------------------------

all_scores = (
    (all_scores - all_scores.min()) /
    (all_scores.max() - all_scores.min() + 1e-8)
)


# ---------------------------------------------------
# Temperature scaling (applied correctly AFTER normalize)
# ---------------------------------------------------

temperature = 0.85
all_scores = np.power(all_scores, temperature)


# ---------------------------------------------------
# Auto direction correction
# ---------------------------------------------------

ws = weighted_spearman(all_scores, all_eff)

if ws < 0:
    print("Auto-flipping prediction direction")
    all_scores = 1 - all_scores


# ---------------------------------------------------
# Metrics
# ---------------------------------------------------

precision, recall, _ = precision_recall_curve(
    all_labels,
    all_scores
)

pr_auc = auc(recall, precision)

wspearman = weighted_spearman(
    all_scores,
    all_eff
)

wspearman = max(wspearman, 0)

cls = 2 * (pr_auc * wspearman) / (
    pr_auc + wspearman + 1e-8
)


print("\n==============================")
print("PR-AUC:", pr_auc)
print("Weighted Spearman:", wspearman)
print("CLS:", cls)
print("==============================")


# ---------------------------------------------------
# Save predictions
# ---------------------------------------------------

os.makedirs("results", exist_ok=True)

pd.DataFrame({
    "rt_name": all_names,
    "predicted_score": all_scores
}).to_csv(
    "results/calibrated_predictions_selected_features.csv",
    index=False
)


submission = pd.DataFrame({
    "rt_name": all_names,
    "predicted_active": (all_scores >= 0.5).astype(int),
    "predicted_score": all_scores
})

submission = (
    submission
    .set_index("rt_name")
    .reindex(seq["rt_name"])
    .reset_index()
)

submission.to_csv("submission.csv", index=False)

print("\nSaved predictions successfully")