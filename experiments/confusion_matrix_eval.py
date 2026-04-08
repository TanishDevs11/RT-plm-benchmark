import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report


print("Loading predictions...")

# Load model predictions
pred = pd.read_csv(
    "results/calibrated_predictions_selected_features.csv"
)

# Load true labels
seq = pd.read_csv("data/rt_sequences.csv")

df = pred.merge(
    seq[["rt_name", "active"]],
    on="rt_name"
)

y_true = df["active"]
if "predicted_active" in df.columns:
    y_pred = df["predicted_active"]
else:
    y_pred = (df["predicted_score"] >= 0.5).astype(int)

# ----------------------------
# Confusion matrix
# ----------------------------

cm = confusion_matrix(y_true, y_pred)

tn, fp, fn, tp = cm.ravel()

print("\n====================")
print("TP:", tp)
print("FP:", fp)
print("TN:", tn)
print("FN:", fn)
print("====================")

# ----------------------------
# Detailed report
# ----------------------------

print("\nClassification Report:\n")
print(classification_report(y_true, y_pred))


# ----------------------------
# Plot
# ----------------------------

plt.figure(figsize=(8,6))

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    cmap="Greens",
    xticklabels=["Predicted Inactive","Predicted Active"],
    yticklabels=["Actual Inactive","Actual Active"]
)

plt.title("Confusion Matrix (LOFO Predictions)")
plt.xlabel("Predicted")
plt.ylabel("Actual")

plt.tight_layout()

plt.savefig(
    "results/confusion_matrix_lofo.png",
    dpi=300
)

print("\nSaved â†’ results/confusion_matrix_lofo.png")
