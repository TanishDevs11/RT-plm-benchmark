import pandas as pd
from sklearn.metrics import confusion_matrix, classification_report

print("Loading predictions...")

# load predictions
pred = pd.read_csv("results/calibrated_predictions_selected_features.csv")

# load ground truth
seq = pd.read_csv("data/rt_sequences.csv")

# merge
df = pred.merge(seq[["rt_name","active"]], on="rt_name")

y_true = df["active"]
y_pred = df["predicted_active"]

# confusion matrix
cm = confusion_matrix(y_true, y_pred)

TN, FP, FN, TP = cm.ravel()

print("\n====================")
print("TP:", TP)
print("FP:", FP)
print("TN:", TN)
print("FN:", FN)
print("====================")

print("\nClassification Report:\n")
print(classification_report(y_true, y_pred))
