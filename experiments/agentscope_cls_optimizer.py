import os
import json
import random
import datetime
import subprocess
import copy
import re
import numpy as np


TARGET_CLS = 0.70
MAX_ITERS = 40

LOG_FILE = "results/cls_search_log.json"
BEST_WEIGHTS_FILE = "results/best_weights.json"


# --------------------------------------------------
# Default ensemble weights
# --------------------------------------------------

DEFAULT_WEIGHTS = {
    "BASELINE_W": 0.00145,
    "SAFE_PCT_L1_W": 0.2890,
    "BOTH_ZSIG_L1_W": 0.00737,
    "CURRENT605_L1_W": 0.1223,
    "SAFE_PCT_L2_W": 0.04606,
    "BOTH_ZSIG_L2_W": 0.2605,
    "GLOBALMM_L2_W": 0.06101,
    "ET_FULL_038_W": 0.12713,
    "HAND_ET_085_W": 0.07927,
    "CLF_ONLY_ETL2_W": 0.00560,
    "GLOBALMM_ET_W": 0.08,
}


# --------------------------------------------------
# Load previous best weights
# --------------------------------------------------

def load_best_weights():

    if os.path.exists(BEST_WEIGHTS_FILE):
        with open(BEST_WEIGHTS_FILE, "r") as f:
            return json.load(f)

    return DEFAULT_WEIGHTS.copy()


# --------------------------------------------------
# Save best weights
# --------------------------------------------------

def save_best_weights(weights):

    os.makedirs("results", exist_ok=True)

    with open(BEST_WEIGHTS_FILE, "w") as f:
        json.dump(weights, f, indent=2)


# --------------------------------------------------
# Logging
# --------------------------------------------------

def log_result(iteration, weights, cls_score):

    os.makedirs("results", exist_ok=True)

    entry = {
        "timestamp": str(datetime.datetime.now()),
        "iteration": iteration,
        "weights": weights,
        "cls": cls_score,
    }

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    else:
        logs = []

    logs.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)


# --------------------------------------------------
# Run calibrated LOFO pipeline
# --------------------------------------------------

def run_lofo(weights):

    env = os.environ.copy()

    for k, v in weights.items():
        env[k] = str(v)

    result = subprocess.run(
        ["python", "experiments/calibrated_lofo_predictions.py"],
        capture_output=True,
        text=True,
        env=env,
    )

    print(result.stdout)

    match = re.search(r"CLS:\s*([0-9.]+)", result.stdout)

    if match:
        return float(match.group(1))

    print("âŒ CLS extraction failed")
    return None


# --------------------------------------------------
# Leakage sanity test
# --------------------------------------------------

def run_shuffle():

    print("\nRunning shuffle-label leakage test...\n")

    subprocess.run(
        ["python", "experiments/shuffle_labels_test.py"]
    )


# --------------------------------------------------
# Multi-weight mutation strategy
# --------------------------------------------------

def mutate_weights(weights, iteration):

    new_weights = copy.deepcopy(weights)

    keys = list(new_weights.keys())

    # early iterations = large exploration
    if iteration < 10:
        mutation_scale = 0.5
        n_mutations = 4

    # mid iterations = moderate tuning
    elif iteration < 25:
        mutation_scale = 0.25
        n_mutations = 3

    # late iterations = fine tuning
    else:
        mutation_scale = 0.12
        n_mutations = 2

    selected = random.sample(keys, n_mutations)

    for key in selected:

        factor = np.exp(np.random.normal(0, mutation_scale))

        new_weights[key] *= factor

    # normalize weights

    total = sum(new_weights.values())

    for k in new_weights:
        new_weights[k] /= total

    print("Mutated keys:", selected)

    return new_weights


# --------------------------------------------------
# Optimization loop
# --------------------------------------------------

def optimize():

    print("\nðŸš€ Starting CLS optimizer...\n")

    best_weights = load_best_weights()

    best_cls = run_lofo(best_weights)

    print("Initial CLS:", best_cls)

    run_shuffle()

    for iteration in range(1, MAX_ITERS + 1):

        print(f"\n=========== ITERATION {iteration} ===========")

        candidate_weights = mutate_weights(best_weights, iteration)

        cls_score = run_lofo(candidate_weights)

        if cls_score is None:
            continue

        print("Candidate CLS:", cls_score)

        if cls_score > best_cls:

            print("âœ… Improvement found!")

            best_cls = cls_score
            best_weights = candidate_weights

            save_best_weights(best_weights)

        log_result(iteration, candidate_weights, cls_score)

        if best_cls >= TARGET_CLS:

            print("\nðŸŽ¯ TARGET CLS REACHED:", best_cls)
            break

    print("\nOptimization finished")
    print("Best CLS:", best_cls)
    print("Best weights saved to:", BEST_WEIGHTS_FILE)


# --------------------------------------------------
# Entry point
# --------------------------------------------------

if __name__ == "__main__":
    optimize()
