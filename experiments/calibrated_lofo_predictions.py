import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    ExtraTreesClassifier,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(os.path.join(ROOT, "src"))
sys.path.append(os.path.join(ROOT, "evaluation"))

from evaluate import compute_cls
from feature_engineering import engineer_features


print("LOFO hybrid rank-classifier pipeline started")


def zsig_by_train(train_scores, test_scores):
    train_scores = np.asarray(train_scores, dtype=float)
    test_scores = np.asarray(test_scores, dtype=float)

    mu = train_scores.mean()
    sigma = train_scores.std() + 1e-8
    z_scores = (test_scores - mu) / sigma

    return 1.0 / (1.0 + np.exp(-z_scores))


def rankpct_by_train(train_scores, test_scores):
    train_scores = np.asarray(train_scores, dtype=float)
    test_scores = np.asarray(test_scores, dtype=float)

    train_sorted = np.sort(train_scores)
    pos = np.searchsorted(train_sorted, test_scores, side="right")

    return pos / max(len(train_sorted), 1)


def run_hybrid_lofo(X, y, groups, seq):
    logo = LeaveOneGroupOut()

    all_scores = []
    all_names = []

    for train_idx, test_idx in logo.split(X, y, groups):
        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train_bin = y.iloc[train_idx]
        y_train_eff = seq.loc[X_train.index, "pe_efficiency_pct"]
        y_train_eff_norm = (
            y_train_eff - y_train_eff.mean()
        ) / (y_train_eff.std() + 1e-8)

        imputer = SimpleImputer(strategy="median")
        X_train = imputer.fit_transform(X_train)
        X_test = imputer.transform(X_test)

        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)

        baseline_reg = RandomForestRegressor(
            n_estimators=700,
            max_depth=8,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=1,
        )
        baseline_clf = RandomForestClassifier(
            n_estimators=700,
            max_depth=8,
            min_samples_leaf=2,
            class_weight="balanced_subsample",
            max_features="sqrt",
            random_state=42,
            n_jobs=1,
        )
        current_reg = RandomForestRegressor(
            n_estimators=900,
            max_depth=8,
            min_samples_leaf=2,
            max_features="log2",
            random_state=42,
            n_jobs=1,
        )
        current_clf = ExtraTreesClassifier(
            n_estimators=1200,
            max_depth=None,
            min_samples_leaf=1,
            class_weight="balanced",
            max_features="sqrt",
            random_state=42,
            n_jobs=1,
        )

        baseline_reg.fit(X_train, y_train_eff_norm)
        baseline_clf.fit(X_train, y_train_bin)
        current_reg.fit(X_train, y_train_eff_norm)
        current_clf.fit(X_train, y_train_bin)

        baseline_rank_train = baseline_reg.predict(X_train)
        baseline_rank_test = zsig_by_train(
            baseline_rank_train,
            baseline_reg.predict(X_test),
        )
        baseline_clf_train = baseline_clf.predict_proba(X_train)[:, 1]
        baseline_clf_test = zsig_by_train(
            baseline_clf_train,
            baseline_clf.predict_proba(X_test)[:, 1],
        )
        baseline_score = 0.67 * baseline_rank_test + 0.33 * baseline_clf_test

        current_rank_train = current_reg.predict(X_train)
        current_rank_test_zsig = zsig_by_train(
            current_rank_train,
            current_reg.predict(X_test),
        )
        current_rank_test_pct = rankpct_by_train(
            current_rank_train,
            current_reg.predict(X_test),
        )
        current_clf_train = current_clf.predict_proba(X_train)[:, 1]
        current_clf_test = zsig_by_train(
            current_clf_train,
            current_clf.predict_proba(X_test)[:, 1],
        )

        safe_pct_score = np.power(current_rank_test_pct + 1e-8, 0.44) * np.power(
            current_clf_test + 1e-8, 0.56
        )
        both_zsig_score = np.power(current_rank_test_zsig + 1e-8, 0.44) * np.power(
            current_clf_test + 1e-8, 0.56
        )
        current605_score = np.power(current_rank_test_zsig + 1e-8, 0.32) * np.power(
            current_clf_test + 1e-8, 0.68
        )

        preds = (
            0.10 * baseline_score +
            0.50 * safe_pct_score +
            0.10 * both_zsig_score +
            0.30 * current605_score
        )

        all_scores.extend(preds)
        all_names.extend(X.index[test_idx])

    prediction_df = pd.DataFrame({
        "rt_name": all_names,
        "predicted_score": np.asarray(all_scores, dtype=float),
    })

    prediction_df = (
        seq.reset_index()[["rt_name"]]
        .merge(prediction_df, on="rt_name", how="left")
    )

    result = compute_cls(
        seq["active"].values,
        prediction_df["predicted_score"].values,
        seq["pe_efficiency_pct"].values,
    )

    return prediction_df, result


if __name__ == "__main__":
    X, y, groups = engineer_features()
    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name")
    seq = seq.loc[X.index]

    prediction_df, result = run_hybrid_lofo(X, y, groups, seq)

    print("\n==============================")
    print(f"PR-AUC: {result['pr_auc']:.6f}")
    print(f"Weighted Spearman: {result['w_spearman']:.6f}")
    print(f"CLS: {result['cls']:.6f}")
    print("==============================")

    os.makedirs("results", exist_ok=True)

    prediction_df.to_csv(
        "results/calibrated_predictions_selected_features.csv",
        index=False,
    )

    submission = prediction_df.copy()
    submission["predicted_active"] = (
        submission["predicted_score"] >= 0.5
    ).astype(int)
    submission = submission[["rt_name", "predicted_active", "predicted_score"]]
    submission_path = Path("submission.csv")
    fallback_path = Path("results") / "submission_latest.csv"

    try:
        submission.to_csv(submission_path, index=False)
        print("\nSaved predictions successfully")
    except PermissionError:
        submission.to_csv(fallback_path, index=False)
        print(
            "\nSaved predictions successfully "
            f"(fallback path: {fallback_path})"
        )
