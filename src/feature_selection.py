import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from feature_engineering import engineer_features


def select_features():

    print("Loading engineered features...\n")

    X, y, groups = engineer_features()

    print("Feature matrix shape:", X.shape)

    model = RandomForestClassifier(
        n_estimators=500,
        max_depth=6,
        random_state=42,
        n_jobs=-1
    )

    print("\nTraining model for feature importance...\n")

    model.fit(X, y)

    importance_df = pd.DataFrame({
        "feature": X.columns,
        "importance": model.feature_importances_
    })

    importance_df = importance_df.sort_values(
        "importance",
        ascending=False
    )

    print("Top 20 Features:\n")
    print(importance_df.head(20))

    # Select top features
    top_features = importance_df.head(50)["feature"].tolist()

    print("\nSelected Feature Count:", len(top_features))

    return top_features, importance_df


if __name__ == "__main__":

    print("Starting feature selection...\n")

    features, importance_table = select_features()

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
    print(features)