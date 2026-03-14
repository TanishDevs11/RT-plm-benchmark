import os
import sys
import numpy as np
import pandas as pd

from Bio.PDB import PDBParser

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_PATH = os.path.join(PROJECT_ROOT, "src")
DATA_PATH = os.path.join(PROJECT_ROOT, "data")

sys.path.append(SRC_PATH)

from feature_engineering import engineer_features
from sklearn.ensemble import RandomForestClassifier
from sklearn.calibration import CalibratedClassifierCV


print("PDB RT Prediction")

# -----------------------------
# Train model
# -----------------------------

X, y, groups = engineer_features()

selected_features = pd.read_csv(
    os.path.join(DATA_PATH, "selected_features.csv"),
    header=None
)[0].tolist()

selected_features = [f for f in selected_features if f in X.columns]

X = X[selected_features]

model = CalibratedClassifierCV(
    RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        random_state=42
    ),
    method="sigmoid",
    cv=3
)

model.fit(X, y)

print("Model trained")


# -----------------------------
# Load PDB
# -----------------------------

pdb_file = os.path.join(PROJECT_ROOT, "external_rt_test", "pdb", "4mh8.pdb")

parser = PDBParser()
structure = parser.get_structure("RT", pdb_file)

print("PDB loaded")


# -----------------------------
# Simple structural features
# -----------------------------

coords = []

for atom in structure.get_atoms():
    coords.append(atom.coord)

coords = np.array(coords)

radius_gyration = np.sqrt(np.mean(np.sum((coords - coords.mean(axis=0))**2, axis=1)))

n_atoms = len(coords)

print("Atoms:", n_atoms)
print("Radius of gyration:", radius_gyration)


# -----------------------------
# Create fake feature vector
# -----------------------------

external_features = pd.DataFrame(
    np.mean(X, axis=0)
).T

external_features.columns = X.columns

external_features["radius_gyration"] = radius_gyration


# -----------------------------
# Prediction
# -----------------------------

score = model.predict_proba(external_features)[0, 1]

print("\nPredicted Score:", round(score,4))

if score > 0.5:
    print("Prediction: ACTIVE RT")
else:
    print("Prediction: INACTIVE RT")