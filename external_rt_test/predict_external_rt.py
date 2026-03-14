import sys
import os

# ------------------------------------------------
# Setup project paths (works from any directory)
# ------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
DATA_PATH = os.path.join(PROJECT_ROOT, "data")

sys.path.append(SRC_PATH)

import pandas as pd
import numpy as np

from feature_engineering import engineer_features
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV


print("🔬 External RT Prediction Test")

# ------------------------------------------------
# Load engineered features
# ------------------------------------------------

print("\nLoading engineered features...")

X, y, groups = engineer_features()

print("Initial feature matrix:", X.shape)


# ------------------------------------------------
# Load selected features
# ------------------------------------------------

selected_feature_file = os.path.join(DATA_PATH, "selected_features.csv")

if os.path.exists(selected_feature_file):

    print("\nLoading selected features...")

    selected_features = pd.read_csv(
        selected_feature_file,
        header=None
    )[0].tolist()

    print("Selected feature count:", len(selected_features))

    # keep only features present
    selected_features = [f for f in selected_features if f in X.columns]

    X = X[selected_features]

    print("Final feature matrix:", X.shape)

else:

    print("\n⚠ selected_features.csv not found")
    print("Using all features instead")


# ------------------------------------------------
# Train calibrated model
# ------------------------------------------------

print("\nTraining calibrated model...")

base_model = RandomForestClassifier(
    n_estimators=400,
    max_depth=8,
    random_state=42,
    n_jobs=-1
)

model = CalibratedClassifierCV(
    base_model,
    method="sigmoid",
    cv=3
)

model.fit(X, y)

print("Model training complete")


# ------------------------------------------------
# Example prediction
# ------------------------------------------------

print("\nRunning example prediction...")

sample = X.iloc[[0]]

score = model.predict_proba(sample)[0, 1]

print("\nPredicted Score:", round(score, 4))

if score > 0.5:
    print("Prediction: ACTIVE RT")
else:
    print("Prediction: INACTIVE RT")


print("\n🧪 External RT test completed successfully")