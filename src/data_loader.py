import pandas as pd
import numpy as np


def load_data():

    # -----------------------------
    # Load sequence dataset
    # -----------------------------
    seq_df = pd.read_csv("data/rt_sequences.csv")

    # -----------------------------
    # Load handcrafted features
    # -----------------------------
    feat_df = pd.read_csv("data/handcrafted_features.csv")

    # -----------------------------
    # Load structure features
    # -----------------------------
    struct_df = pd.read_csv("data/structure_features.csv")

    # -----------------------------
    # Load topology/contact-map features (optional)
    # -----------------------------
    topo_path = "data/topology_features.csv"
    topo_df = None
    try:
        topo_df = pd.read_csv(topo_path)
    except Exception:
        topo_df = None

    # -----------------------------
    # Load ESM embeddings
    # -----------------------------
    esm = np.load("data/esm2_embeddings.npz", allow_pickle=True)

    embeddings = esm["embeddings"]
    names = esm["names"]

    # Convert to dataframe
    esm_df = pd.DataFrame(
        embeddings,
        columns=[f"esm_{i}" for i in range(embeddings.shape[1])]
    )

    # Attach correct IDs from embedding file
    esm_df["rt_name"] = names


    # -----------------------------
    # Merge datasets correctly
    # -----------------------------
    df = seq_df.merge(feat_df, on="rt_name", how="left")

    df = df.merge(struct_df, on="rt_name", how="left")

    if topo_df is not None and "rt_name" in topo_df.columns:
        # The canonical dataset uses "-RT" suffix; PDB-derived names may omit it.
        topo_df = topo_df.copy()
        topo_df["rt_name"] = topo_df["rt_name"].astype(str)
        topo_alt = topo_df.copy()
        needs_suffix = ~topo_alt["rt_name"].str.endswith("-RT")
        topo_alt.loc[needs_suffix, "rt_name"] = topo_alt.loc[needs_suffix, "rt_name"] + "-RT"
        topo_merged = pd.concat([topo_df, topo_alt], ignore_index=True)
        topo_merged = topo_merged.drop_duplicates(subset=["rt_name"], keep="first")

        df = df.merge(topo_merged, on="rt_name", how="left")

        # Keep feature matrix numeric-only for modeling
        if "pdb_filename" in df.columns:
            df = df.drop(columns=["pdb_filename"], errors="ignore")

    df = df.merge(esm_df, on="rt_name", how="left")


    return df


if __name__ == "__main__":

    df = load_data()

    print("Loaded dataset shape:", df.shape)
    print(df.head())