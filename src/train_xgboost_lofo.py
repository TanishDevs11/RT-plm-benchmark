import pandas as pd
import xgboost as xgb
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import f1_score
import numpy as np
import os

# Data load panrom
print("Loading data files...")
features_path = 'data/handcrafted_features.csv'
sequences_path = 'data/rt_sequences.csv'

features_df = pd.read_csv(features_path)
sequences_df = pd.read_csv(sequences_path)

# Merge logic
df = features_df.merge(sequences_df[['rt_name', 'active', 'rt_family']], on='rt_name', how='inner')

X = df.drop(['rt_name', 'active', 'rt_family'], axis=1)
y = df['active']
groups = df['rt_family']

# --- DATA LEAKAGE FIX (Unga friend sonna logic) ---
# FoldSeek columns-ah remove panrom because they leak 'evolutionary shortcuts'
foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)
print(f"Removed {len(foldseek_cols)} FoldSeek columns to prevent leakage.")
print(f"Final feature count for training: {X.shape[1]}")
# --------------------------------------------------

model = xgb.XGBClassifier(
    n_estimators=200,
    learning_rate=0.05,
    max_depth=5,
    random_state=42,
    eval_metric='logloss'
)

logo = LeaveOneGroupOut()
scores = []

print("\nStarting LOFO Validation (Clean Training)...")
for train_idx, test_idx in logo.split(X, y, groups):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    score = f1_score(y_test, preds, average='macro')
    scores.append(score)
    
    family_name = groups.iloc[test_idx].unique()[0]
    print(f"Family: {family_name:25} | F1 Score: {score:.4f}")

final_score = np.mean(scores)
print("\n" + "="*40)
print(f"Final CLEAN XGBoost F1 Score: {final_score:.4f}")
print(f"Target to beat (Friend's Score): 0.5330")
print("="*40)

# Feature Importance
importances = pd.Series(model.feature_importances_, index=X.columns)
print("\nTop 10 REAL Biophysical Features:")
print(importances.sort_values(ascending=False).head(10))