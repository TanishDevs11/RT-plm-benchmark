import sys
import os

# allow imports from src/
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import precision_recall_curve, auc
from scipy.stats import spearmanr

from feature_engineering import engineer_features


print("🚀 Calibrated LOFO pipeline started")


# ---------------------------------------------------
# Load engineered features
# ---------------------------------------------------

print("Loading engineered features...")

X, y, groups = engineer_features()

print("Initial feature matrix:", X.shape)


# ---------------------------------------------------
# Load selected features
# ---------------------------------------------------

selected_features = pd.read_csv(
    "data/selected_features.csv",
    header=None
)[0].tolist()

print("Selected feature count:", len(selected_features))


# ---------------------------------------------------
# Remove features that don't exist
# ---------------------------------------------------

available_features = [f for f in selected_features if f in X.columns]
missing_features = [f for f in selected_features if f not in X.columns]

print("Available features:", len(available_features))
print("Missing features:", missing_features)

X = X[available_features]

print("Final feature matrix:", X.shape)


# ---------------------------------------------------
# Load RT metadata
# ---------------------------------------------------

seq = pd.read_csv("data/rt_sequences.csv")


# ---------------------------------------------------
# LOFO setup
# ---------------------------------------------------

logo = LeaveOneGroupOut()

all_scores = []
all_labels = []
all_eff = []
all_preds = []
all_names = []

print("\nRunning LOFO predictions...\n")


# ---------------------------------------------------
# LOFO loop
# ---------------------------------------------------

for train_idx, test_idx in logo.split(X, y, groups):

    fam = groups.iloc[test_idx].unique()[0]
    print("Testing family:", fam)

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y.iloc[train_idx]
    y_test = y.iloc[test_idx]

    base_model = RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        random_state=42
    )

    model = CalibratedClassifierCV(
        base_model,
        method="sigmoid",
        cv=3
    )

    model.fit(X_train, y_train)

    prob = model.predict_proba(X_test)[:, 1]

    pred = (prob > 0.5).astype(int)

    all_scores.extend(prob)
    all_labels.extend(y_test)
    all_preds.extend(pred)

    all_eff.extend(seq.iloc[test_idx]["pe_efficiency_pct"])
    all_names.extend(seq.iloc[test_idx]["rt_name"])


# ---------------------------------------------------
# Convert arrays
# ---------------------------------------------------

all_scores = np.array(all_scores)
all_labels = np.array(all_labels)
all_eff = np.array(all_eff)


# ---------------------------------------------------
# PR-AUC
# ---------------------------------------------------

precision, recall, _ = precision_recall_curve(
    all_labels,
    all_scores
)

pr_auc = auc(recall, precision)


# ---------------------------------------------------
# Weighted Spearman
# ---------------------------------------------------

corr, _ = spearmanr(all_scores, all_eff)

wspearman = max(corr, 0)


# ---------------------------------------------------
# CLS
# ---------------------------------------------------

cls = 2 * (pr_auc * wspearman) / (pr_auc + wspearman + 1e-8)


print("\n==============================")
print("PR-AUC:", pr_auc)
print("Weighted Spearman:", wspearman)
print("CLS:", cls)
print("==============================")


# ---------------------------------------------------
# Save predictions
# ---------------------------------------------------

os.makedirs("results", exist_ok=True)

pred_df = pd.DataFrame({
    "rt_name": all_names,
    "predicted_active": all_preds,
    "predicted_score": all_scores
})

pred_df.to_csv(
    "results/calibrated_predictions_selected_features.csv",
    index=False
)

print("\nSaved predictions → results/calibrated_predictions_selected_features.csv")
print("✅ Finished")