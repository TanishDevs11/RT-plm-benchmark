import pandas as pd
import numpy as np

from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from data_loader import load_data


def add_active_site_features(df):

    # Only compute if catalytic distances exist
    if {"D1_D2_dist", "D2_D3_dist"}.issubset(df.columns):

        print("Adding active-site geometry features...")

        df["triad_distance_ratio"] = df["D1_D2_dist"] / (df["D2_D3_dist"] + 1e-6)

        df["triad_spread"] = (
            df["D1_D2_dist"] + df["D2_D3_dist"]
        ) / 2

        df["triad_compactness"] = 1 / (df["triad_spread"] + 1e-6)

        a = df["D1_D2_dist"]
        b = df["D2_D3_dist"]
        c = df["D1_D2_dist"] + df["D2_D3_dist"]

        df["triad_angle_proxy"] = (
            (a**2 + b**2 - c**2) /
            (2 * a * b + 1e-6)
        )

    return df


def engineer_features():

    # -----------------------------
    # Load dataset
    # -----------------------------
    df = load_data()

    # Add catalytic geometry features
    df = add_active_site_features(df)

    y = df["active"]
    groups = df["rt_family"]

    # -----------------------------
    # Remove non-feature columns
    # -----------------------------
    drop_cols = [
        "active",
        "rt_name",
        "sequence",
        "rt_family",
        "pe_efficiency_pct"
    ]

    X = df.drop(columns=drop_cols)

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
    if X_imputed.shape[1] >= 1280:

        esm_cols = X_imputed.columns[-1280:]

        print("Detected ESM embedding columns:", len(esm_cols))

        pca = PCA(n_components=20, random_state=42)

        esm_reduced = pca.fit_transform(X_imputed[esm_cols])

        esm_df = pd.DataFrame(
            esm_reduced,
            columns=[f"esm_pca_{i}" for i in range(20)]
        )

        X_imputed = X_imputed.drop(columns=esm_cols)

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

    # -----------------------------
    # Apply Feature Selection
    # -----------------------------
    try:

        selected_features = pd.read_csv(
            "data/selected_features.csv",
            header=None
        )[0].tolist()

        # keep only features that exist
        selected_features = [
            f for f in selected_features if f in X_scaled.columns
        ]

        X_scaled = X_scaled[selected_features]

        print("Applied feature selection:", len(selected_features))

    except FileNotFoundError:

        print("No selected_features.csv found — using all features")

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