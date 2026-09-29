import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.linalg import expm
from scipy.optimize import differential_evolution, minimize
from scipy.special import logsumexp
from scipy.stats import rankdata
from sklearn.ensemble import ExtraTreesClassifier, RandomForestRegressor
from sklearn.decomposition import PCA
from sklearn.cross_decomposition import PLSRegression
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent
AA_ORDER = list("ACDEFGHIKLMNPQRSTVWY")

import sys

sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "evaluation"))
from feature_engineering import engineer_features
from evaluate import compute_cls


def zsig_by_train(train_scores, test_scores):
    train_scores = np.asarray(train_scores, dtype=float)
    test_scores = np.asarray(test_scores, dtype=float)
    mu = train_scores.mean()
    sigma = train_scores.std() + 1e-8
    z = (test_scores - mu) / sigma
    return 1.0 / (1.0 + np.exp(-z))


def rankpct_by_train(train_scores, test_scores):
    train_sorted = np.sort(np.asarray(train_scores, dtype=float))
    positions = np.searchsorted(
        train_sorted,
        np.asarray(test_scores, dtype=float),
        side="right",
    )
    return positions / (len(train_sorted) + 1.0)


def minmax(values):
    values = np.asarray(values, dtype=float)
    return (values - values.min()) / (values.max() - values.min() + 1e-8)


def build_sequence_features(seq_series):
    rows = []
    for seq in seq_series.astype(str):
        length = max(len(seq), 1)
        counts = {aa: seq.count(aa) for aa in AA_ORDER}
        row = {f"aa_{aa}": counts[aa] / length for aa in AA_ORDER}
        pos = counts["R"] + counts["K"]
        neg = counts["D"] + counts["E"]
        row["positive_fraction"] = pos / length
        row["negative_fraction"] = neg / length
        row["net_charge_density"] = (pos - neg) / length
        row["charge_ratio"] = (pos - neg) / (pos + neg + 1e-8)
        rows.append(row)
    return pd.DataFrame(rows, index=seq_series.index)


def load_embeddings(rt_names):
    emb = np.load(ROOT / "data" / "esm2_embeddings.npz", allow_pickle=True)
    if "rt_names" in emb.files:
        emb_names = [str(name) for name in emb["rt_names"]]
    elif "names" in emb.files:
        emb_names = [str(name) for name in emb["names"]]
    else:
        emb_names = list(rt_names)
    name_to_idx = {name: idx for idx, name in enumerate(emb_names)}
    vectors = emb["embeddings"].astype(float)
    return np.vstack([vectors[name_to_idx[name]] for name in rt_names])


def group_exclusion_scale(X_train, groups_train, X_test):
    X_train_scaled = np.zeros_like(X_train, dtype=float)
    for fam in pd.Series(groups_train).unique():
        mask = groups_train == fam
        ref = X_train[~mask]
        if ref.shape[0] < 2:
            ref = X_train
        scaler = StandardScaler()
        scaler.fit(ref)
        X_train_scaled[mask] = scaler.transform(X_train[mask])

    test_scaler = StandardScaler()
    test_scaler.fit(X_train)
    X_test_scaled = test_scaler.transform(X_test)
    return X_train_scaled, X_test_scaled


def build_embedding_features(train_emb, test_emb, y_train, groups_train, eff_train):
    train_mean = train_emb.mean(axis=0, keepdims=True)
    train_centered = train_emb - train_mean
    test_centered = test_emb - train_mean
    train_centered /= np.linalg.norm(train_centered, axis=1, keepdims=True) + 1e-8
    test_centered /= np.linalg.norm(test_centered, axis=1, keepdims=True) + 1e-8

    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)
    groups_train = np.asarray(groups_train)
    weights = eff_train + 0.01

    active_mask = y_train == 1
    inactive_mask = ~active_mask
    active_center = np.average(
        train_centered[active_mask], axis=0, weights=weights[active_mask]
    )
    inactive_center = train_centered[inactive_mask].mean(axis=0)
    eff_center = np.average(train_centered, axis=0, weights=weights)
    active_center /= np.linalg.norm(active_center) + 1e-8
    inactive_center /= np.linalg.norm(inactive_center) + 1e-8
    eff_center /= np.linalg.norm(eff_center) + 1e-8

    family_centers = {}
    family_strengths = {}
    for fam in np.unique(groups_train):
        fam_active = (groups_train == fam) & active_mask
        if fam_active.sum() == 0:
            continue
        fam_center = np.average(
            train_centered[fam_active], axis=0, weights=weights[fam_active]
        )
        fam_center /= np.linalg.norm(fam_center) + 1e-8
        family_centers[fam] = fam_center
        family_strengths[fam] = float(weights[fam_active].mean())

    def cross_family_similarity(vector, sample_family=None):
        sims = []
        wts = []
        for fam, center in family_centers.items():
            if sample_family is not None and fam == sample_family:
                continue
            sims.append(float(vector @ center))
            wts.append(family_strengths[fam])
        if not sims:
            sims = [float(vector @ active_center)]
            wts = [1.0]
        return float(np.average(sims, weights=wts))

    train_crossfam = np.array(
        [
            cross_family_similarity(vec, fam)
            for vec, fam in zip(train_centered, groups_train)
        ],
        dtype=float,
    )
    test_crossfam = np.array(
        [cross_family_similarity(vec) for vec in test_centered],
        dtype=float,
    )

    train_active_sim = train_centered @ active_center
    test_active_sim = test_centered @ active_center
    train_inactive_sim = train_centered @ inactive_center
    test_inactive_sim = test_centered @ inactive_center
    train_eff_sim = train_centered @ eff_center
    test_eff_sim = test_centered @ eff_center

    train_margin = train_crossfam - train_inactive_sim
    test_margin = test_crossfam - test_inactive_sim
    train_curvature = np.sum((train_centered - active_center) ** 2, axis=1) - np.sum(
        (train_centered - inactive_center) ** 2, axis=1
    )
    test_curvature = np.sum((test_centered - active_center) ** 2, axis=1) - np.sum(
        (test_centered - inactive_center) ** 2, axis=1
    )

    # Whiten the fold embedding space, then extract the dominant
    # efficiency direction from training families only.
    n_white = int(min(16, train_centered.shape[0] - 1, train_centered.shape[1]))
    if n_white >= 2:
        pca_white = PCA(n_components=n_white, whiten=True, random_state=42)
        train_white = pca_white.fit_transform(train_centered)
        test_white = pca_white.transform(test_centered)
    else:
        train_white = train_centered
        test_white = test_centered

    weighted_train = train_white * np.sqrt(weights)[:, None]
    _, _, vt = np.linalg.svd(weighted_train, full_matrices=False)
    eff_vec = vt[0]
    eff_projection_train = train_white @ eff_vec
    eff_projection_test = test_white @ eff_vec

    sim_train = train_centered @ train_centered.T
    np.fill_diagonal(sim_train, -np.inf)
    sim_test = test_centered @ train_centered.T
    k = min(6, train_centered.shape[0])
    train_knn = []
    for row in range(sim_train.shape[0]):
        idx = np.argsort(sim_train[row])[::-1][:k]
        neigh_sim = np.maximum(sim_train[row, idx], 0.0) + 1e-8
        train_knn.append(float(np.average(eff_train[idx], weights=neigh_sim)))
    test_knn = []
    for row in range(sim_test.shape[0]):
        idx = np.argsort(sim_test[row])[::-1][:k]
        neigh_sim = np.maximum(sim_test[row, idx], 0.0) + 1e-8
        test_knn.append(float(np.average(eff_train[idx], weights=neigh_sim)))

    # Local manifold residual: distance from a sample to the local embedding plane
    # spanned by its nearest neighbors. This captures unusual RTs relative to
    # their structural neighborhood, which is useful once global centroid signals
    # are saturated.
    train_manifold = []
    for row in range(train_centered.shape[0]):
        idx = np.argsort(sim_train[row])[::-1][: max(3, min(8, train_centered.shape[0] - 1))]
        neigh = train_centered[idx]
        if neigh.shape[0] >= 3:
            local_mean = neigh.mean(axis=0, keepdims=True)
            local_rank = int(min(3, neigh.shape[0] - 1, neigh.shape[1]))
            if local_rank >= 1:
                pca = PCA(n_components=local_rank, random_state=42)
                pca.fit(neigh - local_mean)
                recon = pca.inverse_transform(pca.transform(train_centered[row : row + 1] - local_mean)) + local_mean
                resid = float(np.linalg.norm(train_centered[row] - recon.ravel()))
            else:
                resid = float(np.linalg.norm(train_centered[row] - local_mean.ravel()))
        else:
            resid = 0.0
        train_manifold.append(resid)

    test_manifold = []
    for row in range(test_centered.shape[0]):
        idx = np.argsort(sim_test[row])[::-1][: max(3, min(8, train_centered.shape[0]))]
        neigh = train_centered[idx]
        if neigh.shape[0] >= 3:
            local_mean = neigh.mean(axis=0, keepdims=True)
            local_rank = int(min(3, neigh.shape[0] - 1, neigh.shape[1]))
            if local_rank >= 1:
                pca = PCA(n_components=local_rank, random_state=42)
                pca.fit(neigh - local_mean)
                recon = pca.inverse_transform(pca.transform(test_centered[row : row + 1] - local_mean)) + local_mean
                resid = float(np.linalg.norm(test_centered[row] - recon.ravel()))
            else:
                resid = float(np.linalg.norm(test_centered[row] - local_mean.ravel()))
        else:
            resid = 0.0
        test_manifold.append(resid)

    # Family-relative efficiency projection. Training rows are centered against
    # other-family reference means; held-out family rows use the training-family
    # mean of the fold as the neutral baseline.
    fam_eff_means = {}
    for fam in np.unique(groups_train):
        fam_mask = groups_train == fam
        fam_eff_means[fam] = float(np.mean(train_eff_sim[fam_mask]))
    global_eff_mean = float(np.mean(list(fam_eff_means.values())))
    train_eff_rel = np.zeros_like(train_eff_sim)
    for idx, fam in enumerate(groups_train):
        other = [v for kfam, v in fam_eff_means.items() if kfam != fam]
        ref = float(np.mean(other)) if other else global_eff_mean
        train_eff_rel[idx] = train_eff_sim[idx] - ref
    test_eff_rel = test_eff_sim - global_eff_mean

    train_out = np.column_stack(
        [
            train_crossfam,
            train_active_sim,
            train_inactive_sim,
            train_eff_sim,
            train_margin,
            np.asarray(train_knn, dtype=float),
            train_curvature,
            train_curvature**2,
            train_curvature**3,
            eff_projection_train,
            np.asarray(train_manifold, dtype=float),
            train_eff_rel,
        ]
    )
    test_out = np.column_stack(
        [
            test_crossfam,
            test_active_sim,
            test_inactive_sim,
            test_eff_sim,
            test_margin,
            np.asarray(test_knn, dtype=float),
            test_curvature,
            test_curvature**2,
            test_curvature**3,
            eff_projection_test,
            np.asarray(test_manifold, dtype=float),
            test_eff_rel,
        ]
    )
    return train_out, test_out


def build_composition_projection(train_comp, test_comp, y_train, eff_train):
    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)
    weights = eff_train + 0.01
    active_mask = y_train == 1
    inactive_mask = ~active_mask

    active_center = np.average(
        train_comp[active_mask],
        axis=0,
        weights=weights[active_mask],
    )
    inactive_center = np.average(train_comp[inactive_mask], axis=0)
    eff_center = np.average(train_comp, axis=0, weights=weights)

    train_active_proj = train_comp @ active_center
    test_active_proj = test_comp @ active_center
    train_inactive_proj = train_comp @ inactive_center
    test_inactive_proj = test_comp @ inactive_center
    train_eff_proj = train_comp @ eff_center
    test_eff_proj = test_comp @ eff_center

    train_margin = train_active_proj - train_inactive_proj
    test_margin = test_active_proj - test_inactive_proj

    return (
        np.column_stack(
            [
                train_active_proj,
                train_inactive_proj,
                train_eff_proj,
                train_margin,
            ]
        ),
        np.column_stack(
            [
                test_active_proj,
                test_inactive_proj,
                test_eff_proj,
                test_margin,
            ]
        ),
    )


def build_similarity_diffusion(train_emb, test_emb, y_train, eff_train, alpha=0.65):
    train_emb = np.asarray(train_emb, dtype=float)
    test_emb = np.asarray(test_emb, dtype=float)
    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)

    train_norm = train_emb / (np.linalg.norm(train_emb, axis=1, keepdims=True) + 1e-8)
    test_norm = test_emb / (np.linalg.norm(test_emb, axis=1, keepdims=True) + 1e-8)

    sim_train = train_norm @ train_norm.T
    np.fill_diagonal(sim_train, 0.0)
    sim_train = np.maximum(sim_train, 0.0)
    row_sum = sim_train.sum(axis=1, keepdims=True) + 1e-8
    trans = sim_train / row_sum

    eff_seed = minmax(eff_train)
    act_seed = y_train.astype(float)
    seed = 0.65 * eff_seed + 0.35 * act_seed
    propagated = np.linalg.solve(
        np.eye(len(train_emb)) - alpha * trans,
        (1.0 - alpha) * seed,
    )

    sim_test = np.maximum(test_norm @ train_norm.T, 0.0)
    test_w = sim_test / (sim_test.sum(axis=1, keepdims=True) + 1e-8)
    test_prop = test_w @ propagated
    train_prop = propagated
    return train_prop, test_prop


def build_similarity_diffusion_adaptive(train_emb, test_emb, y_train, eff_train):
    train_emb = np.asarray(train_emb, dtype=float)
    test_emb = np.asarray(test_emb, dtype=float)
    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)

    train_norm = train_emb / (np.linalg.norm(train_emb, axis=1, keepdims=True) + 1e-8)
    test_norm = test_emb / (np.linalg.norm(test_emb, axis=1, keepdims=True) + 1e-8)

    sim_train = np.maximum(train_norm @ train_norm.T, 0.0)
    np.fill_diagonal(sim_train, 0.0)
    density = sim_train.mean(axis=1)
    median_density = np.median(density) + 1e-8
    row_alpha = 0.45 + 0.35 * np.clip(median_density / (density + 1e-8), 0.5, 1.5)
    trans = sim_train / (sim_train.sum(axis=1, keepdims=True) + 1e-8)
    weighted_trans = trans * row_alpha[:, None]
    seed = 0.65 * minmax(eff_train) + 0.35 * y_train.astype(float)
    propagated = np.linalg.solve(np.eye(len(train_emb)) - weighted_trans, (1.0 - row_alpha) * seed)

    sim_test = np.maximum(test_norm @ train_norm.T, 0.0)
    test_w = sim_test / (sim_test.sum(axis=1, keepdims=True) + 1e-8)
    test_prop = test_w @ propagated
    return propagated, test_prop


def build_quantum_features(train_emb, test_emb, y_train, eff_train, beta=0.35):
    train_emb = np.asarray(train_emb, dtype=float)
    test_emb = np.asarray(test_emb, dtype=float)
    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)

    train_norm = train_emb / (np.linalg.norm(train_emb, axis=1, keepdims=True) + 1e-8)
    test_norm = test_emb / (np.linalg.norm(test_emb, axis=1, keepdims=True) + 1e-8)

    sim_train = np.clip(train_norm @ train_norm.T, -1.0, 1.0)
    sim_test = np.clip(test_norm @ train_norm.T, -1.0, 1.0)
    qk_train = np.cos(sim_train) ** 2
    qk_test = np.cos(sim_test) ** 2
    np.fill_diagonal(qk_train, 0.0)

    active_mask = y_train == 1
    inactive_mask = ~active_mask
    weights = eff_train + 0.01
    active_center = np.average(train_norm[active_mask], axis=0, weights=weights[active_mask])
    inactive_center = train_norm[inactive_mask].mean(axis=0)
    active_center /= np.linalg.norm(active_center) + 1e-8
    inactive_center /= np.linalg.norm(inactive_center) + 1e-8

    train_q_active = np.arccos(np.clip(train_norm @ active_center, -1.0, 1.0))
    test_q_active = np.arccos(np.clip(test_norm @ active_center, -1.0, 1.0))
    train_q_inactive = np.arccos(np.clip(train_norm @ inactive_center, -1.0, 1.0))
    test_q_inactive = np.arccos(np.clip(test_norm @ inactive_center, -1.0, 1.0))
    train_q_margin = train_q_inactive - train_q_active
    test_q_margin = test_q_inactive - test_q_active

    deg = np.diag(qk_train.sum(axis=1))
    lap = deg - qk_train
    seed = 0.7 * minmax(eff_train) + 0.3 * y_train.astype(float)
    walk = expm(-beta * lap) @ seed
    qtest_weights = qk_test / (qk_test.sum(axis=1, keepdims=True) + 1e-8)
    qtest_walk = qtest_weights @ walk

    eigvals, eigvecs = np.linalg.eigh(qk_train + 1e-6 * np.eye(qk_train.shape[0]))
    lead = eigvecs[:, -1] / np.sqrt(max(eigvals[-1], 1e-8))
    train_qpca = qk_train @ lead
    test_qpca = qk_test @ lead

    return (
        np.column_stack([train_q_margin, walk, train_qpca]),
        np.column_stack([test_q_margin, qtest_walk, test_qpca]),
    )


def build_cleft_family_features(train_df, test_df, groups_train):
    cleft_score_col = "cleft_open_score"
    if cleft_score_col not in train_df.columns:
        return np.zeros((len(train_df), 2)), np.zeros((len(test_df), 2))

    train_score = train_df[cleft_score_col].to_numpy(dtype=float)
    test_score = test_df[cleft_score_col].to_numpy(dtype=float)
    train_fill = float(np.nanmean(train_score)) if np.isfinite(np.nanmean(train_score)) else 0.0
    test_fill = train_fill
    train_score = np.nan_to_num(train_score, nan=train_fill)
    test_score = np.nan_to_num(test_score, nan=test_fill)
    groups_train = np.asarray(groups_train)
    family_means = {}
    unique_fams = np.unique(groups_train)
    for fam in unique_fams:
        fam_mask = groups_train == fam
        family_means[fam] = float(np.nanmean(train_score[fam_mask]))

    all_family_vals = np.array(list(family_means.values()), dtype=float)
    global_mean = float(np.nanmean(all_family_vals))
    global_std = float(np.nanstd(all_family_vals) + 1e-8)

    train_z = np.zeros(len(train_df), dtype=float)
    for idx, fam in enumerate(groups_train):
        other_vals = [v for k, v in family_means.items() if k != fam]
        if other_vals:
            ref_mean = float(np.nanmean(other_vals))
            ref_std = float(np.nanstd(other_vals) + 1e-8)
        else:
            ref_mean = global_mean
            ref_std = global_std
        train_z[idx] = (train_score[idx] - ref_mean) / ref_std

    test_z = (test_score - global_mean) / global_std
    return (
        np.column_stack([train_score, train_z]),
        np.column_stack([test_score, test_z]),
    )


def build_cleft_residual_features(
    train_df,
    test_df,
    train_emb,
    test_emb,
    y_train,
    eff_train,
    groups_train,
):
    cleft_cols = [
        col
        for col in [
            "cleft_triangle_area",
            "cleft_sasa_mean",
            "cleft_local_density",
            "thumb_palm_distance_proxy",
            "cleft_open_score",
            "cleft_curvature_proxy",
            "cleft_thumb_asymmetry",
            "cleft_tunnel_curvature_score",
        ]
        if col in train_df.columns
    ]
    if not cleft_cols:
        return np.zeros((len(train_df), 5)), np.zeros((len(test_df), 5))

    imp = SimpleImputer(strategy="median")
    cleft_train = imp.fit_transform(train_df[cleft_cols])
    cleft_test = imp.transform(test_df[cleft_cols])

    emb_train = np.asarray(train_emb, dtype=float)
    emb_test = np.asarray(test_emb, dtype=float)
    emb_scaler = StandardScaler()
    emb_train_s = emb_scaler.fit_transform(emb_train)
    emb_test_s = emb_scaler.transform(emb_test)

    n_comp = int(min(8, emb_train_s.shape[0] - 1, emb_train_s.shape[1], cleft_train.shape[1]))
    if n_comp >= 2:
        pls = PLSRegression(n_components=n_comp, scale=True)
        pls.fit(emb_train_s, cleft_train)
        pred_train = pls.predict(emb_train_s)
        pred_test = pls.predict(emb_test_s)
    else:
        pred_train = np.tile(np.nanmean(cleft_train, axis=0, keepdims=True), (len(train_df), 1))
        pred_test = np.tile(np.nanmean(cleft_train, axis=0, keepdims=True), (len(test_df), 1))

    resid_train = cleft_train - pred_train
    resid_test = cleft_test - pred_test

    weights = np.asarray(eff_train, dtype=float) + 0.01
    active_mask = np.asarray(y_train, dtype=int) == 1
    inactive_mask = ~active_mask

    emb_center = emb_train_s - emb_train_s.mean(axis=0, keepdims=True)
    eff_center = np.average(emb_center, axis=0, weights=weights)
    inactive_center = emb_center[inactive_mask].mean(axis=0)
    axis = eff_center - inactive_center
    axis /= np.linalg.norm(axis) + 1e-8

    projection_train = emb_center @ axis
    projection_test = (emb_test_s - emb_train_s.mean(axis=0, keepdims=True)) @ axis

    cleft_open_idx = cleft_cols.index("cleft_open_score") if "cleft_open_score" in cleft_cols else 0
    cleft_asym_idx = cleft_cols.index("cleft_thumb_asymmetry") if "cleft_thumb_asymmetry" in cleft_cols else 0
    cleft_curve_idx = cleft_cols.index("cleft_tunnel_curvature_score") if "cleft_tunnel_curvature_score" in cleft_cols else 0

    open_resid_train = resid_train[:, cleft_open_idx]
    open_resid_test = resid_test[:, cleft_open_idx]
    asym_train = cleft_train[:, cleft_asym_idx]
    asym_test = cleft_test[:, cleft_asym_idx]
    curve_train = cleft_train[:, cleft_curve_idx]
    curve_test = cleft_test[:, cleft_curve_idx]

    align_train = open_resid_train * projection_train
    align_test = open_resid_test * projection_test

    groups_train = np.asarray(groups_train)
    family_active_means = {}
    for fam in np.unique(groups_train):
        fam_mask = (groups_train == fam) & active_mask
        if fam_mask.sum() > 0:
            family_active_means[fam] = float(np.mean(open_resid_train[fam_mask]))
    global_family_mean = float(np.mean(list(family_active_means.values()))) if family_active_means else 0.0
    global_family_std = float(np.std(list(family_active_means.values())) + 1e-8) if family_active_means else 1.0
    train_family_resid = np.zeros(len(train_df), dtype=float)
    for idx, fam in enumerate(groups_train):
        other = [v for k, v in family_active_means.items() if k != fam]
        ref_mean = float(np.mean(other)) if other else global_family_mean
        ref_std = float(np.std(other) + 1e-8) if other else global_family_std
        train_family_resid[idx] = (open_resid_train[idx] - ref_mean) / ref_std
    test_family_resid = (open_resid_test - global_family_mean) / global_family_std

    return (
        np.column_stack(
            [
                open_resid_train,
                align_train,
                asym_train,
                curve_train,
                train_family_resid,
            ]
        ),
        np.column_stack(
            [
                open_resid_test,
                align_test,
                asym_test,
                curve_test,
                test_family_resid,
            ]
        ),
    )


def load_pdb_graph_features(rt_names, threshold=10.0):
    rows = []
    struct_dir = ROOT / "data" / "structures"
    for name in rt_names:
        pdb_path = struct_dir / f"{name}.pdb"
        coords = []
        if pdb_path.exists():
            with pdb_path.open("r", encoding="utf-8", errors="ignore") as handle:
                for line in handle:
                    if not line.startswith("ATOM"):
                        continue
                    atom_name = line[12:16].strip()
                    if atom_name != "CA":
                        continue
                    try:
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                    except ValueError:
                        continue
                    coords.append((x, y, z))
        arr = np.asarray(coords, dtype=float)
        if arr.shape[0] < 3:
            rows.append(
                {
                    "rt_name": name,
                    "graph_edge_density": 0.0,
                    "graph_mean_degree": 0.0,
                    "graph_std_degree": 0.0,
                    "graph_spectral_radius": 0.0,
                    "graph_lambda2": 0.0,
                    "graph_contact_entropy": 0.0,
                }
            )
            continue

        diff = arr[:, None, :] - arr[None, :, :]
        dist = np.sqrt(np.sum(diff**2, axis=2))
        adj = ((dist < threshold) & (dist > 0)).astype(float)
        deg = adj.sum(axis=1)
        n = adj.shape[0]
        edge_density = adj.sum() / (n * (n - 1) + 1e-8)
        spectral_radius = float(np.max(np.linalg.eigvalsh(adj)))
        lap = np.diag(deg) - adj
        lap_eigs = np.sort(np.linalg.eigvalsh(lap))
        lambda2 = float(lap_eigs[1]) if lap_eigs.size > 1 else 0.0
        p = deg / (deg.sum() + 1e-8)
        contact_entropy = float(-(p * np.log(p + 1e-8)).sum())
        rows.append(
            {
                "rt_name": name,
                "graph_edge_density": float(edge_density),
                "graph_mean_degree": float(deg.mean()),
                "graph_std_degree": float(deg.std()),
                "graph_spectral_radius": float(spectral_radius),
                "graph_lambda2": float(lambda2),
                "graph_contact_entropy": float(contact_entropy),
            }
        )

    return pd.DataFrame(rows).set_index("rt_name")


def build_graph_proxy_features(X_train_df, X_test_df, graph_train_df, graph_test_df, structure_cols, topology_cols):
    cols = [c for c in (structure_cols + topology_cols) if c in X_train_df.columns]
    train_num = graph_train_df.copy()
    test_num = graph_test_df.copy()

    if cols:
        train_num = pd.concat([train_num, X_train_df[cols].copy()], axis=1)
        test_num = pd.concat([test_num, X_test_df[cols].copy()], axis=1)
    if train_num.shape[1] == 0:
        return np.zeros((len(X_train_df), 1)), np.zeros((len(X_test_df), 1))

    for left in ["radius_gyration", "avg_ca_distance", "top_mean_ca_dist", "top_max_ca_dist"]:
        for right in ["top_contact_density", "top_mean_degree", "top_entropy_degree", "top_contact_entropy"]:
            if left in train_num.columns and right in train_num.columns:
                name = f"{left}__x__{right}"
                train_num[name] = train_num[left] * train_num[right]
                test_num[name] = test_num[left] * test_num[right]

    for left, right, name in [
        ("top_mean_degree", "top_std_degree", "degree_cv_proxy"),
        ("top_contact_density", "top_long_range_ratio", "contact_long_range_mul"),
        ("top_clustering_proxy", "top_contact_entropy", "cluster_entropy_mul"),
    ]:
        if left in train_num.columns and right in train_num.columns:
            train_num[name] = train_num[left] / (train_num[right] + 1e-8)
            test_num[name] = test_num[left] / (test_num[right] + 1e-8)

    imp = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    train_arr = scaler.fit_transform(imp.fit_transform(train_num))
    test_arr = scaler.transform(imp.transform(test_num))
    return train_arr, test_arr


def fit_weighted_rank_head(train_features, eff_train, y_train, sample_weight, test_features):
    base_mask = np.asarray(y_train, dtype=int) == 1
    if base_mask.sum() < 3:
        base_mask = np.ones_like(base_mask, dtype=bool)

    masked_eff = eff_train[base_mask]
    use_mask = base_mask.copy()
    if masked_eff.size >= 6:
        lo = np.quantile(masked_eff, 0.30)
        hi = np.quantile(masked_eff, 0.70)
        use_mask[base_mask] = (masked_eff <= lo) | (masked_eff >= hi)
        if use_mask.sum() < 4:
            use_mask = base_mask

    rank_targets = rankdata(eff_train[use_mask], method="average").astype(float)
    rank_targets = rank_targets / (rank_targets.max() + 1e-8)
    local_weight = np.asarray(sample_weight[use_mask], dtype=float).copy()
    local_weight *= np.where(np.asarray(y_train, dtype=int)[use_mask] == 1, 2.0, 1.0)
    model = Ridge(alpha=1.5, random_state=42)
    model.fit(
        train_features[use_mask],
        rank_targets,
        sample_weight=local_weight,
    )
    train_scores = model.predict(train_features[use_mask])
    test_scores = model.predict(test_features)
    return train_scores, test_scores, use_mask


def fit_listwise_rank_head(train_features, eff_train, y_train, sample_weight, test_features):
    mask = np.asarray(y_train, dtype=int) == 1
    if mask.sum() < 4:
        mask = np.ones_like(mask, dtype=bool)

    x_train = np.asarray(train_features[mask], dtype=float)
    x_test = np.asarray(test_features, dtype=float)
    y_eff = np.asarray(eff_train[mask], dtype=float)
    w = np.asarray(sample_weight[mask], dtype=float)

    scaler = StandardScaler()
    x_train = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)

    order = np.argsort(y_eff)[::-1]
    x_ord = x_train[order]
    w_ord = w[order] / (w.sum() + 1e-8)

    def objective(theta):
        beta = theta[:-1]
        bias = theta[-1]
        scores = x_ord @ beta + bias
        tails = np.empty_like(scores)
        acc = -np.inf
        for idx in range(len(scores) - 1, -1, -1):
            acc = np.logaddexp(acc, scores[idx])
            tails[idx] = acc
        loss = -np.sum(w_ord * (scores - tails))
        reg = 1e-3 * np.sum(beta**2)
        return float(loss + reg)

    theta0 = np.zeros(x_train.shape[1] + 1, dtype=float)
    result = minimize(objective, theta0, method="L-BFGS-B")
    if not result.success:
        ridge = Ridge(alpha=1.0, random_state=42)
        rank_targets = rankdata(y_eff, method="average").astype(float)
        rank_targets = rank_targets / (rank_targets.max() + 1e-8)
        ridge.fit(x_train, rank_targets, sample_weight=w)
        train_scores = ridge.predict(x_train)
        test_scores = ridge.predict(x_test)
    else:
        beta = result.x[:-1]
        bias = result.x[-1]
        train_scores = x_train @ beta + bias
        test_scores = x_test @ beta + bias
    return train_scores, test_scores, mask


def fit_pairwise_rank_head(train_features, eff_train, y_train, sample_weight, test_features):
    mask = np.asarray(y_train, dtype=int) == 1
    if mask.sum() < 4:
        mask = np.ones_like(mask, dtype=bool)

    x_train = np.asarray(train_features[mask], dtype=float)
    x_test = np.asarray(test_features, dtype=float)
    eff = np.asarray(eff_train[mask], dtype=float)
    w = np.asarray(sample_weight[mask], dtype=float)

    scaler = StandardScaler()
    x_train = scaler.fit_transform(x_train)
    x_test = scaler.transform(x_test)

    pairs = []
    pair_weights = []
    n = x_train.shape[0]
    for i in range(n):
        for j in range(i + 1, n):
            if eff[i] == eff[j]:
                continue
            if eff[i] > eff[j]:
                diff = x_train[i] - x_train[j]
                pw = w[i] * w[j]
            else:
                diff = x_train[j] - x_train[i]
                pw = w[i] * w[j]
            pairs.append(diff)
            pair_weights.append(pw)

    if len(pairs) < 3:
        ridge = Ridge(alpha=1.0, random_state=42)
        rank_targets = rankdata(eff, method="average").astype(float)
        rank_targets = rank_targets / (rank_targets.max() + 1e-8)
        ridge.fit(x_train, rank_targets, sample_weight=w)
        return ridge.predict(x_train), ridge.predict(x_test), mask

    pair_x = np.asarray(pairs, dtype=float)
    pair_w = np.asarray(pair_weights, dtype=float)
    pair_w = pair_w / (pair_w.mean() + 1e-8)

    def objective(theta):
        beta = theta[:-1]
        bias = theta[-1]
        margins = pair_x @ beta + bias
        loss = np.sum(pair_w * np.log1p(np.exp(-margins)))
        reg = 1e-3 * np.sum(beta**2)
        return float(loss + reg)

    theta0 = np.zeros(x_train.shape[1] + 1, dtype=float)
    res = minimize(objective, theta0, method="L-BFGS-B")
    if not res.success:
        ridge = Ridge(alpha=1.0, random_state=42)
        rank_targets = rankdata(eff, method="average").astype(float)
        rank_targets = rank_targets / (rank_targets.max() + 1e-8)
        ridge.fit(x_train, rank_targets, sample_weight=w)
        return ridge.predict(x_train), ridge.predict(x_test), mask

    beta = res.x[:-1]
    bias = res.x[-1]
    return x_train @ beta + bias, x_test @ beta + bias, mask


def run_search():
    X, y, groups = engineer_features()
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv").set_index("rt_name")
    seq = seq.loc[X.index]
    seq_comp = build_sequence_features(seq["sequence"])
    embeddings = load_embeddings(X.index.tolist())
    pdb_graph = load_pdb_graph_features(X.index.tolist()).loc[X.index]
    base_pred = pd.read_csv(ROOT / "results" / "calibrated_predictions_selected_features.csv")
    base_map = base_pred.set_index("rt_name")["predicted_score"]
    base_oof = base_map.loc[X.index].to_numpy(dtype=float)

    structure_cols = [
        col
        for col in ["n_atoms", "n_residues", "radius_gyration", "avg_ca_distance"]
        if col in X.columns
    ]
    topology_cols = [col for col in X.columns if str(col).startswith("top_")]
    kinetic_cols = [
        col
        for col in X.columns
        if any(
            key in str(col).lower()
            for key in [
                "perplexity",
                "likelihood",
                "instability",
                "isoelectric",
                "helix",
                "turn",
                "sheet",
                "gravy",
                "charge",
                "t40",
                "t45",
                "t50",
                "t55",
                "t60",
                "t65",
                "t70",
                "t75",
                "t80",
                "thermo",
                "triad",
                "motif",
                "camsol",
                "sasa",
                "thumb",
                "surface",
                "entropy",
                "contact",
                "degree",
                "clustering",
                "radius_gyration",
                "avg_ca_distance",
            ]
        )
    ]
    cleft_cols = [
        col
        for col in [
            "cleft_triangle_area",
            "cleft_sasa_mean",
            "cleft_local_density",
            "thumb_palm_distance_proxy",
            "cleft_open_score",
            "cleft_curvature_proxy",
        ]
        if col in X.columns
    ]

    logo = LeaveOneGroupOut()
    reg_branch = np.zeros(len(X), dtype=float)
    clf_branch = np.zeros(len(X), dtype=float)
    struct_branch = np.zeros(len(X), dtype=float)
    topo_branch = np.zeros(len(X), dtype=float)
    rank_branch = np.zeros(len(X), dtype=float)
    pairwise_branch = np.zeros(len(X), dtype=float)
    effproj_branch = np.zeros(len(X), dtype=float)
    margin_branch = np.zeros(len(X), dtype=float)
    diffusion_branch = np.zeros(len(X), dtype=float)
    diffusion_adapt_branch = np.zeros(len(X), dtype=float)
    graph_branch = np.zeros(len(X), dtype=float)
    listwise_branch = np.zeros(len(X), dtype=float)
    adapter_branch = np.zeros(len(X), dtype=float)
    qmargin_branch = np.zeros(len(X), dtype=float)
    qdiff_branch = np.zeros(len(X), dtype=float)
    qpca_branch = np.zeros(len(X), dtype=float)
    kinetic_branch = np.zeros(len(X), dtype=float)
    cleft_branch = np.zeros(len(X), dtype=float)

    for train_idx, test_idx in logo.split(X, y, groups):
        X_train_df = X.iloc[train_idx]
        X_test_df = X.iloc[test_idx]
        y_train = y.iloc[train_idx].to_numpy(dtype=int)
        groups_train = groups.iloc[train_idx].to_numpy()
        eff_train = seq.iloc[train_idx]["pe_efficiency_pct"].to_numpy(dtype=float)

        imputer = SimpleImputer(strategy="median")
        X_train_imp = imputer.fit_transform(X_train_df)
        X_test_imp = imputer.transform(X_test_df)
        X_train_scaled, X_test_scaled = group_exclusion_scale(
            X_train_imp,
            groups_train,
            X_test_imp,
        )

        comp_scaler = StandardScaler()
        train_comp = comp_scaler.fit_transform(seq_comp.iloc[train_idx].to_numpy(dtype=float))
        test_comp = comp_scaler.transform(seq_comp.iloc[test_idx].to_numpy(dtype=float))

        embed_train_feat, embed_test_feat = build_embedding_features(
            embeddings[train_idx],
            embeddings[test_idx],
            y_train,
            groups_train,
            eff_train,
        )
        comp_train_feat, comp_test_feat = build_composition_projection(
            train_comp,
            test_comp,
            y_train,
            eff_train,
        )
        diff_train_feat, diff_test_feat = build_similarity_diffusion(
            embeddings[train_idx],
            embeddings[test_idx],
            y_train,
            eff_train,
        )
        diffa_train_feat, diffa_test_feat = build_similarity_diffusion_adaptive(
            embeddings[train_idx],
            embeddings[test_idx],
            y_train,
            eff_train,
        )
        quantum_train_feat, quantum_test_feat = build_quantum_features(
            embeddings[train_idx],
            embeddings[test_idx],
            y_train,
            eff_train,
        )
        emb_train_norm = embeddings[train_idx] / (
            np.linalg.norm(embeddings[train_idx], axis=1, keepdims=True) + 1e-8
        )
        emb_test_norm = embeddings[test_idx] / (
            np.linalg.norm(embeddings[test_idx], axis=1, keepdims=True) + 1e-8
        )
        graph_train_feat, graph_test_feat = build_graph_proxy_features(
            X_train_df,
            X_test_df,
            pdb_graph.iloc[train_idx],
            pdb_graph.iloc[test_idx],
            structure_cols,
            topology_cols,
        )
        cleft_train_family, cleft_test_family = build_cleft_family_features(
            X_train_df,
            X_test_df,
            groups_train,
        )
        cleft_resid_train, cleft_resid_test = build_cleft_residual_features(
            X_train_df,
            X_test_df,
            embeddings[train_idx],
            embeddings[test_idx],
            y_train,
            eff_train,
            groups_train,
        )

        X_train_aug = np.hstack([X_train_scaled, train_comp, comp_train_feat, embed_train_feat])
        X_test_aug = np.hstack([X_test_scaled, test_comp, comp_test_feat, embed_test_feat])

        reg = RandomForestRegressor(
            n_estimators=1000,
            max_depth=8,
            min_samples_leaf=2,
            max_features="log2",
            random_state=42,
            n_jobs=1,
        )
        clf = ExtraTreesClassifier(
            n_estimators=1200,
            max_depth=None,
            min_samples_leaf=1,
            class_weight="balanced",
            max_features="sqrt",
            random_state=42,
            n_jobs=1,
        )

        eff_train_norm = (eff_train - eff_train.mean()) / (eff_train.std() + 1e-8)
        reg.fit(X_train_aug, eff_train_norm)
        clf.fit(X_train_aug, y_train)

        reg_train = reg.predict(X_train_aug)
        reg_test = reg.predict(X_test_aug)
        clf_train = clf.predict_proba(X_train_aug)[:, 1]
        clf_test = clf.predict_proba(X_test_aug)[:, 1]

        reg_branch[test_idx] = rankpct_by_train(reg_train, reg_test)
        clf_branch[test_idx] = zsig_by_train(clf_train, clf_test)
        margin_branch[test_idx] = rankpct_by_train(
            embed_train_feat[:, 4],
            embed_test_feat[:, 4],
        )
        effproj_branch[test_idx] = rankpct_by_train(
            embed_train_feat[:, 9],
            embed_test_feat[:, 9],
        )
        # New manifold residual and family-relative efficiency projection signals.
        manifold_train = embed_train_feat[:, 10]
        manifold_test = embed_test_feat[:, 10]
        familyrel_train = embed_train_feat[:, 11]
        familyrel_test = embed_test_feat[:, 11]
        diffusion_branch[test_idx] = rankpct_by_train(diff_train_feat, diff_test_feat)
        diffusion_adapt_branch[test_idx] = rankpct_by_train(diffa_train_feat, diffa_test_feat)
        qmargin_branch[test_idx] = rankpct_by_train(
            quantum_train_feat[:, 0],
            quantum_test_feat[:, 0],
        )
        qdiff_branch[test_idx] = rankpct_by_train(
            quantum_train_feat[:, 1],
            quantum_test_feat[:, 1],
        )
        qpca_branch[test_idx] = rankpct_by_train(
            quantum_train_feat[:, 2],
            quantum_test_feat[:, 2],
        )
        n_pls = int(min(8, emb_train_norm.shape[0] - 1, emb_train_norm.shape[1]))
        if n_pls >= 2:
            pls = PLSRegression(n_components=n_pls, scale=True)
            pls.fit(emb_train_norm, eff_train_norm)
            adapter_train = pls.predict(emb_train_norm).ravel()
            adapter_test = pls.predict(emb_test_norm).ravel()
            adapter_branch[test_idx] = rankpct_by_train(adapter_train, adapter_test)

        if structure_cols:
            struct_imputer = SimpleImputer(strategy="median")
            struct_scaler = StandardScaler()
            X_train_struct = struct_scaler.fit_transform(
                struct_imputer.fit_transform(X_train_df[structure_cols])
            )
            X_test_struct = struct_scaler.transform(
                struct_imputer.transform(X_test_df[structure_cols])
            )
            struct_model = Ridge(alpha=2.0, random_state=42)
            struct_model.fit(
                X_train_struct,
                eff_train_norm - reg_train,
                sample_weight=eff_train + 0.01,
            )
            struct_train = struct_model.predict(X_train_struct)
            struct_test = struct_model.predict(X_test_struct)
            struct_branch[test_idx] = zsig_by_train(struct_train, struct_test)

        if topology_cols:
            topo_imputer = SimpleImputer(strategy="median")
            X_train_topo_imp = topo_imputer.fit_transform(X_train_df[topology_cols])
            X_test_topo_imp = topo_imputer.transform(X_test_df[topology_cols])
            X_train_topo, X_test_topo = group_exclusion_scale(
                X_train_topo_imp,
                groups_train,
                X_test_topo_imp,
            )
            topo_model = Ridge(alpha=1.2, random_state=42)
            topo_model.fit(
                X_train_topo,
                eff_train_norm - reg_train,
                sample_weight=eff_train + 0.01,
            )
            topo_train = topo_model.predict(X_train_topo)
            topo_test = topo_model.predict(X_test_topo)
            topo_branch[test_idx] = zsig_by_train(topo_train, topo_test)

        rank_train_feat = np.column_stack(
            [
                reg_train,
                clf_train,
                diff_train_feat,
                embed_train_feat[:, 0],
                embed_train_feat[:, 3],
                embed_train_feat[:, 4],
                embed_train_feat[:, 5],
                embed_train_feat[:, 6],
                embed_train_feat[:, 7],
                embed_train_feat[:, 8],
                embed_train_feat[:, 9],
                manifold_train,
                familyrel_train,
                comp_train_feat[:, 2],
                comp_train_feat[:, 3],
            ]
        )
        rank_test_feat = np.column_stack(
            [
                reg_test,
                clf_test,
                diff_test_feat,
                embed_test_feat[:, 0],
                embed_test_feat[:, 3],
                embed_test_feat[:, 4],
                embed_test_feat[:, 5],
                embed_test_feat[:, 6],
                embed_test_feat[:, 7],
                embed_test_feat[:, 8],
                embed_test_feat[:, 9],
                manifold_test,
                familyrel_test,
                comp_test_feat[:, 2],
                comp_test_feat[:, 3],
            ]
        )
        rank_train_scores, rank_test_scores, rank_mask = fit_weighted_rank_head(
            rank_train_feat,
            eff_train,
            y_train,
            eff_train + 0.01,
            rank_test_feat,
        )
        rank_branch[test_idx] = rankpct_by_train(rank_train_scores, rank_test_scores)
        list_train_scores, list_test_scores, _ = fit_listwise_rank_head(
            rank_train_feat,
            eff_train,
            y_train,
            eff_train + 0.01,
            rank_test_feat,
        )
        listwise_branch[test_idx] = rankpct_by_train(list_train_scores, list_test_scores)
        pair_train_scores, pair_test_scores, _ = fit_pairwise_rank_head(
            rank_train_feat,
            eff_train,
            y_train,
            eff_train + 0.01,
            rank_test_feat,
        )
        pairwise_branch[test_idx] = rankpct_by_train(pair_train_scores, pair_test_scores)

        if graph_train_feat.shape[1] > 0:
            graph_model = Ridge(alpha=1.0, random_state=42)
            graph_targets = rankdata(eff_train, method="average").astype(float)
            graph_targets = graph_targets / (graph_targets.max() + 1e-8)
            graph_model.fit(
                graph_train_feat,
                graph_targets,
                sample_weight=eff_train + 0.01,
            )
            graph_train_scores = graph_model.predict(graph_train_feat)
            graph_test_scores = graph_model.predict(graph_test_feat)
            graph_branch[test_idx] = rankpct_by_train(graph_train_scores, graph_test_scores)

        if kinetic_cols:
            kin_imp = SimpleImputer(strategy="median")
            kin_train_imp = kin_imp.fit_transform(X_train_df[kinetic_cols])
            kin_test_imp = kin_imp.transform(X_test_df[kinetic_cols])
            kin_train, kin_test = group_exclusion_scale(
                kin_train_imp,
                groups_train,
                kin_test_imp,
            )
            kin_reg = RandomForestRegressor(
                n_estimators=600,
                max_depth=7,
                min_samples_leaf=2,
                max_features="sqrt",
                random_state=42,
                n_jobs=1,
            )
            kin_reg.fit(kin_train, eff_train_norm)
            kin_train_reg = kin_reg.predict(kin_train)
            kin_test_reg = kin_reg.predict(kin_test)

            kin_rank_train_feat = np.column_stack(
                [
                    kin_train_reg,
                    kin_train[:, : min(12, kin_train.shape[1])],
                ]
            )
            kin_rank_test_feat = np.column_stack(
                [
                    kin_test_reg,
                    kin_test[:, : min(12, kin_test.shape[1])],
                ]
            )
            kin_rank_train, kin_rank_test, _ = fit_weighted_rank_head(
                kin_rank_train_feat,
                eff_train,
                y_train,
                eff_train + 0.01,
                kin_rank_test_feat,
            )
            kin_reg_score = rankpct_by_train(kin_train_reg, kin_test_reg)
            kin_rank_score = rankpct_by_train(kin_rank_train, kin_rank_test)
            kinetic_branch[test_idx] = 0.55 * kin_reg_score + 0.45 * kin_rank_score

        if cleft_cols:
            cleft_imp = SimpleImputer(strategy="median")
            cleft_train_imp = cleft_imp.fit_transform(X_train_df[cleft_cols])
            cleft_test_imp = cleft_imp.transform(X_test_df[cleft_cols])
            cleft_train_scaled, cleft_test_scaled = group_exclusion_scale(
                cleft_train_imp,
                groups_train,
                cleft_test_imp,
            )
            cleft_train_feat = np.hstack(
                [cleft_train_scaled, cleft_train_family, cleft_resid_train]
            )
            cleft_test_feat = np.hstack(
                [cleft_test_scaled, cleft_test_family, cleft_resid_test]
            )
            cleft_reg = Ridge(alpha=1.5, random_state=42)
            cleft_reg.fit(
                cleft_train_feat,
                eff_train_norm,
                sample_weight=eff_train + 0.01,
            )
            cleft_train_reg = cleft_reg.predict(cleft_train_feat)
            cleft_test_reg = cleft_reg.predict(cleft_test_feat)
            cleft_rank_train, cleft_rank_test, _ = fit_weighted_rank_head(
                cleft_train_feat,
                eff_train,
                y_train,
                eff_train + 0.01,
                cleft_test_feat,
            )
            cleft_reg_score = rankpct_by_train(cleft_train_reg, cleft_test_reg)
            cleft_rank_score = rankpct_by_train(cleft_rank_train, cleft_rank_test)
            active_frac = float(y_train.mean())
            cleft_mix = 0.35 * cleft_reg_score + 0.65 * cleft_rank_score
            cleft_branch[test_idx] = cleft_mix * (0.75 + 0.25 * active_frac)

    components = {
        "base": minmax(base_oof),
        "reg": minmax(reg_branch),
        "clf": minmax(clf_branch),
        "struct": minmax(struct_branch),
        "topo": minmax(topo_branch),
        "rank": minmax(rank_branch),
        "pairwise": minmax(pairwise_branch),
        "effproj": minmax(effproj_branch),
        "margin": minmax(margin_branch),
        "diffusion": minmax(diffusion_branch),
        "diffusion_adapt": minmax(diffusion_adapt_branch),
        "graph": minmax(graph_branch),
        "listwise": minmax(listwise_branch),
        "adapter": minmax(adapter_branch),
        "qmargin": minmax(qmargin_branch),
        "qdiff": minmax(qdiff_branch),
        "qpca": minmax(qpca_branch),
        "kinetic": minmax(kinetic_branch),
        "cleft": minmax(cleft_branch),
    }

    y_true = y.to_numpy(dtype=float)
    eff_true = seq["pe_efficiency_pct"].to_numpy(dtype=float)

    keys = list(components.keys())

    def objective(weights):
        score = np.zeros(len(X), dtype=float)
        for key, weight in zip(keys, weights):
            score += weight * components[key]
        result = compute_cls(y_true, score, eff_true)
        return -float(result["cls"])

    result = differential_evolution(
        objective,
        bounds=[(-1.0, 2.5)] * len(keys),
        seed=42,
        polish=True,
        updating="deferred",
        workers=1,
        maxiter=60,
        popsize=14,
    )

    best_weights = {key: float(val) for key, val in zip(keys, result.x)}
    final_score = np.zeros(len(X), dtype=float)
    for key in keys:
        final_score += best_weights[key] * components[key]

    final_metric = compute_cls(y_true, final_score, eff_true)
    prediction_df = pd.DataFrame(
        {"rt_name": X.index.to_list(), "predicted_score": final_score}
    )
    component_df = pd.DataFrame(
        {
            "rt_name": X.index.to_list(),
            "base": components["base"],
            "reg": components["reg"],
            "clf": components["clf"],
            "struct": components["struct"],
            "topo": components["topo"],
            "rank": components["rank"],
            "pairwise": components["pairwise"],
            "effproj": components["effproj"],
            "margin": components["margin"],
            "diffusion": components["diffusion"],
            "diffusion_adapt": components["diffusion_adapt"],
            "graph": components["graph"],
            "listwise": components["listwise"],
            "adapter": components["adapter"],
            "qmargin": components["qmargin"],
            "qdiff": components["qdiff"],
            "qpca": components["qpca"],
            "kinetic": components["kinetic"],
            "cleft": components["cleft"],
        }
    )
    return prediction_df, component_df, final_metric, best_weights


def main():
    prediction_df, component_df, final_metric, best_weights = run_search()
    out_csv = ROOT / "results" / "family_conditioned_lofo_candidate.csv"
    out_components = ROOT / "results" / "family_conditioned_lofo_components.csv"
    out_json = ROOT / "results" / "family_conditioned_lofo_candidate.json"
    prediction_df.to_csv(out_csv, index=False)
    component_df.to_csv(out_components, index=False)
    out_json.write_text(
        json.dumps(
            {
                "pr_auc": float(final_metric["pr_auc"]),
                "w_spearman": float(final_metric["w_spearman"]),
                "cls": float(final_metric["cls"]),
                "weights": best_weights,
            },
            indent=2,
        )
    )
    print(
        f"PR-AUC: {final_metric['pr_auc']:.6f}\n"
        f"Weighted Spearman: {final_metric['w_spearman']:.6f}\n"
        f"CLS: {final_metric['cls']:.6f}\n"
        f"Weights: {best_weights}"
    )


if __name__ == "__main__":
    main()
