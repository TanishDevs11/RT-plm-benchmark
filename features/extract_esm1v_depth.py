import esm
import torch
import pandas as pd
import numpy as np
from tqdm import tqdm

df = pd.read_csv("data/rt_sequences.csv")

model, alphabet = esm.pretrained.esm1v_t33_650M_UR90S()
batch_converter = alphabet.get_batch_converter()
model.eval()

rows = []

for _, row in tqdm(df.iterrows(), total=len(df)):

    seq = row.sequence
    data = [("protein", seq)]

    _, _, tokens = batch_converter(data)

    with torch.no_grad():
        out = model(tokens)

    logits = out["logits"]

    log_probs = torch.log_softmax(logits, dim=-1)

    token_loglikelihood = log_probs.mean().item()

    residue_variance = log_probs.var().item()

    surprisal_entropy = (-log_probs * torch.exp(log_probs)).mean().item()

    rows.append([
        row.rt_name,
        token_loglikelihood,
        residue_variance,
        surprisal_entropy
    ])

out_df = pd.DataFrame(rows, columns=[
    "rt_name",
    "esm1v_loglikelihood_true",
    "esm1v_residue_variance",
    "esm1v_surprisal_entropy"
])

out_df.to_csv(
    "data/esm1v_depth_features.csv",
    index=False
)

print("Saved esm1v_depth_features.csv")
