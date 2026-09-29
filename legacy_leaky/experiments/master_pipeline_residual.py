from pathlib import Path
import json

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut

ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.append(str(ROOT / "experiments"))
sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "evaluation"))

from feature_engineering import engineer_features
from evaluate import compute_cls
from master_pipeline import (
    load_embeddings,
    get_feature_subset,
    build_fold_components,
    rankpct_by_train,
)


SEED = 42
RNG = np.random.default_rng(SEED)


def residual_search(pooled_components, y_true, eff_true, n_trials=1200):
    comp_names = ["isotonic", "gradient", "bootstrap"]
    base_train = np.concatenate(pooled_components["anchor"]["train"])
    base_test = np.concatenate(pooled_components["anchor"]["test"])
    base_rank = rankpct_by_train(base_train, base_test)

    comp_ranks = {}
    for name in comp_names:
        train_vals = np.concatenate(pooled_components[name]["train"])
        test_vals = np.concatenate(pooled_components[name]["test"])
        comp_ranks[name] = rankpct_by_train(train_vals, test_vals)

    best_cls = -1.0
    best_w = {name: 0.0 for name in comp_names}
    presets = [
        np.array([0.0, 0.0, 0.0]),
        np.array([0.02, 0.00, 0.00]),
        np.array([0.03, 0.01, 0.00]),
        np.array([0.02, 0.02, 0.01]),
        np.array([0.04, 0.01, 0.01]),
        np.array([0.05, 0.02, 0.01]),
    ]
    trials = presets + [RNG.uniform(0.0, 0.08, size=3) for _ in range(n_trials)]
    for weights in trials:
        score = base_rank.copy()
        for i, name in enumerate(comp_names):
            score += weights[i] * (comp_ranks[name] - base_rank)
        score = np.clip(score, 0.0, 1.0)
        m = compute_cls(y_true, score, eff_true)
        if m["cls"] > best_cls:
            best_cls = m["cls"]
            best_w = {name: float(weights[i]) for i, name in enumerate(comp_names)}
    return best_w, best_cls


def pick_nested_weights(X, y, groups, eff, base, embeddings, outer_train_idx, cols):
    inner_X = X.iloc[outer_train_idx].reset_index(drop=True)
    inner_y = y.iloc[outer_train_idx].reset_index(drop=True)
    inner_g = groups.iloc[outer_train_idx].reset_index(drop=True)
    inner_eff = eff.iloc[outer_train_idx].reset_index(drop=True)
    inner_base = base[outer_train_idx]
    inner_emb = embeddings[outer_train_idx]

    pooled = {
        "anchor": {"train": [], "test": []},
        "isotonic": {"train": [], "test": []},
        "gradient": {"train": [], "test": []},
        "bootstrap": {"train": [], "test": []},
    }
    pooled_y = []
    pooled_eff = []

    logo = LeaveOneGroupOut()
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
    return residual_search(pooled, y_true, eff_true)


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
        best_w, inner_cls = pick_nested_weights(X, y, groups, eff, base, embeddings, train_idx, cols)
        chosen.append(best_w)
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
        base_rank = rankpct_by_train(components["anchor"][0], components["anchor"][1])
        score = base_rank.copy()
        for name in ["isotonic", "gradient", "bootstrap"]:
            comp_rank = rankpct_by_train(components[name][0], components[name][1])
            score += best_w[name] * (comp_rank - base_rank)
        score = np.clip(score, 0.0, 1.0)
        oof[test_idx] = score

        fold_metric = compute_cls(
            y.iloc[test_idx].to_numpy(dtype=float),
            oof[test_idx],
            eff.iloc[test_idx].to_numpy(dtype=float),
        )
        print(
            f"Fold {fold_id} [{groups.iloc[test_idx].iloc[0]}] innerCLS={inner_cls:.6f} "
            f"weights={best_w} PR-AUC={fold_metric['pr_auc']:.6f} "
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
    out_csv = ROOT / "results" / "master_pipeline_residual_candidate.csv"
    out_json = ROOT / "results" / "master_pipeline_residual_candidate.json"
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
