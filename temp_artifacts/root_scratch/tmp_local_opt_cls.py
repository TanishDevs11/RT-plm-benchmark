import ast
import json
import re

import numpy as np
from scipy.stats import rankdata

from evaluation.evaluate import compute_cls
import pandas as pd


def parse_base():
    text = open("experiments/calibrated_lofo_predictions.py", "r", encoding="utf-8").read()
    power_m = re.search(r"RANK_POWER\s*=\s*([0-9.]+)", text)
    weights_m = re.search(r"RANK_BLEND_WEIGHTS\s*=\s*\{([\s\S]*?)\n\}", text)
    if not power_m or not weights_m:
        raise RuntimeError("Could not parse base blend from experiments script")
    power = float(power_m.group(1))
    weights = ast.literal_eval("{" + weights_m.group(1) + "\n}")
    return power, weights


def cls_for(weights, power, rank_arrays, seq_active, seq_eff, branch_names):
    cur = np.zeros(len(seq_active), dtype=float)
    for name in branch_names:
        w = float(weights.get(name, 0.0))
        if abs(w) > 1e-12:
            cur += w * np.power(rank_arrays[name], power)
    return float(compute_cls(seq_active, cur, seq_eff)["cls"])


def main():
    component_arrays = json.load(open("results/component_arrays.json", "r"))
    component_arrays = {
        k: np.nan_to_num(np.asarray(v, dtype=float), nan=0.0, posinf=0.0, neginf=0.0)
        for k, v in component_arrays.items()
    }
    try:
        all_names = json.load(open("results/component_rt_names.json", "r"))
    except Exception:
        all_names = pd.read_csv("results/calibrated_predictions_selected_features.csv")["rt_name"].astype(str).tolist()

    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name").loc[all_names]
    seq_active = seq["active"].values
    seq_eff = seq["pe_efficiency_pct"].values

    rank_arrays = {k: rankdata(v, method="average") / (len(v) + 1.0) for k, v in component_arrays.items()}
    branch_names = list(rank_arrays.keys())

    base_power, base_weights = parse_base()
    base_cls = cls_for(base_weights, base_power, rank_arrays, seq_active, seq_eff, branch_names)
    print(f"Base CLS={base_cls:.6f} power={base_power}")

    # Optimize only non-zero-ish baseline keys first.
    keys = [k for k, v in base_weights.items() if abs(float(v)) > 1e-6 and k in rank_arrays]
    # Sort by magnitude (helps local search converge)
    keys = sorted(keys, key=lambda kk: -abs(float(base_weights.get(kk, 0.0))))
    keys = keys[:18]
    print("Keys to optimize:", keys)

    w_cur = dict(base_weights)
    power_cur = float(base_power)
    cls_cur = base_cls

    # Coordinate ascent
    deltas = np.linspace(-0.35, 0.35, 15)  # coarse
    for it in range(5):
        improved = False
        for k in keys:
            w0 = float(w_cur.get(k, 0.0))
            best_k_cls = cls_cur
            best_k_w = w0
            for d in deltas:
                wk = max(-2.0, min(2.0, w0 + float(d)))
                w_try = dict(w_cur)
                w_try[k] = wk
                cls_try = cls_for(w_try, power_cur, rank_arrays, seq_active, seq_eff, branch_names)
                if cls_try > best_k_cls + 1e-10:
                    best_k_cls = cls_try
                    best_k_w = wk
            if best_k_cls > cls_cur + 1e-10:
                w_cur[k] = best_k_w
                cls_cur = best_k_cls
                improved = True
                print(f"Iter {it} improved via {k}: CLS={cls_cur:.6f} w={best_k_w:.6f}")
        if not improved:
            break

    print(f"Final CLS={cls_cur:.6f}")
    # Show changes vs base for optimized keys
    for k in keys:
        if abs(float(w_cur.get(k, 0.0)) - float(base_weights.get(k, 0.0))) > 1e-6:
            print(f"  {k}: {base_weights.get(k, 0.0)} -> {w_cur.get(k, 0.0)}")


if __name__ == "__main__":
    main()

