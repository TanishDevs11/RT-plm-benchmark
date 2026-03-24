import sys
import os

# allow imports from src/
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
import numpy as np

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import precision_recall_curve, auc
from scipy.stats import spearmanr

from feature_engineering import engineer_features


print("LOFO regression pipeline started")


# ---------------------------------------------------
# Load engineered features
# ---------------------------------------------------

X, y, groups = engineer_features()


# ---------------------------------------------------
# Load selected features safely
# ---------------------------------------------------

selected_features = pd.read_csv(
    "data/selected_features.csv",
    header=None
)[0].tolist()

selected_features = [f for f in selected_features if f in X.columns]

X = X[selected_features]


# ---------------------------------------------------
# Load RT metadata
# ---------------------------------------------------

seq = pd.read_csv("data/rt_sequences.csv")


# ---------------------------------------------------
# Prepare containers
# ---------------------------------------------------

logo = LeaveOneGroupOut()

all_scores = []
all_labels = []
all_eff = []
all_preds = []
all_names = []


# ---------------------------------------------------
# LOFO loop
# ---------------------------------------------------

for train_idx, test_idx in logo.split(X, y, groups):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train_eff = seq.iloc[train_idx]["pe_efficiency_pct"]
    y_test_eff = seq.iloc[test_idx]["pe_efficiency_pct"]

    y_test_binary = y.iloc[test_idx]


    # REGRESSION MODEL (important change)
    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train_eff)

    prob = model.predict(X_test)

    pred = (prob > 0.5).astype(int)


    all_scores.extend(prob)
    all_labels.extend(y_test_binary)
    all_preds.extend(pred)

    all_eff.extend(y_test_eff.values)
    all_names.extend(seq.iloc[test_idx]["rt_name"].values)


# ---------------------------------------------------
# Convert arrays
# ---------------------------------------------------

all_scores = np.array(all_scores)
all_labels = np.array(all_labels)
all_eff = np.array(all_eff)


# ---------------------------------------------------
# Metrics
# ---------------------------------------------------

precision, recall, _ = precision_recall_curve(
    all_labels,
    all_scores
)

pr_auc = auc(recall, precision)

corr, _ = spearmanr(all_scores, all_eff)
wspearman = max(corr, 0)

cls = 2 * (pr_auc * wspearman) / (pr_auc + wspearman + 1e-8)


print("\n==============================")
print("PR-AUC:", pr_auc)
print("Weighted Spearman:", wspearman)
print("CLS:", cls)
print("==============================")


# ---------------------------------------------------
# Save predictions safely
# ---------------------------------------------------

os.makedirs("results", exist_ok=True)


results_df = pd.DataFrame({
    "rt_name": all_names,
    "predicted_active": all_preds,
    "predicted_score": all_scores
})

results_df.to_csv(
    "results/calibrated_predictions_selected_features.csv",
    index=False
)


submission = pd.DataFrame({
    "rt_name": all_names,
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