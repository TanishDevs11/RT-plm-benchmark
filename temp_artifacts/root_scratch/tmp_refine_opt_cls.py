import ast
import json
import re

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from evaluation.evaluate import compute_cls as eval_compute_cls


def parse_base():
    text = open("experiments/calibrated_lofo_predictions.py", "r", encoding="utf-8").read()
    power_m = re.search(r"RANK_POWER\s*=\s*([0-9.]+)", text)
    weights_m = re.search(r"RANK_BLEND_WEIGHTS\s*=\s*\{([\s\S]*?)\n\}", text)
    power = float(power_m.group(1))
    weights = ast.literal_eval("{" + weights_m.group(1) + "\n}")
    return power, weights


def compute_cls_local(weights, power, rank_arrays, seq_active, seq_eff):
    branch_names = list(rank_arrays.keys())
    cur = np.zeros(len(seq_active), dtype=float)
    for name in branch_names:
        w = float(weights.get(name, 0.0))
        if abs(w) > 1e-12:
            cur += w * np.power(rank_arrays[name], power)
    return float(eval_compute_cls(seq_active, cur, seq_eff)["cls"])


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

    base_power, base_weights = parse_base()

    # Start from the prior local optimum found (or recompute via base weights)
    start_weights = dict(base_weights)
    start_power = base_power

    # Apply the earlier found changes if present (heuristic)
    start_weights.update(
        {
            "esm_block_svc": float(start_weights.get("esm_block_svc", 0.0)) + 0.05,
            "stack_ridge": float(start_weights.get("stack_ridge", 0.0)) - 0.05,
            "esm_active_density": float(start_weights.get("esm_active_density", 0.0)) + 0.05,
            "svc_hand32": float(start_weights.get("svc_hand32", 0.0)) - 0.05,
        }
    )

    def cls(weights, power):
        branch_names = list(rank_arrays.keys())
        cur = np.zeros(len(seq_active), dtype=float)
        for name in branch_names:
            w = float(weights.get(name, 0.0))
            if abs(w) > 1e-12:
                cur += w * np.power(rank_arrays[name], power)
        return float(eval_compute_cls(seq_active, cur, seq_eff)["cls"])

    cls_start = cls(start_weights, start_power)
    print(f"Start CLS={cls_start:.6f} power={start_power}")

    keys = list(base_weights.keys())
    # focus: biggest movers plus topology + power-sensitive terms
    focus = [
        "stack_ridge",
        "esm_block_svc",
        "esm_active_density",
        "svc_hand32",
        "topo_contact_density",
        "globalmm_l2",
        "esm_curvature",
        "esm_delta_contrast",
        "both_zsig_l1",
        "both_zsig_l2",
        "proto_posneg",
        "hand_et_085",
    ]
    keys = [k for k in focus if k in rank_arrays]

    best_w = dict(start_weights)
    best_power = float(start_power)
    best_cls = cls_start

    # Fine grid for power around base
    power_candidates = np.linspace(best_power - 0.05, best_power + 0.05, 21)
    for p in power_candidates:
        c = cls(best_w, float(p))
        if c > best_cls + 1e-12:
            best_cls = c
            best_power = float(p)
    print(f"After power grid: CLS={best_cls:.6f}, power={best_power}")

    # Coordinate ascent with finer deltas
    deltas = np.linspace(-0.12, 0.12, 25)
    for it in range(6):
        improved = False
        for k in keys:
            w0 = float(best_w.get(k, 0.0))
            best_k_cls = best_cls
            best_k_w = w0
            for d in deltas:
                wk = float(np.clip(w0 + float(d), -2.0, 2.0))
                w_try = dict(best_w)
                w_try[k] = wk
                c = cls(w_try, best_power)
                if c > best_k_cls + 1e-12:
                    best_k_cls = c
                    best_k_w = wk
            if best_k_cls > best_cls + 1e-12:
                best_cls = best_k_cls
                best_w[k] = best_k_w
                improved = True
                print(f"Iter {it} improved via {k}: CLS={best_cls:.6f} w={best_k_w:.6f}")
        if not improved:
            break

    print(f"Final refined CLS={best_cls:.6f} power={best_power}")
    for k in keys:
        print(f"  {k}: {best_w.get(k, 0.0):.6f}")


if __name__ == "__main__":
    main()

