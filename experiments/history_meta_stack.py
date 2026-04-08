import io
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.append(str(ROOT / "evaluation"))
from evaluate import compute_cls


def zsig_by_train(train_scores, test_scores):
    train_scores = np.asarray(train_scores, dtype=float)
    test_scores = np.asarray(test_scores, dtype=float)
    mu = train_scores.mean()
    sigma = train_scores.std() + 1e-8
    z_scores = (test_scores - mu) / sigma
    return 1.0 / (1.0 + np.exp(-z_scores))


def rankpct_by_train(train_scores, test_scores):
    train_scores = np.asarray(train_scores, dtype=float)
    test_scores = np.asarray(test_scores, dtype=float)
    train_sorted = np.sort(train_scores)
    pos = np.searchsorted(train_sorted, test_scores, side="right")
    return pos / max(len(train_sorted), 1)


def load_prediction_frame(name_to_source):
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    frame = seq[["rt_name", "active", "pe_efficiency_pct", "rt_family"]].copy()

    for name, source in name_to_source.items():
        if isinstance(source, Path):
            pred = pd.read_csv(source)
        else:
            content = subprocess.check_output(
                ["git", "show", source],
                text=True,
            )
            pred = pd.read_csv(io.StringIO(content))

        pred = pred[["rt_name", "predicted_score"]].rename(
            columns={"predicted_score": name}
        )
        frame = frame.merge(pred, on="rt_name", how="left")

    return frame


def add_meta_features(df, score_cols):
    out = df.copy()

    for col in score_cols:
        vals = out[col].to_numpy(dtype=float)
        out[f"{col}_sq"] = vals * vals
        out[f"{col}_abs"] = np.abs(vals)

    for i, left in enumerate(score_cols):
        for right in score_cols[i + 1 :]:
            out[f"{left}_minus_{right}"] = out[left] - out[right]
            out[f"{left}_plus_{right}"] = out[left] + out[right]
            out[f"{left}_mul_{right}"] = out[left] * out[right]

    return out


def run_meta_stack():
    sources = {
        "candidate": ROOT / "results" / "calibrated_predictions_candidate.csv",
        "selected": ROOT / "results" / "calibrated_predictions_selected_features.csv",
        "de": ROOT / "results" / "calibrated_predictions_de.csv",
        "git_08234": "f46416e:results/calibrated_predictions_selected_features.csv",
        "git_07984": "f131fc4:results/calibrated_predictions_selected_features.csv",
        "git_07566": "3e17085:results/calibrated_predictions_selected_features.csv",
    }
    frame = load_prediction_frame(sources)
    score_cols = list(sources.keys())
    frame = add_meta_features(frame, score_cols)

    feature_cols = [
        c
        for c in frame.columns
        if c not in {"rt_name", "active", "pe_efficiency_pct", "rt_family"}
    ]

    X = frame[feature_cols]
    y_bin = frame["active"]
    y_eff = frame["pe_efficiency_pct"]
    groups = frame["rt_family"]
    logo = LeaveOneGroupOut()

    results = []
    alphas = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65]

    for alpha in alphas:
        scores = []
        for train_idx, test_idx in logo.split(X, y_bin, groups):
            X_train = X.iloc[train_idx]
            X_test = X.iloc[test_idx]
            y_train_bin = y_bin.iloc[train_idx]
            y_train_eff = y_eff.iloc[train_idx]

            imputer = SimpleImputer(strategy="median")
            scaler = StandardScaler()
            X_train_t = scaler.fit_transform(imputer.fit_transform(X_train))
            X_test_t = scaler.transform(imputer.transform(X_test))

            clf = LogisticRegression(
                C=0.8,
                class_weight="balanced",
                max_iter=4000,
                random_state=42,
            )
            reg = Ridge(alpha=2.0, random_state=42)

            clf.fit(X_train_t, y_train_bin)
            reg.fit(
                X_train_t,
                np.log1p(y_train_eff),
                sample_weight=y_train_eff.to_numpy(dtype=float) + 0.01,
            )

            clf_train = clf.predict_proba(X_train_t)[:, 1]
            clf_test = clf.predict_proba(X_test_t)[:, 1]
            reg_train = reg.predict(X_train_t)
            reg_test = reg.predict(X_test_t)

            clf_part = zsig_by_train(clf_train, clf_test)
            reg_rank = rankpct_by_train(reg_train, reg_test)
            fold_scores = alpha * clf_part + (1.0 - alpha) * reg_rank
            scores.extend(fold_scores.tolist())

        result = compute_cls(
            y_bin.to_numpy(dtype=float),
            np.asarray(scores, dtype=float),
            y_eff.to_numpy(dtype=float),
        )
        results.append((alpha, np.asarray(scores, dtype=float), result))

    best_alpha, best_scores, best_result = max(
        results,
        key=lambda item: item[2]["cls"],
    )

    prediction_df = frame[["rt_name"]].copy()
    prediction_df["predicted_score"] = best_scores

    return prediction_df, best_alpha, best_result


if __name__ == "__main__":
    prediction_df, best_alpha, best_result = run_meta_stack()
    out_csv = ROOT / "results" / "history_meta_stack_predictions.csv"
    out_json = ROOT / "results" / "history_meta_stack_result.json"

    prediction_df.to_csv(out_csv, index=False)
    out_json.write_text(
        json.dumps(
            {
                "alpha": best_alpha,
                "pr_auc": float(best_result["pr_auc"]),
                "w_spearman": float(best_result["w_spearman"]),
                "cls": float(best_result["cls"]),
            },
            indent=2,
        )
    )

    print(
        f"PR-AUC: {best_result['pr_auc']:.6f}\n"
        f"Weighted Spearman: {best_result['w_spearman']:.6f}\n"
        f"CLS: {best_result['cls']:.6f}\n"
        f"Best alpha: {best_alpha:.2f}"
    )
