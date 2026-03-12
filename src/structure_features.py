import os
import numpy as np
import pandas as pd

from Bio.PDB import PDBParser


def compute_radius_of_gyration(coords):
    """
    Compute radius of gyration for a set of coordinates
    """
    center = coords.mean(axis=0)
    squared_dist = ((coords - center) ** 2).sum(axis=1)
    return np.sqrt(squared_dist.mean())


def extract_structure_features(structure_dir="data/structures"):

    parser = PDBParser(QUIET=True)

    records = []

    pdb_files = [f for f in os.listdir(structure_dir) if f.endswith(".pdb")]

    print("Found PDB files:", len(pdb_files))

    for pdb_file in pdb_files:

        pdb_path = os.path.join(structure_dir, pdb_file)

        structure = parser.get_structure(pdb_file, pdb_path)

        atoms = []
        residues = []

        for atom in structure.get_atoms():
            atoms.append(atom.coord)

        for residue in structure.get_residues():
            residues.append(residue)

        atoms = np.array(atoms)

        if len(atoms) == 0:
            continue

        # Basic structural metrics
        num_atoms = len(atoms)
        num_residues = len(residues)

        radius_gyration = compute_radius_of_gyration(atoms)

        # CA atom spread
        ca_coords = [
            atom.coord
            for atom in structure.get_atoms()
            if atom.get_name() == "CA"
        ]

        if len(ca_coords) > 1:
            ca_coords = np.array(ca_coords)
            ca_distances = np.linalg.norm(
                ca_coords - ca_coords.mean(axis=0), axis=1
            )
            avg_ca_distance = ca_distances.mean()
        else:
            avg_ca_distance = 0

        rt_name = pdb_file.replace(".pdb", "")

        records.append({
            "rt_name": rt_name,
            "n_atoms": num_atoms,
            "n_residues": num_residues,
            "radius_gyration": radius_gyration,
            "avg_ca_distance": avg_ca_distance
        })

    df = pd.DataFrame(records)

    return df


if __name__ == "__main__":

    df = extract_structure_features()

    print("\nExtracted structure features:")
    print(df.head())

    # Save features
    os.makedirs("data", exist_ok=True)

    output_path = "data/structure_features.csv"

    df.to_csv(output_path, index=False)

    print("\nSaved to:", output_path)