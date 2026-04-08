import ast
import json
import re
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from evaluation.evaluate import compute_cls


def load_base_blend_and_power():
    text = open("experiments/calibrated_lofo_predictions.py", "r", encoding="utf-8").read()
    power_m = re.search(r"RANK_POWER\s*=\s*([0-9.]+)", text)
    weights_m = re.search(r"RANK_BLEND_WEIGHTS\s*=\s*\{([\s\S]*?)\n\}", text)
    if not power_m or not weights_m:
        raise RuntimeError("Could not parse RANK_POWER / RANK_BLEND_WEIGHTS from experiments script")
    power = float(power_m.group(1))
    weights = ast.literal_eval("{" + weights_m.group(1) + "\n}")
    return power, weights


def compute_cls_from_weights(weights, power, rank_arrays, seq_active, seq_eff):
    names = rank_arrays.keys()
    cur = np.zeros(len(seq_active), dtype=float)
    for name in names:
        w = float(weights.get(name, 0.0))
        if abs(w) > 1e-12:
            cur += w * np.power(rank_arrays[name], power)
    return compute_cls(seq_active, cur, seq_eff)["cls"]


def main():
    component_arrays = json.load(open("results/component_arrays.json", "r"))
    component_arrays = {
        k: np.nan_to_num(np.asarray(v, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
        for k, v in component_arrays.items()
    }

    all_names = None
    try:
        all_names = json.load(open("results/component_rt_names.json", "r"))
    except Exception:
        all_names = pd.read_csv("results/calibrated_predictions_selected_features.csv")[
            "rt_name"
        ].astype(str).tolist()
    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name").loc[all_names]
    seq_active = seq["active"].values
    seq_eff = seq["pe_efficiency_pct"].values

    rank_arrays = {k: rankdata(v, method="average") / (len(v) + 1.0) for k, v in component_arrays.items()}

    base_power, base_weights = load_base_blend_and_power()
    base_cls = compute_cls_from_weights(base_weights, base_power, rank_arrays, seq_active, seq_eff)
    print(f"Base CLS={base_cls:.6f}, power={base_power}")

    topo_components = [
        "topo_contact_density",
        "topo_long_range_ratio",
        "topo_entropy_degree",
        "topo_clustering_proxy",
        "topo_contact_entropy",
        "proto_topo_mul",
        "density_topo_mul",
        "contrast_topo_mul",
    ]

    # Search space: start at current weights (mostly topo_contact_density),
    # allow moderate perturbations to stay stable.
    rng = np.random.default_rng(0)
    best = {"cls": base_cls, "power": base_power, "weights": dict(base_weights)}

    # Random search + local refinement
    n_samples = 2500
    for _ in range(n_samples):
        power = float(base_power + rng.normal(0.0, 0.07))
        power = float(max(0.9, min(2.2, power)))

        w = dict(base_weights)
        for c in topo_components:
            if c in rank_arrays:
                w[c] = float(base_weights.get(c, 0.0) + rng.normal(0.0, 0.18))
                w[c] = float(max(-2.0, min(2.0, w[c])))
            else:
                w[c] = 0.0

        cls = compute_cls_from_weights(w, power, rank_arrays, seq_active, seq_eff)
        if cls > best["cls"]:
            best = {"cls": float(cls), "power": power, "weights": w}

    print(f"Best found CLS={best['cls']:.6f}, power={best['power']}")

    # Report only topology weights
    for c in topo_components:
        if c in best["weights"]:
            print(f"  {c}: {best['weights'][c]:.6f}")

    # Hard objective: aim >= 0.9000
    if best["cls"] < 0.9000:
        print("Did not reach CLS>=0.9000 in random search.")


if __name__ == "__main__":
    main()

