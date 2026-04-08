import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from evaluation.evaluate import compute_cls as eval_compute_cls

def cls(weights, power, rank_arrays, seq_active, seq_eff):
    branch_names = list(rank_arrays.keys())
    cur = np.zeros(len(seq_active), dtype=float)
    for name in branch_names:
        w = float(weights.get(name, 0.0))
        if abs(w) > 1e-12:
            cur += w * np.power(rank_arrays[name], power)
    return float(eval_compute_cls(seq_active, cur, seq_eff)["cls"])

def main():
    component_arrays = json.load(open("results/component_arrays.json", "r"))
    all_names = json.load(open("results/component_rt_names.json", "r"))
    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name").loc[all_names]
    seq_active = seq["active"].values
    seq_eff = seq["pe_efficiency_pct"].values

    rank_arrays = {k: rankdata(v, method="average") / (len(v) + 1.0) for k, v in component_arrays.items()}

    best_out = json.load(open("results/de_best_weights.json", "r"))
    best_w = best_out["weights"]
    best_power = best_out["power"]
    best_cls = best_out["best_cls"]
    keys = list(best_w.keys())
    
    print(f"Start CLS={best_cls:.6f} power={best_power}")

    deltas = np.linspace(-0.25, 0.25, 51)
    
    for it in range(10):
        improved = False
        for k in keys:
            w0 = float(best_w.get(k, 0.0))
            best_k_cls = best_cls
            best_k_w = w0
            for d in deltas:
                wk = float(np.clip(w0 + float(d), -2.0, 2.0))
                w_try = dict(best_w)
                w_try[k] = wk
                c = cls(w_try, best_power, rank_arrays, seq_active, seq_eff)
                if c > best_k_cls + 1e-12:
                    best_k_cls = c
                    best_k_w = wk
            if best_k_cls > best_cls + 1e-12:
                best_cls = best_k_cls
                best_w[k] = best_k_w
                improved = True
                print(f"Iter {it} improved via {k}: CLS={best_cls:.6f} w={best_k_w:.6f}")
                
        # Power tune
        for p in np.linspace(best_power - 0.1, best_power + 0.1, 41):
            c = cls(best_w, float(p), rank_arrays, seq_active, seq_eff)
            if c > best_cls + 1e-12:
                best_cls = c
                best_power = float(p)
                improved = True
                print(f"Iter {it} improved via power: CLS={best_cls:.6f} power={best_power:.6f}")

        if not improved:
            break

    print(f"Final refined CLS={best_cls:.6f} power={best_power}")

    best_out = {
        "best_cls": float(best_cls),
        "power": float(best_power),
        "weights": {k: float(v) for k, v in best_w.items()}
    }
    with open("results/de_best_weights.json", "w") as f:
        json.dump(best_out, f, indent=2)
    print("Saved refined weights to results/de_best_weights.json")

if __name__ == "__main__":
    main()
