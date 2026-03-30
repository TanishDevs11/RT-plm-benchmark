import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

print("Generating model comparison plot...")

# -----------------------------
# Model results
# -----------------------------

data = {
    "Model": [
        "Handcrafted RF",
        "ESM RF",
        "Hybrid RF",
        "Linear (LogReg)"
    ],
    "LOFO_F1": [
        0.551,
        0.631,
        0.626,
        0.703
    ]
}

df = pd.DataFrame(data)

print(df)

# -----------------------------
# Create results folder
# -----------------------------

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

# -----------------------------
# Plot
# -----------------------------

plt.figure(figsize=(8,6))

bars = plt.bar(
    df["Model"],
    df["LOFO_F1"]
)

plt.ylabel("LOFO F1 Score")
plt.title("Model Performance Comparison")

plt.ylim(0,1)

# annotate bars
for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        height + 0.02,
        f"{height:.2f}",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    results_dir / "model_comparison.png",
    dpi=300
)

plt.show()

print(" Saved: results/model_comparison.png")