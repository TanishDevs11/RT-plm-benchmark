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


def global_minmax(values):
    values = np.asarray(values, dtype=float)
    return (values - values.min()) / (values.max() - values.min() + 1e-8)


def run_hybrid_lofo(X, y, groups, seq):
    logo = LeaveOneGroupOut()

    component_scores = {
        "baseline": [],
        "safe_pct_l1": [],
        "both_zsig_l1": [],
        "current605_l1": [],
        "safe_pct_l2": [],
        "both_zsig_l2": [],
        "et_full_038": [],
        "hand_et_085": [],
        "clf_only_etl2": [],
    }
    raw_rank_l2 = []
    clf_zsig_l2 = []
    all_names = []

    for train_idx, test_idx in logo.split(X, y, groups):
        X_train_df = X.iloc[train_idx]
        X_test_df = X.iloc[test_idx]

        y_train_bin = y.iloc[train_idx]
        y_train_eff = seq.loc[X_train_df.index, "pe_efficiency_pct"]
        y_train_eff_norm = (
            y_train_eff - y_train_eff.mean()
        ) / (y_train_eff.std() + 1e-8)

        imputer = SimpleImputer(strategy="median")
        X_train = imputer.fit_transform(X_train_df)
        X_test = imputer.transform(X_test_df)

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
        component_scores["baseline"].extend(
            0.67 * baseline_rank_test + 0.33 * baseline_clf_test
        )
        rf_full_036 = np.power(baseline_rank_test + 1e-8, 0.36) * np.power(
            baseline_clf_test + 1e-8, 0.64
        )

        current_rank_train = current_reg.predict(X_train)
        current_rank_test_raw = current_reg.predict(X_test)
        current_rank_test_zsig = zsig_by_train(
            current_rank_train,
            current_rank_test_raw,
        )
        current_rank_test_pct = rankpct_by_train(
            current_rank_train,
            current_rank_test_raw,
        )
        current_clf_train = current_clf.predict_proba(X_train)[:, 1]
        current_clf_test = zsig_by_train(
            current_clf_train,
            current_clf.predict_proba(X_test)[:, 1],
        )

        component_scores["safe_pct_l1"].extend(
            np.power(current_rank_test_pct + 1e-8, 0.44) * np.power(
                current_clf_test + 1e-8, 0.56
            )
        )
        component_scores["both_zsig_l1"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.44) * np.power(
                current_clf_test + 1e-8, 0.56
            )
        )
        component_scores["current605_l1"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.32) * np.power(
                current_clf_test + 1e-8, 0.68
            )
        )

        current_clf_l2 = ExtraTreesClassifier(
            n_estimators=1200,
            max_depth=None,
            min_samples_leaf=2,
            class_weight="balanced",
            max_features="sqrt",
            random_state=42,
            n_jobs=1,
        )
        current_clf_l2.fit(X_train, y_train_bin)
        current_clf_l2_train = current_clf_l2.predict_proba(X_train)[:, 1]
        current_clf_l2_test = zsig_by_train(
            current_clf_l2_train,
            current_clf_l2.predict_proba(X_test)[:, 1],
        )

        component_scores["safe_pct_l2"].extend(
            np.power(current_rank_test_pct + 1e-8, 0.44) * np.power(
                current_clf_l2_test + 1e-8, 0.56
            )
        )
        component_scores["both_zsig_l2"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.36) * np.power(
                current_clf_l2_test + 1e-8, 0.64
            )
        )
        raw_rank_l2.extend(current_rank_test_raw)
        clf_zsig_l2.extend(current_clf_l2_test)
        component_scores["clf_only_etl2"].extend(current_clf_l2_test)

        et_full = ExtraTreesClassifier(
            n_estimators=700,
            max_depth=8,
            min_samples_leaf=2,
            class_weight="balanced",
            max_features="sqrt",
            random_state=42,
            n_jobs=1,
        )
        et_full.fit(X_train, y_train_bin)
        et_full_train = et_full.predict_proba(X_train)[:, 1]
        et_full_test = zsig_by_train(
            et_full_train,
            et_full.predict_proba(X_test)[:, 1],
        )
        component_scores["et_full_038"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.38) * np.power(
                et_full_test + 1e-8, 0.62
            )
        )

        hand_cols = [c for c in X.columns if not str(c).startswith("esm_")]
        hand_imputer = SimpleImputer(strategy="median")
        X_train_hand = hand_imputer.fit_transform(X_train_df[hand_cols])
        X_test_hand = hand_imputer.transform(X_test_df[hand_cols])
        hand_scaler = StandardScaler()
        X_train_hand = hand_scaler.fit_transform(X_train_hand)
        X_test_hand = hand_scaler.transform(X_test_hand)
        hand_et = ExtraTreesClassifier(
            n_estimators=900,
            max_depth=8,
            min_samples_leaf=2,
            class_weight="balanced",
            max_features="sqrt",
            random_state=42,
            n_jobs=1,
        )
        hand_et.fit(X_train_hand, y_train_bin)
        hand_et_train = hand_et.predict_proba(X_train_hand)[:, 1]
        hand_et_test = zsig_by_train(
            hand_et_train,
            hand_et.predict_proba(X_test_hand)[:, 1],
        )
        component_scores["hand_et_085"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.85) * np.power(
                hand_et_test + 1e-8, 0.15
            )
        )

        _ = rf_full_036
        all_names.extend(X_test_df.index)

    globalmm_l2 = np.power(
        global_minmax(raw_rank_l2) + 1e-8,
        0.20,
    ) * np.power(np.asarray(clf_zsig_l2, dtype=float) + 1e-8, 0.80)

    final_scores = (
        0.0014509314472144666 * np.asarray(component_scores["baseline"], dtype=float) +
        0.28904656984589244 * np.asarray(component_scores["safe_pct_l1"], dtype=float) +
        0.007377624699222617 * np.asarray(component_scores["both_zsig_l1"], dtype=float) +
        0.12231384811764691 * np.asarray(component_scores["current605_l1"], dtype=float) +
        0.04606269416873803 * np.asarray(component_scores["safe_pct_l2"], dtype=float) +
        0.26051360724138833 * np.asarray(component_scores["both_zsig_l2"], dtype=float) +
        0.06101274899649034 * globalmm_l2 +
        0.12713302728791645 * np.asarray(component_scores["et_full_038"], dtype=float) +
        0.07927264181940237 * np.asarray(component_scores["hand_et_085"], dtype=float) +
        0.005609423996971588 * np.asarray(component_scores["clf_only_etl2"], dtype=float)
    )

    prediction_df = pd.DataFrame({
        "rt_name": all_names,
        "predicted_score": final_scores,
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
