import pandas as pd

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score

from feature_engineering import engineer_features


def run_lofo_validation(model, X, y, groups):

    logo = LeaveOneGroupOut()

    all_preds = []
    all_true = []

    print("\nRunning LOFO validation...\n")

    for train_idx, test_idx in logo.split(X, y, groups):

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        family = groups.iloc[test_idx].iloc[0]

        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        f1 = f1_score(y_test, preds, zero_division=0)

        print(f"Family held out: {family}")
        print(f"Samples: {len(test_idx)}")
        print(f"F1 Score: {f1:.3f}")
        print("------------------------")

        all_preds.extend(preds)
        all_true.extend(y_test)

    overall_f1 = f1_score(all_true, all_preds)

    print("\nOverall LOFO F1:", overall_f1)

    return overall_f1


def train_lofo():

    # Load engineered features
    X, y, groups = engineer_features()

    # Baseline model
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        random_state=42
    )

    score = run_lofo_validation(model, X, y, groups)

    return score


if __name__ == "__main__":
    train_lofo()