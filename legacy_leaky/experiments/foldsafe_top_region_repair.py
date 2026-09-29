import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut


ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.append(str(ROOT / "evaluation"))
from evaluate import compute_cls


def rankpct_by_train(train_values, test_values):
    train_sorted = np.sort(np.asarray(train_values, dtype=float))
    positions = np.searchsorted(
        train_sorted, np.asarray(test_values, dtype=float), side="right"
    )
    return positions / (len(train_sorted) + 1.0)


def load_frame():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    floor = pd.read_csv(ROOT / "results" / "floor_09620.csv").rename(
        columns={"predicted_score": "base_score"}
    )
    topo = pd.read_csv(ROOT / "data" / "topology_features.csv")
    topo = topo.copy()
    topo["rt_name"] = topo["rt_name"].astype(str)
    topo_alt = topo.copy()
    needs_suffix = ~topo_alt["rt_name"].str.endswith("-RT")
    topo_alt.loc[needs_suffix, "rt_name"] = topo_alt.loc[needs_suffix, "rt_name"] + "-RT"
    topo = pd.concat([topo, topo_alt], ignore_index=True)
    topo = topo.drop_duplicates(subset=["rt_name"], keep="first")

    frame = seq[
        ["rt_name", "active", "pe_efficiency_pct", "rt_family"]
    ].merge(floor, on="rt_name", how="left")
    frame = frame.merge(
        topo[
            [
                "rt_name",
                "top_contact_density",
                "top_entropy_degree",
                "top_clustering_proxy",
                "top_contact_entropy",
                "top_mean_degree",
                "top_std_degree",
            ]
        ],
        on="rt_name",
        how="left",
    )
    return frame


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


def derive_signals(frame, embeddings, train_idx, eval_idx):
    train_vectors = embeddings[train_idx]
    eval_vectors = embeddings[eval_idx]
    mean_vec = train_vectors.mean(axis=0, keepdims=True)

    train_centered = train_vectors - mean_vec
    eval_centered = eval_vectors - mean_vec
    train_centered /= np.linalg.norm(train_centered, axis=1, keepdims=True) + 1e-8
    eval_centered /= np.linalg.norm(eval_centered, axis=1, keepdims=True) + 1e-8

    train_df = frame.iloc[train_idx]
    active_mask = train_df["active"].to_numpy(dtype=int) == 1
    inactive_mask = ~active_mask

    active_center = np.average(
        train_centered[active_mask],
        axis=0,
        weights=train_df.loc[active_mask, "pe_efficiency_pct"].to_numpy(dtype=float)
        + 0.01,
    )
    inactive_center = train_centered[inactive_mask].mean(axis=0)
    active_center /= np.linalg.norm(active_center) + 1e-8
    inactive_center /= np.linalg.norm(inactive_center) + 1e-8

    mmlv_idx = frame.index[frame["rt_name"].eq("MMLV-RT")][0]
    mmlv_vec = embeddings[[mmlv_idx]] - mean_vec
    mmlv_vec /= np.linalg.norm(mmlv_vec) + 1e-8
    mmlv_vec = mmlv_vec.ravel()

    anisotropic_mmlv_sim = eval_centered @ mmlv_vec
    inactive_sim = eval_centered @ inactive_center
    active_margin = (eval_centered @ active_center) - inactive_sim

    topo_cols = [
        "top_contact_density",
        "top_entropy_degree",
        "top_clustering_proxy",
        "top_contact_entropy",
        "top_mean_degree",
        "top_std_degree",
    ]
    topo_train = train_df[topo_cols].fillna(train_df.mean(numeric_only=True))
    topo_eval = frame.iloc[eval_idx][topo_cols].fillna(train_df.mean(numeric_only=True))

    topology_rank = (
        rankpct_by_train(topo_train["top_contact_density"], topo_eval["top_contact_density"])
        + rankpct_by_train(topo_train["top_clustering_proxy"], topo_eval["top_clustering_proxy"])
        + rankpct_by_train(topo_train["top_mean_degree"], topo_eval["top_mean_degree"])
        - rankpct_by_train(topo_train["top_contact_entropy"], topo_eval["top_contact_entropy"])
        - rankpct_by_train(topo_train["top_std_degree"], topo_eval["top_std_degree"])
    ) / 5.0

    return {
        "anisotropic_mmlv_sim": anisotropic_mmlv_sim,
        "inactive_sim": inactive_sim,
        "active_margin": active_margin,
        "topology_rank": topology_rank,
    }


def apply_params(frame, embeddings, train_idx, eval_idx, params):
    eval_df = frame.iloc[eval_idx]
    signals = derive_signals(frame, embeddings, train_idx, eval_idx)

    score = eval_df["base_score"].to_numpy(dtype=float).copy()
    topk = min(params["topk"], len(score))
    top_idx = np.argsort(score)[-topk:]

    score[top_idx] += (
        params["w_mmlv"] * signals["anisotropic_mmlv_sim"][top_idx]
        - params["w_inactive"] * signals["inactive_sim"][top_idx]
        + params["w_margin"] * signals["active_margin"][top_idx]
        + params["w_topology"] * (signals["topology_rank"][top_idx] - 0.5)
    )

    smooth_k = min(params["smooth_k"], len(score))
    if params["curvature_alpha"] != 0 and smooth_k >= 3:
        order = np.argsort(score)[::-1]
        top_order = order[:smooth_k]
        local = score[top_order].copy()
        curvature = np.roll(local, -1) - 2.0 * local + np.roll(local, 1)
        curvature[0] = 0.0
        curvature[-1] = 0.0
        score[top_order] += params["curvature_alpha"] * curvature

    return score


def sample_params(rng, n_samples):
    params = [
        {
            "topk": 18,
            "w_mmlv": 0.015,
            "w_inactive": 0.01,
            "w_margin": 0.02,
            "w_topology": 0.005,
            "smooth_k": 15,
            "curvature_alpha": 0.002,
        },
        {
            "topk": 18,
            "w_mmlv": 0.0,
            "w_inactive": 0.0,
            "w_margin": 0.0,
            "w_topology": 0.0,
            "smooth_k": 0,
            "curvature_alpha": 0.0,
        },
    ]
    for _ in range(n_samples):
        params.append(
            {
                "topk": int(rng.choice([10, 12, 15, 18, 20])),
                "w_mmlv": float(rng.uniform(-0.01, 0.03)),
                "w_inactive": float(rng.uniform(0.0, 0.02)),
                "w_margin": float(rng.uniform(-0.005, 0.03)),
                "w_topology": float(rng.uniform(-0.01, 0.01)),
                "smooth_k": int(rng.choice([0, 8, 10, 12, 15])),
                "curvature_alpha": float(rng.uniform(-0.003, 0.003)),
            }
        )
    return params


def score_inner(frame, embeddings, train_idx, params):
    groups = frame.iloc[train_idx]["rt_family"]
    logo = LeaveOneGroupOut()
    inner_scores = np.zeros(len(train_idx), dtype=float)

    for inner_train_local, inner_val_local in logo.split(
        np.zeros(len(train_idx)), frame.iloc[train_idx]["active"], groups
    ):
        inner_train_idx = train_idx[inner_train_local]
        inner_val_idx = train_idx[inner_val_local]
        inner_scores[inner_val_local] = apply_params(
            frame, embeddings, inner_train_idx, inner_val_idx, params
        )

    inner_df = frame.iloc[train_idx]
    return compute_cls(
        inner_df["active"].to_numpy(dtype=float),
        inner_scores,
        inner_df["pe_efficiency_pct"].to_numpy(dtype=float),
    )


def run_repair(n_candidates=120, seed=42):
    frame = load_frame()
    embeddings = load_embeddings(frame["rt_name"].tolist())
    rng = np.random.default_rng(seed)
    logo = LeaveOneGroupOut()
    outer_scores = np.zeros(len(frame), dtype=float)
    fold_params = []

    for outer_train_idx, outer_test_idx in logo.split(
        np.zeros(len(frame)), frame["active"], frame["rt_family"]
    ):
        candidates = sample_params(rng, n_candidates)
        best = None
        best_params = None
        for params in candidates:
            result = score_inner(frame, embeddings, outer_train_idx, params)
            if best is None or result["cls"] > best["cls"]:
                best = result
                best_params = params

        outer_scores[outer_test_idx] = apply_params(
            frame, embeddings, outer_train_idx, outer_test_idx, best_params
        )
        fold_params.append(
            {
                "held_family": frame.iloc[outer_test_idx]["rt_family"].iloc[0],
                "inner_cls": float(best["cls"]),
                "params": best_params,
            }
        )

    result = compute_cls(
        frame["active"].to_numpy(dtype=float),
        outer_scores,
        frame["pe_efficiency_pct"].to_numpy(dtype=float),
    )

    prediction_df = frame[["rt_name"]].copy()
    prediction_df["predicted_score"] = outer_scores
    return prediction_df, result, fold_params


def main():
    prediction_df, result, fold_params = run_repair()
    out_csv = ROOT / "results" / "foldsafe_top_region_repair.csv"
    out_json = ROOT / "results" / "foldsafe_top_region_repair.json"
    prediction_df.to_csv(out_csv, index=False)
    out_json.write_text(
        json.dumps(
            {
                "pr_auc": float(result["pr_auc"]),
                "w_spearman": float(result["w_spearman"]),
                "cls": float(result["cls"]),
                "folds": fold_params,
            },
            indent=2,
        )
    )
    print(
        f"PR-AUC: {result['pr_auc']:.6f}\n"
        f"Weighted Spearman: {result['w_spearman']:.6f}\n"
        f"CLS: {result['cls']:.6f}"
    )


if __name__ == "__main__":
    main()
