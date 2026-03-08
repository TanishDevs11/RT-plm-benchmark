import pandas as pd
import numpy as np

from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from data_loader import load_data


def engineer_features():

    # -----------------------------
    # Load dataset
    # -----------------------------
    df = load_data()

    # Target variable
    y = df["active"]

    # Groups for LOFO validation
    groups = df["rt_family"]

    # -----------------------------
    # Remove non-feature columns
    # -----------------------------
    drop_cols = [
        "active",
        "rt_name",
        "sequence",
        "rt_family",      # prevent leakage
        "pe_efficiency_pct"
    ]

    X = df.drop(columns=drop_cols)

    # Ensure sklearn compatibility
    X.columns = X.columns.astype(str)

    # -----------------------------
    # Handle missing values
    # -----------------------------
    imputer = SimpleImputer(strategy="median")

    X_imputed = imputer.fit_transform(X)

    X_imputed = pd.DataFrame(
        X_imputed,
        columns=X.columns
    )

    # -----------------------------
    # Remove FoldSeek features
    # -----------------------------
    foldseek_cols = [c for c in X_imputed.columns if "foldseek" in c]

    if foldseek_cols:
        X_imputed = X_imputed.drop(columns=foldseek_cols)

    print("Removed FoldSeek features:", len(foldseek_cols))

    # -----------------------------
    # Detect ESM embeddings
    # -----------------------------
    # ESM embeddings are always the LAST 1280 columns
    if X_imputed.shape[1] >= 1280:

        esm_cols = X_imputed.columns[-1280:]

        print("Detected ESM embedding columns:", len(esm_cols))

        # -----------------------------
        # PCA compression
        # -----------------------------
        pca = PCA(n_components=20, random_state=42)

        esm_reduced = pca.fit_transform(X_imputed[esm_cols])

        esm_df = pd.DataFrame(
            esm_reduced,
            columns=[f"esm_pca_{i}" for i in range(20)]
        )

        # Remove original embeddings
        X_imputed = X_imputed.drop(columns=esm_cols)

        # Add compressed embeddings
        X_imputed = pd.concat(
            [X_imputed.reset_index(drop=True), esm_df],
            axis=1
        )

    # -----------------------------
    # Feature Scaling
    # -----------------------------
    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X_imputed)

    X_scaled = pd.DataFrame(
        X_scaled,
        columns=X_imputed.columns
    )

    print("Final feature matrix shape:", X_scaled.shape)

    return X_scaled, y, groups


# -----------------------------
# Standalone test
# -----------------------------
if __name__ == "__main__":

    X, y, groups = engineer_features()

    print("\nFeature matrix shape:", X.shape)
    print("Target shape:", y.shape)
    print("Groups shape:", groups.shape)