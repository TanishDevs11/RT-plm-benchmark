import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from data_loader import load_data

# Clean plot style
sns.set_style("whitegrid")

# Load dataset
df = load_data()

# Convert numeric labels to readable labels
df["activity_label"] = df["active"].map({0: "Inactive", 1: "Active"})

# Basic dataset information
print("Total samples:", len(df))

print("\nActive vs Inactive")
print(df["activity_label"].value_counts())

print("\nFamily distribution")
print(df["rt_family"].value_counts())

print("\nMissing values (top 10)")
print(df.isna().sum().sort_values(ascending=False).head(10))


# ---------------------------------------------------
# Plot 1: Activity distribution across families
# ---------------------------------------------------

plt.figure(figsize=(12,7))

sns.countplot(
    data=df,
    x="rt_family",
    hue="activity_label",
    palette=["steelblue", "orange"]
)

plt.title("RT Activity Across Families", fontsize=14)
plt.xlabel("RT Family", fontsize=12)
plt.ylabel("Count", fontsize=12)

plt.xticks(rotation=45, ha="right")

plt.legend(title="Activity")

plt.tight_layout()
plt.show()


# ---------------------------------------------------
# Plot 2: Protein length vs editing efficiency
# ---------------------------------------------------

plt.figure(figsize=(8,6))

sns.scatterplot(
    data=df,
    x="protein_length_aa",
    y="pe_efficiency_pct",
    hue="activity_label",
    palette=["steelblue", "orange"]
)

plt.title("Protein Length vs Prime Editing Efficiency", fontsize=14)
plt.xlabel("Protein Length (aa)", fontsize=12)
plt.ylabel("Prime Editing Efficiency (%)", fontsize=12)

plt.legend(title="Activity")

plt.tight_layout()
plt.show()