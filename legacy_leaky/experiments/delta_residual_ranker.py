from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
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
    "cleft_thumb_asymmetry",
    "cleft_tunnel_curvature_score",
    "sasa_avg",
    "sasa_high_pct",
    "sasa_low_pct",
    "helix",
    "sheet",
    "turn",
    "helix_sheet_ratio",
    "radius_gyration",
    "avg_ca_distance",
    "gravy",
    "isoelectric_point",
    "native_net_charge",
    "arginine_r_charge",
    "lysine_k_charge",
    "aspartate_d_charge",
    "glutamate_e_charge",
    "thumb_surface_net_charge",
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


def get_feature_subset(X_df):
    return [c for c in FEATURE_KEYS if c in X_df.columns]


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

    active_idx = np.where(active_mask)[0]
    active_eff = np.asarray(eff_train)[active_mask]
    order = np.argsort(active_eff)
    top_idx = active_idx[order[-min(3, len(order)):]]
    bot_idx = active_idx[order[: min(3, len(order))]]

    top_center = E_train_norm[top_idx].mean(axis=0)
    bot_center = E_train_norm[bot_idx].mean(axis=0)
    top_center /= np.linalg.norm(top_center) + 1e-8
    bot_center /= np.linalg.norm(bot_center) + 1e-8

    top_train = E_train_norm @ top_center
    top_test = E_test_norm @ top_center
    bot_train = E_train_norm @ bot_center
    bot_test = E_test_norm @ bot_center
    delta_train = top_train - bot_train
    delta_test = top_test - bot_test

    # Family-relative efficiency projection
    weights = np.asarray(eff_train, dtype=float) + 0.01
    eff_center = np.average(E_train_norm, axis=0, weights=weights)
    eff_center /= np.linalg.norm(eff_center) + 1e-8
    eff_proj_train = E_train_norm @ eff_center
    eff_proj_test = E_test_norm @ eff_center

    # Local manifold residual
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
            top_train[:, None],
            bot_train[:, None],
            delta_train[:, None],
            eff_proj_train[:, None],
            np.asarray(train_resid, dtype=float)[:, None],
        ]
    )
    F_test = np.hstack(
        [
            X_test,
            top_test[:, None],
            bot_test[:, None],
            delta_test[:, None],
            eff_proj_test[:, None],
            np.asarray(test_resid, dtype=float)[:, None],
        ]
    )
    return F_train.astype(float), F_test.astype(float)


def fit_delta_ranker(X_train, eff_train, n_models=30):
    n = len(eff_train)
    if n < 4:
        return [], np.zeros(n, dtype=float)

    models = []
    train_preds = []
    for _ in range(n_models):
        boot = RNG.integers(0, n, size=n)
        Xb = X_train[boot]
        yb = np.asarray(eff_train)[boot]
        diffs = []
        targets = []
        weights = []
        for i in range(len(yb)):
            for j in range(i + 1, len(yb)):
                if yb[i] == yb[j]:
                    continue
                diffs.append(Xb[i] - Xb[j])
                targets.append(yb[i] - yb[j])
                weights.append(max(yb[i], yb[j]) + 0.01)
        if len(diffs) < 3:
            continue
        diffs = np.asarray(diffs, dtype=float)
        targets = np.asarray(targets, dtype=float)
        weights = np.asarray(weights, dtype=float)
        model = Ridge(alpha=2.5, fit_intercept=False, random_state=SEED)
        model.fit(diffs, targets, sample_weight=weights)
        models.append(model)
        train_preds.append(X_train @ model.coef_)

    if not models:
        return [], np.zeros(n, dtype=float)
    mean_train_pred = np.mean(np.vstack(train_preds), axis=0)
    return models, mean_train_pred


def predict_delta_ranker(models, X_test):
    if not models:
        return np.zeros(len(X_test), dtype=float)
    preds = np.vstack([X_test @ model.coef_ for model in models])
    return preds.mean(axis=0)


def active_gate(train_base, test_base):
    train_base = np.asarray(train_base, dtype=float)
    test_base = np.asarray(test_base, dtype=float)
    lo = float(np.quantile(train_base, 0.60))
    hi = float(np.quantile(train_base, 0.90))
    scale = max(hi - lo, 1e-6)
    return np.clip((test_base - lo) / scale, 0.0, 1.0)


def blend_score(base_train, base_test, train_resid_pred, test_resid_pred, alpha, mode):
    resid_rank = rankpct_by_train(train_resid_pred, test_resid_pred)
    base_rank = rankpct_by_train(base_train, base_test)
    centered = resid_rank - 0.5
    gate = active_gate(base_train, base_test)
    if mode == "rank_anchor":
        return (1 - alpha) * base_test + alpha * resid_rank
    if mode == "mul_anchor":
        return base_test * (1.0 + alpha * centered)
    if mode == "rank_mix":
        return (1 - alpha) * base_rank + alpha * resid_rank
    if mode == "gated_add":
        return base_test + alpha * centered * gate * np.sqrt(np.clip(base_test, 0.0, 1.0))
    if mode == "gated_rank":
        return base_rank + alpha * centered * gate
    return base_test + alpha * centered * np.sqrt(np.clip(base_test, 0.0, 1.0))


def pick_nested_config(X, y, groups, eff, base_score, embeddings, outer_train_idx, cols):
    inner_X = X.iloc[outer_train_idx].reset_index(drop=True)
    inner_y = y.iloc[outer_train_idx].reset_index(drop=True)
    inner_g = groups.iloc[outer_train_idx].reset_index(drop=True)
    inner_eff = eff.iloc[outer_train_idx].reset_index(drop=True)
    inner_base = base_score[outer_train_idx]
    inner_emb = embeddings[outer_train_idx]

    logo = LeaveOneGroupOut()
    alphas = [-0.08, -0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06, 0.08]
    modes = ["add_anchor", "mul_anchor", "rank_anchor", "rank_mix", "gated_add", "gated_rank"]
    pooled = {(mode, alpha): {"score": [], "y": [], "eff": []} for mode in modes for alpha in alphas}

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
        models, train_pred = fit_delta_ranker(X_tr[active_mask], eff_tr[active_mask])
        test_pred = predict_delta_ranker(models, X_va)

        for mode in modes:
            for alpha in alphas:
                score = blend_score(base_tr, base_va, train_pred, test_pred, alpha, mode)
                pooled[(mode, alpha)]["score"].append(score)
                pooled[(mode, alpha)]["y"].append(inner_y.iloc[va].to_numpy(dtype=float))
                pooled[(mode, alpha)]["eff"].append(inner_eff.iloc[va].to_numpy(dtype=float))

    best_mode = "add_anchor"
    best_alpha = 0.0
    best_cls = -1.0
    for mode in modes:
        for alpha in alphas:
            score = np.concatenate(pooled[(mode, alpha)]["score"])
            yy = np.concatenate(pooled[(mode, alpha)]["y"])
            ee = np.concatenate(pooled[(mode, alpha)]["eff"])
            m = compute_cls(yy, score, ee)
            if m["cls"] > best_cls:
                best_cls = m["cls"]
                best_mode = mode
                best_alpha = alpha
    return best_mode, best_alpha, best_cls


def run_outer():
    X, y, groups = engineer_features()
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv").set_index("rt_name").loc[X.index]
    eff = seq["pe_efficiency_pct"]
    embeddings = load_embeddings(X.index.tolist())
    base = pd.read_csv(ROOT / "results" / "calibrated_predictions_selected_features.csv").set_index("rt_name").loc[X.index]["predicted_score"].to_numpy(dtype=float)
    cols = get_feature_subset(X)

    logo = LeaveOneGroupOut()
    oof = np.zeros(len(X), dtype=float)
    chosen = []
    for fold_id, (train_idx, test_idx) in enumerate(logo.split(X, y, groups), start=1):
        mode, alpha, inner_cls = pick_nested_config(X, y, groups, eff, base, embeddings, train_idx, cols)
        chosen.append({"mode": mode, "alpha": float(alpha)})

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
        models, train_pred = fit_delta_ranker(X_train[active_mask], eff_train[active_mask])
        test_pred = predict_delta_ranker(models, X_test)
        oof[test_idx] = blend_score(base_train, base_test, train_pred, test_pred, alpha, mode)

        fold_metric = compute_cls(
            y.iloc[test_idx].to_numpy(dtype=float),
            oof[test_idx],
            eff.iloc[test_idx].to_numpy(dtype=float),
        )
        print(
            f"Fold {fold_id} [{groups.iloc[test_idx].iloc[0]}] mode={mode} alpha={alpha:+.3f} "
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
    out_csv = ROOT / "results" / "delta_residual_candidate.csv"
    out_json = ROOT / "results" / "delta_residual_candidate.json"
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
