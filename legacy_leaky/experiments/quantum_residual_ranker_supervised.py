from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent
SEED = 42
RNG = np.random.default_rng(SEED)

import sys

sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "evaluation"))
from feature_engineering import engineer_features
from evaluate import compute_cls


FEATURE_KEYS = [
    "triad_distance_ratio",
    "triad_mean_dist",
    "triad_diff_dist",
    "triad_geom_mean",
    "triad_compactness",
    "triad_angle_proxy",
    "triad_best_rmsd",
    "cleft_triangle_area",
    "cleft_sasa_mean",
    "cleft_open_score",
    "cleft_curvature_proxy",
    "sasa_avg",
    "helix_sheet_ratio",
    "radius_gyration",
    "gravy",
    "isoelectric_point",
    "native_net_charge",
    "thumb_charge_ratio",
    "top_contact_entropy",
    "top_entropy_degree",
]


def load_embeddings(rt_names):
    emb = np.load(ROOT / "data" / "esm2_embeddings.npz", allow_pickle=True)
    emb_names = [str(name) for name in emb["names"]]
    name_to_idx = {name: idx for idx, name in enumerate(emb_names)}
    return np.vstack([emb["embeddings"][name_to_idx[name]] for name in rt_names]).astype(float)


def rankpct_by_train(train_scores, test_scores):
    train_sorted = np.sort(np.asarray(train_scores, dtype=float))
    positions = np.searchsorted(train_sorted, np.asarray(test_scores, dtype=float), side="right")
    return positions / (len(train_sorted) + 1.0)


def manifold_residual(base_vec, neigh_mat):
    if neigh_mat.shape[0] < 3:
        return 0.0
    local_mean = neigh_mat.mean(axis=0, keepdims=True)
    n_comp = int(min(3, neigh_mat.shape[0] - 1, neigh_mat.shape[1]))
    if n_comp < 1:
        return float(np.linalg.norm(base_vec - local_mean.ravel()))
    pca = PCA(n_components=n_comp, random_state=SEED)
    pca.fit(neigh_mat - local_mean)
    recon = pca.inverse_transform(pca.transform(base_vec[None, :] - local_mean)) + local_mean
    return float(np.linalg.norm(base_vec - recon.ravel()))


def get_feature_subset(X_df):
    return [c for c in FEATURE_KEYS if c in X_df.columns]


def prepare_specialist_features(X_train_df, X_test_df, cols, emb_train, emb_test, y_train, eff_train):
    imp = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(imp.fit_transform(X_train_df[cols])) if cols else np.zeros((len(X_train_df), 1))
    X_test = scaler.transform(imp.transform(X_test_df[cols])) if cols else np.zeros((len(X_test_df), 1))

    emb_scaler = StandardScaler()
    E_train = emb_scaler.fit_transform(emb_train)
    E_test = emb_scaler.transform(emb_test)

    n_comp = int(min(16, E_train.shape[0] - 1, E_train.shape[1]))
    if n_comp >= 2:
        pca = PCA(n_components=n_comp, random_state=SEED)
        E_train_red = pca.fit_transform(E_train)
        E_test_red = pca.transform(E_test)
    else:
        E_train_red, E_test_red = E_train, E_test

    E_train_norm = E_train_red / (np.linalg.norm(E_train_red, axis=1, keepdims=True) + 1e-8)
    E_test_norm = E_test_red / (np.linalg.norm(E_test_red, axis=1, keepdims=True) + 1e-8)

    active_mask = np.asarray(y_train, dtype=int) == 1
    if active_mask.sum() < 4:
        active_mask = np.ones_like(active_mask, dtype=bool)

    weights = np.asarray(eff_train, dtype=float) + 0.01
    eff_center = np.average(E_train_norm, axis=0, weights=weights)
    eff_center /= np.linalg.norm(eff_center) + 1e-8
    eff_proj_train = E_train_norm @ eff_center
    eff_proj_test = E_test_norm @ eff_center

    active_center = E_train_norm[active_mask].mean(axis=0)
    active_center /= np.linalg.norm(active_center) + 1e-8
    inactive_center = E_train_norm[~active_mask].mean(axis=0) if (~active_mask).sum() > 0 else -active_center
    inactive_center /= np.linalg.norm(inactive_center) + 1e-8
    margin_train = (E_train_norm @ active_center) - (E_train_norm @ inactive_center)
    margin_test = (E_test_norm @ active_center) - (E_test_norm @ inactive_center)

    sim_train = E_train_norm @ E_train_norm.T
    np.fill_diagonal(sim_train, -np.inf)
    sim_test = E_test_norm @ E_train_norm.T
    k = min(8, len(E_train_norm) - 1) if len(E_train_norm) > 1 else 1
    train_resid = []
    for i in range(len(E_train_norm)):
        idx = np.argsort(sim_train[i])[::-1][: max(3, k)]
        train_resid.append(manifold_residual(E_train_norm[i], E_train_norm[idx]))
    test_resid = []
    for i in range(len(E_test_norm)):
        idx = np.argsort(sim_test[i])[::-1][: max(3, min(8, len(E_train_norm)))]
        test_resid.append(manifold_residual(E_test_norm[i], E_train_norm[idx]))

    F_train = np.hstack(
        [
            X_train,
            eff_proj_train[:, None],
            margin_train[:, None],
            np.asarray(train_resid, dtype=float)[:, None],
        ]
    )
    F_test = np.hstack(
        [
            X_test,
            eff_proj_test[:, None],
            margin_test[:, None],
            np.asarray(test_resid, dtype=float)[:, None],
        ]
    )
    return F_train.astype(float), F_test.astype(float)


def fit_supervised_feature_map(X_active, eff_active, proj_dim):
    n, d = X_active.shape
    proj_dim = int(min(proj_dim, d, max(n - 1, 1)))
    if proj_dim < 1:
        return np.eye(d, 1)

    Xc = X_active - X_active.mean(axis=0, keepdims=True)
    yc = eff_active - np.average(eff_active, weights=eff_active + 0.01)
    weights = np.sqrt(eff_active + 0.01)[:, None]
    Xw = Xc * weights

    direction = Xw.T @ yc
    if np.linalg.norm(direction) < 1e-8:
        direction = np.ones(d, dtype=float)
    direction = direction / (np.linalg.norm(direction) + 1e-8)

    if proj_dim == 1:
        return direction[:, None]

    pca = PCA(n_components=proj_dim - 1, random_state=SEED)
    pca.fit(Xw)
    W = np.column_stack([direction, pca.components_.T])
    return W


def fit_quantum_residual(F_train, base_train, eff_train, beta=1.0, gamma=0.5, proj_dim=8):
    n = len(eff_train)
    if n < 3:
        return None, np.zeros(n, dtype=float)

    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(base_train, eff_train)
    resid_target = eff_train - iso.predict(base_train)

    W = fit_supervised_feature_map(F_train, eff_train, proj_dim)
    proj_train = F_train @ W
    phi_train = np.hstack([np.sin(beta * proj_train), np.cos(beta * proj_train)])

    sq = np.sum(phi_train ** 2, axis=1, keepdims=True)
    dist2 = np.maximum(sq + sq.T - 2.0 * (phi_train @ phi_train.T), 0.0)
    K = np.exp(-gamma * dist2)
    np.fill_diagonal(K, 0.0)
    row_sum = K.sum(axis=1, keepdims=True) + 1e-8
    train_pred = (K @ resid_target[:, None] / row_sum).ravel()
    state = {
        "W": W,
        "beta": beta,
        "gamma": gamma,
        "proj_train": proj_train,
        "phi_train": phi_train,
        "resid_target": resid_target,
    }
    return state, train_pred


def predict_quantum_residual(state, F_test):
    if state is None:
        return np.zeros(len(F_test), dtype=float)
    proj_test = F_test @ state["W"]
    phi_test = np.hstack([np.sin(state["beta"] * proj_test), np.cos(state["beta"] * proj_test)])
    phi_train = state["phi_train"]
    resid_target = state["resid_target"]
    gamma = state["gamma"]
    test_sq = np.sum(phi_test ** 2, axis=1, keepdims=True)
    train_sq = np.sum(phi_train ** 2, axis=1, keepdims=True).T
    dist2 = np.maximum(test_sq + train_sq - 2.0 * (phi_test @ phi_train.T), 0.0)
    K = np.exp(-gamma * dist2)
    row_sum = K.sum(axis=1, keepdims=True) + 1e-8
    return (K @ resid_target[:, None] / row_sum).ravel()


def active_gate(train_base, test_base, threshold):
    train_base = np.asarray(train_base, dtype=float)
    test_base = np.asarray(test_base, dtype=float)
    hi = float(np.quantile(train_base, threshold))
    scale = max(float(np.quantile(train_base, 0.95)) - hi, 1e-6)
    return np.clip((test_base - hi) / scale, 0.0, 1.0)


def blend_score(base_train, base_test, train_resid_pred, test_resid_pred, alpha, threshold, mode):
    resid_rank = rankpct_by_train(train_resid_pred, test_resid_pred)
    base_rank = rankpct_by_train(base_train, base_test)
    centered = resid_rank - 0.5
    gate = active_gate(base_train, base_test, threshold)
    if mode == "rank":
        return (1 - alpha) * base_rank + alpha * resid_rank * gate + base_rank * (1 - gate)
    return base_test + alpha * centered * gate * np.sqrt(np.clip(base_test, 0.0, 1.0))


def pick_nested_config(X, y, groups, eff, base_score, embeddings, outer_train_idx, cols):
    inner_X = X.iloc[outer_train_idx].reset_index(drop=True)
    inner_y = y.iloc[outer_train_idx].reset_index(drop=True)
    inner_g = groups.iloc[outer_train_idx].reset_index(drop=True)
    inner_eff = eff.iloc[outer_train_idx].reset_index(drop=True)
    inner_base = base_score[outer_train_idx]
    inner_emb = embeddings[outer_train_idx]

    logo = LeaveOneGroupOut()
    alphas = [0.0, 0.01, 0.02, 0.03, 0.04]
    betas = [0.7, 1.0, 1.4]
    gammas = [0.15, 0.30, 0.50, 0.80]
    proj_dims = [4, 6, 8]
    thresholds = [0.55, 0.60, 0.65]
    modes = ["add", "rank"]
    pooled = {
        (mode, alpha, beta, gamma, proj_dim, threshold): {"score": [], "y": [], "eff": []}
        for mode in modes
        for alpha in alphas
        for beta in betas
        for gamma in gammas
        for proj_dim in proj_dims
        for threshold in thresholds
    }

    for tr, va in logo.split(inner_X, inner_y, inner_g):
        X_tr, X_va = prepare_specialist_features(
            inner_X.iloc[tr],
            inner_X.iloc[va],
            cols,
            inner_emb[tr],
            inner_emb[va],
            inner_y.iloc[tr].to_numpy(dtype=int),
            inner_eff.iloc[tr].to_numpy(dtype=float),
        )
        y_tr = inner_y.iloc[tr].to_numpy(dtype=int)
        eff_tr = inner_eff.iloc[tr].to_numpy(dtype=float)
        base_tr = inner_base[tr]
        base_va = inner_base[va]
        active_mask = y_tr == 1
        if active_mask.sum() < 4:
            active_mask = np.ones_like(y_tr, dtype=bool)

        for beta in betas:
            for gamma in gammas:
                for proj_dim in proj_dims:
                    state, train_pred = fit_quantum_residual(
                        X_tr[active_mask],
                        base_tr[active_mask],
                        eff_tr[active_mask],
                        beta=beta,
                        gamma=gamma,
                        proj_dim=proj_dim,
                    )
                    test_pred = predict_quantum_residual(state, X_va)
                    for mode in modes:
                        for alpha in alphas:
                            for threshold in thresholds:
                                score = blend_score(base_tr, base_va, train_pred, test_pred, alpha, threshold, mode)
                                pooled[(mode, alpha, beta, gamma, proj_dim, threshold)]["score"].append(score)
                                pooled[(mode, alpha, beta, gamma, proj_dim, threshold)]["y"].append(inner_y.iloc[va].to_numpy(dtype=float))
                                pooled[(mode, alpha, beta, gamma, proj_dim, threshold)]["eff"].append(inner_eff.iloc[va].to_numpy(dtype=float))

    best = ("add", 0.0, 1.0, 0.5, 6, 0.6)
    best_cls = -1.0
    for key, bags in pooled.items():
        score = np.concatenate(bags["score"])
        yy = np.concatenate(bags["y"])
        ee = np.concatenate(bags["eff"])
        m = compute_cls(yy, score, ee)
        if m["cls"] > best_cls:
            best_cls = m["cls"]
            best = key
    return best, best_cls


def run_outer():
    X, y, groups = engineer_features()
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv").set_index("rt_name").loc[X.index]
    eff = seq["pe_efficiency_pct"]
    embeddings = load_embeddings(X.index.tolist())
    base = (
        pd.read_csv(ROOT / "results" / "calibrated_predictions_selected_features.csv")
        .set_index("rt_name")
        .loc[X.index]["predicted_score"]
        .to_numpy(dtype=float)
    )
    cols = get_feature_subset(X)

    logo = LeaveOneGroupOut()
    oof = np.zeros(len(X), dtype=float)
    chosen = []
    for fold_id, (train_idx, test_idx) in enumerate(logo.split(X, y, groups), start=1):
        (mode, alpha, beta, gamma, proj_dim, threshold), inner_cls = pick_nested_config(
            X, y, groups, eff, base, embeddings, train_idx, cols
        )
        chosen.append(
            {
                "mode": mode,
                "alpha": float(alpha),
                "beta": float(beta),
                "gamma": float(gamma),
                "proj_dim": int(proj_dim),
                "threshold": float(threshold),
            }
        )

        X_train, X_test = prepare_specialist_features(
            X.iloc[train_idx],
            X.iloc[test_idx],
            cols,
            embeddings[train_idx],
            embeddings[test_idx],
            y.iloc[train_idx].to_numpy(dtype=int),
            eff.iloc[train_idx].to_numpy(dtype=float),
        )
        y_train = y.iloc[train_idx].to_numpy(dtype=int)
        eff_train = eff.iloc[train_idx].to_numpy(dtype=float)
        base_train = base[train_idx]
        base_test = base[test_idx]
        active_mask = y_train == 1
        if active_mask.sum() < 4:
            active_mask = np.ones_like(y_train, dtype=bool)

        state, train_pred = fit_quantum_residual(
            X_train[active_mask],
            base_train[active_mask],
            eff_train[active_mask],
            beta=beta,
            gamma=gamma,
            proj_dim=proj_dim,
        )
        test_pred = predict_quantum_residual(state, X_test)
        oof[test_idx] = blend_score(base_train, base_test, train_pred, test_pred, alpha, threshold, mode)

        fold_metric = compute_cls(
            y.iloc[test_idx].to_numpy(dtype=float),
            oof[test_idx],
            eff.iloc[test_idx].to_numpy(dtype=float),
        )
        print(
            f"Fold {fold_id} [{groups.iloc[test_idx].iloc[0]}] mode={mode} alpha={alpha:+.3f} "
            f"beta={beta:.2f} gamma={gamma:.2f} dim={proj_dim} thr={threshold:.2f} "
            f"innerCLS={inner_cls:.6f} PR-AUC={fold_metric['pr_auc']:.6f} "
            f"WSP={fold_metric['w_spearman']:.6f} CLS={fold_metric['cls']:.6f}"
        )

    final = compute_cls(y.to_numpy(dtype=float), oof, eff.to_numpy(dtype=float))
    pred_df = pd.DataFrame({"rt_name": X.index.to_list(), "predicted_score": oof})
    meta = {
        "pr_auc": float(final["pr_auc"]),
        "w_spearman": float(final["w_spearman"]),
        "cls": float(final["cls"]),
        "configs": chosen,
        "feature_count": len(cols),
        "features": cols,
    }
    return pred_df, final, meta


def main():
    pred_df, final, meta = run_outer()
    out_csv = ROOT / "results" / "quantum_residual_supervised_candidate.csv"
    out_json = ROOT / "results" / "quantum_residual_supervised_candidate.json"
    pred_df.to_csv(out_csv, index=False)
    out_json.write_text(json.dumps(meta, indent=2))
    print(
        f"PR-AUC: {final['pr_auc']:.6f}\n"
        f"Weighted Spearman: {final['w_spearman']:.6f}\n"
        f"CLS: {final['cls']:.6f}\n"
        f"Configs: {meta['configs']}"
    )


if __name__ == "__main__":
    main()
