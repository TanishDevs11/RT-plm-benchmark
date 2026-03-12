import sys
print("🚀 ESM MODEL SCRIPT STARTED", flush=True)

import numpy as np
import pandas as pd

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from data_loader import load_data


print("Loading dataset...", flush=True)

df = load_data()

print("Dataset shape:", df.shape, flush=True)


# -----------------------------
# Target + groups
# -----------------------------

y = df["active"].values
groups = df["rt_family"]


# -----------------------------
# Drop non-feature columns
# -----------------------------

drop_cols = [
    "active",
    "rt_name",
    "sequence",
    "rt_family",
    "pe_efficiency_pct"
]

feature_df = df.drop(columns=drop_cols)


# -----------------------------
# Extract LAST 1280 columns
# -----------------------------

print("Extracting last 1280 columns as ESM embeddings...", flush=True)

X = feature_df.iloc[:, -1280:].values

print("Embedding matrix shape:", X.shape, flush=True)


# -----------------------------
# Scale embeddings
# -----------------------------

scaler = StandardScaler()

X = scaler.fit_transform(X)


# -----------------------------
# Model
# -----------------------------

model = RandomForestClassifier(
    n_estimators=400,
    max_depth=8,
    random_state=42
)

logo = LeaveOneGroupOut()

scores = []

print("\nRunning LOFO validation...\n", flush=True)


for train_idx, test_idx in logo.split(X, y, groups):

    X_train = X[train_idx]
    X_test = X[test_idx]

    y_train = y[train_idx]
    y_test = y[test_idx]

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    score = f1_score(y_test, preds, average="macro")

    scores.append(score)

    fam = groups.iloc[test_idx].unique()[0]

    print(f"Family: {fam:25} | F1: {score:.3f}", flush=True)


print("\nFinal ESM LOFO F1:", np.mean(scores), flush=True)