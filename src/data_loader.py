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

    df = df.merge(esm_df, on="rt_name", how="left")


    return df


if __name__ == "__main__":

    df = load_data()

    print("Loaded dataset shape:", df.shape)
    print(df.head())