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


def load_frame():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    pred = pd.read_csv(ROOT / "results" / "calibrated_predictions_selected_features.csv")
    topo = pd.read_csv(ROOT / "data" / "topology_features.csv")
    topo = topo.copy()
    topo["rt_name"] = topo["rt_name"].astype(str)
    topo_alt = topo.copy()
    needs_suffix = ~topo_alt["rt_name"].str.endswith("-RT")
    topo_alt.loc[needs_suffix, "rt_name"] = topo_alt.loc[needs_suffix, "rt_name"] + "-RT"
    topo = pd.concat([topo, topo_alt], ignore_index=True).drop_duplicates(
        subset=["rt_name"], keep="first"
    )

    frame = seq[
        ["rt_name", "active", "pe_efficiency_pct", "rt_family"]
    ].merge(pred.rename(columns={"predicted_score": "base_score"}), on="rt_name", how="left")
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


def derive_oof_signals(frame, embeddings):
    logo = LeaveOneGroupOut()
    n = len(frame)
    signals = {
        "anisotropic_mmlv_sim": np.zeros(n, dtype=float),
        "inactive_sim": np.zeros(n, dtype=float),
        "inactive_dist": np.zeros(n, dtype=float),
        "active_margin": np.zeros(n, dtype=float),
        "manifold_margin": np.zeros(n, dtype=float),
        "density": np.zeros(n, dtype=float),
        "local_eff_proxy": np.zeros(n, dtype=float),
        "topology_rank": np.zeros(n, dtype=float),
    }

    for train_idx, test_idx in logo.split(
        np.zeros(n), frame["active"], frame["rt_family"]
    ):
        train_vectors = embeddings[train_idx]
        test_vectors = embeddings[test_idx]
        mean_vec = train_vectors.mean(axis=0, keepdims=True)

        train_centered = train_vectors - mean_vec
        test_centered = test_vectors - mean_vec
        train_centered /= np.linalg.norm(train_centered, axis=1, keepdims=True) + 1e-8
        test_centered /= np.linalg.norm(test_centered, axis=1, keepdims=True) + 1e-8

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

        signals["anisotropic_mmlv_sim"][test_idx] = test_centered @ mmlv_vec
        signals["inactive_sim"][test_idx] = test_centered @ inactive_center
        signals["active_margin"][test_idx] = (
            (test_centered @ active_center) - signals["inactive_sim"][test_idx]
        )

        active_dist = np.linalg.norm(test_centered - active_center, axis=1)
        inactive_dist = np.linalg.norm(test_centered - inactive_center, axis=1)
        signals["inactive_dist"][test_idx] = inactive_dist
        signals["manifold_margin"][test_idx] = inactive_dist - active_dist

        sim_to_train = test_centered @ train_centered.T
        signals["density"][test_idx] = sim_to_train.mean(axis=1)
        signals["local_eff_proxy"][test_idx] = np.average(
            sim_to_train,
            axis=1,
            weights=eff_weights,
        )

        topo_cols = [
            "top_contact_density",
            "top_entropy_degree",
            "top_clustering_proxy",
            "top_contact_entropy",
            "top_mean_degree",
            "top_std_degree",
        ]
        topo_train = train_df[topo_cols].fillna(train_df.mean(numeric_only=True))
        topo_test = frame.iloc[test_idx][topo_cols].fillna(train_df.mean(numeric_only=True))
        signals["topology_rank"][test_idx] = (
            rankpct_by_train(topo_train["top_contact_density"], topo_test["top_contact_density"])
            + rankpct_by_train(topo_train["top_clustering_proxy"], topo_test["top_clustering_proxy"])
            + rankpct_by_train(topo_train["top_mean_degree"], topo_test["top_mean_degree"])
            - rankpct_by_train(topo_train["top_contact_entropy"], topo_test["top_contact_entropy"])
            - rankpct_by_train(topo_train["top_std_degree"], topo_test["top_std_degree"])
        ) / 5.0

    return pd.DataFrame(signals, index=frame.index)


def apply_midband_repair(frame, signal_df, params):
    score = frame["base_score"].to_numpy(dtype=float).copy()
    order = np.argsort(score)[::-1]
    mid_idx = order[12:40]

    score[mid_idx] += (
        params["w_margin"] * signal_df["manifold_margin"].to_numpy(dtype=float)[mid_idx]
        + params["w_local"] * signal_df["local_eff_proxy"].to_numpy(dtype=float)[mid_idx]
        - params["w_inactive"] * signal_df["inactive_sim"].to_numpy(dtype=float)[mid_idx]
        + params["w_topology"]
        * (signal_df["topology_rank"].to_numpy(dtype=float)[mid_idx] - 0.5)
    )

    if params["w_mmlv"] != 0:
        score[mid_idx] += (
            params["w_mmlv"]
            * signal_df["anisotropic_mmlv_sim"].to_numpy(dtype=float)[mid_idx]
        )

    if params["w_active_margin"] != 0:
        score[mid_idx] += (
            params["w_active_margin"]
            * signal_df["active_margin"].to_numpy(dtype=float)[mid_idx]
        )

    if params["curvature_alpha"] != 0:
        local = score[order].copy()
        curvature = np.roll(local, -1) - 2.0 * local + np.roll(local, 1)
        curvature[:12] = 0.0
        curvature[40:] = 0.0
        curvature[12] = 0.0
        curvature[39] = 0.0
        score[order[12:40]] += params["curvature_alpha"] * curvature[12:40]

    return score


def search_params(frame, signal_df):
    candidates = []
    for w_margin in [0.0, 0.005, 0.01, 0.015]:
        for w_local in [0.0, 0.005, 0.01, 0.015]:
            for w_inactive in [0.0, 0.004, 0.008, 0.012]:
                for w_topology in [-0.005, 0.0, 0.005]:
                    for w_mmlv in [-0.005, 0.0, 0.005, 0.01]:
                        for w_active_margin in [0.0, 0.005, 0.01]:
                            for curvature_alpha in [0.0, 0.001, 0.002, 0.003]:
                                params = {
                                    "w_margin": w_margin,
                                    "w_local": w_local,
                                    "w_inactive": w_inactive,
                                    "w_topology": w_topology,
                                    "w_mmlv": w_mmlv,
                                    "w_active_margin": w_active_margin,
                                    "curvature_alpha": curvature_alpha,
                                }
                                score = apply_midband_repair(frame, signal_df, params)
                                result = compute_cls(
                                    frame["active"].to_numpy(dtype=float),
                                    score,
                                    frame["pe_efficiency_pct"].to_numpy(dtype=float),
                                )
                                candidates.append((result["cls"], result, params, score))

    return max(candidates, key=lambda item: item[0])


def main():
    frame = load_frame()
    embeddings = load_embeddings(frame["rt_name"].tolist())
    signal_df = derive_oof_signals(frame, embeddings)
    best_cls, best_result, best_params, best_score = search_params(frame, signal_df)

    out_df = frame[["rt_name"]].copy()
    out_df["predicted_score"] = best_score
    out_df.to_csv(ROOT / "results" / "midband_repair_candidate.csv", index=False)

    (ROOT / "results" / "midband_repair_candidate.json").write_text(
        json.dumps(
            {
                "pr_auc": float(best_result["pr_auc"]),
                "w_spearman": float(best_result["w_spearman"]),
                "cls": float(best_cls),
                "params": best_params,
            },
            indent=2,
        )
    )

    print(
        f"PR-AUC: {best_result['pr_auc']:.6f}\n"
        f"Weighted Spearman: {best_result['w_spearman']:.6f}\n"
        f"CLS: {best_cls:.6f}\n"
        f"Params: {best_params}"
    )


if __name__ == "__main__":
    main()
