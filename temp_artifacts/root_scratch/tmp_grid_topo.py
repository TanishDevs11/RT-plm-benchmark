import ast
import json
import re

import numpy as np
import pandas as pd
from scipy.stats import rankdata

from evaluation.evaluate import compute_cls


def main():
    comp = json.load(open("results/component_arrays.json", "r"))
    comp = {
        k: np.nan_to_num(np.array(v, float), nan=0.0, posinf=0.0, neginf=0.0)
        for k, v in comp.items()
    }
    rank = {k: rankdata(v, method="average") / (len(v) + 1.0) for k, v in comp.items()}

    text = open("experiments/calibrated_lofo_predictions.py", "r", encoding="utf-8").read()
    power = float(re.search(r"RANK_POWER\s*=\s*([0-9.]+)", text).group(1))
    m = re.search(r"RANK_BLEND_WEIGHTS\s*=\s*\{([\s\S]*?)\n\}", text)
    base_w = ast.literal_eval("{" + m.group(1) + "\n}")

    names = (
        pd.read_csv("results/calibrated_predictions_selected_features.csv")["rt_name"]
        .astype(str)
        .tolist()
    )
    seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name").loc[names]

    def cls_for(w):
        s = np.zeros(len(names))
        for k, v in w.items():
            if v != 0 and k in rank:
                s += v * np.power(rank[k], power)
        return compute_cls(seq["active"].values, s, seq["pe_efficiency_pct"].values)["cls"]

    base_cls = cls_for(base_w)
    print("Base CLS", base_cls)

    cands = [
        "topo_contact_density",
        "topo_long_range_ratio",
        "topo_entropy_degree",
        "topo_clustering_proxy",
        "topo_contact_entropy",
        "proto_topo_mul",
        "density_topo_mul",
        "contrast_topo_mul",
    ]

    best_overall = (base_cls, None, 0.0)
    for c in cands:
        if c not in rank:
            print("missing", c)
            continue
        best = (base_cls, 0.0)
        for a in np.linspace(-1.5, 1.5, 61):
            w = dict(base_w)
            w[c] = float(a)
            cur = cls_for(w)
            if cur > best[0]:
                best = (cur, float(a))
        print(c, "best", best)
        if best[0] > best_overall[0]:
            best_overall = (best[0], c, best[1])

    print("Best single add", best_overall)

    # Coordinate ascent over topology-only weights (keep baseline fixed)
    w_cur = dict(base_w)
    cls_cur = float(base_cls)
    step_grid = np.linspace(-0.30, 0.30, 25)

    for it in range(6):
        improved = False
        for c in cands:
            cur_w = float(w_cur.get(c, 0.0))
            best = (cls_cur, cur_w)
            for delta in step_grid:
                w = dict(w_cur)
                w[c] = max(-1.5, min(1.5, cur_w + float(delta)))
                cur = float(cls_for(w))
                if cur > best[0]:
                    best = (cur, w[c])
            if best[0] > cls_cur + 1e-10:
                cls_cur = best[0]
                w_cur[c] = best[1]
                improved = True
        print(
            f"Iter {it}: CLS={cls_cur:.6f} "
            + " ".join([f"{c}={w_cur.get(c, 0.0):.3f}" for c in cands])
        )
        if not improved:
            break

    print("Final coord-ascent CLS", cls_cur)
    print("Final topo weights", {c: float(w_cur.get(c, 0.0)) for c in cands})


if __name__ == "__main__":
    main()

