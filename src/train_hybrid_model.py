import sys
print("🚀 HYBRID MODEL STARTED", flush=True)

import numpy as np
import pandas as pd

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier

from feature_engineering import engineer_features
from data_loader import load_data


# --------------------------------
# Load engineered features
# --------------------------------

print("Loading engineered features...", flush=True)

X_handcrafted, y, groups = engineer_features()

# ensure numpy compatibility
X_handcrafted = np.array(X_handcrafted)
y = np.array(y)

print("Handcrafted feature matrix:", X_handcrafted.shape, flush=True)


# --------------------------------
# Load raw dataset
# --------------------------------

print("Loading raw dataset...", flush=True)

df = load_data()

print("Dataset shape:", df.shape, flush=True)


# --------------------------------
# Extract ESM embeddings
# --------------------------------

print("Extracting ESM embeddings...", flush=True)

drop_cols = [
    "active",
    "rt_name",
    "sequence",
    "rt_family",
    "pe_efficiency_pct"
]

feature_df = df.drop(columns=drop_cols)

# last 1280 columns = embeddings
X_esm = feature_df.iloc[:, -1280:].to_numpy()

print("ESM matrix:", X_esm.shape, flush=True)


# --------------------------------
# Combine features
# --------------------------------

print("Combining features...", flush=True)

X_combined = np.concatenate([X_handcrafted, X_esm], axis=1)

print("Combined matrix:", X_combined.shape, flush=True)


# --------------------------------
# LOFO validation
# --------------------------------

logo = LeaveOneGroupOut()

scores = []

print("\nRunning LOFO validation...\n", flush=True)

for train_idx, test_idx in logo.split(X_combined, y, groups):

    X_train = X_combined[train_idx]
    X_test = X_combined[test_idx]

    y_train = y[train_idx]
    y_test = y[test_idx]

    model = RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    score = f1_score(y_test, preds, average="macro")

    scores.append(score)

    fam = groups.iloc[test_idx].unique()[0]

    print(f"Family: {fam:25} | F1: {score:.3f}", flush=True)


# --------------------------------
# Final score
# --------------------------------

print("\nFinal HYBRID LOFO F1:", np.mean(scores), flush=True)