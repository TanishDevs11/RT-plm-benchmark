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
    esm = np.load("data/esm2_embeddings.npz")

    esm_embeddings = esm["embeddings"]

    esm_df = pd.DataFrame(esm_embeddings)

    # -----------------------------
    # Merge datasets
    # -----------------------------
    df = seq_df.merge(feat_df, on="rt_name", how="left")

    df = df.merge(struct_df, on="rt_name", how="left")

    df = pd.concat([df, esm_df], axis=1)

    return df


if __name__ == "__main__":

    df = load_data()

    print("Loaded dataset shape:", df.shape)
    print(df.head())