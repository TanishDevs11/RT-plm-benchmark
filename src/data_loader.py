import pandas as pd
import numpy as np

def load_data():

    # Load sequence metadata
    seq_df = pd.read_csv("data/rt_sequences.csv")

    # Load engineered features
    feat_df = pd.read_csv("data/handcrafted_features.csv")

    # Load ESM embeddings
    emb = np.load("data/esm2_embeddings.npz", allow_pickle=True)

    emb_df = pd.DataFrame(emb["embeddings"])
    emb_df["rt_name"] = emb["names"]

    # Merge datasets
    df = seq_df.merge(feat_df, on="rt_name")
    df = df.merge(emb_df, on="rt_name")

    return df


if __name__ == "__main__":

    df = load_data()

    print("Dataset Shape:", df.shape)
    print(df.head())