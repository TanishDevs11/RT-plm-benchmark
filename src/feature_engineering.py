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

    # Target variable
    y = df["active"]

    # -----------------------------
    # Remove non-feature columns
    # -----------------------------
    drop_cols = [
        "active",
        "rt_name",
        "sequence",
        "rt_family",       # Prevent family leakage
        "pe_efficiency_pct"
    ]

    X = df.drop(columns=drop_cols)

    # Ensure column names are strings (sklearn requirement)
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
    # Identify embedding columns
    # -----------------------------
    # In this dataset the LAST 1280 columns correspond to ESM embeddings
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

    # -----------------------------
    # Final output
    # -----------------------------
    print("Final feature matrix shape:", X_imputed.shape)

    return X_imputed, y


# -----------------------------
# Run standalone test
# -----------------------------
if __name__ == "__main__":

    X, y = engineer_features()

    print("\nFeature matrix shape:", X.shape)
    print("Target shape:", y.shape)