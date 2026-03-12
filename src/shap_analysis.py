import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier
from feature_engineering import engineer_features


def run_shap():

    print("Loading features...")

    X, y, groups = engineer_features()

    print("Feature matrix:", X.shape)

    print("Training RandomForest model...")

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=4,
        min_samples_leaf=1,
        max_features="sqrt",
        random_state=42
    )

    model.fit(X, y)

    print("Computing SHAP values...")

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(X)

    # ------------------------------------------------
    # Handle SHAP output format (important fix)
    # ------------------------------------------------

    if isinstance(shap_values, list):
        # Old SHAP format
        print("SHAP returned list format")
        shap_values_to_use = shap_values[1]

    elif isinstance(shap_values, np.ndarray):

        if shap_values.ndim == 3:
            # (samples, features, classes)
            print("SHAP returned 3D array")
            shap_values_to_use = shap_values[:, :, 1]

        else:
            # (samples, features)
            print("SHAP returned 2D array")
            shap_values_to_use = shap_values

    else:
        raise ValueError("Unexpected SHAP output format")

    # ------------------------------------------------
    # Ensure results folder exists
    # ------------------------------------------------

    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    # ------------------------------------------------
    # SHAP Summary Plot
    # ------------------------------------------------

    print("Generating SHAP summary plot...")

    plt.figure()

    shap.summary_plot(
        shap_values_to_use,
        X,
        show=False
    )

    plt.title("SHAP Feature Impact on RT Activity")

    plt.tight_layout()

    plt.savefig(results_dir / "shap_summary_plot.png", dpi=300)

    plt.close()

    # ------------------------------------------------
    # SHAP Bar Plot
    # ------------------------------------------------

    print("Generating SHAP bar plot...")

    plt.figure()

    shap.summary_plot(
        shap_values_to_use,
        X,
        plot_type="bar",
        show=False
    )

    plt.title("Global Feature Importance (SHAP)")

    plt.tight_layout()

    plt.savefig(results_dir / "shap_bar_plot.png", dpi=300)

    plt.close()

    print("\nSHAP analysis complete.")

    print("Saved files:")
    print("results/shap_summary_plot.png")
    print("results/shap_bar_plot.png")


if __name__ == "__main__":
    run_shap()