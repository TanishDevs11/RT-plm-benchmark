import pandas as pd
import numpy as np

from sklearn.ensemble import RandomForestClassifier

from feature_engineering import engineer_features


def select_features(top_k=30):

    print("🚀 Loading engineered features...\n")

    # Load engineered features
    X, y, groups = engineer_features()

    print("Initial feature matrix shape:", X.shape)

    # -----------------------------
    # Clean features
    # -----------------------------

    X = X.replace([np.inf, -np.inf], np.nan)
    X = X.fillna(X.median())

    print("Cleaned feature matrix shape:", X.shape)

    # -----------------------------
    # Train RandomForest
    # -----------------------------

    model = RandomForestClassifier(
        n_estimators=600,
        max_depth=8,
        random_state=42,
        n_jobs=-1
    )

    print("\nTraining model for feature importance...\n")

    model.fit(X, y)

    # -----------------------------
    # Compute importance
    # -----------------------------

    importance_df = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_
    })

    importance_df = importance_df.sort_values(
        "importance",
        ascending=False
    ).reset_index(drop=True)

    # -----------------------------
    # Show results
    # -----------------------------

    print("Top 20 Important Features:\n")
    print(importance_df.head(20))

    # -----------------------------
    # Select top features
    # -----------------------------

    top_features = importance_df.head(top_k)["feature"].tolist()

    print("\nSelected Feature Count:", len(top_features))

    # -----------------------------
    # Return results
    # -----------------------------

    return top_features, importance_df


if __name__ == "__main__":

    print("Starting feature selection...\n")

    features, importance_table = select_features(top_k=30)

    print("\nSaving selected features...")

    # Save selected feature list
    pd.Series(features).to_csv(
        "data/selected_features.csv",
        index=False,
        header=False
    )

    # Save full importance table
    importance_table.to_csv(
        "data/feature_importance_table.csv",
        index=False
    )

    print("\nFiles saved:")
    print("data/selected_features.csv")
    print("data/feature_importance_table.csv")

    print("\nSelected features:\n")
    for f in features:
        print(f)

    print("\n✅ Feature selection complete.")