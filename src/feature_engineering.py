import pandas as pd
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.decomposition import PCA
from data_loader import load_data


def engineer_features():

    # -----------------------------
    # Load dataset
    # -----------------------------
    df = load_data()

    y = df["active"]

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

    # ensure sklearn compatibility
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
    # REMOVE FOLDSEEK FEATURES
    # -----------------------------
    foldseek_cols = [c for c in X_imputed.columns if "foldseek" in c]

    X_imputed = X_imputed.drop(columns=foldseek_cols)

    print("Removed FoldSeek features:", len(foldseek_cols))

    # -----------------------------
    # Identify embedding columns
    # -----------------------------
    esm_cols = X_imputed.columns[-1280:]

    # -----------------------------
    # PCA compression of embeddings
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
        [X_imputed.reset_index(drop=True),
         esm_df.reset_index(drop=True)],
        axis=1
    )

    print("Final feature matrix shape:", X_imputed.shape)

    return X_imputed, y


if __name__ == "__main__":

    X, y = engineer_features()

    print("\nFeature matrix shape:", X.shape)
    print("Target shape:", y.shape)