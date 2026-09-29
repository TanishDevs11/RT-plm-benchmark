import pandas as pd
import xgboost as xgb
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, classification_report

# 1. Load Data
print("Loading data for analysis...")
features_df = pd.read_csv('data/handcrafted_features.csv')
sequences_df = pd.read_csv('data/rt_sequences.csv')
df = features_df.merge(sequences_df[['rt_name', 'active', 'rt_family']], on='rt_name', how='inner')

X = df.drop(['rt_name', 'active', 'rt_family'], axis=1)
y = df['active']

# Remove Leakage (Must do this to be consistent)
foldseek_cols = [c for c in X.columns if "foldseek" in c]
X = X.drop(columns=foldseek_cols)

# 2. Model Training (Quick train for analysis)
model = xgb.XGBClassifier(n_estimators=200, learning_rate=0.05, max_depth=5, random_state=42)
model.fit(X, y)

# 3. Predictions
y_pred = model.predict(X)

# 4. Generate Confusion Matrix
cm = confusion_matrix(y, y_pred)

# 5. Visualizing the Results
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Greens', 
            xticklabels=['Predicted Inactive', 'Predicted Active'],
            yticklabels=['Actual Inactive', 'Actual Active'])
plt.title('Confusion Matrix: RT Activity Prediction')
plt.ylabel('Actual')
plt.xlabel('Predicted')
plt.savefig('confusion_matrix.png')

print("\n--- Detailed Performance Report ---")
print(classification_report(y, y_pred))
print("\nConfusion Matrix image saved as 'confusion_matrix.png'")
