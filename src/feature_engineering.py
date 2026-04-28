import re
from pathlib import Path

import numpy as np
import pandas as pd

from data_loader import load_data


def add_active_site_features(df):
    if {"D1_D2_dist", "D2_D3_dist"}.issubset(df.columns):
        a = df["D1_D2_dist"]
        b = df["D2_D3_dist"]
        triad_features = pd.DataFrame(
            {
                "triad_distance_ratio": a / (b + 1e-6),
                "triad_mean_dist": (a + b) / 2,
                "triad_diff_dist": abs(a - b),
                "triad_geom_mean": np.sqrt(a * b),
                "triad_compactness": 1 / ((a + b) / 2 + 1e-6),
                "triad_angle_proxy": (a**2 + b**2 - (a + b) ** 2) / (2 * a * b + 1e-6),
            },
            index=df.index,
        )
        df = pd.concat([df, triad_features], axis=1)
    return df


def add_interaction_features(df):
    interaction_features = {}
    if {"triad_compactness", "pocket_hydrophobic"}.issubset(df.columns):
        interaction_features["triad_hydrophobic_interaction"] = (
            df["triad_compactness"] * df["pocket_hydrophobic"]
        )
    if {"triad_distance_ratio", "n_hbonds"}.issubset(df.columns):
        interaction_features["triad_hbond_interaction"] = (
            df["triad_distance_ratio"] * df["n_hbonds"]
        )
    if {"radius_gyration", "salt_per_res"}.issubset(df.columns):
        interaction_features["salt_compaction_score"] = (
            df["salt_per_res"] / (df["radius_gyration"] + 1e-6)
        )
    if {"pocket_hydrophobic", "hydrophobic_per_res"}.issubset(df.columns):
        interaction_features["hydrophobic_core_score"] = (
            df["pocket_hydrophobic"] * df["hydrophobic_per_res"]
        )
    if {"n_hbonds", "protein_length_aa"}.issubset(df.columns):
        interaction_features["hbonds_density"] = (
            df["n_hbonds"] / (df["protein_length_aa"] + 1e-6)
        )
    if interaction_features:
        df = pd.concat([df, pd.DataFrame(interaction_features, index=df.index)], axis=1)
    return df


def _parse_ca_coords(pdb_path):
    coords = []
    try:
        with open(pdb_path, "r", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                if not line.startswith("ATOM"):
                    continue
                if line[12:16].strip() != "CA":
                    continue
                try:
                    coords.append(
                        [
                            float(line[30:38]),
                            float(line[38:46]),
                            float(line[46:54]),
                        ]
                    )
                except ValueError:
                    continue
    except OSError:
        return np.empty((0, 3), dtype=float)
    return np.asarray(coords, dtype=float)


def _find_catalytic_indices(sequence):
    seq = str(sequence).upper()
    match = re.search(r"Y.DD", seq)
    if match:
        d1 = match.start() + 2
        d2 = match.start() + 3
        d3 = seq.find("D", d2 + 1, min(len(seq), d2 + 16))
        if d3 != -1:
            return [d1, d2, d3]
    d_positions = [idx for idx, aa in enumerate(seq) if aa == "D"]
    if len(d_positions) >= 3:
        return d_positions[:3]
    return None


def add_cleft_geometry_features(df):
    struct_dir = Path("data") / "structures"
    rows = []
    for rt_name, row in df.iterrows():
        sequence = row.get("sequence", "")
        cat_idx = _find_catalytic_indices(sequence)
        ca_coords = _parse_ca_coords(struct_dir / f"{rt_name}.pdb")
        result = {
            "cleft_triangle_area": np.nan,
            "cleft_sasa_mean": np.nan,
            "cleft_local_density": np.nan,
            "thumb_palm_distance_proxy": np.nan,
            "cleft_open_score": np.nan,
            "cleft_curvature_proxy": np.nan,
            "cleft_thumb_asymmetry": np.nan,
            "cleft_tunnel_curvature_score": np.nan,
        }
        if cat_idx is None or ca_coords.shape[0] == 0:
            rows.append(result)
            continue
        valid_idx = [idx for idx in cat_idx if idx < ca_coords.shape[0]]
        if len(valid_idx) < 3:
            rows.append(result)
            continue

        p1, p2, p3 = ca_coords[valid_idx[0]], ca_coords[valid_idx[1]], ca_coords[valid_idx[2]]
        d12 = np.linalg.norm(p1 - p2)
        d23 = np.linalg.norm(p2 - p3)
        d13 = np.linalg.norm(p1 - p3)
        s = (d12 + d23 + d13) / 2.0
        triangle_area = np.sqrt(max(s * (s - d12) * (s - d23) * (s - d13), 0.0))

        catalytic_pts = ca_coords[valid_idx]
        catalytic_center = catalytic_pts.mean(axis=0)
        dists_to_center = np.linalg.norm(ca_coords - catalytic_center, axis=1)
        local_density = float((dists_to_center <= 8.0).sum())

        neighbor_counts = []
        for idx in valid_idx:
            row_d = np.linalg.norm(ca_coords - ca_coords[idx], axis=1)
            neighbor_counts.append(float(((row_d <= 8.0) & (row_d > 0)).sum()))
        exposure_proxy = np.mean([1.0 / (1.0 + x) for x in neighbor_counts])
        sasa_scale = float(row.get("sasa_avg", 1.0))
        if np.isnan(sasa_scale):
            sasa_scale = 1.0
        cleft_sasa_mean = exposure_proxy * sasa_scale

        thumb_start = max(int(0.75 * ca_coords.shape[0]), 0)
        thumb_coords = ca_coords[thumb_start:]
        if thumb_coords.shape[0] == 0:
            thumb_coords = ca_coords[-max(3, ca_coords.shape[0] // 5) :]
        thumb_centroid = thumb_coords.mean(axis=0)
        thumb_palm_distance = float(np.linalg.norm(thumb_centroid - catalytic_center))

        neighbor_core = ca_coords[dists_to_center <= 12.0]
        if neighbor_core.shape[0] > 0:
            neighbor_centroid = neighbor_core.mean(axis=0)
            curvature_proxy = float(
                np.linalg.norm(p1 - neighbor_centroid)
                + np.linalg.norm(p2 - neighbor_centroid)
                + np.linalg.norm(p3 - neighbor_centroid)
            )
        else:
            curvature_proxy = np.nan

        thumb_asymmetry = float(
            np.linalg.norm(p1 - thumb_centroid) - np.linalg.norm(p3 - thumb_centroid)
        )
        tunnel_curvature_score = float(
            curvature_proxy * (cleft_sasa_mean / (sasa_scale + 1e-8))
            if np.isfinite(curvature_proxy)
            else np.nan
        )

        cleft_open_score = (
            triangle_area + cleft_sasa_mean - local_density + thumb_palm_distance
        )
        result.update(
            {
                "cleft_triangle_area": float(triangle_area),
                "cleft_sasa_mean": float(cleft_sasa_mean),
                "cleft_local_density": float(local_density),
                "thumb_palm_distance_proxy": float(thumb_palm_distance),
                "cleft_open_score": float(cleft_open_score),
                "cleft_curvature_proxy": float(curvature_proxy),
                "cleft_thumb_asymmetry": float(thumb_asymmetry),
                "cleft_tunnel_curvature_score": float(tunnel_curvature_score),
            }
        )
        rows.append(result)

    cleft_df = pd.DataFrame(rows, index=df.index)
    return pd.concat([df, cleft_df], axis=1)


def engineer_features():
    df = load_data()
    if "rt_name" in df.columns:
        df = df.set_index("rt_name")

    df = add_active_site_features(df)
    df = add_cleft_geometry_features(df)
    df = add_interaction_features(df)

    if {"helix", "sheet"}.issubset(df.columns):
        df["helix_sheet_ratio"] = df["helix"] / (df["sheet"] + 1e-6)

    if {"whole_mean_hydrophobicity", "radius_gyration"}.issubset(df.columns):
        df["compactness_hydro"] = df["whole_mean_hydrophobicity"] / (
            df["radius_gyration"] + 1e-6
        )

    if {"ramachandran_favoured", "ramachandran_outliers"}.issubset(df.columns):
        df["rama_quality_score"] = (
            df["ramachandran_favoured"] - df["ramachandran_outliers"]
        )

    y = df["active"]
    groups = df["rt_family"]

    drop_cols = ["active", "sequence", "rt_family", "pe_efficiency_pct"]
    X = df.drop(columns=drop_cols, errors="ignore")
    X.columns = X.columns.astype(str)

    foldseek_cols = [c for c in X.columns if "foldseek" in c.lower()]
    if foldseek_cols:
        X = X.drop(columns=foldseek_cols)

    X = X.replace([np.inf, -np.inf], np.nan)

    print("Removed FoldSeek features:", len(foldseek_cols))
    print("Returning enhanced feature matrix")
    print("Feature matrix shape:", X.shape)
    return X, y, groups


if __name__ == "__main__":
    X, y, groups = engineer_features()
    print("\nFeature matrix shape:", X.shape)
    print("Target shape:", y.shape)
    print("Groups shape:", groups.shape)
