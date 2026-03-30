import pandas as pd
import numpy as np
from scipy.stats import rankdata

print("Mis-Ranking Analysis")

# -----------------------------
# Load predictions
# -----------------------------

pred = pd.read_csv("results/calibrated_predictions.csv")

seq = pd.read_csv("data/rt_sequences.csv")

df = pred.merge(
    seq[["rt_name","active","pe_efficiency_pct"]],
    on="rt_name"
)

# -----------------------------
# Compute rankings
# -----------------------------

df["pred_rank"] = rankdata(-df["predicted_score"], method="average")
df["true_rank"] = rankdata(-df["pe_efficiency_pct"], method="average")

# ranking error
df["rank_error"] = df["pred_rank"] - df["true_rank"]

# absolute error
df["abs_rank_error"] = np.abs(df["rank_error"])

# -----------------------------
# Show worst ranking mistakes
# -----------------------------

print("\nTop RTs hurting ranking:\n")

worst = df.sort_values("abs_rank_error", ascending=False)

print(
    worst[
        [
            "rt_name",
            "active",
            "pe_efficiency_pct",
            "predicted_score",
            "true_rank",
            "pred_rank",
            "rank_error"
        ]
    ].head(15)
)

# -----------------------------
# Focus on active RTs
# -----------------------------

print("\nActive RTs ranked incorrectly:\n")

active_errors = df[df["active"] == 1]

active_errors = active_errors.sort_values(
    "abs_rank_error",
    ascending=False
)

print(
    active_errors[
        [
            "rt_name",
            "pe_efficiency_pct",
            "predicted_score",
            "true_rank",
            "pred_rank",
            "rank_error"
        ]
    ].head(10)
)

# -----------------------------
# Save analysis
# -----------------------------

import os
os.makedirs("results", exist_ok=True)

df.to_csv(
    "results/misranking_analysis.csv",
    index=False
)

print("\nSaved → results/misranking_analysis.csv")
print("Analysis complete")