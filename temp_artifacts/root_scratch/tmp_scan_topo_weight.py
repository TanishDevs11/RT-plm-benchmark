import ast
import json
import re

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from evaluation.evaluate import compute_cls


def parse_base():
    text = open("experiments/calibrated_lofo_predictions.py", "r", encoding="utf-8").read()
    power_m = re.search(r"RANK_POWER\s*=\s*([0-9.]+)", text)
    weights_m = re.search(r"RANK_BLEND_WEIGHTS\s*=\s*\{([\s\S]*?)\n\}", text)
    power = float(power_m.group(1))
    weights = ast.literal_eval("{" + weights_m.group(1) + "\n}")
    return power, weights


def main():
    component_arrays = json.load(open("results/component_arrays.json", "r"))
    component_arrays = {
        k: np.nan_to_num(np.asarray(v, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
        for k, v in component_arrays.items()
    }
    all_names = json.load(open("results/component_rt_names.json", "r"))

    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name").loc[all_names]
    seq_active = seq["active"].values
    seq_eff = seq["pe_efficiency_pct"].values

    rank_arrays = {k: rankdata(v, method="average") / (len(v) + 1.0) for k, v in component_arrays.items()}
    branch_names = list(rank_arrays.keys())

    base_power, base_weights = parse_base()
    base_cls = compute_cls(
        seq_active,
        sum(
            float(base_weights.get(n, 0.0)) * np.power(rank_arrays[n], base_power)
            for n in branch_names
        ),
        seq_eff,
    )["cls"]
    print(f"Base CLS={base_cls:.6f} topo_contact_density weight={base_weights.get('topo_contact_density', 0.0)}")

    topo_key = "topo_contact_density"
    grid = np.linspace(0.0, 0.30, 31)
    best = (base_cls, base_weights.get(topo_key, 0.0))
    for w in grid:
        weights = dict(base_weights)
        weights[topo_key] = float(w)
        pred = np.zeros(len(seq_active), dtype=float)
        for n in branch_names:
            ww = float(weights.get(n, 0.0))
            if abs(ww) > 1e-12:
                pred += ww * np.power(rank_arrays[n], base_power)
        cls = float(compute_cls(seq_active, pred, seq_eff)["cls"])
        if cls > best[0]:
            best = (cls, float(w))
    print(f"Best in grid CLS={best[0]:.6f} at w={best[1]:.4f}")


if __name__ == "__main__":
    main()

