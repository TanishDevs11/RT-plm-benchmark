import pandas as pd
import xgboost as xgb
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.model_selection import StratifiedKFold, cross_val_predict

# 1. Load Data
print("Refining model to reduce False Positives...")
features_df = pd.read_csv('data/handcrafted_features.csv')
sequences_df = pd.read_csv('data/rt_sequences.csv')
df = features_df.merge(sequences_df[['rt_name', 'active', 'rt_family']], on='rt_name', how='inner')

# --- NEW: Feature Interaction ---
# Creating a combined stability feature based on SHAP findings
df['stability_index'] = df['hbonds_per_res'] * df['n_hydrophobic_contacts']

X = df.drop(['rt_name', 'active', 'rt_family'], axis=1)
y = df['active']

# Remove Leakage
foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

# 2. Advanced Model Configuration
ratio = float(np.sum(y == 0)) / np.sum(y == 1)
model = xgb.XGBClassifier(
    n_estimators=300, 
    learning_rate=0.02, # Slower learning for better precision
    max_depth=4,        # Shorter trees to prevent overfitting
    scale_pos_weight=ratio,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    eval_metric='logloss'
)

# 3. Get Probabilities instead of direct predictions
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
y_probs = cross_val_predict(model, X, y, cv=cv, method='predict_proba')[:, 1]

# --- NEW: Strict Threshold (0.65) ---
# Making the model more 'conservative' to stop wrong active calls
threshold = 0.65
y_pred_strict = (y_probs >= threshold).astype(int)

# 4. Results
cm = confusion_matrix(y, y_pred_strict)
print(f"\n--- Performance with Threshold {threshold} ---")
print(classification_report(y, y_pred_strict))

# 5. Visualize Matrix
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Oranges', 
            xticklabels=['Predicted Inactive', 'Predicted Active'],
            yticklabels=['Actual Inactive', 'Actual Active'])
plt.title(f'Strict Model (Threshold {threshold}) Confusion Matrix')
plt.savefig('results/strict_confusion_matrix.png')
print("\nStrict model results saved in 'results/strict_confusion_matrix.png'")