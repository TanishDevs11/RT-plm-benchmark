import json
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution
import sys
import os

ROOT = os.path.join(os.path.dirname(__file__))
sys.path.append(os.path.join(ROOT, "src"))
sys.path.append(os.path.join(ROOT, "evaluation"))

from evaluate import compute_cls

with open("results/component_arrays.json", "r") as f:
    component_arrays = json.load(f)

# Convert to numpy
component_arrays = {k: np.array(v) for k, v in component_arrays.items()}

seq = pd.read_csv("data/rt_sequences.csv").set_index("rt_name")
# we need all_names. We can get it from component_arrays keys length, but wait, the order matters!
# Let's derive all_names from the CSV directly. Wait, the sequence of all_names in component_arrays is the output of LeaveOneGroupOut.
# It's better to just extract the names from `calibrated_lofo_predictions.py` execution.
# But wait, in the 57 folds, what was `all_names`? 
