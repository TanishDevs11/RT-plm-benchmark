import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pandas as pd

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_recall_curve, auc
from scipy.stats import spearmanr

from feature_engineering import engineer_features


print("🚨 SHUFFLE LABEL SANITY TEST")


# ----------------------------
# Load engineered features
# ----------------------------

X, y, groups = engineer_features()

print("Dataset shape:", X.shape)
print("Active count:", y.sum())


# ----------------------------
# Shuffle labels
# ----------------------------

y_shuffled = y.sample(frac=1, random_state=42).reset_index(drop=True)

print("\nLabels shuffled")


# ----------------------------
# LOFO
# ----------------------------

logo = LeaveOneGroupOut()

all_scores = []
all_labels = []

for train_idx, test_idx in logo.split(X, y_shuffled, groups):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y_shuffled.iloc[train_idx]
    y_test = y_shuffled.iloc[test_idx]

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        random_state=42
    )

    model.fit(X_train, y_train)

    prob = model.predict_proba(X_test)[:,1]

    all_scores.extend(prob)
    all_labels.extend(y_test)


all_scores = np.array(all_scores)
all_labels = np.array(all_labels)


# ----------------------------
# PR-AUC
# ----------------------------

precision, recall, _ = precision_recall_curve(
    all_labels,
    all_scores
)

pr_auc = auc(recall, precision)


print("\n======================")
print("SHUFFLED PR-AUC:", pr_auc)
print("======================")