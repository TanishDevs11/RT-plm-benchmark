import json
import ast
import re
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
    arr = np.array(component_arrays[k], dtype=float)
    component_arrays[k] = np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)

seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name")
try:
    with open("results/component_rt_names.json", "r") as f:
        all_names = json.load(f)
except Exception:
    # Fallback: previous behavior if component_rt_names.json isn't present.
    all_names = pd.read_csv("results/calibrated_predictions_selected_features.csv")[
        "rt_name"
    ].astype(str).tolist()

# Critical: ensure label order matches component_arrays order
seq = seq.loc[all_names]

def global_rank_percentile(values):
    values = np.asarray(values, dtype=float)
    values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
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
    y_score = np.nan_to_num(
        df_tmp["predicted_score"].to_numpy(dtype=float),
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )
    res = compute_cls(
        seq["active"].values,
        y_score,
        seq["pe_efficiency_pct"].values,
    )
    return -res["cls"]

bounds = [(-1.5, 1.5) for _ in branch_names] + [(0.2, 1.5)]

# Seed DE near the current known-good baseline blend.
base_text = open("experiments/calibrated_lofo_predictions.py", "r", encoding="utf-8").read()
power_m = re.search(r"RANK_POWER\s*=\s*([0-9.]+)", base_text)
weights_m = re.search(r"RANK_BLEND_WEIGHTS\s*=\s*\{([\s\S]*?)\n\}", base_text)
if not power_m or not weights_m:
    raise RuntimeError("Could not parse baseline RANK_POWER / RANK_BLEND_WEIGHTS")
base_power = float(power_m.group(1))
base_weights = ast.literal_eval("{" + weights_m.group(1) + "\n}")

x0 = [float(base_weights.get(name, 0.0)) for name in branch_names] + [base_power]
print("DE starting point (baseline) CLS will be evaluated implicitly by objective.")

print("Running DE...")
res = differential_evolution(
    obj_func,
    bounds,
    maxiter=260,
    popsize=10,
    tol=1e-4,
    seed=42,
    x0=x0,
    polish=False,
    updating="deferred",
    workers=1,
    disp=True,
)

print(f"BEST CLS: {-res.fun:.6f}")
best = {
    "best_cls": float(-res.fun),
    "power": float(res.x[-1]),
    "weights": {name: float(res.x[idx]) for idx, name in enumerate(branch_names)},
}

print("POWER:", best["power"])
print("Top weights (abs desc):")
for k, v in sorted(best["weights"].items(), key=lambda kv: -abs(kv[1]))[:25]:
    print(f"  {k}: {v:.6f}")

out_path = os.path.join("results", "de_best_weights.json")
with open(out_path, "w") as f:
    json.dump(best, f, indent=2)
print(f"Saved best weights to {out_path}")

# Write DE predictions for evaluator
cur_s = np.zeros(len(all_names), dtype=float)
for name in branch_names:
    cur_s += best["weights"][name] * np.power(rank_arrays[name], best["power"])
df_pred = df_tmp_base.merge(
    pd.DataFrame({"rt_name": all_names, "predicted_score": cur_s}),
    on="rt_name",
    how="left",
)
pred_out = os.path.join("results", "calibrated_predictions_de.csv")
df_pred.to_csv(pred_out, index=False)
print(f"Saved DE predictions to {pred_out}")
