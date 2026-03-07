import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier

from feature_engineering import engineer_features


def analyze_feature_importance():

    print("Loading features...")

    X, y = engineer_features()

    print("Training Random Forest...")

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=6,
        random_state=42
    )

    model.fit(X, y)

    importances = model.feature_importances_

    feature_df = pd.DataFrame({
        "feature": X.columns,
        "importance": importances
    })

    feature_df = feature_df.sort_values(
        by="importance",
        ascending=False
    )

    print("\nTop 20 Important Features:\n")
    print(feature_df.head(20))

    # Plot
    top = feature_df.head(15)

    plt.figure(figsize=(8,6))
    plt.barh(top["feature"], top["importance"])
    plt.gca().invert_yaxis()
    plt.title("Top Feature Importances")
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    analyze_feature_importance()