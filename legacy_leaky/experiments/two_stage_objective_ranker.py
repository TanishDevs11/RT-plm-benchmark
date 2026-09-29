from pathlib import Path
import json
import os
import random

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parent.parent
TMP_ROOT = ROOT / "temp_artifacts" / "torch_tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)
os.environ["TMP"] = str(TMP_ROOT)
os.environ["TEMP"] = str(TMP_ROOT)
os.environ["TMPDIR"] = str(TMP_ROOT)
os.environ["TORCHINDUCTOR_CACHE_DIR"] = str(TMP_ROOT / "torchinductor")
os.environ["TORCH_HOME"] = str(TMP_ROOT / "torchhome")

import torch
import torch.nn as nn
import torch.nn.functional as F

import sys

sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT / "evaluation"))
from feature_engineering import engineer_features
from evaluate import compute_cls


SEED = 42
torch.manual_seed(SEED)
np.random.seed(SEED)
random.seed(SEED)


def minmax(values):
    values = np.asarray(values, dtype=float)
    return (values - values.min()) / (values.max() - values.min() + 1e-8)


def rankpct_by_train(train_scores, test_scores):
    train_sorted = np.sort(np.asarray(train_scores, dtype=float))
    positions = np.searchsorted(train_sorted, np.asarray(test_scores, dtype=float), side="right")
    return positions / (len(train_sorted) + 1.0)


def load_embeddings(rt_names):
    emb = np.load(ROOT / "data" / "esm2_embeddings.npz", allow_pickle=True)
    emb_names = [str(name) for name in emb["names"]]
    name_to_idx = {name: idx for idx, name in enumerate(emb_names)}
    return np.vstack([emb["embeddings"][name_to_idx[name]] for name in rt_names]).astype(float)


def build_features(X_train_df, X_test_df, emb_train, emb_test, y_train, eff_train, groups_train):
    imp = SimpleImputer(strategy="median")
    scaler = StandardScaler()
    X_train = scaler.fit_transform(imp.fit_transform(X_train_df))
    X_test = scaler.transform(imp.transform(X_test_df))

    emb_scaler = StandardScaler()
    emb_train_s = emb_scaler.fit_transform(emb_train)
    emb_test_s = emb_scaler.transform(emb_test)

    pca_x_n = int(min(24, X_train.shape[0] - 1, X_train.shape[1]))
    if pca_x_n >= 2:
        pca_x = PCA(n_components=pca_x_n, random_state=SEED)
        X_train_red = pca_x.fit_transform(X_train)
        X_test_red = pca_x.transform(X_test)
    else:
        X_train_red, X_test_red = X_train, X_test

    pca_e_n = int(min(24, emb_train_s.shape[0] - 1, emb_train_s.shape[1]))
    if pca_e_n >= 2:
        pca_e = PCA(n_components=pca_e_n, random_state=SEED)
        E_train_red = pca_e.fit_transform(emb_train_s)
        E_test_red = pca_e.transform(emb_test_s)
    else:
        E_train_red, E_test_red = emb_train_s, emb_test_s

    E_train_norm = E_train_red / (np.linalg.norm(E_train_red, axis=1, keepdims=True) + 1e-8)
    E_test_norm = E_test_red / (np.linalg.norm(E_test_red, axis=1, keepdims=True) + 1e-8)

    # Local manifold residual from embedding neighborhood
    sim_train = E_train_norm @ E_train_norm.T
    np.fill_diagonal(sim_train, -np.inf)
    sim_test = E_test_norm @ E_train_norm.T

    def manifold_residual(base_vec, neigh_mat):
        if neigh_mat.shape[0] < 3:
            return 0.0
        local_mean = neigh_mat.mean(axis=0, keepdims=True)
        n_comp = int(min(3, neigh_mat.shape[0] - 1, neigh_mat.shape[1]))
        if n_comp < 1:
            return float(np.linalg.norm(base_vec - local_mean.ravel()))
        pca = PCA(n_components=n_comp, random_state=SEED)
        pca.fit(neigh_mat - local_mean)
        recon = pca.inverse_transform(pca.transform(base_vec[None, :] - local_mean)) + local_mean
        return float(np.linalg.norm(base_vec - recon.ravel()))

    k = min(8, len(E_train_norm) - 1) if len(E_train_norm) > 1 else 1
    train_resid = []
    for i in range(len(E_train_norm)):
        idx = np.argsort(sim_train[i])[::-1][: max(3, k)]
        train_resid.append(manifold_residual(E_train_norm[i], E_train_norm[idx]))
    test_resid = []
    for i in range(len(E_test_norm)):
        idx = np.argsort(sim_test[i])[::-1][: max(3, min(8, len(E_train_norm)))]
        test_resid.append(manifold_residual(E_test_norm[i], E_train_norm[idx]))

    # Family-relative efficiency projection
    weights = eff_train + 0.01
    eff_center = np.average(E_train_norm, axis=0, weights=weights)
    eff_center /= np.linalg.norm(eff_center) + 1e-8
    train_eff_proj = E_train_norm @ eff_center
    test_eff_proj = E_test_norm @ eff_center
    fam_means = {}
    groups_train = np.asarray(groups_train)
    for fam in np.unique(groups_train):
        fam_means[fam] = float(np.mean(train_eff_proj[groups_train == fam]))
    global_mean = float(np.mean(list(fam_means.values())))
    train_eff_rel = np.zeros_like(train_eff_proj)
    for i, fam in enumerate(groups_train):
        others = [v for kfam, v in fam_means.items() if kfam != fam]
        ref = float(np.mean(others)) if others else global_mean
        train_eff_rel[i] = train_eff_proj[i] - ref
    test_eff_rel = test_eff_proj - global_mean

    F_train = np.hstack(
        [
            X_train_red,
            E_train_red,
            np.asarray(train_resid, dtype=float)[:, None],
            train_eff_rel[:, None],
        ]
    )
    F_test = np.hstack(
        [
            X_test_red,
            E_test_red,
            np.asarray(test_resid, dtype=float)[:, None],
            test_eff_rel[:, None],
        ]
    )

    # Stage-2 specialist subset: only continuous efficiency-resolving signals.
    specialist_cols = [
        c
        for c in [
            "D1_D2_dist",
            "D2_D3_dist",
            "triad_best_rmsd",
            "triad_distance_ratio",
            "triad_mean_dist",
            "triad_diff_dist",
            "triad_geom_mean",
            "triad_compactness",
            "triad_angle_proxy",
            "cleft_triangle_area",
            "cleft_sasa_mean",
            "cleft_open_score",
            "cleft_curvature_proxy",
            "cleft_thumb_asymmetry",
            "cleft_tunnel_curvature_score",
            "sasa_avg",
            "sasa_high_pct",
            "sasa_low_pct",
            "helix",
            "sheet",
            "turn",
            "helix_sheet_ratio",
            "radius_gyration",
            "avg_ca_distance",
            "gravy",
            "isoelectric_point",
            "native_net_charge",
            "arginine_r_charge",
            "lysine_k_charge",
            "aspartate_d_charge",
            "glutamate_e_charge",
            "thumb_surface_net_charge",
            "thumb_charge_ratio",
            "top_contact_entropy",
            "top_entropy_degree",
        ]
        if c in X_train_df.columns
    ]

    spec_imp = SimpleImputer(strategy="median")
    spec_scaler = StandardScaler()
    if specialist_cols:
        spec_train = spec_scaler.fit_transform(spec_imp.fit_transform(X_train_df[specialist_cols]))
        spec_test = spec_scaler.transform(spec_imp.transform(X_test_df[specialist_cols]))
    else:
        spec_train = np.zeros((len(X_train_df), 1), dtype=float)
        spec_test = np.zeros((len(X_test_df), 1), dtype=float)

    # Add only orthogonal embedding-derived rank features to the specialist head.
    specialist_train = np.hstack(
        [
            spec_train,
            E_train_red[:, : min(8, E_train_red.shape[1])],
            np.asarray(train_resid, dtype=float)[:, None],
            train_eff_rel[:, None],
        ]
    )
    specialist_test = np.hstack(
        [
            spec_test,
            E_test_red[:, : min(8, E_test_red.shape[1])],
            np.asarray(test_resid, dtype=float)[:, None],
            test_eff_rel[:, None],
        ]
    )

    return (
        F_train.astype(np.float32),
        F_test.astype(np.float32),
        specialist_train.astype(np.float32),
        specialist_test.astype(np.float32),
        E_train_norm,
        E_test_norm,
    )


class RankMLP(nn.Module):
    def __init__(self, d):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(-1)


def train_listmle_model(X, eff, epochs=220, lr=0.01):
    device = "cpu"
    X_t = torch.tensor(X, dtype=torch.float32, device=device)
    y_t = torch.tensor(eff, dtype=torch.float32, device=device)
    weights = y_t + 0.01
    model = RankMLP(X.shape[1]).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    order = torch.argsort(y_t, descending=True)

    best_state = None
    best_loss = float("inf")
    patience = 30
    wait = 0
    for _ in range(epochs):
        model.train()
        opt.zero_grad()
        preds = model(X_t)
        s = preds[order]
        w = weights[order]
        tails = torch.logcumsumexp(torch.flip(s, dims=[0]), dim=0)
        tails = torch.flip(tails, dims=[0])
        loss = -(w * (s - tails)).sum() / (w.sum() + 1e-8)
        loss = loss + 1e-4 * sum((p**2).sum() for p in model.parameters())
        loss.backward()
        opt.step()
        current = float(loss.item())
        if current < best_loss - 1e-6:
            best_loss = current
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model


def train_pairwise_model(X, eff, epochs=220, lr=0.01):
    device = "cpu"
    X_t = torch.tensor(X, dtype=torch.float32, device=device)
    y = np.asarray(eff, dtype=float)
    pairs = []
    pair_w = []
    for i in range(len(y)):
        for j in range(i + 1, len(y)):
            if y[i] == y[j]:
                continue
            if y[i] > y[j]:
                pairs.append((i, j))
                pair_w.append((y[i] + 0.01) * (y[j] + 0.01))
            else:
                pairs.append((j, i))
                pair_w.append((y[i] + 0.01) * (y[j] + 0.01))
    if len(pairs) < 3:
        return train_listmle_model(X, eff, epochs=120, lr=lr)

    i_idx = torch.tensor([p[0] for p in pairs], dtype=torch.long, device=device)
    j_idx = torch.tensor([p[1] for p in pairs], dtype=torch.long, device=device)
    w_t = torch.tensor(pair_w, dtype=torch.float32, device=device)
    w_t = w_t / (w_t.mean() + 1e-8)

    model = RankMLP(X.shape[1]).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    best_state = None
    best_loss = float("inf")
    patience = 30
    wait = 0
    for _ in range(epochs):
        model.train()
        opt.zero_grad()
        preds = model(X_t)
        margins = preds[i_idx] - preds[j_idx]
        loss = (w_t * F.softplus(0.2 - margins)).mean()
        loss = loss + 1e-4 * sum((p**2).sum() for p in model.parameters())
        loss.backward()
        opt.step()
        current = float(loss.item())
        if current < best_loss - 1e-6:
            best_loss = current
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            wait = 0
        else:
            wait += 1
            if wait >= patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model


def predict_model(model, X):
    with torch.no_grad():
        preds = model(torch.tensor(X, dtype=torch.float32)).cpu().numpy()
    return preds


def build_diffusion_scores(E_train_norm, E_test_norm, y_train, eff_train):
    sim_train = np.maximum(E_train_norm @ E_train_norm.T, 0.0)
    np.fill_diagonal(sim_train, 0.0)
    seed = 0.65 * minmax(eff_train) + 0.35 * np.asarray(y_train, dtype=float)
    row_sum = sim_train.sum(axis=1, keepdims=True) + 1e-8
    trans = sim_train / row_sum
    propagated = np.linalg.solve(np.eye(len(E_train_norm)) - 0.62 * trans, 0.38 * seed)

    sim_test = np.maximum(E_test_norm @ E_train_norm.T, 0.0)
    test_w = sim_test / (sim_test.sum(axis=1, keepdims=True) + 1e-8)
    test_prop = test_w @ propagated
    return propagated, test_prop


def run_single_split(X_df, y, groups, eff, embeddings, train_idx, test_idx):
    X_train_df = X_df.iloc[train_idx]
    X_test_df = X_df.iloc[test_idx]
    y_train = y.iloc[train_idx].to_numpy(dtype=int)
    y_test = y.iloc[test_idx].to_numpy(dtype=int)
    groups_train = groups.iloc[train_idx].to_numpy()
    eff_train = eff.iloc[train_idx].to_numpy(dtype=float)

    F_train, F_test, R_train, R_test, E_train_norm, E_test_norm = build_features(
        X_train_df,
        X_test_df,
        embeddings[train_idx],
        embeddings[test_idx],
        y_train,
        eff_train,
        groups_train,
    )

    clf = LogisticRegression(
        C=0.7,
        class_weight="balanced",
        max_iter=4000,
        random_state=SEED,
        solver="liblinear",
    )
    clf.fit(F_train, y_train)
    p_active_train = clf.predict_proba(F_train)[:, 1]
    p_active_test = clf.predict_proba(F_test)[:, 1]

    active_mask = y_train == 1
    if active_mask.sum() < 4:
        active_mask = np.ones_like(y_train, dtype=bool)

    X_rank = R_train[active_mask]
    eff_rank = eff_train[active_mask]
    list_model = train_listmle_model(X_rank, eff_rank)
    pair_model = train_pairwise_model(X_rank, eff_rank)

    list_train = predict_model(list_model, X_rank)
    list_test = predict_model(list_model, R_test)
    pair_train = predict_model(pair_model, X_rank)
    pair_test = predict_model(pair_model, R_test)

    rank_list = rankpct_by_train(list_train, list_test)
    rank_pair = rankpct_by_train(pair_train, pair_test)

    diff_train, diff_test = build_diffusion_scores(E_train_norm, E_test_norm, y_train, eff_train)
    rank_diff = rankpct_by_train(diff_train, diff_test)

    return {
        "p_active_test": p_active_test,
        "rank_list_test": rank_list,
        "rank_pair_test": rank_pair,
        "rank_diff_test": rank_diff,
        "y_test": y.iloc[test_idx].to_numpy(dtype=float),
        "eff_test": eff.iloc[test_idx].to_numpy(dtype=float),
    }


BLEND_CONFIGS = [
    ("list70_diff30", lambda p, rl, rp, rd: p * (0.70 * rl + 0.30 * rd)),
    ("pair70_diff30", lambda p, rl, rp, rd: p * (0.70 * rp + 0.30 * rd)),
    ("avg70_diff30", lambda p, rl, rp, rd: p * (0.70 * ((rl + rp) / 2.0) + 0.30 * rd)),
    ("geom_avg_diff", lambda p, rl, rp, rd: p * np.sqrt(np.clip(((rl + rp) / 2.0) * rd, 0.0, None))),
    ("rank_mean_all", lambda p, rl, rp, rd: p * ((rl + rp + rd) / 3.0)),
    ("anchor_plus_list", lambda p, rl, rp, rd: 0.72 * p + 0.28 * p * rl),
    ("anchor_plus_pair", lambda p, rl, rp, rd: 0.72 * p + 0.28 * p * rp),
    ("anchor_plus_avg", lambda p, rl, rp, rd: 0.70 * p + 0.30 * p * ((rl + rp) / 2.0)),
    ("anchor_plus_diff", lambda p, rl, rp, rd: 0.74 * p + 0.26 * p * rd),
    ("anchor_geom", lambda p, rl, rp, rd: 0.68 * p + 0.32 * p * np.sqrt(np.clip(((rl + rp) / 2.0) * rd, 0.0, None))),
]


def select_inner_config(X_df, y, groups, eff, embeddings, train_idx):
    inner_X = X_df.iloc[train_idx]
    inner_y = y.iloc[train_idx].reset_index(drop=True)
    inner_g = groups.iloc[train_idx].reset_index(drop=True)
    inner_eff = eff.iloc[train_idx].reset_index(drop=True)
    inner_emb = embeddings[train_idx]

    logo = LeaveOneGroupOut()
    pooled = {name: {"score": [], "y": [], "eff": []} for name, _ in BLEND_CONFIGS}
    for inner_tr, inner_va in logo.split(inner_X, inner_y, inner_g):
        fold = run_single_split(inner_X, inner_y, inner_g, inner_eff, inner_emb, inner_tr, inner_va)
        for name, fn in BLEND_CONFIGS:
            score = fn(
                fold["p_active_test"],
                fold["rank_list_test"],
                fold["rank_pair_test"],
                fold["rank_diff_test"],
            )
            pooled[name]["score"].append(score)
            pooled[name]["y"].append(fold["y_test"])
            pooled[name]["eff"].append(fold["eff_test"])

    best_name = None
    best_cls = -1.0
    for name, _ in BLEND_CONFIGS:
        score = np.concatenate(pooled[name]["score"])
        yy = np.concatenate(pooled[name]["y"])
        ee = np.concatenate(pooled[name]["eff"])
        m = compute_cls(yy, score, ee)
        if m["cls"] > best_cls:
            best_cls = m["cls"]
            best_name = name
    return best_name


def run_outer():
    X, y, groups = engineer_features()
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv").set_index("rt_name").loc[X.index]
    eff = seq["pe_efficiency_pct"]
    embeddings = load_embeddings(X.index.tolist())

    logo = LeaveOneGroupOut()
    oof = np.zeros(len(X), dtype=float)
    chosen = []
    for fold_id, (train_idx, test_idx) in enumerate(logo.split(X, y, groups), start=1):
        cfg_name = select_inner_config(X, y, groups, eff, embeddings, train_idx)
        chosen.append(cfg_name)
        cfg_fn = dict(BLEND_CONFIGS)[cfg_name]
        fold = run_single_split(X, y, groups, eff, embeddings, train_idx, test_idx)
        oof[test_idx] = cfg_fn(
            fold["p_active_test"],
            fold["rank_list_test"],
            fold["rank_pair_test"],
            fold["rank_diff_test"],
        )
        metrics = compute_cls(fold["y_test"], oof[test_idx], fold["eff_test"])
        print(
            f"Fold {fold_id} [{groups.iloc[test_idx].iloc[0]}] config={cfg_name} "
            f"PR-AUC={metrics['pr_auc']:.6f} WSP={metrics['w_spearman']:.6f} CLS={metrics['cls']:.6f}"
        )

    final = compute_cls(y.to_numpy(dtype=float), oof, eff.to_numpy(dtype=float))
    pred_df = pd.DataFrame({"rt_name": X.index.to_list(), "predicted_score": oof})
    meta = {
        "pr_auc": float(final["pr_auc"]),
        "w_spearman": float(final["w_spearman"]),
        "cls": float(final["cls"]),
        "configs": chosen,
    }
    return pred_df, final, meta


def main():
    pred_df, final, meta = run_outer()
    out_csv = ROOT / "results" / "two_stage_objective_candidate.csv"
    out_json = ROOT / "results" / "two_stage_objective_candidate.json"
    pred_df.to_csv(out_csv, index=False)
    out_json.write_text(json.dumps(meta, indent=2))
    print(
        f"PR-AUC: {final['pr_auc']:.6f}\n"
        f"Weighted Spearman: {final['w_spearman']:.6f}\n"
        f"CLS: {final['cls']:.6f}\n"
        f"Configs: {meta['configs']}"
    )


if __name__ == "__main__":
    main()
