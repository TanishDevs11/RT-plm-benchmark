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
from sklearn.feature_selection import mutual_info_classif
from sklearn.impute import SimpleImputer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler, normalize
from sklearn.svm import SVC

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(os.path.join(ROOT, "src"))
sys.path.append(os.path.join(ROOT, "evaluation"))

from evaluate import compute_cls
from feature_engineering import engineer_features

# Quantum libraries
from qiskit.circuit.library import ZZFeatureMap
from qiskit_machine_learning.kernels import FidelityQuantumKernel


print("LOFO hybrid rank-classifier pipeline started")

RANK_POWER = 1.408715395639527

RANK_BLEND_WEIGHTS = {
    "baseline": -0.04867410060369404,
    "safe_pct_l1": 0.04357328414322137,
    "both_zsig_l1": 1.0889779580311232,
    "current605_l1": 0.5149317945924597,
    "safe_pct_l2": -1.4272610848754903,
    "both_zsig_l2": -0.2355235670750192,
    "et_full_038": -0.26331256065795056,
    "hand_et_085": -0.4808459637036665,
    "clf_only_etl2": -0.3101569498715384,
    "proto_posneg": 0.39976472498212423,
    "svc_mi64": 0.09611439215052842,
    "svc_hand64": 0.11969391436391308,
    "svc_hand32": 0.7347704429305597,
    "qsvc_hand4": -0.31774012086497894,
    "globalmm_l2": 0.9709850994621647,
}


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
    return (
        np.argsort(np.argsort(values)).astype(float) + 1.0
    ) / (len(values) + 1.0)


def run_hybrid_lofo(X, y, groups, seq):
    logo = LeaveOneGroupOut()
    hand_cols = [c for c in X.columns if not str(c).startswith("esm_")]
    esm_cols = [c for c in X.columns if str(c).startswith("esm_")]

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
        "qsvc_hand4": [],
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
            et_full_train,
            et_full.predict_proba(X_test)[:, 1],
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
            hand_et_train,
            hand_et.predict_proba(X_test_hand)[:, 1],
        )
        component_scores["hand_et_085"].extend(
            np.power(current_rank_test_zsig + 1e-8, 0.85)
            * np.power(hand_et_test + 1e-8, 0.15)
        )

        svc_feature_sets = [
            ("svc_mi64", X_train, X_test, 64, 1.5),
            ("svc_hand64", X_train_hand, X_test_hand, 64, 2.0),
            ("svc_hand32", X_train_hand, X_test_hand, 32, 1.0),
        ]

        for branch_name, train_features, test_features, k, c in svc_feature_sets:
            max_k = min(k, train_features.shape[1])
            selector_scores = mutual_info_classif(
                train_features,
                y_train_bin,
                random_state=42,
            )
            top_idx = np.argsort(selector_scores)[-max_k:]

            svc_train = train_features[:, top_idx]
            svc_test = test_features[:, top_idx]

            svc = SVC(
                C=c,
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

        # ==========================================
        # Quantum SVM (QSVC) branch
        # ==========================================
        max_k_q = min(4, X_train_hand.shape[1])
        selector_scores_q = mutual_info_classif(X_train_hand, y_train_bin, random_state=42)
        top_idx_q = np.argsort(selector_scores_q)[-max_k_q:]
        q_train_features = X_train_hand[:, top_idx_q]
        q_test_features = X_test_hand[:, top_idx_q]
        
        feature_map = ZZFeatureMap(feature_dimension=max_k_q, reps=1)
        qkernel = FidelityQuantumKernel(feature_map=feature_map)
        
        qkernel_train = qkernel.evaluate(x_vec=q_train_features)
        qkernel_test = qkernel.evaluate(x_vec=q_test_features, y_vec=q_train_features)
        
        qsvc_sklearn = SVC(kernel="precomputed", probability=True, class_weight="balanced", C=1.0, random_state=42)
        qsvc_sklearn.fit(qkernel_train, y_train_bin)
        
        component_scores["qsvc_hand4"].extend(
            zsig_by_train(
                qsvc_sklearn.predict_proba(qkernel_train)[:, 1],
                qsvc_sklearn.predict_proba(qkernel_test)[:, 1],
            )
        )

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
        if active_weights.sum() > 0:
            active_weights = active_weights / active_weights.sum()
        else:
            active_weights = np.ones_like(active_weights) / len(active_weights)

        global_active_proto = (X_train_esm[active_mask] * active_weights[:, None]).sum(axis=0, keepdims=True)
        if (~active_mask).any():
            global_inactive_proto = X_train_esm[~active_mask].mean(axis=0, keepdims=True)
        else:
            global_inactive_proto = np.zeros_like(global_active_proto)
            
        train_groups = groups.iloc[train_idx].values
        fam_active_protos = []
        fam_inactive_protos = []
        fam_sigmas = []
        
        unique_train_fams = np.unique(train_groups)
        for fam in unique_train_fams:
            fam_mask = train_groups == fam
            fam_act_mask = fam_mask & active_mask
            if fam_act_mask.any():
                f_w = np.log1p(y_train_eff.to_numpy()[fam_act_mask])
                f_w = f_w / f_w.sum() if f_w.sum() > 0 else np.ones_like(f_w)/len(f_w)
                fam_proto_act = (X_train_esm[fam_act_mask] * f_w[:, None]).sum(axis=0, keepdims=True)
                fam_active_protos.append(fam_proto_act)
                
                f_std = np.std(X_train_esm[fam_mask], axis=0).mean()
                fam_sigmas.append(max(f_std, 0.1))
                
            fam_inact_mask = fam_mask & (~active_mask)
            if fam_inact_mask.any():
                fam_inactive_protos.append(X_train_esm[fam_inact_mask].mean(axis=0, keepdims=True))
                
        if len(fam_inactive_protos) == 0:
            fam_inactive_protos.append(global_inactive_proto)
            
        fam_active_protos = np.vstack(fam_active_protos) if len(fam_active_protos) > 0 else global_active_proto
        fam_inactive_protos = np.vstack(fam_inactive_protos)
        fam_sigmas = np.array(fam_sigmas) if len(fam_sigmas) > 0 else np.array([1.0])

        from sklearn.metrics.pairwise import euclidean_distances
        def rbf_sim(x, p, s):
            return np.exp(-euclidean_distances(x, p, squared=True) / (s**2))

        def calc_similarity_features(X_curr, is_train=True):
            s_scales = [0.3, 1.0, 3.0]
            g_act = np.mean([rbf_sim(X_curr, global_active_proto, s).ravel() for s in s_scales], axis=0)
            g_inact = np.mean([rbf_sim(X_curr, global_inactive_proto, s).ravel() for s in s_scales], axis=0)
            global_score = g_act - g_inact
            
            f_act_sims = np.zeros((X_curr.shape[0], len(fam_active_protos)))
            for i, p in enumerate(fam_active_protos):
                s = fam_sigmas[i] if i < len(fam_sigmas) else 1.0
                f_act_sims[:, i] = rbf_sim(X_curr, p.reshape(1, -1), s).ravel()
                
            f_inact_sims = np.zeros((X_curr.shape[0], len(fam_inactive_protos)))
            s_mean = np.mean(fam_sigmas) if len(fam_sigmas) > 0 else 1.0
            for i, p in enumerate(fam_inactive_protos):
                f_inact_sims[:, i] = rbf_sim(X_curr, p.reshape(1, -1), s_mean).ravel()
                
            family_score = np.max(f_act_sims, axis=1) - np.mean(f_inact_sims, axis=1)
            
            dists_to_active = euclidean_distances(X_curr, X_train_esm[active_mask])
            sims_to_active = np.exp(-dists_to_active**2 / 1.0)
            neighbor_score = np.mean(np.sort(sims_to_active, axis=1)[:, -3:], axis=1)
            
            return 0.6 * family_score + 0.3 * global_score + 0.1 * neighbor_score

        proto_train = calc_similarity_features(X_train_esm, is_train=True)
        proto_test = calc_similarity_features(X_test_esm, is_train=False)

        component_scores["proto_posneg"].extend(
            zsig_by_train(proto_train, proto_test)
        )

        all_names.extend(X_test_df.index)

    globalmm_l2 = np.power(
        global_minmax(raw_rank_l2) + 1e-8,
        0.20,
    ) * np.power(np.asarray(clf_zsig_l2, dtype=float) + 1e-8, 0.80)

    component_arrays = {
        key: np.asarray(values, dtype=float)
        for key, values in component_scores.items()
    }
    component_arrays["globalmm_l2"] = globalmm_l2

    rank_arrays = {
        name: global_rank_percentile(component_arrays[name])
        for name in component_arrays.keys()
    }

    final_scores = np.zeros(len(all_names), dtype=float)
    for name, w in RANK_BLEND_WEIGHTS.items():
        if w != 0 and name in rank_arrays:
            final_scores += w * np.power(rank_arrays[name], RANK_POWER)

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

    return prediction_df, result, component_arrays

if __name__ == "__main__":
    X, y, groups = engineer_features()
    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name")
    seq = seq.loc[X.index]

    prediction_df, result, component_arrays = run_hybrid_lofo(X, y, groups, seq)

    print("\n==============================")
    print(f"PR-AUC: {result['pr_auc']:.6f}")
    print(f"Weighted Spearman: {result['w_spearman']:.6f}")
    print(f"CLS: {result['cls']:.6f}")
    print("==============================")

    os.makedirs("results", exist_ok=True)
    import json
    with open("results/component_arrays.json", "w") as f:
        json.dump({k: v.tolist() for k, v in component_arrays.items()}, f)

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
