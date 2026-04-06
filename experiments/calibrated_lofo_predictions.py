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
try:
    from qiskit.circuit.library import ZZFeatureMap
    from qiskit_machine_learning.kernels import FidelityQuantumKernel

    _HAS_QISKIT = True
except Exception:
    _HAS_QISKIT = False


print("LOFO hybrid rank-classifier pipeline started")

RANK_POWER = 1.4906030108132808

RANK_BLEND_WEIGHTS = {
    "baseline": -0.18318453678433988,
    "safe_pct_l1": -0.6477018518329005,
    "both_zsig_l1": 1.479724996815146,
    "current605_l1": 0.0214469618136075,
    "safe_pct_l2": 0.4515058633986655,
    "both_zsig_l2": -1.0327260103521705,
    "et_full_038": 1.3449915809517394,
    "hand_et_085": 0.5350148254038496,
    "clf_only_etl2": -1.2266232221563378,
    "proto_posneg": 0.6179440781913468,
    "svc_mi64": -0.6112889661517735,
    "svc_hand64": 0.027043337383369948,
    "svc_hand32": 1.388940306627069,
    "qsvc_hand4": -0.3496644000495559,
    "binary_manifold": -1.0415066940965003,
    "svc_esm_interact": 0.17341156304585637,
    "esm_interact_sim": 0.03074433565989998,
    "esm_curvature": -1.2191075114192154,
    "esm_ratio_contrast": -0.5670021778526173,
    "esm_delta_contrast": -0.7891743600912584,
    "esm_active_density": -1.1356946699074515,
    "esm_subcluster": -0.035396069720866286,
    "esm_synth_reg": -0.3992571140072944,
    "esm_block_svc": 0.9317955420963084,
    "esm_proto_curv_mul": -1.208698705972739,
    "esm_proto_curv_div": 1.317266721217674,
    "esm_proto_density_mul": 0.18551455505005376,
    "stack_ridge": 0.8328901192884279,
    "globalmm_l2": 0.0884790238791966,
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
    try:
        from scipy.stats import rankdata

        return rankdata(values, method="average") / (len(values) + 1.0)
    except Exception:
        # Fallback: average-tie ranking via pandas
        return (
            pd.Series(values)
            .rank(method="average")
            .to_numpy(dtype=float)
            / (len(values) + 1.0)
        )


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
        "binary_manifold": [],
        "svc_esm_interact": [],
        "esm_interact_sim": [],
        "esm_curvature": [],
        "esm_ratio_contrast": [],
        "esm_delta_contrast": [],
        "esm_active_density": [],
        "esm_subcluster": [],
        "esm_synth_reg": [],
        "esm_block_svc": [],
        "esm_proto_curv_mul": [],
        "esm_proto_curv_div": [],
        "esm_proto_density_mul": [],
        "stack_ridge": [],
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

        p_act_train = current_clf_l2.predict_proba(X_train)[:, 1]
        eff_pred_train = current_reg.predict(X_train)
        eff_pred_train = np.clip(eff_pred_train, 0, None)
        eff_pred_test = np.clip(current_rank_test_raw, 0, None)
        
        binary_rank_train = p_act_train * eff_pred_train
        binary_rank_test = current_clf_l2.predict_proba(X_test)[:, 1] * eff_pred_test
        component_scores["binary_manifold"].extend(
            zsig_by_train(binary_rank_train, binary_rank_test)
        )

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
            ("svc_mi64", X_train, X_test, 64, 1.5, False),
            ("svc_hand64", X_train_hand, X_test_hand, 64, 2.0, False),
            ("svc_hand32", X_train_hand, X_test_hand, 32, 1.0, False),
        ]

        for branch_name, train_features, test_features, k, c, use_interact in svc_feature_sets:
            max_k = min(k, train_features.shape[1])
            selector_scores = mutual_info_classif(
                train_features,
                y_train_bin,
                random_state=42,
            )
            top_idx = np.argsort(selector_scores)[-max_k:]

            svc_train = train_features[:, top_idx]
            svc_test = test_features[:, top_idx]
            
            if use_interact:
                from sklearn.preprocessing import PolynomialFeatures
                poly = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
                svc_train = poly.fit_transform(svc_train)
                svc_test = poly.transform(svc_test)

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
        # Quantum SVM (QSVC) branch (optional)
        # ==========================================
        if _HAS_QISKIT:
            max_k_q = min(4, X_train_hand.shape[1])
            selector_scores_q = mutual_info_classif(
                X_train_hand, y_train_bin, random_state=42
            )
            top_idx_q = np.argsort(selector_scores_q)[-max_k_q:]
            q_train_features = X_train_hand[:, top_idx_q]
            q_test_features = X_test_hand[:, top_idx_q]

            feature_map = ZZFeatureMap(
                feature_dimension=max_k_q,
                reps=1,
            )
            qkernel = FidelityQuantumKernel(feature_map=feature_map)

            qkernel_train = qkernel.evaluate(x_vec=q_train_features)
            qkernel_test = qkernel.evaluate(
                x_vec=q_test_features,
                y_vec=q_train_features,
            )

            qsvc_sklearn = SVC(
                kernel="precomputed",
                probability=True,
                class_weight="balanced",
                C=1.0,
                random_state=42,
            )
            qsvc_sklearn.fit(qkernel_train, y_train_bin)

            component_scores["qsvc_hand4"].extend(
                zsig_by_train(
                    qsvc_sklearn.predict_proba(qkernel_train)[:, 1],
                    qsvc_sklearn.predict_proba(qkernel_test)[:, 1],
                )
            )
        else:
            # Keep array length aligned per fold if qiskit isn't installed.
            component_scores["qsvc_hand4"].extend(np.zeros(X_test.shape[0], dtype=float))

        X_train_esm = X_train_df[esm_cols].to_numpy(dtype=float, copy=True)
        X_test_esm = X_test_df[esm_cols].to_numpy(dtype=float, copy=True)
        esm_medians = np.nanmedian(X_train_esm, axis=0)

        train_nan = np.where(np.isnan(X_train_esm))
        X_train_esm[train_nan] = np.take(esm_medians, train_nan[1])

        test_nan = np.where(np.isnan(X_test_esm))
        X_test_esm[test_nan] = np.take(esm_medians, test_nan[1])

        X_train_esm = normalize(X_train_esm)
        X_test_esm = normalize(X_test_esm)

        max_k_esm = 20
        selector_scores_esm = mutual_info_classif(X_train_esm, y_train_bin, random_state=42)
        top_esm_idx = np.argsort(selector_scores_esm)[-max_k_esm:]
        
        esm_train_top = X_train_esm[:, top_esm_idx]
        esm_test_top = X_test_esm[:, top_esm_idx]
        
        X_train_blocks = [
            X_train_esm[:, 0:320], X_train_esm[:, 320:640], 
            X_train_esm[:, 640:960], X_train_esm[:, 960:1280]
        ]
        X_test_blocks = [
            X_test_esm[:, 0:320], X_test_esm[:, 320:640], 
            X_test_esm[:, 640:960], X_test_esm[:, 960:1280]
        ]
        
        block_train_preds = np.zeros(X_train_esm.shape[0])
        block_test_preds = np.zeros(X_test_esm.shape[0])
        
        for tr_blk, te_blk in zip(X_train_blocks, X_test_blocks):
            blk_svc = SVC(C=1.0, kernel='rbf', probability=True, class_weight='balanced', random_state=42)
            blk_svc.fit(tr_blk, y_train_bin)
            block_train_preds += blk_svc.predict_proba(tr_blk)[:, 1]
            block_test_preds += blk_svc.predict_proba(te_blk)[:, 1]
            
        component_scores["esm_block_svc"].extend(
            zsig_by_train(block_train_preds, block_test_preds)
        )
        
        from sklearn.preprocessing import PolynomialFeatures
        poly_esm = PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)
        esm_train_interact = poly_esm.fit_transform(esm_train_top)
        esm_test_interact = poly_esm.transform(esm_test_top)
        
        svc_esm = SVC(C=1.0, gamma="scale", kernel="rbf", probability=True, class_weight="balanced", random_state=42)
        svc_esm.fit(esm_train_interact, y_train_bin)
        
        component_scores["svc_esm_interact"].extend(
            zsig_by_train(svc_esm.predict_proba(esm_train_interact)[:, 1], svc_esm.predict_proba(esm_test_interact)[:, 1])
        )

        active_mask = y_train_eff.to_numpy() > 0
        
        X_train_act = X_train_esm[active_mask]
        eff_act = y_train_eff.to_numpy()[active_mask]
        synth_X, synth_y = [], []
        import itertools
        if len(X_train_act) > 1:
            for i, j in itertools.combinations(range(len(X_train_act)), 2):
                xi, xj = X_train_act[i], X_train_act[j]
                yi, yj = eff_act[i], eff_act[j]
                for alpha in [0.25, 0.5, 0.75]:
                    synth_X.append(alpha * xi + (1 - alpha) * xj)
                    synth_y.append(alpha * yi + (1 - alpha) * yj)
                    
        if len(synth_X) > 0:
            X_train_expanded = np.vstack([X_train_esm, np.vstack(synth_X)])
            y_train_expanded = np.concatenate([y_train_eff.to_numpy(), np.array(synth_y)])
        else:
            X_train_expanded, y_train_expanded = X_train_esm, y_train_eff.to_numpy()
            
        from sklearn.svm import SVR
        svr_synth = SVR(kernel='rbf', C=1.0)
        svr_synth.fit(X_train_expanded, y_train_expanded)
        component_scores["esm_synth_reg"].extend(
            zsig_by_train(svr_synth.predict(X_train_esm), svr_synth.predict(X_test_esm))
        )

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
        # ------------------------------------------------
        # Tier-4/5/7 family-conditioned geometric features
        # (computed strictly from fold-train data)
        # ------------------------------------------------
        def _l2_normalize_rows(a):
            denom = np.linalg.norm(a, axis=1, keepdims=True) + 1e-12
            return a / denom

        # Normalize prototypes (X_train_esm / X_test_esm are already normalized)
        global_active_proto = _l2_normalize_rows(global_active_proto)
        global_inactive_proto = _l2_normalize_rows(global_inactive_proto)

        train_fams = groups.iloc[train_idx].astype(str).to_numpy()
        unique_train_fams = np.unique(train_fams)
        y_eff_train_np = y_train_eff.to_numpy(dtype=float)

        fam_active_protos = []
        fam_inactive_protos = []
        fam_sub_centroids = []

        for fam in unique_train_fams:
            fam_mask = train_fams == fam
            fam_act_mask = fam_mask & active_mask
            fam_inact_mask = fam_mask & (~active_mask)

            if fam_act_mask.any():
                X_fam_act = X_train_esm[fam_act_mask]
                f_w = np.log1p(y_eff_train_np[fam_act_mask])
                fw_sum = float(f_w.sum())
                fw_norm = f_w / fw_sum if fw_sum > 0 else np.ones_like(f_w) / max(len(f_w), 1)
                act_proto = (X_fam_act * fw_norm[:, None]).sum(axis=0, keepdims=True)
                fam_active_protos.append(act_proto)

                n_act = X_fam_act.shape[0]
                if n_act >= 4:
                    from sklearn.cluster import KMeans

                    k_clusters = 3 if n_act >= 9 else 2
                    kmeans = KMeans(
                        n_clusters=k_clusters,
                        random_state=42,
                        n_init=10,
                    )
                    kmeans.fit(X_fam_act, sample_weight=f_w)
                    fam_sub_centroids.append(kmeans.cluster_centers_.astype(float, copy=False))
                else:
                    fam_sub_centroids.append(act_proto.copy())

            if fam_inact_mask.any():
                fam_inactive_protos.append(X_train_esm[fam_inact_mask].mean(axis=0, keepdims=True))

        if len(fam_active_protos) == 0:
            fam_active_mat = global_active_proto.copy()
            fam_sub_mat = global_active_proto.copy()
        else:
            fam_active_mat = _l2_normalize_rows(np.vstack(fam_active_protos))
            fam_sub_mat = _l2_normalize_rows(np.vstack(fam_sub_centroids))

        if len(fam_inactive_protos) == 0:
            fam_inactive_mat = global_inactive_proto.copy()
        else:
            fam_inactive_mat = _l2_normalize_rows(np.vstack(fam_inactive_protos))

        def calc_similarity_features(X_curr):
            eps = 1e-4
            n = X_curr.shape[0]

            # Global prototype similarity (cosine; embeddings are normalized)
            g_act = (X_curr @ global_active_proto.T).ravel()
            g_inact = (X_curr @ global_inactive_proto.T).ravel()
            global_delta = g_act - g_inact

            # LOFO-safe "family" signal: best-matching train-family regime
            f_act = np.max(X_curr @ fam_active_mat.T, axis=1)
            f_inact = np.mean(X_curr @ fam_inactive_mat.T, axis=1)
            f_sub = np.max(X_curr @ fam_sub_mat.T, axis=1)

            family_delta = f_act - f_inact

            # Neighbor similarities (top-k within fold-train actives/inactives)
            X_act = X_train_esm[active_mask]
            X_inact = X_train_esm[~active_mask] if (~active_mask).any() else None

            sims_to_act = X_curr @ X_act.T if X_act.shape[0] > 0 else np.zeros((n, 0), dtype=float)
            sims_to_inact = (
                (X_curr @ X_inact.T) if (X_inact is not None and X_inact.shape[0] > 0) else np.zeros((n, 0), dtype=float)
            )

            topk_a = min(5, sims_to_act.shape[1]) if sims_to_act.shape[1] > 0 else 0
            topk_i = min(5, sims_to_inact.shape[1]) if sims_to_inact.shape[1] > 0 else 0

            if topk_a > 0:
                sorted_a = np.sort(sims_to_act, axis=1)[:, ::-1]
                top_a = sorted_a[:, :topk_a]
                mean_top_a_3 = np.mean(top_a[:, : min(3, topk_a)], axis=1)
                mean_top_a = np.mean(top_a, axis=1)
            else:
                top_a = np.zeros((n, 0), dtype=float)
                mean_top_a_3 = np.zeros(n, dtype=float)
                mean_top_a = np.zeros(n, dtype=float)

            if topk_i > 0:
                sorted_i = np.sort(sims_to_inact, axis=1)[:, ::-1]
                top_i = sorted_i[:, :topk_i]
                mean_top_i = np.mean(top_i, axis=1)
            else:
                mean_top_i = np.zeros(n, dtype=float)

            neighbor_score = mean_top_a_3

            # Tier-1: combinatorial epistasis interactions (top-k actives)
            import itertools

            interact_sims = []
            if top_a.shape[1] >= 2:
                for ii, jj in itertools.combinations(range(top_a.shape[1]), 2):
                    interact_sims.append(top_a[:, ii] * top_a[:, jj])
            indiv_interact_score = (
                np.mean(interact_sims, axis=0) if len(interact_sims) > 0 else np.zeros(n, dtype=float)
            )

            # Tier-3: local manifold curvature (uncertainty) from top-k actives
            curvature_score = -np.std(top_a, axis=1) if top_a.shape[1] > 0 else np.zeros(n, dtype=float)

            # Tier-5: ratio-contrast + delta-contrast (global/family/neighbor/subcluster)
            global_contrast = g_act / (g_inact + eps)
            family_contrast = f_act / (f_inact + eps)
            neighbor_contrast = mean_top_a / (mean_top_i + eps)
            cluster_contrast = f_sub / (f_inact + eps)

            ratio_contrast_score = (
                0.20 * global_contrast
                + 0.35 * family_contrast
                + 0.25 * neighbor_contrast
                + 0.20 * cluster_contrast
            )

            neighbor_delta = mean_top_a - mean_top_i
            cluster_delta = f_sub - f_inact
            delta_contrast_score = (
                0.20 * global_delta
                + 0.35 * family_delta
                + 0.25 * neighbor_delta
                + 0.20 * cluster_delta
            )

            # Tier-7: active neighborhood density (top-k adaptive KDE over actives)
            if top_a.shape[1] > 0:
                dist = 1.0 - top_a  # cosine distance proxy on normalized vectors

                # Adaptive bandwidth: use distance to kth active neighbor (balloon KDE-ish)
                h = np.maximum(dist[:, -1], 0.05)
                active_density_score = np.sum(
                    np.exp(-(dist * dist) / (2.0 * (h[:, None] * h[:, None]))),
                    axis=1,
                )
            else:
                active_density_score = np.zeros(n, dtype=float)

            # Tier-4: family subcluster similarity (max to family sub-centroids)
            subcluster_score = f_sub

            # Prototype blending (family/global/neighbor)
            proto_score = 0.60 * family_delta + 0.30 * global_delta + 0.10 * neighbor_score

            return (
                proto_score,
                indiv_interact_score,
                curvature_score,
                ratio_contrast_score,
                delta_contrast_score,
                active_density_score,
                subcluster_score,
            )

        p_tr, i_tr, c_tr, r_tr, dr_tr, d_tr, s_tr = calc_similarity_features(X_train_esm)
        p_te, i_te, c_te, r_te, dr_te, d_te, s_te = calc_similarity_features(X_test_esm)

        component_scores["proto_posneg"].extend(zsig_by_train(p_tr, p_te))
        component_scores["esm_interact_sim"].extend(zsig_by_train(i_tr, i_te))
        component_scores["esm_curvature"].extend(zsig_by_train(c_tr, c_te))
        component_scores["esm_ratio_contrast"].extend(zsig_by_train(r_tr, r_te))
        component_scores["esm_delta_contrast"].extend(zsig_by_train(dr_tr, dr_te))
        component_scores["esm_active_density"].extend(zsig_by_train(d_tr, d_te))
        component_scores["esm_subcluster"].extend(zsig_by_train(s_tr, s_te))
        
        component_scores["esm_proto_curv_mul"].extend(zsig_by_train(p_tr * c_tr, p_te * c_te))
        component_scores["esm_proto_curv_div"].extend(
            zsig_by_train(
                p_tr / (np.abs(c_tr) + 1e-4),
                p_te / (np.abs(c_te) + 1e-4),
            )
        )
        component_scores["esm_proto_density_mul"].extend(
            zsig_by_train(p_tr * d_tr, p_te * d_te)
        )

        # ------------------------------------------------
        # Tier-E: fold-safe stacking meta-learner
        # ------------------------------------------------
        from sklearn.linear_model import Ridge

        # Use stable, diverse signals for stacking
        stack_feats_train = np.column_stack(
            [
                zsig_by_train(p_tr, p_tr),
                zsig_by_train(i_tr, i_tr),
                zsig_by_train(c_tr, c_tr),
                zsig_by_train(r_tr, r_tr),
                zsig_by_train(dr_tr, dr_tr),
                zsig_by_train(d_tr, d_tr),
                zsig_by_train(s_tr, s_tr),
                current_clf_l2_train,
                zsig_by_train(current_rank_train, current_rank_train),
            ]
        )
        stack_feats_test = np.column_stack(
            [
                zsig_by_train(p_tr, p_te),
                zsig_by_train(i_tr, i_te),
                zsig_by_train(c_tr, c_te),
                zsig_by_train(r_tr, r_te),
                zsig_by_train(dr_tr, dr_te),
                zsig_by_train(d_tr, d_te),
                zsig_by_train(s_tr, s_te),
                current_clf_l2_test,
                current_rank_test_zsig,
            ]
        )

        # Target: activity-weighted efficiency for CLS alignment
        y_combo_train = y_train_bin.to_numpy(dtype=float) * (y_train_eff.to_numpy(dtype=float) + 0.01)
        w_combo = y_train_eff.to_numpy(dtype=float) + 0.01

        ridge = Ridge(alpha=2.0, random_state=42)
        ridge.fit(stack_feats_train, y_combo_train, sample_weight=w_combo)

        ridge_tr = ridge.predict(stack_feats_train)
        ridge_te = ridge.predict(stack_feats_test)
        component_scores["stack_ridge"].extend(zsig_by_train(ridge_tr, ridge_te))

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
