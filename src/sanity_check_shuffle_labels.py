import numpy as np
import pandas as pd
import xgboost as xgb

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score

print("SANITY CHECK: SHUFFLED LABELS TEST")

# -------------------------
# Load Data
# -------------------------

features = pd.read_csv("data/handcrafted_features.csv")
seq = pd.read_csv("data/rt_sequences.csv")

df = features.merge(
    seq[["rt_name","active","rt_family"]],
    on="rt_name"
)

X = df.drop(["rt_name","active","rt_family"], axis=1)
y = df["active"].values
groups = df["rt_family"]

# -------------------------
# Remove FoldSeek leakage
# -------------------------

foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

print("Removed FoldSeek:", len(foldseek_cols))

# -------------------------
# SHUFFLE LABELS
# -------------------------

np.random.seed(42)
y = np.random.permutation(y)

print("Labels shuffled.")

# -------------------------
# Model
# -------------------------

model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    eval_metric="logloss",
    random_state=42
)

logo = LeaveOneGroupOut()

scores = []

print("\nRunning LOFO with random labels...\n")

for train_idx, test_idx in logo.split(X, y, groups):

    X_train = X.iloc[train_idx]
    X_test = X.iloc[test_idx]

    y_train = y[train_idx]
    y_test = y[test_idx]

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    score = f1_score(y_test, preds, average="macro")

    scores.append(score)

    fam = groups.iloc[test_idx].unique()[0]

    print(f"Family: {fam:25} | F1: {score:.3f}")

print("\nFinal SHUFFLED LOFO F1:", np.mean(scores))