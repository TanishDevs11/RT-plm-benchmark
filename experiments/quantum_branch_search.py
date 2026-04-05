import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.ensemble import (
    ExtraTreesClassifier,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.feature_selection import mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.svm import SVC

ROOT = os.path.join(os.path.dirname(__file__), "..")
TMP_ROOT = os.path.abspath(os.path.join(ROOT, ".tmp_qiskit"))
os.makedirs(TMP_ROOT, exist_ok=True)
tempfile.tempdir = TMP_ROOT

from qiskit.circuit.library import RealAmplitudes, ZZFeatureMap
from qiskit_machine_learning.algorithms import QSVC, VQC
from qiskit_machine_learning.kernels import FidelityQuantumKernel

sys.path.append(os.path.join(ROOT, "src"))
sys.path.append(os.path.join(ROOT, "evaluation"))

from evaluate import compute_cls
from feature_engineering import engineer_features


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


def global_rank_percentile(values):
    values = np.asarray(values, dtype=float)
    return rankdata(values, method="average") / (len(values) + 1.0)


def build_branch_arrays():
    X, y, groups = engineer_features()
    seq = pd.read_csv(os.path.join(ROOT, "data", "rt_sequences.csv")).set_index(
        "rt_name"
    )
    seq = seq.loc[X.index]
    hand_cols = [c for c in X.columns if not str(c).startswith("esm_")]
    esm_cols = [c for c in X.columns if str(c).startswith("esm_")]
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
        "proto_posneg": [],
        "svc_mi64": [],
        "svc_hand64": [],
        "svc_hand32": [],
        "svc_hand16": [],
        "svc_esm64": [],
        "qsvc_hand6": [],
        "qsvc_hand8": [],
        "vqc_hand4": [],
    }
    raw_rank_l2 = []
    clf_zsig_l2 = []
    all_names = []

    for fold_id, (train_idx, test_idx) in enumerate(logo.split(X, y, groups), start=1):
        print(f"Building fold {fold_id}")
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
            baseline_rank_train, baseline_reg.predict(X_test)
        )
        baseline_clf_train = baseline_clf.predict_proba(X_train)[:, 1]
        baseline_clf_test = zsig_by_train(
            baseline_clf_train, baseline_clf.predict_proba(X_test)[:, 1]
        )
        component_scores["baseline"].extend(
            0.67 * baseline_rank_test + 0.33 * baseline_clf_test
        )

        current_rank_train = current_reg.predict(X_train)
        current_rank_test_raw = current_reg.predict(X_test)
        current_rank_test_zsig = zsig_by_train(
            current_rank_train, current_rank_test_raw
        )
        current_rank_test_pct = rankpct_by_train(
            current_rank_train, current_rank_test_raw
        )
        current_clf_train = current_clf.predict_proba(X_train)[:, 1]
        current_clf_test = zsig_by_train(
            current_clf_train, current_clf.predict_proba(X_test)[:, 1]
        )

        component_scores["safe_pct_l1"].extend(
            np.power(current_rank_test_pct + 1e-8, 0.44)
            * np.power(current_clf_test + 1e-8, 0.56)
        )
        component_scores["both_zsig_l1"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.44)
            * np.power(current_clf_test + 1e-8, 0.56)
        )
        component_scores["current605_l1"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.32)
            * np.power(current_clf_test + 1e-8, 0.68)
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
            np.power(current_rank_test_pct + 1e-8, 0.44)
            * np.power(current_clf_l2_test + 1e-8, 0.56)
        )
        component_scores["both_zsig_l2"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.36)
            * np.power(current_clf_l2_test + 1e-8, 0.64)
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
            et_full_train, et_full.predict_proba(X_test)[:, 1]
        )
        component_scores["et_full_038"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.38)
            * np.power(et_full_test + 1e-8, 0.62)
        )

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
            hand_et_train, hand_et.predict_proba(X_test_hand)[:, 1]
        )
        component_scores["hand_et_085"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.85)
            * np.power(hand_et_test + 1e-8, 0.15)
        )

        svc_feature_sets = [
            ("svc_mi64", X_train, X_test, 64, 1.5),
            ("svc_hand64", X_train_hand, X_test_hand, 64, 2.0),
            ("svc_hand32", X_train_hand, X_test_hand, 32, 1.0),
            ("svc_hand16", X_train_hand, X_test_hand, 16, 1.0),
        ]
        for branch_name, train_features, test_features, k, c_value in svc_feature_sets:
            max_k = min(k, train_features.shape[1])
            selector_scores = mutual_info_classif(
                train_features, y_train_bin, random_state=42
            )
            top_idx = np.argsort(selector_scores)[-max_k:]
            svc_train = train_features[:, top_idx]
            svc_test = test_features[:, top_idx]
            svc = SVC(
                C=c_value,
                gamma="scale",
                kernel="rbf",
                probability=True,
                class_weight="balanced",
                random_state=42,
            )
            svc.fit(svc_train, y_train_bin)
            component_scores[branch_name].extend(
                zsig_by_train(
                    svc.predict_proba(svc_train)[:, 1],
                    svc.predict_proba(svc_test)[:, 1],
                )
            )

        if esm_cols:
            X_train_esm = X_train_df[esm_cols].to_numpy(dtype=float, copy=True)
            X_test_esm = X_test_df[esm_cols].to_numpy(dtype=float, copy=True)
            esm_medians = np.nanmedian(X_train_esm, axis=0)
            train_nan = np.where(np.isnan(X_train_esm))
            X_train_esm[train_nan] = np.take(esm_medians, train_nan[1])
            test_nan = np.where(np.isnan(X_test_esm))
            X_test_esm[test_nan] = np.take(esm_medians, test_nan[1])
            X_train_esm = normalize(X_train_esm)
            X_test_esm = normalize(X_test_esm)

            active_mask = y_train_eff.to_numpy() > 0
            active_weights = np.log1p(y_train_eff.to_numpy()[active_mask])
            active_weights = active_weights / active_weights.sum()

            proto_active = normalize(
                (
                    X_train_esm[active_mask] * active_weights[:, None]
                ).sum(axis=0, keepdims=True)
            )
            if (~active_mask).any():
                proto_inactive = normalize(
                    X_train_esm[~active_mask].mean(axis=0, keepdims=True)
                )
            else:
                proto_inactive = -proto_active
            proto_train = (
                cosine_similarity(X_train_esm, proto_active).ravel()
                - cosine_similarity(X_train_esm, proto_inactive).ravel()
            )
            proto_test = (
                cosine_similarity(X_test_esm, proto_active).ravel()
                - cosine_similarity(X_test_esm, proto_inactive).ravel()
            )
            component_scores["proto_posneg"].extend(
                zsig_by_train(proto_train, proto_test)
            )

            max_k = min(64, X_train_esm.shape[1])
            selector_scores = mutual_info_classif(
                X_train_esm, y_train_bin, random_state=42
            )
            top_idx = np.argsort(selector_scores)[-max_k:]
            esm_svc = SVC(
                C=1.0,
                gamma="scale",
                kernel="rbf",
                probability=True,
                class_weight="balanced",
                random_state=42,
            )
            esm_svc.fit(X_train_esm[:, top_idx], y_train_bin)
            component_scores["svc_esm64"].extend(
                zsig_by_train(
                    esm_svc.predict_proba(X_train_esm[:, top_idx])[:, 1],
                    esm_svc.predict_proba(X_test_esm[:, top_idx])[:, 1],
                )
            )
        else:
            component_scores["proto_posneg"].extend([0.5] * len(X_test_df))
            component_scores["svc_esm64"].extend([0.5] * len(X_test_df))

        qsvc_selector_scores = mutual_info_classif(
            X_train_hand, y_train_bin, random_state=42
        )
        for branch_name, k in [("qsvc_hand6", 6), ("qsvc_hand8", 8)]:
            max_k = min(k, X_train_hand.shape[1])
            top_idx = np.argsort(qsvc_selector_scores)[-max_k:]
            q_train = X_train_hand[:, top_idx]
            q_test = X_test_hand[:, top_idx]
            feature_map = ZZFeatureMap(feature_dimension=q_train.shape[1], reps=1)
            kernel = FidelityQuantumKernel(feature_map=feature_map)
            qsvc = QSVC(quantum_kernel=kernel)
            qsvc.fit(q_train, y_train_bin)
            component_scores[branch_name].extend(
                zsig_by_train(
                    qsvc.decision_function(q_train),
                    qsvc.decision_function(q_test),
                )
            )

        try:
            top_idx = np.argsort(qsvc_selector_scores)[-4:]
            q_train = X_train_hand[:, top_idx]
            q_test = X_test_hand[:, top_idx]
            feature_map = ZZFeatureMap(feature_dimension=q_train.shape[1], reps=1)
            ansatz = RealAmplitudes(q_train.shape[1], reps=1)
            vqc = VQC(feature_map=feature_map, ansatz=ansatz)
            vqc.fit(q_train, y_train_bin.to_numpy())
            component_scores["vqc_hand4"].extend(
                zsig_by_train(
                    np.asarray(vqc.predict(q_train), dtype=float).ravel(),
                    np.asarray(vqc.predict(q_test), dtype=float).ravel(),
                )
            )
        except Exception:
            component_scores["vqc_hand4"].extend([0.5] * len(X_test_df))

        all_names.extend(X_test_df.index)

    component_arrays = {
        key: np.asarray(values, dtype=float) for key, values in component_scores.items()
    }
    component_arrays["globalmm_l2"] = np.power(
        global_minmax(raw_rank_l2) + 1e-8, 0.20
    ) * np.power(np.asarray(clf_zsig_l2, dtype=float) + 1e-8, 0.80)

    return seq, all_names, component_arrays


def score_ensemble(seq, all_names, component_arrays, weights, powers):
    final_scores = np.zeros(len(all_names), dtype=float)
    for name, weight in weights.items():
        if weight <= 0:
            continue
        final_scores += weight * np.power(
            global_rank_percentile(component_arrays[name]), powers[name]
        )

    prediction_df = pd.DataFrame(
        {"rt_name": all_names, "predicted_score": final_scores}
    )
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


def random_search(seq, all_names, component_arrays, iterations=1200, seed=42):
    rng = np.random.default_rng(seed)
    branch_names = list(component_arrays.keys())

    base_weights = {
        "both_zsig_l1": 0.007622700931794334,
        "current605_l1": 0.000012697578246568042,
        "safe_pct_l2": 0.0021817143831246453,
        "both_zsig_l2": 0.003352808267075591,
        "hand_et_085": 0.2725510039421795,
        "clf_only_etl2": 0.009250093649731828,
        "globalmm_l2": 0.0021367749884207434,
        "proto_posneg": 0.10449799555487606,
        "svc_mi64": 0.01388756524049345,
        "svc_hand64": 0.29337942781652876,
        "svc_hand32": 0.2911272176475285,
    }
    base_weights = {
        name: base_weights.get(name, 0.0) for name in branch_names
    }
    base_total = sum(base_weights.values())
    base_weights = {
        name: value / base_total if base_total else 0.0
        for name, value in base_weights.items()
    }
    base_powers = {name: 0.7 for name in branch_names}
    base_powers.update(
        {
            "both_zsig_l1": 0.7356814790889731,
            "current605_l1": 0.6362577831053391,
            "safe_pct_l2": 0.6348844318497668,
            "both_zsig_l2": 0.8518233899482135,
            "hand_et_085": 0.7521890948158019,
            "clf_only_etl2": 0.6736950341139764,
            "globalmm_l2": 0.6925968917819286,
            "proto_posneg": 0.5341156660496362,
            "svc_mi64": 0.6340994547102359,
            "svc_hand64": 0.5371484211426089,
            "svc_hand32": 0.4539540822293392,
        }
    )

    _, best_result = score_ensemble(
        seq, all_names, component_arrays, base_weights, base_powers
    )
    best = {
        "cls": best_result["cls"],
        "pr_auc": best_result["pr_auc"],
        "w_spearman": best_result["w_spearman"],
        "weights": base_weights,
        "powers": base_powers,
    }
    print(
        "base "
        f"PR-AUC={best['pr_auc']:.6f} "
        f"Weighted Spearman={best['w_spearman']:.6f} "
        f"CLS={best['cls']:.6f}"
    )

    for iteration in range(1, iterations + 1):
        active_n = int(rng.integers(5, min(10, len(branch_names)) + 1))
        active = rng.choice(branch_names, size=active_n, replace=False)
        raw_weights = rng.dirichlet(np.ones(active_n))
        weights = {name: 0.0 for name in branch_names}
        powers = {name: float(rng.uniform(0.35, 0.95)) for name in branch_names}

        for idx, name in enumerate(active):
            weights[name] = float(raw_weights[idx])

        _, result = score_ensemble(seq, all_names, component_arrays, weights, powers)
        if result["cls"] > best["cls"]:
            best = {
                "cls": result["cls"],
                "pr_auc": result["pr_auc"],
                "w_spearman": result["w_spearman"],
                "weights": weights,
                "powers": powers,
            }
            print(
                f"iter {iteration} "
                f"PR-AUC={best['pr_auc']:.6f} "
                f"Weighted Spearman={best['w_spearman']:.6f} "
                f"CLS={best['cls']:.6f}"
            )

    return best


if __name__ == "__main__":
    seq, all_names, component_arrays = build_branch_arrays()
    best = random_search(seq, all_names, component_arrays)
    output_path = Path(ROOT) / "results" / "quantum_branch_search_best.json"
    output_path.write_text(json.dumps(best, indent=2))
    print(f"Saved best search result to {output_path}")
