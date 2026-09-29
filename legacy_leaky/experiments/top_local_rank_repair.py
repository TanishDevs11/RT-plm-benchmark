import io
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent


def first_existing(*paths):
    for path in paths:
        if path.exists():
            return path
    raise FileNotFoundError(str(paths[0]))


def load_scores():
    seq = pd.read_csv(ROOT / "data" / "rt_sequences.csv")
    selected_path = first_existing(
        ROOT / "results" / "calibrated_predictions_top20_repair.csv",
        ROOT / "temp_artifacts" / "results_scratch" / "calibrated_predictions_history_blend_triplet.csv",
        ROOT / "results" / "calibrated_predictions_selected_features.csv",
    )
    selected = pd.read_csv(selected_path).rename(
        columns={"predicted_score": "selected"}
    )
    repair_path = first_existing(
        ROOT / "results" / "rank_repair_search_candidate.csv",
        ROOT / "temp_artifacts" / "results_scratch" / "rank_repair_search_candidate.csv",
    )
    repair = pd.read_csv(repair_path).rename(
        columns={"predicted_score": "repair"}
    )
    meta_path = first_existing(
        ROOT / "results" / "calibrated_predictions_meta_refine.csv",
        ROOT
        / "temp_artifacts"
        / "results_scratch"
        / "calibrated_predictions_meta_refine.csv",
    )
    meta = pd.read_csv(meta_path).rename(columns={"predicted_score": "meta"})

    git_content = subprocess.check_output(
        ["git", "show", "3bad349:results/calibrated_predictions_selected_features.csv"],
        text=True,
        cwd=ROOT,
    )
    git0538 = pd.read_csv(io.StringIO(git_content)).rename(
        columns={"predicted_score": "git0538"}
    )

    frame = seq[["rt_name"]].merge(selected, on="rt_name", how="left")
    frame = frame.merge(repair, on="rt_name", how="left")
    frame = frame.merge(meta, on="rt_name", how="left")
    frame = frame.merge(git0538, on="rt_name", how="left")
    return frame


def load_mmlv_similarity(rt_names):
    emb = np.load(ROOT / "data" / "esm2_embeddings.npz")
    if "rt_names" in emb.files:
        emb_names = [str(name) for name in emb["rt_names"]]
    else:
        emb_names = list(rt_names)

    name_to_idx = {name: idx for idx, name in enumerate(emb_names)}
    vectors = emb["embeddings"].astype(float)
    vectors /= np.linalg.norm(vectors, axis=1, keepdims=True) + 1e-8

    aligned = np.vstack([vectors[name_to_idx[name]] for name in rt_names])
    mmlv_idx = list(rt_names).index("MMLV-RT")
    mmlv_vec = aligned[mmlv_idx]
    return aligned @ mmlv_vec


def rankpct(values):
    return pd.Series(values).rank(method="average").to_numpy(dtype=float) / (
        len(values) + 1.0
    )


def apply_repair(frame):
    repaired = frame["selected"].to_numpy(dtype=float).copy()
    repair_rank = rankpct(frame["repair"])
    meta_rank = rankpct(frame["meta"])
    git0538_rank = rankpct(frame["git0538"])
    sim_mmlv = load_mmlv_similarity(frame["rt_name"].tolist())

    top18 = np.argsort(repaired)[-18:]
    repaired[top18] += 0.016 * (repair_rank[top18] - 0.5)
    repaired[top18] += 0.012 * (meta_rank[top18] - 0.5)
    repaired[top18] += -0.04 * sim_mmlv[top18]

    top9 = np.argsort(repaired)[-9:]
    repaired[top9] += -0.01 * (repair_rank[top9] - 0.5)
    repaired[top9] += -0.005 * (meta_rank[top9] - 0.5)
    repaired[top9] += 0.015 * (git0538_rank[top9] - 0.5)
    repaired[top9] += -0.04 * sim_mmlv[top9]

    out = frame[["rt_name"]].copy()
    out["predicted_score"] = repaired
    return out


def main():
    frame = load_scores()
    out = apply_repair(frame)
    out_path = ROOT / "results" / "top_local_repair_tier2.csv"
    out.to_csv(out_path, index=False)
    print(f"Saved {out_path}")


if __name__ == "__main__":
    main()
