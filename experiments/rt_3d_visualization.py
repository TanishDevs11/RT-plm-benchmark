import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

import pandas as pd
import numpy as np

import umap
import plotly.express as px

from feature_engineering import engineer_features


print("Generating 3D RT feature space visualization")

# -------------------------
# Load engineered features
# -------------------------

X, y, groups = engineer_features()

print("Feature matrix:", X.shape)

# -------------------------
# 3D UMAP projection
# -------------------------

reducer = umap.UMAP(
    n_components=3,
    n_neighbors=10,
    min_dist=0.2,
    random_state=42
)

embedding = reducer.fit_transform(X)

print("UMAP embedding shape:", embedding.shape)

# -------------------------
# Create dataframe
# -------------------------

df_plot = pd.DataFrame()

df_plot["UMAP1"] = embedding[:,0]
df_plot["UMAP2"] = embedding[:,1]
df_plot["UMAP3"] = embedding[:,2]

df_plot["active"] = y
df_plot["family"] = groups


# -------------------------
# Plot
# -------------------------

fig = px.scatter_3d(
    df_plot,
    x="UMAP1",
    y="UMAP2",
    z="UMAP3",
    color="active",
    symbol="family",
    title="3D Feature Space of Reverse Transcriptases",
)

fig.update_traces(marker=dict(size=6))

fig.write_html("results/rt_3d_feature_space.html")

print("Saved → results/rt_3d_feature_space.html")

fig.show()