"""Exact out-of-fold Shapley attributions for the Task A logistic head.

Used by `bench/interpret_taskA.py`, and only for a representation that cleared a null.

Why no SHAP package
-------------------
The head is a logistic regression, so the Shapley value of feature j on instance i is
exactly the coefficient of j times the centred value of feature j. That is what a linear
SHAP explainer computes for the independent-feature case, and computing it directly means
the attributions here are exact for the model actually fitted rather than sampled
estimates of them. It also removes a heavy dependency that would otherwise be installed
to reimplement one multiplication.

Why out of fold
---------------
For each held-out family, the configuration that family's inner loop selected is refitted
on the training families, and attributions are taken for the held-out rows only. Fitting
once on all 57 rows would describe a model that had seen every label, which is not the
model the benchmark scored. Because the pipeline standardizes on the training fold, the
training mean of each scaled feature is zero, so the centring term vanishes and the
attribution is the coefficient times the scaled value.
"""

from __future__ import annotations

import numpy as np

SEED = 42

# Attribution mass is summarised at two concentrations: the top decile of
# family-explained features, and the top one percent of features by mass. Both are shares
# so they can be read against the share of features they represent.
LINEAGE_DECILE = 10
CONCENTRATION_PERCENT = 100


def out_of_fold_attributions(matrix, data, selected: dict) -> dict:
    """Exact Shapley attributions for the linear head, computed fold by fold."""
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    attribution = np.zeros((len(data), matrix.shape[1]), dtype=float)
    covered = np.zeros(len(data), dtype=bool)
    for family in sorted(data["rt_family"].unique()):
        test_mask = (data["rt_family"] == family).to_numpy()
        train_index = data.loc[~test_mask].index.to_numpy()
        test_index = data.loc[test_mask].index.to_numpy()
        config = selected.get(family) or {}
        c_value = config.get("C")
        if c_value is None:
            continue
        imputer = SimpleImputer(strategy="median").fit(matrix[train_index])
        x_train = imputer.transform(matrix[train_index])
        scaler = StandardScaler().fit(x_train)
        model = LogisticRegression(C=c_value, max_iter=5000, random_state=SEED)
        model.fit(scaler.transform(x_train), data.loc[~test_mask, "active"].to_numpy())
        x_test = scaler.transform(imputer.transform(matrix[test_index]))
        attribution[test_index] = x_test * model.coef_[0]
        covered[test_index] = True
    return {
        "attribution": attribution,
        "importance": np.abs(attribution).mean(axis=0),
        "rows_covered": int(covered.sum()),
    }


def family_explained_variance(matrix, families) -> np.ndarray:
    """Eta squared per feature: the share of its variance that family label explains.

    A one-way analysis of variance effect size per dimension. It answers how much of each
    dimension is simply lineage, which is the confound this whole benchmark is built
    around.
    """
    overall = matrix.mean(axis=0)
    total = np.square(matrix - overall).sum(axis=0)
    between = np.zeros(matrix.shape[1], dtype=float)
    for family in np.unique(families):
        mask = families == family
        between += mask.sum() * np.square(matrix[mask].mean(axis=0) - overall)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(total > 0, between / total, 0.0)


def summarise(matrix, data, selected: dict, scores: np.ndarray) -> dict:
    """Everything the interpretation report needs for one representation."""
    from scipy.stats import spearmanr

    families = data["rt_family"].to_numpy()
    lengths = data["protein_length_aa"].to_numpy(dtype=float)
    result = out_of_fold_attributions(matrix, data, selected)
    importance = result["importance"]
    total = float(importance.sum())
    eta = family_explained_variance(matrix, families)

    n_features = matrix.shape[1]
    decile = max(1, n_features // LINEAGE_DECILE)
    lineage = np.argsort(eta)[::-1][:decile]
    top_percent = max(1, n_features // CONCENTRATION_PERCENT)
    concentrated = np.argsort(importance)[::-1][:top_percent]

    rho_length, p_length = spearmanr(scores, lengths)
    rho_eta, p_eta = spearmanr(eta, importance)

    return {
        "n_features": int(n_features),
        "rows_covered": result["rows_covered"],
        "importance": importance,
        "eta": eta,
        "total_mass": total,
        "top_indices": np.argsort(importance)[::-1][:15],
        "lineage_mass_share": float(importance[lineage].sum() / total) if total else float("nan"),
        "lineage_feature_share": float(decile / n_features),
        "concentration_share": float(importance[concentrated].sum() / total) if total else float("nan"),
        "concentration_feature_share": float(top_percent / n_features),
        "score_vs_length_rho": float(rho_length),
        "score_vs_length_p": float(p_length),
        "importance_vs_eta_rho": float(rho_eta),
        "importance_vs_eta_p": float(p_eta),
    }
