import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.append(os.path.join(ROOT, "src"))
sys.path.append(os.path.join(ROOT, "evaluation"))

from feature_engineering import engineer_features
from calibrated_lofo_predictions import run_hybrid_lofo


print("Hybrid shuffle-label sanity test started")

X, _, groups = engineer_features()
seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name")
seq = seq.loc[X.index]

print("Dataset shape:", X.shape)
print("Active count:", int(seq["active"].sum()))


def shuffled_targets(seq_df, seed):
    rng = np.random.default_rng(seed)
    shuffled = seq_df.copy()
    perm_a = rng.permutation(len(shuffled))
    perm_e = rng.permutation(len(shuffled))

    # Shuffle classification and regression targets independently to ensure
    # any coupling learned from real labels is destroyed.
    shuffled["active"] = shuffled["active"].to_numpy()[perm_a]
    shuffled["pe_efficiency_pct"] = shuffled["pe_efficiency_pct"].to_numpy()[perm_e]

    return shuffled


shuffle_runs = []

for seed in [7, 17, 27]:
    shuffled_seq = shuffled_targets(seq, seed)
    _, result, _, _ = run_hybrid_lofo(
        X,
        shuffled_seq["active"],
        groups,
        shuffled_seq,
    )

    shuffle_runs.append({
        "seed": seed,
        "pr_auc": result["pr_auc"],
        "w_spearman": result["w_spearman"],
        "cls": result["cls"],
    })

    print(
        f"Seed {seed}: "
        f"PR-AUC={result['pr_auc']:.6f} "
        f"Weighted Spearman={result['w_spearman']:.6f} "
        f"CLS={result['cls']:.6f}"
    )

shuffle_df = pd.DataFrame(shuffle_runs)

print("\n======================")
print(
    "Mean shuffled scores: "
    f"PR-AUC={shuffle_df['pr_auc'].mean():.6f} "
    f"Weighted Spearman={shuffle_df['w_spearman'].mean():.6f} "
    f"CLS={shuffle_df['cls'].mean():.6f}"
)
print(f"Max shuffled CLS: {shuffle_df['cls'].max():.6f}")
print("======================")
