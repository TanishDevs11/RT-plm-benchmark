import pandas as pd
from itertools import product

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score

from feature_engineering import engineer_features


def run_lofo(model, X, y, groups):

    logo = LeaveOneGroupOut()

    all_preds = []
    all_true = []

    for train_idx, test_idx in logo.split(X, y, groups):

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        all_preds.extend(preds)
        all_true.extend(y_test)

    return f1_score(all_true, all_preds)


def hyperparameter_search():

    print("Loading features...")

    X, y, groups = engineer_features()

    print("Feature matrix:", X.shape)

    # -----------------------------
    # Hyperparameter grid
    # -----------------------------

    n_estimators = [200, 400, 600]
    max_depth = [4, 6, 8]
    min_samples_leaf = [1, 2, 3]
    max_features = ["sqrt", "log2"]

    param_grid = list(product(
        n_estimators,
        max_depth,
        min_samples_leaf,
        max_features
    ))

    print("\nTotal configurations:", len(param_grid))

    results = []

    best_score = 0
    best_params = None

    # -----------------------------
    # Search loop
    # -----------------------------

    for i, params in enumerate(param_grid):

        n_est, depth, leaf, feat = params

        model = RandomForestClassifier(
            n_estimators=n_est,
            max_depth=depth,
            min_samples_leaf=leaf,
            max_features=feat,
            random_state=42
        )

        score = run_lofo(model, X, y, groups)

        print(
            f"Run {i+1}/{len(param_grid)} | "
            f"trees={n_est}, depth={depth}, leaf={leaf}, feat={feat} "
            f"→ F1={score:.4f}"
        )

        results.append({
            "n_estimators": n_est,
            "max_depth": depth,
            "min_samples_leaf": leaf,
            "max_features": feat,
            "f1_score": score
        })

        if score > best_score:

            best_score = score
            best_params = params

    # -----------------------------
    # Save results
    # -----------------------------

    results_df = pd.DataFrame(results)

    results_df.to_csv(
        "data/hyperparameter_results.csv",
        index=False
    )

    print("\n=========================")
    print("BEST CONFIGURATION")
    print("=========================")

    print("Trees:", best_params[0])
    print("Depth:", best_params[1])
    print("Min leaf:", best_params[2])
    print("Max features:", best_params[3])
    print("Best LOFO F1:", best_score)


if __name__ == "__main__":

    hyperparameter_search()