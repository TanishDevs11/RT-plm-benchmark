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


def get_feature_subset(X_df):
    return [c for c in FEATURE_KEYS if c in X_df.columns]


def rankpct_by_train(train_scores, test_scores):
    train_sorted = np.sort(np.asarray(train_scores, dtype=float))
    positions = np.searchsorted(train_sorted, np.asarray(test_scores, dtype=float), side="right")
    return positions / (len(train_sorted) + 1.0)


def prepare_struct_features(X_train_df, X_test_df, cols):
    if not cols:
        return np.zeros((len(X_train_df), 1)), np.zeros((len(X_test_df), 1))
    imp = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(imp.fit_transform(X_train_df[cols]))
    X_test = scaler.transform(imp.transform(X_test_df[cols]))
    return X_train.astype(float), X_test.astype(float)


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


def build_centroid_gradient(train_emb, test_emb, y_train, eff_train):
    emb_scaler = StandardScaler()
    E_train = emb_scaler.fit_transform(train_emb)
    E_test = emb_scaler.transform(test_emb)

    n_comp = int(min(16, E_train.shape[0] - 1, E_train.shape[1]))
    if n_comp >= 2:
        pca = PCA(n_components=n_comp, random_state=SEED)
        E_train = pca.fit_transform(E_train)
        E_test = pca.transform(E_test)

    E_train = E_train / (np.linalg.norm(E_train, axis=1, keepdims=True) + 1e-8)
    E_test = E_test / (np.linalg.norm(E_test, axis=1, keepdims=True) + 1e-8)

    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)
    active_mask = y_train == 1
    if active_mask.sum() < 4:
        active_mask = np.ones_like(y_train, dtype=bool)

    active_idx = np.where(active_mask)[0]
    active_eff = eff_train[active_mask]
    order = np.argsort(active_eff)
    top_idx = active_idx[order[-min(3, len(order)):]]
    bot_idx = active_idx[order[: min(3, len(order))]]
    top_center = E_train[top_idx].mean(axis=0)
    bot_center = E_train[bot_idx].mean(axis=0)
    top_center /= np.linalg.norm(top_center) + 1e-8
    bot_center /= np.linalg.norm(bot_center) + 1e-8

    top_train = E_train @ top_center
    top_test = E_test @ top_center
    bot_train = E_train @ bot_center
    bot_test = E_test @ bot_center
    grad_train = top_train - bot_train
    grad_test = top_test - bot_test

    sim_train = E_train @ E_train.T
    np.fill_diagonal(sim_train, -np.inf)
    sim_test = E_test @ E_train.T
    k = min(8, len(E_train) - 1) if len(E_train) > 1 else 1
    train_resid = []
    for i in range(len(E_train)):
        idx = np.argsort(sim_train[i])[::-1][: max(3, k)]
        train_resid.append(manifold_residual(E_train[i], E_train[idx]))
    test_resid = []
    for i in range(len(E_test)):
        idx = np.argsort(sim_test[i])[::-1][: max(3, min(8, len(E_train)))]
        test_resid.append(manifold_residual(E_test[i], E_train[idx]))

    return grad_train, grad_test, np.asarray(train_resid, dtype=float), np.asarray(test_resid, dtype=float)


def fit_isotonic_branch(base_train, eff_train, y_train, base_test):
    y_train = np.asarray(y_train, dtype=int)
    active_mask = y_train == 1
    if active_mask.sum() < 3:
        return base_train.copy(), base_test.copy()
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(base_train[active_mask], eff_train[active_mask])
    return iso.predict(base_train), iso.predict(base_test)


def fit_bootstrap_residual(X_train, base_train, eff_train, y_train, n_bootstrap=60, alpha=2.0, top_k_features=6):
    y_train = np.asarray(y_train, dtype=int)
    active_mask = y_train == 1
    if active_mask.sum() < 4:
        return np.array([], dtype=int), [], np.zeros(len(X_train), dtype=float)

    Xa = X_train[active_mask]
    base_a = base_train[active_mask]
    eff_a = eff_train[active_mask]

    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(base_a, eff_a)
    resid_target = eff_a - iso.predict(base_a)

    if Xa.shape[1] == 0:
        return np.array([], dtype=int), [], np.zeros(len(X_train), dtype=float)

    corrs = []
    for j in range(Xa.shape[1]):
        col = Xa[:, j]
        if np.std(col) < 1e-8 or np.std(resid_target) < 1e-8:
            corrs.append(0.0)
        else:
            corrs.append(abs(np.corrcoef(col, resid_target)[0, 1]))
    corrs = np.nan_to_num(np.asarray(corrs), nan=0.0)
    top_idx = np.argsort(corrs)[-min(top_k_features, Xa.shape[1]):]

    models = []
    train_preds = np.zeros(len(X_train), dtype=float)
    for _ in range(n_bootstrap):
        boot = RNG.integers(0, len(Xa), size=len(Xa))
        model = Ridge(alpha=alpha, random_state=SEED)
        model.fit(Xa[boot][:, top_idx], resid_target[boot], sample_weight=eff_a[boot] + 0.01)
        models.append(model)
        train_preds += model.predict(X_train[:, top_idx])
    train_preds /= max(len(models), 1)
    return top_idx, models, train_preds


def predict_bootstrap_residual(X_test, top_idx, models):
    if len(models) == 0:
        return np.zeros(len(X_test), dtype=float)
    preds = np.zeros(len(X_test), dtype=float)
    for model in models:
        preds += model.predict(X_test[:, top_idx])
    return preds / len(models)


def build_fold_components(X_train_df, X_test_df, emb_train, emb_test, y_train, eff_train, base_train, base_test, cols):
    X_train_struct, X_test_struct = prepare_struct_features(X_train_df, X_test_df, cols)
    grad_train, grad_test, mres_train, mres_test = build_centroid_gradient(emb_train, emb_test, y_train, eff_train)
    X_train_boot = np.hstack([X_train_struct, grad_train[:, None], mres_train[:, None]])
    X_test_boot = np.hstack([X_test_struct, grad_test[:, None], mres_test[:, None]])

    iso_train, iso_test = fit_isotonic_branch(base_train, eff_train, y_train, base_test)
    top_idx, models, boot_train, boot_test = None, None, None, None
    top_idx, models, boot_train = fit_bootstrap_residual(X_train_boot, base_train, eff_train, y_train)
    boot_test = predict_bootstrap_residual(X_test_boot, top_idx, models)

    return {
        "anchor": (base_train, base_test),
        "isotonic": (iso_train, iso_test),
        "gradient": (grad_train, grad_test),
        "bootstrap": (boot_train, boot_test),
    }


def random_weight_search(pooled_components, y_true, eff_true, n_trials=800):
    names = list(pooled_components.keys())
    best_cls = -1.0
    best_weights = {name: 0.0 for name in names}
    presets = [
        np.array([1.0, 0.0, 0.0, 0.0]),
        np.array([0.7, 0.2, 0.05, 0.05]),
        np.array([0.7, 0.15, 0.1, 0.05]),
        np.array([0.7, 0.1, 0.1, 0.1]),
        np.array([0.6, 0.2, 0.1, 0.1]),
    ]
    trials = presets + [RNG.dirichlet(np.ones(len(names))) for _ in range(n_trials)]
    for weights in trials:
        blended_parts = []
        for idx, name in enumerate(names):
            train_vals = np.concatenate(pooled_components[name]["train"])
            test_vals = np.concatenate(pooled_components[name]["test"])
            blended_parts.append(weights[idx] * rankpct_by_train(train_vals, test_vals))
        score = np.sum(blended_parts, axis=0)
        m = compute_cls(y_true, score, eff_true)
        if m["cls"] > best_cls:
            best_cls = m["cls"]
            best_weights = {name: float(weights[i]) for i, name in enumerate(names)}
    return best_weights, best_cls


def pick_nested_weights(X, y, groups, eff, base, embeddings, outer_train_idx, cols):
    inner_X = X.iloc[outer_train_idx].reset_index(drop=True)
    inner_y = y.iloc[outer_train_idx].reset_index(drop=True)
    inner_g = groups.iloc[outer_train_idx].reset_index(drop=True)
    inner_eff = eff.iloc[outer_train_idx].reset_index(drop=True)
    inner_base = base[outer_train_idx]
    inner_emb = embeddings[outer_train_idx]

    logo = LeaveOneGroupOut()
    pooled = {
        "anchor": {"train": [], "test": []},
        "isotonic": {"train": [], "test": []},
        "gradient": {"train": [], "test": []},
        "bootstrap": {"train": [], "test": []},
    }
    pooled_y = []
    pooled_eff = []
    for tr, va in logo.split(inner_X, inner_y, inner_g):
        components = build_fold_components(
            inner_X.iloc[tr],
            inner_X.iloc[va],
            inner_emb[tr],
            inner_emb[va],
            inner_y.iloc[tr].to_numpy(dtype=int),
            inner_eff.iloc[tr].to_numpy(dtype=float),
            inner_base[tr],
            inner_base[va],
            cols,
        )
        for name in pooled:
            pooled[name]["train"].append(np.asarray(components[name][0], dtype=float))
            pooled[name]["test"].append(np.asarray(components[name][1], dtype=float))
        pooled_y.append(inner_y.iloc[va].to_numpy(dtype=float))
        pooled_eff.append(inner_eff.iloc[va].to_numpy(dtype=float))

    y_true = np.concatenate(pooled_y)
    eff_true = np.concatenate(pooled_eff)
    return random_weight_search(pooled, y_true, eff_true)


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
        best_weights, inner_cls = pick_nested_weights(X, y, groups, eff, base, embeddings, train_idx, cols)
        chosen.append({"weights": best_weights})

        components = build_fold_components(
            X.iloc[train_idx],
            X.iloc[test_idx],
            embeddings[train_idx],
            embeddings[test_idx],
            y.iloc[train_idx].to_numpy(dtype=int),
            eff.iloc[train_idx].to_numpy(dtype=float),
            base[train_idx],
            base[test_idx],
            cols,
        )
        blend = np.zeros(len(test_idx), dtype=float)
        for name, weight in best_weights.items():
            blend += weight * rankpct_by_train(components[name][0], components[name][1])
        oof[test_idx] = blend

        fold_metric = compute_cls(
            y.iloc[test_idx].to_numpy(dtype=float),
            oof[test_idx],
            eff.iloc[test_idx].to_numpy(dtype=float),
        )
        print(
            f"Fold {fold_id} [{groups.iloc[test_idx].iloc[0]}] innerCLS={inner_cls:.6f} "
            f"weights={best_weights} PR-AUC={fold_metric['pr_auc']:.6f} "
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
    out_csv = ROOT / "results" / "master_pipeline_candidate.csv"
    out_json = ROOT / "results" / "master_pipeline_candidate.json"
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
