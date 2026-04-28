from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "evaluation"))
from feature_engineering import engineer_features
from evaluate import compute_cls


SEED = 42
RNG = np.random.default_rng(SEED)


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


def rankpct_by_train(train_scores, test_scores):
    train_sorted = np.sort(np.asarray(train_scores, dtype=float))
    positions = np.searchsorted(train_sorted, np.asarray(test_scores, dtype=float), side="right")
    return positions / (len(train_sorted) + 1.0)


def get_feature_subset(X_df):
    cols = [c for c in FEATURE_KEYS if c in X_df.columns]
    return cols


def prepare_fold_features(X_train_df, X_test_df, cols):
    if not cols:
        return np.zeros((len(X_train_df), 1)), np.zeros((len(X_test_df), 1))
    imp = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(imp.fit_transform(X_train_df[cols]))
    X_test = scaler.transform(imp.transform(X_test_df[cols]))
    return X_train, X_test


def fit_bagged_residual(
    X_train,
    base_train,
    eff_train,
    mode="residual",
    n_models=24,
):
    # Active-only caller should already filter the arrays down.
    iso = IsotonicRegression(out_of_bounds="clip")
    iso.fit(base_train, eff_train)
    if mode == "rank_residual":
        eff_rank = np.argsort(np.argsort(eff_train)).astype(float) / max(len(eff_train) - 1, 1)
        base_rank = np.argsort(np.argsort(base_train)).astype(float) / max(len(base_train) - 1, 1)
        resid_target = eff_rank - base_rank
    else:
        resid_target = eff_train - iso.predict(base_train)

    models = []
    train_preds = []
    n = len(eff_train)
    if n < 4:
        return iso, models, np.zeros(n, dtype=float)

    for _ in range(n_models):
        boot_idx = RNG.integers(0, n, size=n)
        model = Ridge(alpha=2.0, random_state=SEED)
        model.fit(X_train[boot_idx], resid_target[boot_idx], sample_weight=eff_train[boot_idx] + 0.01)
        models.append(model)
        train_preds.append(model.predict(X_train))

    mean_train_pred = np.mean(np.vstack(train_preds), axis=0)
    return iso, models, mean_train_pred


def predict_bagged(models, X_test):
    if not models:
        return np.zeros(len(X_test), dtype=float)
    preds = np.vstack([model.predict(X_test) for model in models])
    return preds.mean(axis=0)


def blend_score(base_score, train_resid_pred, test_resid_pred, epsilon):
    resid_rank = rankpct_by_train(train_resid_pred, test_resid_pred) - 0.5
    return base_score + epsilon * resid_rank * np.sqrt(np.clip(base_score, 0.0, 1.0))


def pick_epsilon_nested(
    X_df,
    y,
    groups,
    eff,
    base_score,
    outer_train_idx,
    cols,
):
    inner_X = X_df.iloc[outer_train_idx].reset_index(drop=True)
    inner_y = y.iloc[outer_train_idx].reset_index(drop=True)
    inner_g = groups.iloc[outer_train_idx].reset_index(drop=True)
    inner_eff = eff.iloc[outer_train_idx].reset_index(drop=True)
    inner_base = base_score[outer_train_idx]

    logo = LeaveOneGroupOut()
    eps_grid = [-0.12, -0.10, -0.08, -0.06, -0.04, -0.02, 0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12]
    modes = ["residual", "rank_residual"]
    pooled = {(mode, eps): {"score": [], "y": [], "eff": []} for mode in modes for eps in eps_grid}

    for inner_tr, inner_va in logo.split(inner_X, inner_y, inner_g):
        X_tr_df = inner_X.iloc[inner_tr]
        X_va_df = inner_X.iloc[inner_va]
        X_tr, X_va = prepare_fold_features(X_tr_df, X_va_df, cols)
        y_tr = inner_y.iloc[inner_tr].to_numpy(dtype=int)
        eff_tr = inner_eff.iloc[inner_tr].to_numpy(dtype=float)
        base_tr = inner_base[inner_tr]
        base_va = inner_base[inner_va]

        active_mask = y_tr == 1
        if active_mask.sum() < 4:
            active_mask = np.ones_like(y_tr, dtype=bool)

        for mode in modes:
            _, models, train_resid_pred = fit_bagged_residual(
                X_tr[active_mask],
                base_tr[active_mask],
                eff_tr[active_mask],
                mode=mode,
            )
            test_resid_pred = predict_bagged(models, X_va)

            for eps in eps_grid:
                score = blend_score(base_va, train_resid_pred, test_resid_pred, eps)
                pooled[(mode, eps)]["score"].append(score)
                pooled[(mode, eps)]["y"].append(inner_y.iloc[inner_va].to_numpy(dtype=float))
                pooled[(mode, eps)]["eff"].append(inner_eff.iloc[inner_va].to_numpy(dtype=float))

    best_eps = 0.0
    best_mode = "residual"
    best_cls = -1.0
    for mode in modes:
        for eps in eps_grid:
            score = np.concatenate(pooled[(mode, eps)]["score"])
            yy = np.concatenate(pooled[(mode, eps)]["y"])
            ee = np.concatenate(pooled[(mode, eps)]["eff"])
            m = compute_cls(yy, score, ee)
            if m["cls"] > best_cls:
                best_cls = m["cls"]
                best_eps = eps
                best_mode = mode
    return best_mode, best_eps, best_cls


def run_outer():
    X, y, groups = engineer_features()
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv").set_index("rt_name").loc[X.index]
    eff = seq["pe_efficiency_pct"]
    selected_df = pd.read_csv(ROOT / "results" / "calibrated_predictions_selected_features.csv").set_index("rt_name")
    base_score = selected_df.loc[X.index]["predicted_score"].to_numpy(dtype=float)
    cols = get_feature_subset(X)

    logo = LeaveOneGroupOut()
    oof = np.zeros(len(X), dtype=float)
    chosen_eps = []
    for fold_id, (train_idx, test_idx) in enumerate(logo.split(X, y, groups), start=1):
        best_mode, best_eps, inner_cls = pick_epsilon_nested(X, y, groups, eff, base_score, train_idx, cols)
        chosen_eps.append({"mode": best_mode, "eps": float(best_eps)})

        X_train_df = X.iloc[train_idx]
        X_test_df = X.iloc[test_idx]
        X_train, X_test = prepare_fold_features(X_train_df, X_test_df, cols)
        y_train = y.iloc[train_idx].to_numpy(dtype=int)
        eff_train = eff.iloc[train_idx].to_numpy(dtype=float)
        base_train = base_score[train_idx]
        base_test = base_score[test_idx]

        active_mask = y_train == 1
        if active_mask.sum() < 4:
            active_mask = np.ones_like(y_train, dtype=bool)
        _, models, train_resid_pred = fit_bagged_residual(
            X_train[active_mask],
            base_train[active_mask],
            eff_train[active_mask],
            mode=best_mode,
        )
        test_resid_pred = predict_bagged(models, X_test)
        oof[test_idx] = blend_score(base_test, train_resid_pred, test_resid_pred, best_eps)

        fold_metric = compute_cls(
            y.iloc[test_idx].to_numpy(dtype=float),
            oof[test_idx],
            eff.iloc[test_idx].to_numpy(dtype=float),
        )
        print(
            f"Fold {fold_id} [{groups.iloc[test_idx].iloc[0]}] mode={best_mode} eps={best_eps:+.3f} "
            f"innerCLS={inner_cls:.6f} PR-AUC={fold_metric['pr_auc']:.6f} "
            f"WSP={fold_metric['w_spearman']:.6f} CLS={fold_metric['cls']:.6f}"
        )

    final = compute_cls(y.to_numpy(dtype=float), oof, eff.to_numpy(dtype=float))
    pred_df = pd.DataFrame({"rt_name": X.index.to_list(), "predicted_score": oof})
    meta = {
        "pr_auc": float(final["pr_auc"]),
        "w_spearman": float(final["w_spearman"]),
        "cls": float(final["cls"]),
        "epsilons": chosen_eps,
        "feature_count": len(cols),
        "features": cols,
    }
    return pred_df, final, meta


def main():
    pred_df, final, meta = run_outer()
    out_csv = ROOT / "results" / "nested_residual_candidate.csv"
    out_json = ROOT / "results" / "nested_residual_candidate.json"
    pred_df.to_csv(out_csv, index=False)
    out_json.write_text(json.dumps(meta, indent=2))
    print(
        f"PR-AUC: {final['pr_auc']:.6f}\n"
        f"Weighted Spearman: {final['w_spearman']:.6f}\n"
        f"CLS: {final['cls']:.6f}\n"
        f"Epsilons: {meta['epsilons']}"
    )


if __name__ == "__main__":
    main()
