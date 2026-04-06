import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "evaluation"))

import numpy as np
import pandas as pd

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from feature_engineering import engineer_features
from evaluate import compute_cls


def run_shuffle_test():

    print("ðŸš¨ SHUFFLE LABEL SANITY TEST (Leakage Detector)")

    # --------------------------------------------------
    # Load engineered features
    # --------------------------------------------------

    X, y, groups = engineer_features()

    print("Dataset shape:", X.shape)
    print("Active count:", y.sum())

    # --------------------------------------------------
    # Load efficiency labels
    # --------------------------------------------------

    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name")
    seq = seq.loc[X.index]

    # --------------------------------------------------
    # Shuffle labels properly
    # --------------------------------------------------

    y_shuffled = y.sample(frac=1, random_state=42).reset_index(drop=True)

    print("\nLabels shuffled correctly")

    # --------------------------------------------------
    # LOFO Cross-validation
    # --------------------------------------------------

    logo = LeaveOneGroupOut()

    all_scores = []
    all_labels = []
    all_eff = []

    for train_idx, test_idx in logo.split(X, y_shuffled, groups):

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y_shuffled.iloc[train_idx]
        y_test = y_shuffled.iloc[test_idx]

        test_names = X_test.index

        # Fold-safe preprocessing

        imputer = SimpleImputer(strategy="median")
        X_train = imputer.fit_transform(X_train)
        X_test = imputer.transform(X_test)

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        # Model

        model = RandomForestClassifier(
            n_estimators=400,
            max_depth=8,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )

        model.fit(X_train, y_train)

        probs = model.predict_proba(X_test)[:, 1]

        all_scores.extend(probs)
        all_labels.extend(y_test)
        all_eff.extend(seq.loc[test_names, "pe_efficiency_pct"].values)

    # --------------------------------------------------
    # Compute CLS
    # --------------------------------------------------

    result = compute_cls(
        np.array(all_labels),
        np.array(all_scores),
        np.array(all_eff)
    )

    print("\n======================")
    print("SHUFFLED PR-AUC:", result["pr_auc"])
    print("SHUFFLED Weighted Spearman:", result["w_spearman"])
    print("SHUFFLED CLS:", result["cls"])
    print("======================")

    return result


# Allow standalone execution too
if __name__ == "__main__":
    run_shuffle_test()
