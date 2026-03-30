import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.impute import SimpleImputer

import xgboost as xgb

print("🚀 Running full model comparison pipeline", flush=True)

# -------------------------
# Load data
# -------------------------

features = pd.read_csv("data/handcrafted_features.csv")
seq = pd.read_csv("data/rt_sequences.csv")

df = features.merge(
    seq[["rt_name", "active", "rt_family"]],
    on="rt_name"
)

print("Dataset shape:", df.shape, flush=True)

# -------------------------
# Prepare features
# -------------------------

X = df.drop(["rt_name", "active", "rt_family"], axis=1)
y = df["active"]
groups = df["rt_family"]

# -------------------------
# Remove FoldSeek leakage
# -------------------------

from sklearn.impute import SimpleImputer
import numpy as np

foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

print("Removed FoldSeek columns:", len(foldseek_cols))

# -----------------------------
# Fix NaN values
# -----------------------------

# convert everything to numeric
X = X.apply(pd.to_numeric, errors="coerce")

# replace infinite values
X = X.replace([np.inf, -np.inf], np.nan)

# impute missing values
imputer = SimpleImputer(strategy="median")

X = pd.DataFrame(
    imputer.fit_transform(X),
    columns=X.columns
)

print("NaN values imputed using median")

print("Final feature count:", X.shape[1])

# -------------------------
# Force numeric conversion
# -------------------------

X = X.apply(pd.to_numeric, errors="coerce")

# -------------------------
# Replace infinities
# -------------------------

X = X.replace([np.inf, -np.inf], np.nan)

# -------------------------
# Impute missing values
# -------------------------

imputer = SimpleImputer(strategy="median")

X = pd.DataFrame(
    imputer.fit_transform(X),
    columns=X.columns
)

print("NaN values fixed using median imputation", flush=True)
print("Final feature count:", X.shape[1], flush=True)

logo = LeaveOneGroupOut()

# -------------------------
# Models
# -------------------------

models = {

    "RandomForest": RandomForestClassifier(
        n_estimators=400,
        max_depth=8,
        random_state=42
    ),

    "LogisticRegression": LogisticRegression(
        max_iter=5000,
        solver="lbfgs"
    ),

    "XGBoost": xgb.XGBClassifier(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=5,
        eval_metric="logloss",
        random_state=42
    )
}

results = {}

# -------------------------
# Run models
# -------------------------

for name, model in models.items():

    print(f"\nTraining model: {name}", flush=True)

    scores = []

    for train_idx, test_idx in logo.split(X, y, groups):

        X_train = X.iloc[train_idx]
        X_test = X.iloc[test_idx]

        y_train = y.iloc[train_idx]
        y_test = y.iloc[test_idx]

        model.fit(X_train, y_train)

        preds = model.predict(X_test)

        score = f1_score(y_test, preds, average="macro")

        scores.append(score)

    final_score = np.mean(scores)

    results[name] = final_score

    print(f"{name} LOFO F1: {final_score:.4f}", flush=True)

# -------------------------
# Save results
# -------------------------

results_df = pd.DataFrame(
    list(results.items()),
    columns=["Model", "LOFO_F1"]
)

results_dir = Path("results")
results_dir.mkdir(exist_ok=True)

results_df.to_csv(
    results_dir / "model_results.csv",
    index=False
)

print("\nSaved results → results/model_results.csv", flush=True)

# -------------------------
# Plot
# -------------------------

plt.figure(figsize=(8,6))

bars = plt.bar(
    results_df["Model"],
    results_df["LOFO_F1"]
)

plt.ylabel("LOFO F1 Score")
plt.title("Model Performance Comparison")

plt.ylim(0,1)

for bar in bars:
    height = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        height + 0.02,
        f"{height:.2f}",
        ha="center"
    )

plt.tight_layout()

plot_path = results_dir / "model_comparison.png"

plt.savefig(plot_path, dpi=300)

plt.show()

print(f"Saved plot → {plot_path}", flush=True)
print("\n✅ Pipeline finished successfully", flush=True)