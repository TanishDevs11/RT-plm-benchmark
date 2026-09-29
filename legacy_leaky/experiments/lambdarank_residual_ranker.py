from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge


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
    "cleft_curvature_proxy",
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

    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)
    active_mask = y_train == 1
    if active_mask.sum() < 4:
        active_mask = np.ones_like(active_mask, dtype=bool)

    weights = eff_train + 0.01
    eff_center = np.average(E_train_norm, axis=0, weights=weights)
    eff_center /= np.linalg.norm(eff_center) + 1e-8
    eff_proj_train = E_train_norm @ eff_center
    eff_proj_test = E_test_norm @ eff_center

    active_center = np.average(E_train_norm[active_mask], axis=0, weights=weights[active_mask])
    active_center /= np.linalg.norm(active_center) + 1e-8
    inactive_center = E_train_norm[~active_mask].mean(axis=0) if (~active_mask).sum() > 0 else -active_center
    inactive_center /= np.linalg.norm(inactive_center) + 1e-8
    margin_train = (E_train_norm @ active_center) - (E_train_norm @ inactive_center)
    margin_test = (E_test_norm @ active_center) - (E_test_norm @ inactive_center)

    active_idx = np.where(active_mask)[0]
    active_eff = eff_train[active_mask]
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
    rel_grad_train = top_train - bot_train
    rel_grad_test = top_test - bot_test

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
            rel_grad_train[:, None],
            np.asarray(train_resid, dtype=float)[:, None],
        ]
    )
    F_test = np.hstack(
        [
            X_test,
            eff_proj_test[:, None],
            margin_test[:, None],
            rel_grad_test[:, None],
            np.asarray(test_resid, dtype=float)[:, None],
        ]
    )
    return F_train.astype(float), F_test.astype(float)


def lambda_gradients(scores, efficiencies, eps=0.01):
    n = len(scores)
    lambdas = np.zeros(n, dtype=float)
    for i in range(n):
        for j in range(n):
            if efficiencies[i] <= efficiencies[j]:
                continue
            w_ij = (efficiencies[i] - efficiencies[j]) + eps
            delta = scores[i] - scores[j]
            sigma = 1.0 / (1.0 + np.exp(-delta))
            lambdas[i] += w_ij * (sigma - 1.0)
            lambdas[j] += w_ij * sigma
    return lambdas


def fit_lambdarank(X_train, eff_train, n_iter=80, learning_rate=0.05, alpha=1.0):
    n, d = X_train.shape
    if n < 4:
        return np.zeros(d, dtype=float), float(np.mean(eff_train)), np.zeros(n, dtype=float)

    weights = np.zeros(d, dtype=float)
    bias = float(np.mean(eff_train))
    scores = X_train @ weights + bias
    for _ in range(n_iter):
        lambdas = lambda_gradients(scores, eff_train)
        ridge = Ridge(alpha=alpha, fit_intercept=True, random_state=SEED)
        ridge.fit(X_train, -lambdas)
        weights += learning_rate * ridge.coef_
        bias += learning_rate * float(ridge.intercept_)
        scores = X_train @ weights + bias
    return weights, bias, scores


def predict_lambdarank(weights, bias, X_test):
    return X_test @ weights + bias


def blend_score(base_train, base_test, train_rank_pred, test_rank_pred, lambda_weight, mode):
    rank_pred = rankpct_by_train(train_rank_pred, test_rank_pred)
    base_rank = rankpct_by_train(base_train, base_test)
    if mode == "rank":
        return (1.0 - lambda_weight) * base_rank + lambda_weight * rank_pred
    centered = rank_pred - 0.5
    return base_test + lambda_weight * centered * np.sqrt(np.clip(base_test, 0.0, 1.0))


def pick_nested_config(X, y, groups, eff, base_score, embeddings, outer_train_idx, cols):
    inner_X = X.iloc[outer_train_idx].reset_index(drop=True)
    inner_y = y.iloc[outer_train_idx].reset_index(drop=True)
    inner_g = groups.iloc[outer_train_idx].reset_index(drop=True)
    inner_eff = eff.iloc[outer_train_idx].reset_index(drop=True)
    inner_base = base_score[outer_train_idx]
    inner_emb = embeddings[outer_train_idx]

    logo = LeaveOneGroupOut()
    lambda_grid = [0.0, 0.03, 0.06, 0.09, 0.12, 0.15, 0.20]
    mode_grid = ["add", "rank"]
    iter_grid = [50, 80]
    lr_grid = [0.03, 0.05]
    alpha_grid = [0.5, 1.0, 2.0]
    pooled = {
        (mode, lam, iters, lr, alpha): {"score": [], "y": [], "eff": []}
        for mode in mode_grid
        for lam in lambda_grid
        for iters in iter_grid
        for lr in lr_grid
        for alpha in alpha_grid
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

        for iters in iter_grid:
            for lr in lr_grid:
                for alpha in alpha_grid:
                    weights, bias, train_rank_pred = fit_lambdarank(
                        X_tr[active_mask], eff_tr[active_mask], n_iter=iters, learning_rate=lr, alpha=alpha
                    )
                    test_rank_pred = predict_lambdarank(weights, bias, X_va)
                    for mode in mode_grid:
                        for lam in lambda_grid:
                            score = blend_score(base_tr, base_va, train_rank_pred, test_rank_pred, lam, mode)
                            pooled[(mode, lam, iters, lr, alpha)]["score"].append(score)
                            pooled[(mode, lam, iters, lr, alpha)]["y"].append(inner_y.iloc[va].to_numpy(dtype=float))
                            pooled[(mode, lam, iters, lr, alpha)]["eff"].append(inner_eff.iloc[va].to_numpy(dtype=float))

    best = ("add", 0.0, 80, 0.05, 1.0)
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
        (mode, lam, iters, lr, alpha), inner_cls = pick_nested_config(
            X, y, groups, eff, base, embeddings, train_idx, cols
        )
        chosen.append(
            {
                "mode": mode,
                "lambda_weight": float(lam),
                "n_iter": int(iters),
                "learning_rate": float(lr),
                "alpha": float(alpha),
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

        weights, bias, train_rank_pred = fit_lambdarank(
            X_train[active_mask], eff_train[active_mask], n_iter=iters, learning_rate=lr, alpha=alpha
        )
        test_rank_pred = predict_lambdarank(weights, bias, X_test)
        oof[test_idx] = blend_score(base_train, base_test, train_rank_pred, test_rank_pred, lam, mode)

        fold_metric = compute_cls(
            y.iloc[test_idx].to_numpy(dtype=float),
            oof[test_idx],
            eff.iloc[test_idx].to_numpy(dtype=float),
        )
        print(
            f"Fold {fold_id} [{groups.iloc[test_idx].iloc[0]}] mode={mode} lambda={lam:.3f} "
            f"iter={iters} lr={lr:.3f} alpha={alpha:.2f} innerCLS={inner_cls:.6f} "
            f"PR-AUC={fold_metric['pr_auc']:.6f} WSP={fold_metric['w_spearman']:.6f} CLS={fold_metric['cls']:.6f}"
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
    out_csv = ROOT / "results" / "lambdarank_residual_candidate.csv"
    out_json = ROOT / "results" / "lambdarank_residual_candidate.json"
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
