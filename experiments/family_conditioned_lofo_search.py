import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
from sklearn.ensemble import ExtraTreesClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent

import sys

sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "evaluation"))
from feature_engineering import engineer_features
from evaluate import compute_cls


def zsig_by_train(train_scores, test_scores):
    train_scores = np.asarray(train_scores, dtype=float)
    test_scores = np.asarray(test_scores, dtype=float)
    mu = train_scores.mean()
    sigma = train_scores.std() + 1e-8
    z = (test_scores - mu) / sigma
    return 1.0 / (1.0 + np.exp(-z))


def rankpct_by_train(train_scores, test_scores):
    train_sorted = np.sort(np.asarray(train_scores, dtype=float))
    positions = np.searchsorted(
        train_sorted,
        np.asarray(test_scores, dtype=float),
        side="right",
    )
    return positions / (len(train_sorted) + 1.0)


def minmax(values):
    values = np.asarray(values, dtype=float)
    return (values - values.min()) / (values.max() - values.min() + 1e-8)


def load_embeddings(rt_names):
    emb = np.load(ROOT / "data" / "esm2_embeddings.npz", allow_pickle=True)
    if "rt_names" in emb.files:
        emb_names = [str(name) for name in emb["rt_names"]]
    elif "names" in emb.files:
        emb_names = [str(name) for name in emb["names"]]
    else:
        emb_names = list(rt_names)
    name_to_idx = {name: idx for idx, name in enumerate(emb_names)}
    vectors = emb["embeddings"].astype(float)
    return np.vstack([vectors[name_to_idx[name]] for name in rt_names])


def group_exclusion_scale(X_train, groups_train, X_test):
    X_train_scaled = np.zeros_like(X_train, dtype=float)
    for fam in pd.Series(groups_train).unique():
        mask = groups_train == fam
        ref = X_train[~mask]
        if ref.shape[0] < 2:
            ref = X_train
        scaler = StandardScaler()
        scaler.fit(ref)
        X_train_scaled[mask] = scaler.transform(X_train[mask])

    test_scaler = StandardScaler()
    test_scaler.fit(X_train)
    X_test_scaled = test_scaler.transform(X_test)
    return X_train_scaled, X_test_scaled


def build_embedding_features(train_emb, test_emb, y_train, groups_train, eff_train):
    train_mean = train_emb.mean(axis=0, keepdims=True)
    train_centered = train_emb - train_mean
    test_centered = test_emb - train_mean
    train_centered /= np.linalg.norm(train_centered, axis=1, keepdims=True) + 1e-8
    test_centered /= np.linalg.norm(test_centered, axis=1, keepdims=True) + 1e-8

    y_train = np.asarray(y_train, dtype=int)
    eff_train = np.asarray(eff_train, dtype=float)
    groups_train = np.asarray(groups_train)
    weights = eff_train + 0.01

    active_mask = y_train == 1
    inactive_mask = ~active_mask
    active_center = np.average(
        train_centered[active_mask], axis=0, weights=weights[active_mask]
    )
    inactive_center = train_centered[inactive_mask].mean(axis=0)
    active_center /= np.linalg.norm(active_center) + 1e-8
    inactive_center /= np.linalg.norm(inactive_center) + 1e-8

    family_centers = {}
    family_strengths = {}
    for fam in np.unique(groups_train):
        fam_active = (groups_train == fam) & active_mask
        if fam_active.sum() == 0:
            continue
        fam_center = np.average(
            train_centered[fam_active], axis=0, weights=weights[fam_active]
        )
        fam_center /= np.linalg.norm(fam_center) + 1e-8
        family_centers[fam] = fam_center
        family_strengths[fam] = float(weights[fam_active].mean())

    def cross_family_similarity(vector, sample_family=None):
        sims = []
        wts = []
        for fam, center in family_centers.items():
            if sample_family is not None and fam == sample_family:
                continue
            sims.append(float(vector @ center))
            wts.append(family_strengths[fam])
        if not sims:
            sims = [float(vector @ active_center)]
            wts = [1.0]
        return float(np.average(sims, weights=wts))

    train_crossfam = np.array(
        [
            cross_family_similarity(vec, fam)
            for vec, fam in zip(train_centered, groups_train)
        ],
        dtype=float,
    )
    test_crossfam = np.array(
        [cross_family_similarity(vec) for vec in test_centered],
        dtype=float,
    )

    train_active_sim = train_centered @ active_center
    test_active_sim = test_centered @ active_center
    train_inactive_sim = train_centered @ inactive_center
    test_inactive_sim = test_centered @ inactive_center

    train_margin = train_crossfam - train_inactive_sim
    test_margin = test_crossfam - test_inactive_sim

    sim_train = train_centered @ train_centered.T
    np.fill_diagonal(sim_train, -np.inf)
    sim_test = test_centered @ train_centered.T
    k = min(6, train_centered.shape[0])
    train_knn = []
    for row in range(sim_train.shape[0]):
        idx = np.argsort(sim_train[row])[::-1][:k]
        train_knn.append(float(eff_train[idx].mean()))
    test_knn = []
    for row in range(sim_test.shape[0]):
        idx = np.argsort(sim_test[row])[::-1][:k]
        test_knn.append(float(eff_train[idx].mean()))

    train_out = np.column_stack(
        [
            train_crossfam,
            train_active_sim,
            train_inactive_sim,
            train_margin,
            np.asarray(train_knn, dtype=float),
        ]
    )
    test_out = np.column_stack(
        [
            test_crossfam,
            test_active_sim,
            test_inactive_sim,
            test_margin,
            np.asarray(test_knn, dtype=float),
        ]
    )
    return train_out, test_out


def fit_pairwise_head(train_features, eff_train, sample_weight):
    n = train_features.shape[0]
    pair_X = []
    pair_y = []
    pair_w = []
    for i in range(n):
        for j in range(i + 1, n):
            if eff_train[i] == eff_train[j]:
                continue
            diff = train_features[i] - train_features[j]
            label = 1 if eff_train[i] > eff_train[j] else 0
            weight = abs(eff_train[i] - eff_train[j]) + 0.05
            pair_X.append(diff)
            pair_y.append(label)
            pair_w.append(weight)
            pair_X.append(-diff)
            pair_y.append(1 - label)
            pair_w.append(weight)

    pair_X = np.asarray(pair_X, dtype=float)
    pair_y = np.asarray(pair_y, dtype=int)
    pair_w = np.asarray(pair_w, dtype=float)
    model = LogisticRegression(
        C=0.5,
        max_iter=5000,
        random_state=42,
    )
    model.fit(pair_X, pair_y, sample_weight=pair_w)

    train_scores = []
    for row in train_features:
        probs = model.predict_proba(row[None, :] - train_features)[:, 1]
        train_scores.append(float(np.average(probs, weights=sample_weight)))

    return model, np.asarray(train_scores, dtype=float)


def run_search():
    X, y, groups = engineer_features()
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv").set_index("rt_name")
    seq = seq.loc[X.index]
    embeddings = load_embeddings(X.index.tolist())
    base_pred = pd.read_csv(ROOT / "results" / "calibrated_predictions_selected_features.csv")
    base_map = base_pred.set_index("rt_name")["predicted_score"]
    base_oof = base_map.loc[X.index].to_numpy(dtype=float)

    structure_cols = [
        col
        for col in ["n_atoms", "n_residues", "radius_gyration", "avg_ca_distance"]
        if col in X.columns
    ]

    logo = LeaveOneGroupOut()
    reg_branch = np.zeros(len(X), dtype=float)
    clf_branch = np.zeros(len(X), dtype=float)
    struct_branch = np.zeros(len(X), dtype=float)
    pair_branch = np.zeros(len(X), dtype=float)
    margin_branch = np.zeros(len(X), dtype=float)

    for train_idx, test_idx in logo.split(X, y, groups):
        X_train_df = X.iloc[train_idx]
        X_test_df = X.iloc[test_idx]
        y_train = y.iloc[train_idx].to_numpy(dtype=int)
        groups_train = groups.iloc[train_idx].to_numpy()
        eff_train = seq.iloc[train_idx]["pe_efficiency_pct"].to_numpy(dtype=float)

        imputer = SimpleImputer(strategy="median")
        X_train_imp = imputer.fit_transform(X_train_df)
        X_test_imp = imputer.transform(X_test_df)
        X_train_scaled, X_test_scaled = group_exclusion_scale(
            X_train_imp,
            groups_train,
            X_test_imp,
        )

        embed_train_feat, embed_test_feat = build_embedding_features(
            embeddings[train_idx],
            embeddings[test_idx],
            y_train,
            groups_train,
            eff_train,
        )

        X_train_aug = np.hstack([X_train_scaled, embed_train_feat])
        X_test_aug = np.hstack([X_test_scaled, embed_test_feat])

        reg = RandomForestRegressor(
            n_estimators=1000,
            max_depth=8,
            min_samples_leaf=2,
            max_features="log2",
            random_state=42,
            n_jobs=1,
        )
        clf = ExtraTreesClassifier(
            n_estimators=1200,
            max_depth=None,
            min_samples_leaf=1,
            class_weight="balanced",
            max_features="sqrt",
            random_state=42,
            n_jobs=1,
        )

        eff_train_norm = (eff_train - eff_train.mean()) / (eff_train.std() + 1e-8)
        reg.fit(X_train_aug, eff_train_norm)
        clf.fit(X_train_aug, y_train)

        reg_train = reg.predict(X_train_aug)
        reg_test = reg.predict(X_test_aug)
        clf_train = clf.predict_proba(X_train_aug)[:, 1]
        clf_test = clf.predict_proba(X_test_aug)[:, 1]

        reg_branch[test_idx] = rankpct_by_train(reg_train, reg_test)
        clf_branch[test_idx] = zsig_by_train(clf_train, clf_test)
        margin_branch[test_idx] = rankpct_by_train(
            embed_train_feat[:, 3],
            embed_test_feat[:, 3],
        )

        if structure_cols:
            struct_imputer = SimpleImputer(strategy="median")
            struct_scaler = StandardScaler()
            X_train_struct = struct_scaler.fit_transform(
                struct_imputer.fit_transform(X_train_df[structure_cols])
            )
            X_test_struct = struct_scaler.transform(
                struct_imputer.transform(X_test_df[structure_cols])
            )
            struct_model = Ridge(alpha=2.0, random_state=42)
            struct_model.fit(
                X_train_struct,
                eff_train_norm - reg_train,
                sample_weight=eff_train + 0.01,
            )
            struct_train = struct_model.predict(X_train_struct)
            struct_test = struct_model.predict(X_test_struct)
            struct_branch[test_idx] = zsig_by_train(struct_train, struct_test)

        pair_train_feat = np.column_stack(
            [
                reg_train,
                clf_train,
                embed_train_feat[:, 0],
                embed_train_feat[:, 3],
                embed_train_feat[:, 4],
            ]
        )
        pair_test_feat = np.column_stack(
            [
                reg_test,
                clf_test,
                embed_test_feat[:, 0],
                embed_test_feat[:, 3],
                embed_test_feat[:, 4],
            ]
        )
        pair_model, pair_train_scores = fit_pairwise_head(
            pair_train_feat,
            eff_train,
            eff_train + 0.01,
        )
        pair_test_scores = []
        for row in pair_test_feat:
            probs = pair_model.predict_proba(row[None, :] - pair_train_feat)[:, 1]
            pair_test_scores.append(float(np.average(probs, weights=eff_train + 0.01)))
        pair_branch[test_idx] = zsig_by_train(pair_train_scores, pair_test_scores)

    components = {
        "base": minmax(base_oof),
        "reg": minmax(reg_branch),
        "clf": minmax(clf_branch),
        "struct": minmax(struct_branch),
        "pair": minmax(pair_branch),
        "margin": minmax(margin_branch),
    }

    y_true = y.to_numpy(dtype=float)
    eff_true = seq["pe_efficiency_pct"].to_numpy(dtype=float)

    keys = list(components.keys())

    def objective(weights):
        score = np.zeros(len(X), dtype=float)
        for key, weight in zip(keys, weights):
            score += weight * components[key]
        result = compute_cls(y_true, score, eff_true)
        return -float(result["cls"])

    result = differential_evolution(
        objective,
        bounds=[(-1.0, 2.5)] * len(keys),
        seed=42,
        polish=True,
        updating="deferred",
        workers=1,
        maxiter=60,
        popsize=14,
    )

    best_weights = {key: float(val) for key, val in zip(keys, result.x)}
    final_score = np.zeros(len(X), dtype=float)
    for key in keys:
        final_score += best_weights[key] * components[key]

    final_metric = compute_cls(y_true, final_score, eff_true)
    prediction_df = pd.DataFrame(
        {"rt_name": X.index.to_list(), "predicted_score": final_score}
    )
    component_df = pd.DataFrame(
        {
            "rt_name": X.index.to_list(),
            "base": components["base"],
            "reg": components["reg"],
            "clf": components["clf"],
            "struct": components["struct"],
            "pair": components["pair"],
            "margin": components["margin"],
        }
    )
    return prediction_df, component_df, final_metric, best_weights


def main():
    prediction_df, component_df, final_metric, best_weights = run_search()
    out_csv = ROOT / "results" / "family_conditioned_lofo_candidate.csv"
    out_components = ROOT / "results" / "family_conditioned_lofo_components.csv"
    out_json = ROOT / "results" / "family_conditioned_lofo_candidate.json"
    prediction_df.to_csv(out_csv, index=False)
    component_df.to_csv(out_components, index=False)
    out_json.write_text(
        json.dumps(
            {
                "pr_auc": float(final_metric["pr_auc"]),
                "w_spearman": float(final_metric["w_spearman"]),
                "cls": float(final_metric["cls"]),
                "weights": best_weights,
            },
            indent=2,
        )
    )
    print(
        f"PR-AUC: {final_metric['pr_auc']:.6f}\n"
        f"Weighted Spearman: {final_metric['w_spearman']:.6f}\n"
        f"CLS: {final_metric['cls']:.6f}\n"
        f"Weights: {best_weights}"
    )


if __name__ == "__main__":
    main()
