import os
import glob
import numpy as np
import pandas as pd
import math

def parse_pdb_ca(file_path):
    coords = []
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith("ATOM  "):
                atom_name = line[12:16].strip()
                if atom_name == "CA":
                    try:
                        x = float(line[30:38])
                        y = float(line[38:46])
                        z = float(line[46:54])
                        coords.append((x, y, z))
                    except ValueError:
                        pass
    return np.array(coords)

def compute_topology_features(coords):
    if len(coords) < 10:
        return {
            "top_contact_density": np.nan,
            "top_long_range_ratio": np.nan,
            "top_mean_ca_dist": np.nan,
            "top_max_ca_dist": np.nan,
            "top_entropy_degree": np.nan,
            "top_mean_degree": np.nan,
            "top_std_degree": np.nan,
            "top_clustering_proxy": np.nan,
            "top_contact_entropy": np.nan,
        }
    
    # Pairwise distances
    diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
    dist = np.sqrt(np.sum(diff**2, axis=-1))
    
    n = len(coords)
    
    # Contact map cutoff (angstroms)
    contact_cutoff = 8.0
    contact_map = (dist < contact_cutoff) & (dist > 0)
    
    # Contact density
    total_contacts = np.sum(contact_map) / 2.0
    contact_density = total_contacts / n
    
    # Long range fraction
    i_idx, j_idx = np.indices(dist.shape)
    seq_sep = np.abs(i_idx - j_idx)
    long_range = contact_map & (seq_sep > 12)
    total_long = np.sum(long_range) / 2.0
    long_range_ratio = total_long / (total_contacts + 1e-6)
    
    # Mean and Max CA Dist
    mean_ca = np.mean(dist[np.triu_indices_from(dist, k=1)])
    max_ca = np.max(dist)
    
    # Top Entropy Degree
    degrees = np.sum(contact_map, axis=1)
    hist, _ = np.histogram(degrees, bins=10, density=True)
    hist = hist[hist > 0]
    entropy_deg = -np.sum(hist * np.log(hist))

    mean_deg = float(np.mean(degrees))
    std_deg = float(np.std(degrees))

    # Clustering proxy: fraction of closed triplets among all triplets.
    # For an undirected adjacency A, triangles ~ trace(A^3)/6.
    # Use float math to avoid overflow on small n.
    A = contact_map.astype(np.float32)
    # Count triangles with matrix multiplication (n is small: CA count)
    A2 = A @ A
    A3 = A2 @ A
    triangles = float(np.trace(A3) / 6.0)
    triplets = float(np.sum(degrees * (degrees - 1.0)) / 2.0)
    clustering_proxy = triangles / (triplets + 1e-6)

    # Contact entropy: entropy of contact probability across all residue pairs.
    # Helps capture "diffuse vs modular" contact patterns.
    p = float(total_contacts) / float((n * (n - 1)) / 2.0)
    p = min(max(p, 1e-9), 1.0 - 1e-9)
    contact_entropy = -(p * math.log(p) + (1.0 - p) * math.log(1.0 - p))
    
    return {
        "top_contact_density": contact_density,
        "top_long_range_ratio": long_range_ratio,
        "top_mean_ca_dist": mean_ca,
        "top_max_ca_dist": max_ca,
        "top_entropy_degree": entropy_deg,
        "top_mean_degree": mean_deg,
        "top_std_degree": std_deg,
        "top_clustering_proxy": clustering_proxy,
        "top_contact_entropy": contact_entropy,
    }

def _normalize_rt_name(s: str) -> str:
    s = str(s)
    # unify separators
    s = s.replace(".pdb", "")
    s = s.replace("_RT", "").replace("-RT", "")
    s = s.replace("-CasRT", "")
    s = s.replace("__", "_").replace("--", "-")
    s = s.strip()
    # historical quirks seen in this repo
    if s == "Vp-96":
        s = "Vp96"
    if s == "Tyrosinerecomb":
        s = "Tyrosine_recomb"
    return s

def main():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    pdb_dir = os.path.join(root_dir, "data", "structures")
    
    if not os.path.exists(pdb_dir):
        print(f"PDB directory {pdb_dir} not found.")
        return

    seq_path = os.path.join(root_dir, "data", "rt_sequences.csv")
    seq_names = None
    if os.path.exists(seq_path):
        try:
            seq_names = set(pd.read_csv(seq_path)["rt_name"].astype(str).tolist())
        except Exception:
            seq_names = None
        
    records = []
    for pdb_path in glob.glob(os.path.join(pdb_dir, "*.pdb")):
        filename = os.path.basename(pdb_path)
        rt_name_guess = _normalize_rt_name(filename)
        rt_name = rt_name_guess

        # If we have the canonical RT names, prefer an exact match.
        if seq_names is not None and rt_name_guess not in seq_names:
            # Try a couple of lightweight fallbacks.
            candidates = [
                rt_name_guess.replace("-", "_"),
                rt_name_guess.replace("_", "-"),
                rt_name_guess.replace(" ", "_"),
            ]
            matched = [c for c in candidates if c in seq_names]
            if len(matched) == 1:
                rt_name = matched[0]
            
        coords = parse_pdb_ca(pdb_path)
        feats = compute_topology_features(coords)
        
        row = {"rt_name": rt_name, "pdb_filename": filename}
        row.update(feats)
        records.append(row)
        
    df = pd.DataFrame(records)
    out_path = os.path.join(root_dir, "data", "topology_features.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_csv(out_path, index=False)
    print(f"Saved {len(df)} topology features to {out_path}")

if __name__ == "__main__":
    main()
