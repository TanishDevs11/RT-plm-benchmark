import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata


ROOT = Path(__file__).resolve().parent.parent

WEIGHTS = {
    "candidate": 0.6976120369479276,
    "git_08234": 0.053366668058730415,
    "de": 0.24902129499334189,
}

POWERS = {
    "candidate": 0.43733736908800747,
    "git_08234": 2.465645991280778,
    "de": 0.4928332226895574,
}

SOURCES = {
    "candidate": ROOT / "results" / "calibrated_predictions_candidate.csv",
    "git_08234": ROOT / "results" / "calibrated_predictions_git_08234.csv",
    "de": ROOT / "results" / "calibrated_predictions_de.csv",
}


def load_rank_scores():
    base = pd.read_csv(ROOT / "data" / "rt_sequences.csv")[["rt_name"]]
    rank_arrays = {}

    for name, path in SOURCES.items():
        pred = pd.read_csv(path)
        merged = base.merge(
            pred[["rt_name", "predicted_score"]],
            on="rt_name",
            how="left",
        )
        scores = merged["predicted_score"].fillna(0.0).to_numpy(dtype=float)
        rank_arrays[name] = rankdata(scores, method="average") / (len(scores) + 1.0)

    return base, rank_arrays


def build_blend():
    base, rank_arrays = load_rank_scores()
    final_scores = np.zeros(len(base), dtype=float)

    for name, weight in WEIGHTS.items():
        final_scores += weight * np.power(rank_arrays[name], POWERS[name])

    prediction_df = base.copy()
    prediction_df["predicted_score"] = final_scores
    return prediction_df


if __name__ == "__main__":
    prediction_df = build_blend()

    results_path = ROOT / "results" / "calibrated_predictions_selected_features.csv"
    triplet_path = ROOT / "results" / "calibrated_predictions_history_blend_triplet.csv"
    submission_path = ROOT / "submission.csv"

    prediction_df.to_csv(results_path, index=False)
    prediction_df.to_csv(triplet_path, index=False)

    submission = prediction_df.copy()
    submission["predicted_active"] = (
        submission["predicted_score"] >= 0.5
    ).astype(int)
    submission = submission[["rt_name", "predicted_active", "predicted_score"]]
    submission.to_csv(submission_path, index=False)

    print(f"Saved blend to {results_path}")
