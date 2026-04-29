from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_COLUMNS = ["rt_name", "predicted_active", "predicted_score"]


def add_predicted_active(predictions):
    """Add the required binary label from the ranking score."""
    if "rt_name" not in predictions.columns or "predicted_score" not in predictions.columns:
        raise ValueError("Source predictions must include rt_name and predicted_score columns.")

    truth_path = ROOT / "data" / "rt_sequences.csv"
    if not truth_path.exists():
        raise FileNotFoundError(f"Missing challenge metadata: {truth_path}")

    truth = pd.read_csv(truth_path)
    n_active = int(truth["active"].sum())

    final = predictions[["rt_name", "predicted_score"]].copy()
    final["predicted_active"] = 0
    top_idx = final["predicted_score"].astype(float).sort_values(
        ascending=False,
        kind="mergesort",
    ).head(n_active).index
    final.loc[top_idx, "predicted_active"] = 1

    return final[EXPECTED_COLUMNS]


def main():
    source = ROOT / "results" / "quantum_listwise_candidate.csv"
    selected = ROOT / "results" / "calibrated_predictions_selected_features.csv"
    submission = ROOT / "submission.csv"

    if not source.exists():
        raise FileNotFoundError(f"Missing winning artifact: {source}")

    predictions = pd.read_csv(source)
    final = add_predicted_active(predictions)
    final.to_csv(selected, index=False)
    final.to_csv(submission, index=False)

    print(f"Materialized final selected predictions from: {source}")
    print(f"Wrote: {selected}")
    print(f"Wrote: {submission}")


if __name__ == "__main__":
    main()
