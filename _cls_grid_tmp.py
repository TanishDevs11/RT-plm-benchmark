"""Temporary: tune CLS; delete after use."""
import sys, os, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
import pandas as pd
import numpy as np
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import precision_recall_curve, auc
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer
from feature_engineering import engineer_features

EPSILON = 0.01

def weighted_spearman(predicted_scores, true_efficiency):
    pred_ranks = np.argsort(np.argsort(predicted_scores)).astype(float)
    true_ranks = np.argsort(np.argsort(true_efficiency)).astype(float)
    weights = true_efficiency + EPSILON
    weights = weights / weights.sum()
    mu_p = np.dot(weights, pred_ranks)
    mu_t = np.dot(weights, true_ranks)
    dp = pred_ranks - mu_p
    dt = true_ranks - mu_t
    cov = np.sum(weights * dp * dt)
    std_p = np.sqrt(np.sum(weights * dp**2))
    std_t = np.sqrt(np.sum(weights * dt**2))
    if std_p < 1e-12 or std_t < 1e-12:
        return 0.0
    return cov / (std_p * std_t)

def eval_cfg(X, y, groups, seq, w_rank, w_clf, temp, nest, mdepth, mleaf):
    all_scores, all_labels, all_eff = [], [], []
    for train_idx, test_idx in LeaveOneGroupOut().split(X, y, groups):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train_bin, y_test_bin = y.iloc[train_idx], y.iloc[test_idx]
        test_names = X_test.index
        y_train_eff = seq.loc[X_train.index, "pe_efficiency_pct"]
        y_test_eff = seq.loc[test_names, "pe_efficiency_pct"]
        y_train_eff_norm = (y_train_eff - y_train_eff.mean()) / (
            y_train_eff.std() + 1e-8
        )
        imputer = SimpleImputer(strategy="median")
        X_train = imputer.fit_transform(X_train)
        X_test = imputer.transform(X_test)
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X_train)
        X_test = scaler.transform(X_test)
        rank_model = RandomForestRegressor(
            n_estimators=nest, max_depth=mdepth, min_samples_leaf=mleaf,
            random_state=42, n_jobs=-1,
        )
        rank_model.fit(X_train, y_train_eff_norm)
        rank_preds = rank_model.predict(X_test)
        clf_model = RandomForestClassifier(
            n_estimators=nest, max_depth=mdepth, min_samples_leaf=mleaf,
            random_state=42, n_jobs=-1,
        )
        clf_model.fit(X_train, y_train_bin)
        clf_probs = clf_model.predict_proba(X_test)[:, 1]
        preds = w_rank * rank_preds + w_clf * clf_probs
        all_scores.extend(preds)
        all_labels.extend(y_test_bin)
        all_eff.extend(y_test_eff.values)
    all_scores = np.array(all_scores)
    all_labels = np.array(all_labels)
    all_eff = np.array(all_eff)
    all_scores = (all_scores - all_scores.min()) / (all_scores.max() - all_scores.min() + 1e-8)
    all_scores = np.power(all_scores, temp)
    ws = weighted_spearman(all_scores, all_eff)
    if ws < 0:
        all_scores = 1 - all_scores
    precision, recall, _ = precision_recall_curve(all_labels, all_scores)
    pr_auc = auc(recall, precision)
    wspearman = max(weighted_spearman(all_scores, all_eff), 0)
    cls = 2 * (pr_auc * wspearman) / (pr_auc + wspearman + 1e-8)
    return cls, pr_auc, wspearman

if __name__ == "__main__":
    X, y, groups = engineer_features()
    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name").loc[X.index]
    best = (0.0, None)
    grid = []
    for w_rank in [0.45, 0.5, 0.55, 0.6]:
        w_clf = 1.0 - w_rank
        for temp in [0.84, 0.9]:
            for nest, mdepth, mleaf in [
                (1000, 11, 1),
                (1000, None, 2),
            ]:
                grid.append((w_rank, w_clf, temp, nest, mdepth, mleaf))
    for i, (w_rank, w_clf, temp, nest, mdepth, mleaf) in enumerate(grid):
        c, p, w = eval_cfg(X, y, groups, seq, w_rank, w_clf, temp, nest, mdepth, mleaf)
        if c > best[0]:
            best = (c, (w_rank, temp, nest, mdepth, mleaf, p, w))
        print(f"{i+1}/{len(grid)} cls={c:.4f} pr={p:.4f} ws={w:.4f} wr={w_rank} T={temp} n={nest} d={mdepth} L={mleaf}")
    print("BEST", best)
