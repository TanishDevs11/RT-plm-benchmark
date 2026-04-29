from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
EXPECTED_COLUMNS = ["rt_name", "predicted_active", "predicted_score"]
ACTIVE_SCORE_THRESHOLD = 1.92


def add_predicted_active(predictions):
    """Add the required binary label from a fixed score threshold."""
    if "rt_name" not in predictions.columns or "predicted_score" not in predictions.columns:
        raise ValueError("Source predictions must include rt_name and predicted_score columns.")

    final = predictions[["rt_name", "predicted_score"]].copy()
    final["predicted_active"] = (
        final["predicted_score"].astype(float) >= ACTIVE_SCORE_THRESHOLD
    ).astype(int)

    return final[EXPECTED_COLUMNS]


def main():
    selected = ROOT / "results" / "calibrated_predictions_selected_features.csv"
    submission = ROOT / "submission.csv"

    if not selected.exists():
        raise FileNotFoundError(f"Missing final LOFO score artifact: {selected}")

    predictions = pd.read_csv(selected)
    final = add_predicted_active(predictions)
    final.to_csv(selected, index=False)
    final.to_csv(submission, index=False)

    print(f"Materialized final selected predictions from: {selected}")
    print(f"Wrote: {selected}")
    print(f"Wrote: {submission}")


if __name__ == "__main__":
    main()
