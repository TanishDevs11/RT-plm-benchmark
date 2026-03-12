import pandas as pd
import umap
import matplotlib.pyplot as plt

from feature_engineering import engineer_features


print("Loading features...")

X, y, groups = engineer_features()

print("Running UMAP...")

reducer = umap.UMAP(
    n_neighbors=10,
    min_dist=0.2,
    random_state=42
)

embedding = reducer.fit_transform(X)

umap_df = pd.DataFrame({
    "UMAP1": embedding[:, 0],
    "UMAP2": embedding[:, 1],
    "active": y,
    "family": groups
})

# --------------------------------------------------
# Plot 1 : Activity (Active vs Inactive)
# --------------------------------------------------

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

scatter = axes[0].scatter(
    umap_df["UMAP1"],
    umap_df["UMAP2"],
    c=umap_df["active"],
    cmap="coolwarm",
    s=80
)

axes[0].set_title("UMAP — RT Activity")
axes[0].set_xlabel("UMAP1")
axes[0].set_ylabel("UMAP2")

cbar = plt.colorbar(scatter, ax=axes[0])
cbar.set_label("Active")


# --------------------------------------------------
# Plot 2 : RT Family Clusters
# --------------------------------------------------

families = umap_df["family"].unique()

for fam in families:

    subset = umap_df[umap_df["family"] == fam]

    axes[1].scatter(
        subset["UMAP1"],
        subset["UMAP2"],
        label=fam,
        s=80
    )

axes[1].set_title("UMAP — RT Families")
axes[1].set_xlabel("UMAP1")
axes[1].set_ylabel("UMAP2")

axes[1].legend(bbox_to_anchor=(1.05, 1), loc="upper left")

plt.tight_layout()
plt.show()