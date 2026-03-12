import sys
import os

print("🚀 LINEAR MODEL STARTED", flush=True)

# Ensure src directory is importable
sys.path.append(os.path.dirname(__file__))

import numpy as np
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score
from sklearn.linear_model import LogisticRegression

from feature_engineering import engineer_features


try:

    print("Loading engineered features...", flush=True)

    X, y, groups = engineer_features()

    X = np.asarray(X)
    y = np.asarray(y)
    groups = np.asarray(groups)

    print("Feature matrix:", X.shape, flush=True)


    model = LogisticRegression(
        max_iter=5000,
        solver="lbfgs"
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

        fam = groups[test_idx][0]

        print(f"Family: {fam:25} | F1: {score:.3f}", flush=True)

    print("\nFinal Linear LOFO F1:", np.mean(scores), flush=True)

except Exception as e:

    print("❌ ERROR OCCURRED:", e, flush=True)