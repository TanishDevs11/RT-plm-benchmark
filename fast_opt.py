import json
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from scipy.stats import rankdata
import sys
import os

ROOT = os.path.dirname(__file__)
sys.path.append(os.path.join(ROOT, "src"))
sys.path.append(os.path.join(ROOT, "evaluation"))
from evaluate import compute_cls

with open("results/component_arrays.json", "r") as f:
    component_arrays = json.load(f)
for k in component_arrays:
    component_arrays[k] = np.array(component_arrays[k])

seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name")
all_names = pd.read_csv("results/calibrated_predictions_selected_features.csv")["rt_name"].tolist()

def global_rank_percentile(values):
    values = np.asarray(values, dtype=float)
    return rankdata(values, method="average") / (len(values) + 1.0)

rank_arrays = {k: global_rank_percentile(v) for k, v in component_arrays.items()}
branch_names = list(rank_arrays.keys())

df_eval = pd.DataFrame({"rt_name": all_names})
df_tmp_base = seq.reset_index()[["rt_name"]].copy()

def obj_func(params):
    w = params[:-1]
    power = params[-1]
    cur_s = np.zeros(len(all_names), dtype=float)
    for idx, name in enumerate(branch_names):
        if w[idx] != 0:
            cur_s += w[idx] * np.power(rank_arrays[name], power)
    df_eval["predicted_score"] = cur_s
    df_tmp = df_tmp_base.merge(df_eval, on="rt_name", how="left")
    try:
        res = compute_cls(seq["active"].values, df_tmp["predicted_score"].values, seq["pe_efficiency_pct"].values)
        return -res["cls"]
    except Exception:
        return 0.0

bounds = [(-1.5, 1.5) for _ in branch_names] + [(0.2, 1.5)]
print("Running DE...")
res = differential_evolution(obj_func, bounds, maxiter=500, popsize=20, tol=1e-4, seed=42)

print(f"BEST CLS: {-res.fun:.6f}")
print("WEIGHTS = {")
for idx, name in enumerate(branch_names):
    print(f'    "{name}": {res.x[idx]},')
print("}")
print(f"POWER: {res.x[-1]}")
