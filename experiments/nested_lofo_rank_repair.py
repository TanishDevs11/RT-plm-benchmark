import io
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut


ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.append(str(ROOT / "evaluation"))
from evaluate import compute_cls


def first_existing(*paths):
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError(str(paths[0]))


def rankpct(values):
    return pd.Series(values).rank(method="average").to_numpy(dtype=float) / (
        len(values) + 1.0
    )


def rankpct_by_train(train_values, test_values):
    train_sorted = np.sort(np.asarray(train_values, dtype=float))
    positions = np.searchsorted(
        train_sorted, np.asarray(test_values, dtype=float), side="right"
    )
    return positions / (len(train_sorted) + 1.0)


def load_frame():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    topology = pd.read_csv(ROOT / "data" / "topology_features.csv")
    topology = topology.copy()
    topology["rt_name"] = topology["rt_name"].astype(str)
    topo_alt = topology.copy()
    needs_suffix = ~topo_alt["rt_name"].str.endswith("-RT")
    topo_alt.loc[needs_suffix, "rt_name"] = (
        topo_alt.loc[needs_suffix, "rt_name"] + "-RT"
    )
    topology = pd.concat([topology, topo_alt], ignore_index=True)
    topology = topology.drop_duplicates(subset=["rt_name"], keep="first")

    base = pd.read_csv(ROOT / "results" / "calibrated_predictions_top20_repair.csv")
    repair = pd.read_csv(
        first_existing(
            ROOT / "results" / "rank_repair_search_candidate.csv",
            ROOT / "temp_artifacts" / "results_scratch" / "rank_repair_search_candidate.csv",
        )
    ).rename(columns={"predicted_score": "repair_score"})
    meta = pd.read_csv(
        first_existing(
            ROOT / "results" / "calibrated_predictions_meta_refine.csv",
            ROOT / "temp_artifacts" / "results_scratch" / "calibrated_predictions_meta_refine.csv",
        )
    ).rename(columns={"predicted_score": "meta_score"})

    git0538_content = subprocess.check_output(
        ["git", "show", "3bad349:results/calibrated_predictions_selected_features.csv"],
        text=True,
        cwd=ROOT,
    )
    git0538 = pd.read_csv(io.StringIO(git0538_content)).rename(
        columns={"predicted_score": "git0538_score"}
    )

    frame = seq[
        ["rt_name", "active", "pe_efficiency_pct", "rt_family"]
    ].merge(base, on="rt_name", how="left")
    frame = frame.rename(columns={"predicted_score": "base_score"})
    frame = frame.merge(repair, on="rt_name", how="left")
    frame = frame.merge(meta, on="rt_name", how="left")
    frame = frame.merge(git0538, on="rt_name", how="left")
    frame = frame.merge(
        topology[
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
    aligned = np.vstack([vectors[name_to_idx[name]] for name in rt_names])
    return aligned


def derive_fold_signals(frame, embeddings, train_idx, eval_idx):
    train_vectors = embeddings[train_idx]
    eval_vectors = embeddings[eval_idx]

    # Anisotropy correction using training families only.
    mean_vec = train_vectors.mean(axis=0, keepdims=True)
    train_centered = train_vectors - mean_vec
    eval_centered = eval_vectors - mean_vec
    train_centered /= np.linalg.norm(train_centered, axis=1, keepdims=True) + 1e-8
    eval_centered /= np.linalg.norm(eval_centered, axis=1, keepdims=True) + 1e-8

    train_df = frame.iloc[train_idx]
    active_mask = train_df["active"].to_numpy(dtype=int) == 1
    inactive_mask = ~active_mask
    eff_weights = train_df["pe_efficiency_pct"].to_numpy(dtype=float) + 0.01

    active_center = np.average(
        train_centered[active_mask], axis=0, weights=eff_weights[active_mask]
    )
    inactive_center = np.average(train_centered[inactive_mask], axis=0)

    active_center /= np.linalg.norm(active_center) + 1e-8
    inactive_center /= np.linalg.norm(inactive_center) + 1e-8

    mmlv_idx = frame.index[frame["rt_name"].eq("MMLV-RT")][0]
    mmlv_vec = embeddings[[mmlv_idx]] - mean_vec
    mmlv_vec /= np.linalg.norm(mmlv_vec) + 1e-8
    mmlv_vec = mmlv_vec.ravel()

    sim_active = eval_centered @ active_center
    sim_inactive = eval_centered @ inactive_center
    sim_mmlv = eval_centered @ mmlv_vec
    margin = sim_active - sim_inactive
    inactive_distance = 1.0 - sim_inactive

    topo_train = train_df[
        [
            "top_contact_density",
            "top_entropy_degree",
            "top_clustering_proxy",
            "top_contact_entropy",
            "top_mean_degree",
            "top_std_degree",
        ]
    ].fillna(train_df.mean(numeric_only=True))
    topo_eval = frame.iloc[eval_idx][topo_train.columns].fillna(
        train_df.mean(numeric_only=True)
    )

    topo_signal = (
        rankpct_by_train(topo_train["top_contact_density"], topo_eval["top_contact_density"])
        + rankpct_by_train(topo_train["top_clustering_proxy"], topo_eval["top_clustering_proxy"])
        + rankpct_by_train(topo_train["top_mean_degree"], topo_eval["top_mean_degree"])
        - rankpct_by_train(topo_train["top_contact_entropy"], topo_eval["top_contact_entropy"])
        - rankpct_by_train(topo_train["top_std_degree"], topo_eval["top_std_degree"])
    ) / 5.0

    return {
        "sim_active": sim_active,
        "sim_inactive": sim_inactive,
        "sim_mmlv": sim_mmlv,
        "margin": margin,
        "inactive_distance": inactive_distance,
        "topology": topo_signal,
    }


def apply_params(frame, embeddings, train_idx, eval_idx, params):
    train_df = frame.iloc[train_idx]
    eval_df = frame.iloc[eval_idx]
    signals = derive_fold_signals(frame, embeddings, train_idx, eval_idx)

    score = eval_df["base_score"].to_numpy(dtype=float).copy()
    repair_rank = rankpct_by_train(
        train_df["repair_score"], eval_df["repair_score"]
    )
    meta_rank = rankpct_by_train(train_df["meta_score"], eval_df["meta_score"])
    git_rank = rankpct_by_train(
        train_df["git0538_score"], eval_df["git0538_score"]
    )

    top1 = np.argsort(score)[-min(params["top1"], len(score)) :]
    score[top1] += params["w_rep1"] * (repair_rank[top1] - 0.5)
    score[top1] += params["w_meta1"] * (meta_rank[top1] - 0.5)
    score[top1] += params["w_margin1"] * signals["margin"][top1]
    score[top1] += params["w_sim1"] * signals["sim_mmlv"][top1]
    score[top1] += params["w_topo1"] * (signals["topology"][top1] - 0.5)

    top2 = np.argsort(score)[-min(params["top2"], len(score)) :]
    score[top2] += params["w_rep2"] * (repair_rank[top2] - 0.5)
    score[top2] += params["w_meta2"] * (meta_rank[top2] - 0.5)
    score[top2] += params["w_git2"] * (git_rank[top2] - 0.5)
    score[top2] += params["w_sim2"] * signals["sim_mmlv"][top2]
    score[top2] += params["w_topo2"] * (signals["topology"][top2] - 0.5)

    score += params["w_margin_global"] * signals["margin"]
    score += params["w_topo_global"] * (signals["topology"] - 0.5)
    score += params["w_inactive_global"] * signals["inactive_distance"]

    return score


def sample_params(rng, n_samples):
    params = [
        {
            "top1": 18,
            "top2": 9,
            "w_rep1": 0.016,
            "w_meta1": 0.012,
            "w_margin1": 0.0,
            "w_sim1": -0.04,
            "w_topo1": 0.0,
            "w_rep2": -0.01,
            "w_meta2": -0.005,
            "w_git2": 0.015,
            "w_sim2": -0.04,
            "w_topo2": 0.0,
            "w_margin_global": 0.0,
            "w_topo_global": 0.0,
            "w_inactive_global": 0.0,
        }
    ]

    for _ in range(n_samples):
        params.append(
            {
                "top1": int(rng.integers(12, 23)),
                "top2": int(rng.integers(5, 13)),
                "w_rep1": rng.uniform(0.008, 0.024),
                "w_meta1": rng.uniform(-0.004, 0.02),
                "w_margin1": rng.uniform(-0.01, 0.02),
                "w_sim1": rng.uniform(-0.06, -0.015),
                "w_topo1": rng.uniform(-0.015, 0.02),
                "w_rep2": rng.uniform(-0.02, 0.01),
                "w_meta2": rng.uniform(-0.015, 0.01),
                "w_git2": rng.uniform(0.0, 0.025),
                "w_sim2": rng.uniform(-0.06, -0.015),
                "w_topo2": rng.uniform(-0.015, 0.02),
                "w_margin_global": rng.uniform(-0.01, 0.015),
                "w_topo_global": rng.uniform(-0.01, 0.015),
                "w_inactive_global": rng.uniform(-0.02, 0.0),
            }
        )
    return params


def score_inner_params(frame, embeddings, train_idx, params):
    inner_groups = frame.iloc[train_idx]["rt_family"]
    logo = LeaveOneGroupOut()
    inner_scores = np.zeros(len(train_idx), dtype=float)

    for inner_train_local, inner_val_local in logo.split(
        np.zeros(len(train_idx)), frame.iloc[train_idx]["active"], inner_groups
    ):
        inner_train_idx = train_idx[inner_train_local]
        inner_val_idx = train_idx[inner_val_local]
        inner_scores[inner_val_local] = apply_params(
            frame, embeddings, inner_train_idx, inner_val_idx, params
        )

    inner_df = frame.iloc[train_idx]
    result = compute_cls(
        inner_df["active"].to_numpy(dtype=float),
        inner_scores,
        inner_df["pe_efficiency_pct"].to_numpy(dtype=float),
    )
    return result, inner_scores


def run_nested_repair(n_candidates=160, seed=42):
    frame = load_frame()
    embeddings = load_embeddings(frame["rt_name"].tolist())
    logo = LeaveOneGroupOut()
    rng = np.random.default_rng(seed)

    outer_scores = np.zeros(len(frame), dtype=float)
    fold_configs = []

    for outer_train_idx, outer_test_idx in logo.split(
        np.zeros(len(frame)), frame["active"], frame["rt_family"]
    ):
        candidates = sample_params(rng, n_candidates)
        best_result = None
        best_params = None

        for params in candidates:
            result, _ = score_inner_params(frame, embeddings, outer_train_idx, params)
            if best_result is None or result["cls"] > best_result["cls"]:
                best_result = result
                best_params = params

        outer_scores[outer_test_idx] = apply_params(
            frame, embeddings, outer_train_idx, outer_test_idx, best_params
        )
        fold_configs.append(
            {
                "held_family": frame.iloc[outer_test_idx]["rt_family"].iloc[0],
                "best_inner_cls": float(best_result["cls"]),
                "best_inner_pr_auc": float(best_result["pr_auc"]),
                "best_inner_w_spearman": float(best_result["w_spearman"]),
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
    return prediction_df, result, fold_configs


def main():
    prediction_df, result, fold_configs = run_nested_repair()
    out_csv = ROOT / "results" / "nested_lofo_rank_repair.csv"
    out_json = ROOT / "results" / "nested_lofo_rank_repair.json"

    prediction_df.to_csv(out_csv, index=False)
    out_json.write_text(
        json.dumps(
            {
                "pr_auc": float(result["pr_auc"]),
                "w_spearman": float(result["w_spearman"]),
                "cls": float(result["cls"]),
                "folds": fold_configs,
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
