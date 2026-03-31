import pandas as pd
import numpy as np

from data_loader import load_data


def add_active_site_features(df):

    if {"D1_D2_dist", "D2_D3_dist"}.issubset(df.columns):

        print("Adding active-site geometry features...")

        df["triad_distance_ratio"] = df["D1_D2_dist"] / (
            df["D2_D3_dist"] + 1e-6
        )

        df["triad_spread"] = (
            df["D1_D2_dist"] + df["D2_D3_dist"]
        ) / 2

        df["triad_compactness"] = 1 / (
            df["triad_spread"] + 1e-6
        )

        a = df["D1_D2_dist"]
        b = df["D2_D3_dist"]
        c = df["D1_D2_dist"] + df["D2_D3_dist"]

        df["triad_angle_proxy"] = (
            (a**2 + b**2 - c**2) /
            (2 * a * b + 1e-6)
        )

    return df


def add_interaction_features(df):

    print("Adding interaction features...")

    if {"triad_compactness", "pocket_hydrophobic"}.issubset(df.columns):

        df["triad_hydrophobic_interaction"] = (
            df["triad_compactness"] * df["pocket_hydrophobic"]
        )

    if {"triad_distance_ratio", "n_hbonds"}.issubset(df.columns):

        df["triad_hbond_interaction"] = (
            df["triad_distance_ratio"] * df["n_hbonds"]
        )

    if {"radius_gyration", "salt_per_res"}.issubset(df.columns):

        df["gyration_salt_interaction"] = (
            df["radius_gyration"] * df["salt_per_res"]
        )

    if {"triad_spread", "hydrophobic_per_res"}.issubset(df.columns):

        df["spread_hydrophobic_interaction"] = (
            df["triad_spread"] * df["hydrophobic_per_res"]
        )

    return df


def engineer_features():

    df = load_data()

    df = add_active_site_features(df)
    df = add_interaction_features(df)

    y = df["active"]
    groups = df["rt_family"]

    drop_cols = [
        "active",
        "rt_name",
        "sequence",
        "rt_family",
        "pe_efficiency_pct"
    ]

    X = df.drop(columns=drop_cols)

    X.columns = X.columns.astype(str)

    # Remove FoldSeek features safely
    foldseek_cols = [
        c for c in X.columns
        if "foldseek" in c.lower()
    ]

    if foldseek_cols:
        X = X.drop(columns=foldseek_cols)

    print("Removed FoldSeek features:", len(foldseek_cols))
    print("Returning raw feature matrix (no scaling applied)")
    print("Feature matrix shape:", X.shape)

    return X, y, groups


if __name__ == "__main__":

    X, y, groups = engineer_features()

    print("\nFeature matrix shape:", X.shape)
    print("Target shape:", y.shape)
    print("Groups shape:", groups.shape)