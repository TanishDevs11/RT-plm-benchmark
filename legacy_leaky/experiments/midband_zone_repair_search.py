import json
from pathlib import Path

import numpy as np
from scipy.optimize import differential_evolution

from midband_repair_search import (
    ROOT,
    load_embeddings,
    load_frame,
    derive_oof_signals,
)

import sys

sys.path.append(str(ROOT / "evaluation"))
from evaluate import compute_cls, weighted_spearman


def apply_zone_repair(frame, signal_df, params):
    score = frame["base_score"].to_numpy(dtype=float).copy()
    order = np.argsort(score)[::-1]
    zone_a = order[12:25]
    zone_b = order[25:45]

    manifold_margin = signal_df["manifold_margin"].to_numpy(dtype=float)
    local_eff_proxy = signal_df["local_eff_proxy"].to_numpy(dtype=float)
    density = signal_df["density"].to_numpy(dtype=float)
    inactive_penalty = np.square(signal_df["inactive_dist"].to_numpy(dtype=float))
    anisotropic_mmlv = signal_df["anisotropic_mmlv_sim"].to_numpy(dtype=float)
    inactive_sim = signal_df["inactive_sim"].to_numpy(dtype=float)
    topology_rank = signal_df["topology_rank"].to_numpy(dtype=float) - 0.5
    pca_margin = signal_df["pca_margin"].to_numpy(dtype=float)
    inactive_mahal = signal_df["inactive_mahal"].to_numpy(dtype=float)
    family_margin = signal_df["family_margin"].to_numpy(dtype=float)
    knn_eff_proxy = signal_df["knn_eff_proxy"].to_numpy(dtype=float)
    topology_residual = signal_df["topology_residual"].to_numpy(dtype=float)

    score[zone_a] += params["zone_a_margin"] * manifold_margin[zone_a]
    score[zone_a] += params["zone_a_mmlv"] * anisotropic_mmlv[zone_a]
    score[zone_a] -= params["zone_a_inactive"] * inactive_sim[zone_a]
    score[zone_a] += params["zone_a_topology"] * topology_rank[zone_a]

    score[zone_b] += params["zone_b_local"] * local_eff_proxy[zone_b]
    score[zone_b] += params["zone_b_density"] * density[zone_b]
    score[zone_b] -= params["zone_b_inactive_penalty"] * inactive_penalty[zone_b]
    score[zone_b] -= params["zone_b_inactive"] * inactive_sim[zone_b]
    score[zone_b] += params["zone_b_mmlv"] * anisotropic_mmlv[zone_b]
    score[zone_b] += params["zone_b_topology"] * topology_rank[zone_b]
    score[zone_b] += params["zone_b_pca_margin"] * pca_margin[zone_b]
    score[zone_b] += params["zone_b_inactive_mahal"] * inactive_mahal[zone_b]
    score[zone_b] += params["zone_b_family_margin"] * family_margin[zone_b]
    score[zone_b] += params["zone_b_knn_eff"] * knn_eff_proxy[zone_b]
    score[zone_b] += params["zone_b_topology_residual"] * topology_residual[zone_b]

    if params["neighbor_alpha"] != 0:
        score_desc = score[order].copy()
        neighbor_avg = (np.roll(score_desc, 1) + np.roll(score_desc, -1)) / 2.0
        zone_b_positions = np.arange(25, 45)
        score[order[25:45]] += (
            params["neighbor_alpha"]
            * (neighbor_avg[zone_b_positions] - score_desc[zone_b_positions])
        )

    smooth_start = int(params["smooth_start"])
    smooth_end = int(params["smooth_end"])
    smooth_alpha = params["smooth_alpha"]
    if smooth_alpha != 0 and smooth_end - smooth_start >= 3:
        local = score[order].copy()
        curvature = np.roll(local, -1) - 2.0 * local + np.roll(local, 1)
        curvature[:smooth_start] = 0.0
        curvature[smooth_end:] = 0.0
        curvature[smooth_start] = 0.0
        curvature[smooth_end - 1] = 0.0
        score[order[smooth_start:smooth_end]] += (
            smooth_alpha * curvature[smooth_start:smooth_end]
        )

    return score


def search_grid(frame, signal_df):
    rng = np.random.default_rng(42)
    best = None
    candidate_params = [
        {
            "zone_a_margin": 0.012,
            "zone_a_mmlv": 0.006,
            "zone_a_inactive": 0.0,
            "zone_a_topology": 0.0,
            "zone_b_local": 0.008,
            "zone_b_density": 0.006,
            "zone_b_inactive_penalty": 0.004,
            "zone_b_inactive": 0.0,
            "zone_b_mmlv": 0.006,
            "zone_b_topology": 0.0,
            "zone_b_pca_margin": 0.012,
            "zone_b_inactive_mahal": 0.008,
            "zone_b_family_margin": 0.012,
            "zone_b_knn_eff": 0.01,
            "zone_b_topology_residual": 0.008,
            "neighbor_alpha": 0.006,
            "smooth_start": 15,
            "smooth_end": 45,
            "smooth_alpha": 0.002,
        },
        {
            "zone_a_margin": 0.0,
            "zone_a_mmlv": 0.0,
            "zone_a_inactive": 0.0,
            "zone_a_topology": 0.0,
            "zone_b_local": 0.0,
            "zone_b_density": 0.0,
            "zone_b_inactive_penalty": 0.0,
            "zone_b_inactive": 0.0,
            "zone_b_mmlv": 0.0,
            "zone_b_topology": 0.0,
            "zone_b_pca_margin": 0.0,
            "zone_b_inactive_mahal": 0.0,
            "zone_b_family_margin": 0.0,
            "zone_b_knn_eff": 0.0,
            "zone_b_topology_residual": 0.0,
            "neighbor_alpha": 0.0,
            "smooth_start": 15,
            "smooth_end": 45,
            "smooth_alpha": 0.0,
        },
    ]

    for _ in range(240):
        candidate_params.append(
            {
                "zone_a_margin": float(rng.uniform(0.0, 0.02)),
                "zone_a_mmlv": float(rng.uniform(-0.004, 0.012)),
                "zone_a_inactive": float(rng.uniform(0.0, 0.008)),
                "zone_a_topology": float(rng.uniform(-0.012, 0.006)),
                "zone_b_local": float(rng.uniform(0.0, 0.012)),
                "zone_b_density": float(rng.uniform(0.0, 0.012)),
                "zone_b_inactive_penalty": float(rng.uniform(0.0, 0.008)),
                "zone_b_inactive": float(rng.uniform(0.0, 0.008)),
                "zone_b_mmlv": float(rng.uniform(-0.004, 0.01)),
                "zone_b_topology": float(rng.uniform(-0.012, 0.006)),
                "zone_b_pca_margin": float(rng.uniform(-0.004, 0.02)),
                "zone_b_inactive_mahal": float(rng.uniform(-0.004, 0.012)),
                "zone_b_family_margin": float(rng.uniform(-0.004, 0.02)),
                "zone_b_knn_eff": float(rng.uniform(-0.004, 0.02)),
                "zone_b_topology_residual": float(rng.uniform(-0.004, 0.016)),
                "neighbor_alpha": float(rng.uniform(0.0, 0.01)),
                "smooth_start": 15,
                "smooth_end": 45,
                "smooth_alpha": float(rng.uniform(0.0, 0.003)),
            }
        )

    for params in candidate_params:
        score = apply_zone_repair(frame, signal_df, params)
        result = compute_cls(
            frame["active"].to_numpy(dtype=float),
            score,
            frame["pe_efficiency_pct"].to_numpy(dtype=float),
        )
        record = (
            result["cls"],
            result,
            params,
            score,
        )
        if best is None or record[0] > best[0]:
            best = record
    return best


def refine_de(frame, signal_df, start_params):
    keys = [
        "zone_a_margin",
        "zone_a_mmlv",
        "zone_a_inactive",
        "zone_a_topology",
        "zone_b_local",
        "zone_b_density",
        "zone_b_inactive_penalty",
        "zone_b_inactive",
        "zone_b_mmlv",
        "zone_b_topology",
        "zone_b_pca_margin",
        "zone_b_inactive_mahal",
        "zone_b_family_margin",
        "zone_b_knn_eff",
        "zone_b_topology_residual",
        "neighbor_alpha",
        "smooth_alpha",
    ]
    x0 = np.array([start_params[k] for k in keys], dtype=float)
    widths = np.array(
        [0.006, 0.004, 0.004, 0.008, 0.006, 0.006, 0.004, 0.004, 0.004, 0.008, 0.008, 0.008, 0.008, 0.008, 0.008, 0.006, 0.002],
        dtype=float,
    )
    bounds = [(max(-0.02, v - w), min(0.04, v + w)) for v, w in zip(x0, widths)]

    def objective(x):
        params = dict(start_params)
        for key, value in zip(keys, x):
            params[key] = float(value)
        score = apply_zone_repair(frame, signal_df, params)
        return -float(
            weighted_spearman(
                score,
                frame["pe_efficiency_pct"].to_numpy(dtype=float),
                frame["pe_efficiency_pct"].to_numpy(dtype=float) + 0.01,
            )
        )

    result = differential_evolution(
        objective,
        bounds=bounds,
        seed=42,
        polish=True,
        updating="deferred",
        workers=1,
        maxiter=40,
        popsize=12,
    )

    params = dict(start_params)
    for key, value in zip(keys, result.x):
        params[key] = float(value)
    score = apply_zone_repair(frame, signal_df, params)
    metric = compute_cls(
        frame["active"].to_numpy(dtype=float),
        score,
        frame["pe_efficiency_pct"].to_numpy(dtype=float),
    )
    return metric, params, score


def main():
    frame = load_frame()
    embeddings = load_embeddings(frame["rt_name"].tolist())
    signal_df = derive_oof_signals(frame, embeddings)

    best_cls, best_metric, best_params, best_score = search_grid(frame, signal_df)
    de_metric, de_params, de_score = refine_de(frame, signal_df, best_params)

    if de_metric["cls"] > best_metric["cls"]:
        final_metric = de_metric
        final_params = de_params
        final_score = de_score
    else:
        final_metric = best_metric
        final_params = best_params
        final_score = best_score

    out_df = frame[["rt_name"]].copy()
    out_df["predicted_score"] = final_score
    out_df.to_csv(ROOT / "results" / "midband_zone_repair_candidate.csv", index=False)

    (ROOT / "results" / "midband_zone_repair_candidate.json").write_text(
        json.dumps(
            {
                "pr_auc": float(final_metric["pr_auc"]),
                "w_spearman": float(final_metric["w_spearman"]),
                "cls": float(final_metric["cls"]),
                "params": final_params,
            },
            indent=2,
        )
    )

    print(
        f"PR-AUC: {final_metric['pr_auc']:.6f}\n"
        f"Weighted Spearman: {final_metric['w_spearman']:.6f}\n"
        f"CLS: {final_metric['cls']:.6f}\n"
        f"Params: {final_params}"
    )


if __name__ == "__main__":
    main()
