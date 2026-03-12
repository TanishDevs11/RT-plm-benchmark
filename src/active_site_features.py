import pandas as pd
import numpy as np


def compute_active_site_features(df):

    print("Computing active-site geometry features...")

    # Distance ratio between catalytic residues
    df["triad_distance_ratio"] = df["D1_D2_dist"] / (df["D2_D3_dist"] + 1e-6)

    # Spread of catalytic residues
    df["triad_spread"] = (
        df["D1_D2_dist"] +
        df["D2_D3_dist"]
    ) / 2

    # Compactness score
    df["triad_compactness"] = 1 / (df["triad_spread"] + 1e-6)

    # Angle approximation using cosine rule
    a = df["D1_D2_dist"]
    b = df["D2_D3_dist"]
    c = df["D1_D2_dist"] + df["D2_D3_dist"]

    df["triad_angle_proxy"] = (
        (a**2 + b**2 - c**2) /
        (2 * a * b + 1e-6)
    )

    print("Added active-site features")

    return df