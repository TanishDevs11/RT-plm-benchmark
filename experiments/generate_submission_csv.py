import sys
import os

# ------------------------------------------------
# Setup project paths (robust import fix)
# ------------------------------------------------

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
DATA_PATH = os.path.join(PROJECT_ROOT, "data")

sys.path.append(SRC_PATH)

# ------------------------------------------------

import pandas as pd
from feature_engineering import engineer_features
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV


print("Generating submission.csv ...")

# Load dataset
X, y, groups = engineer_features()

# Train model
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

# Predict scores
scores = model.predict_proba(X)[:, 1]

# Load RT names
rt_names = pd.read_csv(os.path.join(DATA_PATH, "rt_sequences.csv"))["rt_name"]

submission = pd.DataFrame({
    "rt_name": rt_names,
    "predicted_score": scores
})

submission.to_csv(os.path.join(PROJECT_ROOT, "submission.csv"), index=False)

print("submission.csv created successfully! ✅")