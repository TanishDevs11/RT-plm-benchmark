"""Statistical validation of the Task A representation benchmark.

A score without its nulls is not a result. This script supplies, for every score in
`bench/results/taskA_representations.json`:

1. **Bootstrap confidence intervals.** RTs resampled with replacement, 10000 draws, 95
   percent percentile interval, for CLS and for both of its components.
2. **A dimensionality-matched noise control.** Each representation is replaced by Gaussian
   noise of identical shape and run through the identical protocol. A representation that
   does not clear its own noise control has shown nothing, however good its score looks.
3. **A search-capacity null at matched K.** The free parameter count actually used here is
   one, the regularization strength, so the matched null is K equals 1 and its p95 is the
   bar. Comparing against a null computed at a different K is invalid, and where this
   repository has done that it is flagged.
4. **Label permutation.** `active` and `pe_efficiency_pct` shuffled inside the protocol,
   20 repeats. This catches leakage the other controls miss, because a leak through the
   protocol's structure survives a noise control but not a permuted label.
5. **The minimum resolvable difference.** Estimated from the paired bootstrap rather than
   assumed from a formula, and then applied: a pairwise gap smaller than its own MRD is
   reported as not resolvable at this sample size, never as a win.
6. **Paired bootstrap for every pairwise comparison**, reporting the probability that A
   beats B rather than a bare point difference.

Stages 1, 5 and 6 need only the stored prediction vectors, so they are cheap. Stages 2 and
4 refit the protocol and are the expensive ones, which is why each stage can be run alone.

    python bench/validate_taskA.py --stage all
    python bench/validate_taskA.py --stage noise
    python bench/validate_taskA.py --stage permutation

Outputs:
    bench/results/taskA_validation.json
    reports/statistical_validation.md
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "bench"))
sys.path.insert(0, str(REPO_ROOT / "evaluation"))

from evaluate import compute_cls  # noqa: E402
from protocol import SEED, run_nested_lofo  # noqa: E402
from representations_taskA import (  # noqa: E402
    LOGISTIC_C_GRID,
    RepresentationHead,
    harmonic_mean,
    load_representations,
    load_taskA_dataset,
)

from schemas.task_schema import print_run_header, sha256_of  # noqa: E402

CURATED = REPO_ROOT / "tasks" / "taskA_crossfamily" / "curated.csv"
RESULTS = REPO_ROOT / "bench" / "results"
MAIN = RESULTS / "taskA_representations.json"
SEARCH_NULL = RESULTS / "search_null.json"
OUT_JSON = RESULTS / "taskA_validation.json"
OUT_MD = REPO_ROOT / "reports" / "statistical_validation.md"

N_BOOTSTRAP = 10000
N_PERMUTATIONS = 20

# The number of free parameters this benchmark's search actually uses: one, the
# regularization strength. The matched search-capacity null is therefore K = 1. Any
# comparison against a null computed at a different K is comparing a one-parameter search
# against the noise ceiling of a larger one.
FREE_PARAMETERS_USED = 1

# Representations put through the label permutation. All twelve would be 480 protocol
# runs, so this is a subset, and it is stated rather than silent.
#
# The selection rule: the trained length baseline, plus every representation that leads
# either headline metric, plus the largest language model. A permutation test is most
# needed exactly where a score looks best, so omitting the leaders would have been the
# one indefensible choice. physicochemical leads CLS at 0.3739 and kmer4 leads
# classification PR-AUC at 0.6212.
PERMUTATION_SUBSET = (
    "length",
    "handcrafted",
    "physicochemical",
    "kmer4",
    "esm2_8M",
    "esm2_650M",
)

# Power constants for the minimum resolvable difference. Two-sided alpha of 0.05 and 80
# percent power, so the detectable effect is about (1.96 + 0.8416) standard errors.
Z_ALPHA_TWO_SIDED = 1.96
Z_POWER = 0.8416


def load_main() -> dict:
    if not MAIN.is_file():
        raise SystemExit(
            "bench/results/taskA_representations.json absent; run "
            "bench/representations_taskA.py first"
        )
    return json.loads(MAIN.read_text(encoding="utf-8"))


def bootstrap_components(
    active: np.ndarray,
    efficiency: np.ndarray,
    scores: np.ndarray,
    seed: int = SEED,
    draws: int = N_BOOTSTRAP,
) -> dict[str, tuple[float, float, float]]:
    """Percentile intervals for CLS, PR-AUC and weighted Spearman, from one score vector."""
    rng = np.random.default_rng(seed)
    n = len(active)
    collected = {"cls": [], "pr_auc": [], "w_spearman": []}
    for _ in range(draws):
        index = rng.integers(0, n, size=n)
        resampled = active[index]
        if resampled.sum() == 0 or resampled.sum() == n:
            continue
        values = compute_cls(resampled, scores[index], efficiency[index])
        for key in collected:
            collected[key].append(float(values[key]))
    out = {}
    for key, values in collected.items():
        array = np.asarray(values, dtype=float)
        low, high = np.percentile(array, [2.5, 97.5])
        out[key] = (float(low), float(high), float(array.std(ddof=1)))
    return out


def paired_bootstrap(
    active: np.ndarray,
    efficiency: np.ndarray,
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    seed: int = SEED,
    draws: int = N_BOOTSTRAP,
) -> dict[str, float]:
    """Resample RTs once per draw and score both vectors on the same resample.

    Pairing matters: the two methods see the same enzymes in the same draw, so the
    comparison is not inflated by the variance of the panel itself.
    """
    rng = np.random.default_rng(seed)
    n = len(active)
    differences = []
    wins = 0
    for _ in range(draws):
        index = rng.integers(0, n, size=n)
        resampled = active[index]
        if resampled.sum() == 0 or resampled.sum() == n:
            continue
        a = compute_cls(resampled, scores_a[index], efficiency[index])["cls"]
        b = compute_cls(resampled, scores_b[index], efficiency[index])["cls"]
        differences.append(float(a - b))
        wins += 1 if a > b else 0
    array = np.asarray(differences, dtype=float)
    low, high = np.percentile(array, [2.5, 97.5])
    return {
        "mean_difference": float(array.mean()),
        "sd_difference": float(array.std(ddof=1)),
        "ci_low": float(low),
        "ci_high": float(high),
        "probability_a_beats_b": float(wins / len(array)),
        "n_draws": int(len(array)),
    }


def run_noise_controls(data, representations: dict, heads: list[str]) -> dict:
    """The same protocol on Gaussian noise of identical dimensionality."""
    out: dict[str, dict] = {}
    for label, (matrix, _) in representations.items():
        rng = np.random.default_rng(abs(hash(label)) % (2**32))
        noise = rng.standard_normal(matrix.shape)
        out[label] = {"n_features": int(matrix.shape[1])}
        for head in heads:
            method = RepresentationHead(label + "_noise", noise, head)
            started = time.time()
            result = run_nested_lofo(method, data)
            out[label][head] = {
                "cls": result.cls,
                "pr_auc": result.pr_auc,
                "w_spearman": result.w_spearman,
                "seconds": round(time.time() - started, 2),
            }
            print(
                "  noise "
                + label.ljust(28)
                + head.ljust(16)
                + "CLS "
                + format(result.cls, ".4f")
                + "  PR-AUC "
                + format(result.pr_auc, ".4f")
                + "  wSpearman "
                + format(result.w_spearman, ".4f")
            )
            sys.stdout.flush()
        if all(h in heads for h in ("classification", "regression")):
            out[label]["two_head_cls"] = harmonic_mean(
                out[label]["classification"]["pr_auc"],
                out[label]["regression"]["w_spearman"],
            )
    return out


def run_permutations(
    data, representations: dict, heads: list[str], only: list[str] | None = None
) -> dict:
    """Shuffle the labels inside the protocol and rerun, 20 times per representation."""
    out: dict[str, dict] = {}
    wanted = only or list(PERMUTATION_SUBSET)
    for label in wanted:
        if label not in representations:
            continue
        matrix = representations[label][0]
        out[label] = {}
        for head in heads:
            scores = []
            pr_scores = []
            for repeat in range(N_PERMUTATIONS):
                rng = np.random.default_rng(SEED + repeat)
                shuffled = data.copy()
                order = rng.permutation(len(shuffled))
                # Both labels are permuted with the same ordering, so their pairing with
                # each other survives and only their pairing with the sequences is broken.
                shuffled["active"] = data["active"].to_numpy()[order]
                shuffled["pe_efficiency_pct"] = data["pe_efficiency_pct"].to_numpy()[order]
                method = RepresentationHead(label + "_perm", matrix, head)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    result = run_nested_lofo(method, shuffled, seed=SEED + repeat)
                scores.append(result.cls)
                pr_scores.append(result.pr_auc)
            array = np.asarray(scores, dtype=float)
            pr_array = np.asarray(pr_scores, dtype=float)
            out[label][head] = {
                "n_repeats": N_PERMUTATIONS,
                "mean": float(array.mean()),
                "std": float(array.std(ddof=1)),
                "min": float(array.min()),
                "p95": float(np.percentile(array, 95)),
                "max": float(array.max()),
                "values": [float(v) for v in array],
                # PR-AUC under permutation too, because the primary claim is
                # classification and CLS can floor at zero for reasons that have nothing
                # to do with separation.
                "pr_auc_mean": float(pr_array.mean()),
                "pr_auc_std": float(pr_array.std(ddof=1)),
                "pr_auc_p95": float(np.percentile(pr_array, 95)),
                "pr_auc_max": float(pr_array.max()),
                "pr_auc_values": [float(v) for v in pr_array],
            }
            print(
                "  permuted "
                + label.ljust(24)
                + head.ljust(16)
                + "mean CLS "
                + format(array.mean(), ".4f")
                + "  p95 "
                + format(np.percentile(array, 95), ".4f")
                + "  max "
                + format(array.max(), ".4f")
            )
            sys.stdout.flush()
    return out


def matched_search_null() -> dict | None:
    if not SEARCH_NULL.is_file():
        return None
    payload = json.loads(SEARCH_NULL.read_text(encoding="utf-8"))
    for entry in payload.get("k_sweep", []):
        if entry.get("k") == FREE_PARAMETERS_USED:
            return entry
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage", default="all", choices=["all", "ci", "noise", "permutation", "report"]
    )
    parser.add_argument(
        "--permute-only",
        nargs="*",
        default=None,
        help="restrict the permutation stage to these representations and merge the "
        "result into any existing permutation results",
    )
    args = parser.parse_args()

    print_run_header("bench/validate_taskA.py", [CURATED, MAIN])
    main_results = load_main()
    data = load_taskA_dataset()
    active = data["active"].to_numpy()
    efficiency = data["pe_efficiency_pct"].to_numpy(dtype=float)
    heads = main_results["heads"]

    existing = {}
    if OUT_JSON.is_file():
        existing = json.loads(OUT_JSON.read_text(encoding="utf-8"))

    payload: dict = {
        "curated_sha256": sha256_of(CURATED),
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "n_permutations": N_PERMUTATIONS,
        "free_parameters_used": FREE_PARAMETERS_USED,
        "permutation_subset": list(PERMUTATION_SUBSET),
        "intervals": existing.get("intervals", {}),
        "noise": existing.get("noise", {}),
        "permutation": existing.get("permutation", {}),
        "pairwise": existing.get("pairwise", {}),
        "search_null_matched": matched_search_null(),
    }

    if args.stage in ("all", "ci"):
        print("")
        print("=== bootstrap intervals, " + str(N_BOOTSTRAP) + " draws ===")
        intervals: dict[str, dict] = {}
        for label, entry in main_results["results"].items():
            intervals[label] = {}
            for head in heads:
                if head not in entry:
                    continue
                scores = np.asarray(entry[head]["predictions"], dtype=float)
                bounds = bootstrap_components(active, efficiency, scores)
                intervals[label][head] = {
                    key: {"ci_low": low, "ci_high": high, "sd": sd}
                    for key, (low, high, sd) in bounds.items()
                }
                print(
                    "  "
                    + label.ljust(28)
                    + head.ljust(16)
                    + "CLS "
                    + format(entry[head]["cls"], ".4f")
                    + " ["
                    + format(bounds["cls"][0], ".4f")
                    + ", "
                    + format(bounds["cls"][1], ".4f")
                    + "]"
                )
        payload["intervals"] = intervals

        print("")
        print("=== paired bootstrap, every pair, classification head ===")
        pairwise: dict[str, dict] = {}
        labels = sorted(main_results["results"])
        for head in heads:
            usable = [
                label
                for label in labels
                if head in main_results["results"][label]
            ]
            for i, a in enumerate(usable):
                for b in usable[i + 1 :]:
                    scores_a = np.asarray(
                        main_results["results"][a][head]["predictions"], dtype=float
                    )
                    scores_b = np.asarray(
                        main_results["results"][b][head]["predictions"], dtype=float
                    )
                    key = head + "|" + a + "|vs|" + b
                    pairwise[key] = paired_bootstrap(
                        active, efficiency, scores_a, scores_b
                    )
            print("  " + head + ": " + str(len(usable) * (len(usable) - 1) // 2) + " pairs")
        payload["pairwise"] = pairwise

    if args.stage in ("all", "noise"):
        print("")
        print("=== dimensionality-matched Gaussian noise controls ===")
        representations = load_representations([])
        payload["noise"] = run_noise_controls(data, representations, heads)

    if args.stage in ("all", "permutation"):
        print("")
        print("=== label permutation, " + str(N_PERMUTATIONS) + " repeats ===")
        wanted = args.permute_only or list(PERMUTATION_SUBSET)
        representations = load_representations(wanted)
        fresh = run_permutations(data, representations, heads, only=wanted)
        # Merge rather than replace, so a targeted rerun does not discard the expensive
        # results already on disk.
        merged = dict(payload["permutation"])
        merged.update(fresh)
        payload["permutation"] = merged

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print("")
    print("wrote " + OUT_JSON.relative_to(REPO_ROOT).as_posix())

    write_report(main_results, payload, heads, float(np.mean(active)))
    print("wrote " + OUT_MD.relative_to(REPO_ROOT).as_posix())
    return 0


def minimum_resolvable_difference(pairwise: dict) -> dict:
    """The smallest CLS gap detectable at 80 percent power, from the paired bootstrap.

    Estimated rather than assumed. The paired bootstrap gives, for each comparison, the
    standard deviation of the difference in CLS under resampling of the enzymes. A
    two-sided test at alpha 0.05 with 80 percent power needs a true difference of about
    (1.96 + 0.8416) of those standard deviations. Taking the median across every pair
    gives one number for the panel; the per-pair value is what each comparison is
    actually judged against, because a pair of near-identical methods has a smaller
    standard error than a pair of very different ones.
    """
    multiplier = Z_ALPHA_TWO_SIDED + Z_POWER
    per_pair = {
        key: multiplier * entry["sd_difference"] for key, entry in pairwise.items()
    }
    values = np.asarray(list(per_pair.values()), dtype=float)
    return {
        "multiplier": multiplier,
        "per_pair": per_pair,
        "median": float(np.median(values)) if values.size else float("nan"),
        "min": float(values.min()) if values.size else float("nan"),
        "max": float(values.max()) if values.size else float("nan"),
    }


def write_report(
    main_results: dict, payload: dict, heads: list[str], prevalence: float
) -> None:
    results = main_results["results"]
    intervals = payload.get("intervals", {})
    noise = payload.get("noise", {})
    permutation = payload.get("permutation", {})
    pairwise = payload.get("pairwise", {})
    search = payload.get("search_null_matched")
    mrd = minimum_resolvable_difference(pairwise) if pairwise else None

    lines = [
        "# Task A statistical validation",
        "",
        "Written by `bench/validate_taskA.py`. Every score in",
        "`bench/results/taskA_representations.md` is reported here with its interval, its",
        "dimensionality-matched noise control, and the search-capacity null at matched",
        "free-parameter count. A score without those is not a result.",
        "",
        "Source: `tasks/taskA_crossfamily/curated.csv`, SHA256",
        "`" + payload["curated_sha256"] + "`. Seed " + str(payload["seed"]) + ".",
        "",
        "## The search-capacity null, at matched K",
        "",
        "This benchmark's inner loop selects exactly **one** free parameter, the",
        "regularization strength, from a grid of "
        + str(len(LOGISTIC_C_GRID))
        + " values fixed a priori. So the matched",
        "search-capacity null is K equals 1.",
        "",
    ]
    if search:
        lines += [
            "| K | repeats | mean | sd | p95 | min | max |",
            "| --- | --- | --- | --- | --- | --- | --- |",
            "| "
            + str(search["k"])
            + " | "
            + str(search["n_repeats"])
            + " | "
            + format(search["mean"], ".4f")
            + " | "
            + format(search["std"], ".4f")
            + " | "
            + format(search["p95"], ".4f")
            + " | "
            + format(search["min"], ".4f")
            + " | "
            + format(search["max"], ".4f")
            + " |",
            "",
            "**The bar every score below has to clear is a CLS of "
            + format(search["p95"], ".4f")
            + "**, the p95 of what",
            "a one-free-parameter search reaches on pure Gaussian noise.",
            "",
            "### An invalid comparison in this repository, and its correction",
            "",
            "The inherited result of 0.9754 was produced by a search holding up to 62 free",
            "parameters, and `bench/results/search_null.json` records that a 29-parameter",
            "search reaches a mean of 0.8662 and a p95 of 0.9340 on noise. Comparing a",
            "62-parameter result against a null computed at any smaller K understates the",
            "null, and comparing a 1-parameter result against the K equals 29 null",
            "overstates it. Each score must be compared against the null at its own K.",
            "",
            "The correction that matters for this report: the scores below are",
            "one-parameter scores, so 0.4433 is their bar, not 0.9340. That is a much lower",
            "bar, and most of them still do not clear it.",
            "",
        ]
    else:
        lines += [
            "`bench/results/search_null.json` has no entry at K equals "
            + str(FREE_PARAMETERS_USED)
            + ", so the matched null",
            "is not available and no score below can be compared against one. Run",
            "`bench/search_null.py`.",
            "",
        ]

    # PR-AUC against its own noise control, for the classification head.
    #
    # This table exists because CLS is the harmonic mean of a separation term and a
    # ranking term, and the ranking term is computed against pe_efficiency_pct, which the
    # Gate G2 ruling established is a digitization of Figure S1A rather than a published
    # measurement. A representation that separates actives well but does not reproduce the
    # digitized ordering scores a CLS of zero, because the harmonic mean floors there. So
    # for the primary claim, which is classification, PR-AUC against the noise control is
    # the test that is actually about the representation rather than about the figure.
    if "classification" in heads:
        lines += [
            "## The primary test: PR-AUC against its own noise control",
            "",
            "CLS is the harmonic mean of a separation term, PR-AUC, and a ranking term,",
            "weighted Spearman against `pe_efficiency_pct`. Per the Gate G2 ruling that",
            "column is a digitization of Figure S1A at roughly half a percentage point of",
            "resolution, so a representation that separates actives from inactives well but",
            "does not reproduce the digitized ordering scores a CLS of zero, because the",
            "harmonic mean floors there.",
            "",
            "For the primary claim, which is classification of the reproducible binary",
            "label, the honest test is therefore PR-AUC against a dimensionality-matched",
            "noise control. The chance level for PR-AUC is the positive prevalence, "
            + format(prevalence, ".4f")
            + ".",
            "",
            "No search-capacity null exists for PR-AUC: `bench/search_null.py` measures what",
            "a search reaches on CLS, not on PR-AUC. That gap is stated rather than papered",
            "over with the CLS bar, which would be a comparison between two different",
            "quantities.",
            "",
            "| representation | PR-AUC | 95 percent CI | noise control PR-AUC | prevalence | margin over the larger | clears both |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        pr_rows = []
        for label, entry in results.items():
            if "classification" not in entry:
                continue
            score = entry["classification"]["pr_auc"]
            interval = (
                intervals.get(label, {}).get("classification", {}).get("pr_auc", {})
            )
            noise_score = noise.get(label, {}).get("classification", {}).get("pr_auc")
            worst = max([v for v in (noise_score, prevalence) if v is not None])
            pr_rows.append((score, label, interval, noise_score, worst, score - worst))
        for score, label, interval, noise_score, worst, margin in sorted(
            pr_rows, key=lambda r: -r[0]
        ):
            clears = "yes" if margin > 0 else "no"
            lines.append(
                "| `"
                + label
                + "` | "
                + format(score, ".4f")
                + " | "
                + (
                    format(interval.get("ci_low", float("nan")), ".4f")
                    + " to "
                    + format(interval.get("ci_high", float("nan")), ".4f")
                    if interval
                    else "not computed"
                )
                + " | "
                + (format(noise_score, ".4f") if noise_score is not None else "not run")
                + " | "
                + format(prevalence, ".4f")
                + " | "
                + format(margin, "+.4f")
                + " | "
                + ("**" + clears + "**" if clears == "yes" else clears)
                + " |"
            )
        lines.append("")

    for head in heads:
        lines += [
            "## CLS results table, " + head + " head",
            "",
            "`signal margin` is the score minus the larger of its two nulls, so a",
            "non-positive margin means the representation has not been shown to carry",
            "anything.",
            "",
            "| representation | CLS | 95 percent CI | noise control CLS | search null p95 | signal margin | clears both |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        rows = []
        for label, entry in results.items():
            if head not in entry:
                continue
            score = entry[head]["cls"]
            interval = intervals.get(label, {}).get(head, {}).get("cls", {})
            noise_score = noise.get(label, {}).get(head, {}).get("cls")
            bar = search["p95"] if search else None
            worst = max([v for v in (noise_score, bar) if v is not None], default=None)
            margin = (score - worst) if worst is not None else None
            rows.append((score, label, entry, interval, noise_score, bar, margin))
        for score, label, entry, interval, noise_score, bar, margin in sorted(
            rows, key=lambda r: -r[0]
        ):
            clears = (
                "yes"
                if margin is not None and margin > 0
                else ("no" if margin is not None else "unknown")
            )
            lines.append(
                "| `"
                + label
                + "` | "
                + format(score, ".4f")
                + " | "
                + (
                    format(interval.get("ci_low", float("nan")), ".4f")
                    + " to "
                    + format(interval.get("ci_high", float("nan")), ".4f")
                    if interval
                    else "not computed"
                )
                + " | "
                + (format(noise_score, ".4f") if noise_score is not None else "not run")
                + " | "
                + (format(bar, ".4f") if bar is not None else "unavailable")
                + " | "
                + (format(margin, "+.4f") if margin is not None else "unknown")
                + " | "
                + ("**" + clears + "**" if clears == "yes" else clears)
                + " |"
            )
        lines.append("")

    if permutation:
        lines += [
            "## Label permutation",
            "",
            "`active` and `pe_efficiency_pct` are permuted together inside the protocol, so",
            "their pairing with each other survives and only their pairing with the",
            "sequences is broken. "
            + str(payload["n_permutations"])
            + " repeats. This catches leakage the noise control",
            "misses: a leak through the protocol's structure survives random features but",
            "not a permuted label.",
            "",
            "Run on " + ", ".join("`" + s + "`" for s in payload["permutation_subset"])
            + ", which span the trained length baseline, the",
            "best handcrafted block and the largest language model. All twelve",
            "representations would be 480 protocol runs; the subset is stated rather than",
            "silent.",
            "",
            "| representation | head | metric | permuted mean | permuted p95 | permuted max | observed | above the permuted p95 |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for label, per_head in permutation.items():
            for head, stats in per_head.items():
                variants = [("CLS", "mean", "p95", "max", "cls")]
                if "pr_auc_p95" in stats:
                    variants.append(
                        ("PR-AUC", "pr_auc_mean", "pr_auc_p95", "pr_auc_max", "pr_auc")
                    )
                for metric, mean_key, p95_key, max_key, observed_key in variants:
                    observed = results.get(label, {}).get(head, {}).get(observed_key)
                    verdict = (
                        ("yes" if observed > stats[p95_key] else "**no**")
                        if observed is not None
                        else "unknown"
                    )
                    lines.append(
                        "| `"
                        + label
                        + "` | "
                        + head
                        + " | "
                        + metric
                        + " | "
                        + format(stats[mean_key], ".4f")
                        + " | "
                        + format(stats[p95_key], ".4f")
                        + " | "
                        + format(stats[max_key], ".4f")
                        + " | "
                        + (format(observed, ".4f") if observed is not None else "n/a")
                        + " | "
                        + verdict
                        + " |"
                    )
        lines.append("")

    if mrd:
        lines += [
            "## Minimum resolvable difference",
            "",
            "Estimated from the paired bootstrap rather than assumed from a formula. For",
            "each comparison the paired bootstrap gives the standard deviation of the CLS",
            "difference under resampling of the enzymes; a two-sided test at alpha 0.05",
            "with 80 percent power needs a true difference of about "
            + format(mrd["multiplier"], ".4f")
            + " of those",
            "standard deviations.",
            "",
            "| quantity | CLS |",
            "| --- | --- |",
            "| median minimum resolvable difference across all pairs | "
            + format(mrd["median"], ".4f")
            + " |",
            "| smallest, for the most similar pair | " + format(mrd["min"], ".4f") + " |",
            "| largest, for the least similar pair | " + format(mrd["max"], ".4f") + " |",
            "",
            "**A median MRD of "
            + format(mrd["median"], ".4f")
            + " CLS on a panel of 57 enzymes with 21 positives and a**",
            "**CLS-weighted effective sample size of 11.338 is the central limitation of this**",
            "**benchmark.** Most of the gaps between representations are smaller than this,",
            "and every such gap is reported below as not resolvable rather than as a win.",
            "",
            "## Pairwise comparisons",
            "",
            "Every pair, by paired bootstrap on the same resamples, reporting the",
            "probability that A scores above B rather than a bare point difference. A gap",
            "smaller than that pair's own MRD is marked not resolvable.",
            "",
            "| head | A | B | CLS A minus B | 95 percent CI of the difference | P(A beats B) | pair MRD | resolvable |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        ranked = sorted(
            pairwise.items(), key=lambda kv: -abs(kv[1]["mean_difference"])
        )
        for key, entry in ranked:
            head, a, _, b = key.split("|")
            pair_mrd = mrd["per_pair"][key]
            resolvable = abs(entry["mean_difference"]) >= pair_mrd
            lines.append(
                "| "
                + head
                + " | `"
                + a
                + "` | `"
                + b
                + "` | "
                + format(entry["mean_difference"], "+.4f")
                + " | "
                + format(entry["ci_low"], "+.4f")
                + " to "
                + format(entry["ci_high"], "+.4f")
                + " | "
                + format(entry["probability_a_beats_b"], ".3f")
                + " | "
                + format(pair_mrd, ".4f")
                + " | "
                + ("yes" if resolvable else "**not resolvable**")
                + " |"
            )

    lines += [
        "",
        "## How to read all of this",
        "",
        "A representation has been shown to carry activity signal only if it clears, at",
        "once: its own dimensionality-matched noise control, the search-capacity null at",
        "its own free-parameter count, and the permuted-label distribution. Clearing a",
        "majority baseline is not evidence of anything, and neither is beating another",
        "representation by less than the minimum resolvable difference.",
        "",
        "Per the Gate G2 ruling, the classification head carries the headline claim",
        "because its label is reproducible from Table S1, while every regression and",
        "weighted-Spearman number inherits the Figure S1A digitization described in",
        "`reports/reconciliation.md` section 4.",
    ]
    OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
