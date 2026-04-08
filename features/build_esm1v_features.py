import esm
import torch
import pandas as pd
from tqdm import tqdm
import os

def main():
    os.makedirs("features", exist_ok=True)
    
    # Check if we should use rt_sequences.csv or sequences.csv
    seq_path = "data/rt_sequences.csv" if os.path.exists("data/rt_sequences.csv") else "data/sequences.csv"
    df = pd.read_csv(seq_path)

    # Load ESM-1v model
    # Model esm1v_t33_650M_UR90S
    model, alphabet = esm.pretrained.esm1v_t33_650M_UR90S_1()
    batch_converter = alphabet.get_batch_converter()
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = model.to(device)

    scores = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        data = [("protein", row.sequence)]
        _, _, tokens = batch_converter(data)
        tokens = tokens.to(device)

        with torch.no_grad():
            out = model(tokens, repr_layers=[33], return_contacts=False)
            
        log_probs = torch.log_softmax(out["logits"], dim=-1)
        # Average likelihood over sequence length
        # tokens are [B, L], log_probs are [B, L, V]
        # To get the log likelihood of the sequence, we need to gather the log probs
        
        sequence_len = len(row.sequence)
        # Sequence tokens excluding <cls> and <eos>
        actual_tokens = tokens[0, 1:sequence_len+1]
        
        # log_probs shape: [1, L+2, V] -> slice to [sequence_len, V]
        sliced_log_probs = log_probs[0, 1:sequence_len+1, :]
        
        # Gather the log prob of actual tokens
        seq_log_probs = torch.gather(sliced_log_probs, 1, actual_tokens.unsqueeze(1)).squeeze(1)
        
        ll = seq_log_probs.mean().item()
        perplexity = torch.exp(-seq_log_probs.mean()).item()
        
        # also compute residue_surprise_std and entropy_variance
        residue_surprise_std = (-seq_log_probs).std().item()
        
        # Entropy of the distribution at each position
        entropy = -(torch.exp(sliced_log_probs) * sliced_log_probs).sum(dim=1)
        entropy_variance = entropy.var().item()

        scores.append((row.rt_name, ll, perplexity, residue_surprise_std, entropy_variance))

    esm_df = pd.DataFrame(scores, columns=[
        "rt_name",
        "esm1v_log_likelihood",
        "esm1v_perplexity",
        "residue_surprise_std",
        "entropy_variance"
    ])

    esm_df.to_csv("features/esm1v_features.csv", index=False)

if __name__ == "__main__":
    main()
