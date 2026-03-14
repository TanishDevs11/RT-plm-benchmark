import sys
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
DATA_PATH = os.path.join(PROJECT_ROOT, "data")

sys.path.append(SRC_PATH)

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV

from feature_engineering import engineer_features


print("🔬 External RT validation test")


# -----------------------------
# Load dataset features
# -----------------------------

X, y, groups = engineer_features()

print("Dataset features:", X.shape)


# -----------------------------
# Load selected features
# -----------------------------

selected_features = pd.read_csv(
    os.path.join(DATA_PATH,"selected_features.csv"),
    header=None
)[0].tolist()

selected_features = [f for f in selected_features if f in X.columns]

X = X[selected_features]

print("Selected feature matrix:", X.shape)


# -----------------------------
# Train model
# -----------------------------

model = CalibratedClassifierCV(
    RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        random_state=42
    ),
    method="sigmoid",
    cv=3
)

model.fit(X,y)

print("Model trained")


# -----------------------------
# Simulate external RT
# -----------------------------

# For now we reuse a real active RT
external_sample = X.iloc[[10]]

score = model.predict_proba(external_sample)[0,1]

print("\nExternal RT predicted score:",round(score,4))

if score > 0.5:
    print("Prediction: ACTIVE RT")
else:
    print("Prediction: INACTIVE RT")