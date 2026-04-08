import pandas as pd
import numpy as np

from data_loader import load_data


# --------------------------------------------------
# Catalytic triad geometry features
# --------------------------------------------------

def add_active_site_features(df):

    if {"D1_D2_dist", "D2_D3_dist"}.issubset(df.columns):

        a = df["D1_D2_dist"]
        b = df["D2_D3_dist"]

        triad_features = pd.DataFrame({

            # geometry symmetry signal
            "triad_distance_ratio": a / (b + 1e-6),

            # catalytic spacing magnitude
            "triad_mean_dist": (a + b) / 2,

            # asymmetry indicator (important ranking signal)
            "triad_diff_dist": abs(a - b),

            # geometric stability proxy
            "triad_geom_mean": np.sqrt(a * b),

            # compactness score
            "triad_compactness":
                1 / ((a + b) / 2 + 1e-6),

            # angle proxy
            "triad_angle_proxy":
                (a**2 + b**2 - (a + b)**2) /
                (2 * a * b + 1e-6)

        }, index=df.index)

        df = pd.concat([df, triad_features], axis=1)

    return df


# --------------------------------------------------
# Interaction features
# --------------------------------------------------

def add_interaction_features(df):

    interaction_features = {}

    # catalytic geometry × hydrophobic pocket strength
    if {"triad_compactness", "pocket_hydrophobic"}.issubset(df.columns):
        interaction_features["triad_hydrophobic_interaction"] = (
            df["triad_compactness"] *
            df["pocket_hydrophobic"]
        )

    # catalytic geometry × hydrogen bonding
    if {"triad_distance_ratio", "n_hbonds"}.issubset(df.columns):
        interaction_features["triad_hbond_interaction"] = (
            df["triad_distance_ratio"] *
            df["n_hbonds"]
        )

    # structural compactness × salt bridges
    if {"radius_gyration", "salt_per_res"}.issubset(df.columns):
        interaction_features["salt_compaction_score"] = (
            df["salt_per_res"] /
            (df["radius_gyration"] + 1e-6)
        )

    # hydrophobic catalytic core strength
    if {"pocket_hydrophobic", "hydrophobic_per_res"}.issubset(df.columns):
        interaction_features["hydrophobic_core_score"] = (
            df["pocket_hydrophobic"] *
            df["hydrophobic_per_res"]
        )

    # normalized hydrogen bonding density
    if {"n_hbonds", "protein_length_aa"}.issubset(df.columns):
        interaction_features["hbonds_density"] = (
            df["n_hbonds"] /
            (df["protein_length_aa"] + 1e-6)
        )

    if interaction_features:
        df = pd.concat(
            [df, pd.DataFrame(interaction_features, index=df.index)],
            axis=1
        )

    return df


# --------------------------------------------------
# Feature engineering pipeline
# --------------------------------------------------

def engineer_features():

    df = load_data()

    # align index with rt_sequences.csv
    if "rt_name" in df.columns:
        df = df.set_index("rt_name")


    # --------------------------------------------------
    # Geometry features
    # --------------------------------------------------

    df = add_active_site_features(df)


    # --------------------------------------------------
    # Interaction features
    # --------------------------------------------------

    df = add_interaction_features(df)


    # --------------------------------------------------
    # Secondary structure balance
    # --------------------------------------------------

    if {"helix", "sheet"}.issubset(df.columns):
        df["helix_sheet_ratio"] = (
            df["helix"] /
            (df["sheet"] + 1e-6)
        )


    # --------------------------------------------------
    # Hydrophobic compactness signal
    # --------------------------------------------------

    if {"whole_mean_hydrophobicity", "radius_gyration"}.issubset(df.columns):
        df["compactness_hydro"] = (
            df["whole_mean_hydrophobicity"] /
            (df["radius_gyration"] + 1e-6)
        )


    # --------------------------------------------------
    # Ramachandran structural quality score
    # --------------------------------------------------

    if {"ramachandran_favoured", "ramachandran_outliers"}.issubset(df.columns):
        df["rama_quality_score"] = (
            df["ramachandran_favoured"] -
            df["ramachandran_outliers"]
        )


    # --------------------------------------------------
    # Targets
    # --------------------------------------------------

    y = df["active"]
    groups = df["rt_family"]


    # --------------------------------------------------
    # Drop non-feature columns
    # --------------------------------------------------

    drop_cols = [
        "active",
        "sequence",
        "rt_family",
        "pe_efficiency_pct"
    ]

    X = df.drop(columns=drop_cols, errors="ignore")

    X.columns = X.columns.astype(str)


    # --------------------------------------------------
    # Remove FoldSeek embeddings (noise-heavy)
    # --------------------------------------------------

    foldseek_cols = [
        c for c in X.columns
        if "foldseek" in c.lower()
    ]

    if foldseek_cols:
        X = X.drop(columns=foldseek_cols)


    # --------------------------------------------------
    # Numerical safety cleanup
    # --------------------------------------------------

    X = X.replace([np.inf, -np.inf], np.nan)


    print("Removed FoldSeek features:", len(foldseek_cols))
    print("Returning enhanced feature matrix")
    print("Feature matrix shape:", X.shape)

    return X, y, groups


# --------------------------------------------------
# Standalone test
# --------------------------------------------------

if __name__ == "__main__":

    X, y, groups = engineer_features()

    print("\nFeature matrix shape:", X.shape)
    print("Target shape:", y.shape)
    print("Groups shape:", groups.shape)

