import sys
print("🚀 Contrastive script started", flush=True)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import numpy as np

    from sklearn.model_selection import LeaveOneGroupOut
    from sklearn.metrics import f1_score
    from sklearn.ensemble import RandomForestClassifier

    from feature_engineering import engineer_features

except Exception as e:
    print("Import error:", e, flush=True)
    sys.exit()


print("Loading features...", flush=True)

X, y, groups = engineer_features()

X = X.values
y = y.values

print("Feature matrix:", X.shape, flush=True)


# -------------------------------------------------
# Encoder Network
# -------------------------------------------------

class Encoder(nn.Module):

    def __init__(self, input_dim):

        super().__init__()

        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 16)
        )

    def forward(self, x):

        return self.net(x)


# -------------------------------------------------
# Contrastive Loss
# -------------------------------------------------

def contrastive_loss(z1, z2, label):

    dist = torch.norm(z1 - z2, dim=1)

    loss = label * dist**2 + (1-label) * torch.clamp(1 - dist, min=0)**2

    return torch.mean(loss)


print("Initializing encoder...", flush=True)

encoder = Encoder(X.shape[1])

optimizer = optim.Adam(encoder.parameters(), lr=0.001)

X_tensor = torch.tensor(X, dtype=torch.float32)
y_tensor = torch.tensor(y, dtype=torch.float32)

print("Training contrastive encoder...", flush=True)

for epoch in range(100):

    idx1 = np.random.randint(0, len(X), 32)
    idx2 = np.random.randint(0, len(X), 32)

    x1 = X_tensor[idx1]
    x2 = X_tensor[idx2]

    label = (y_tensor[idx1] == y_tensor[idx2]).float()

    z1 = encoder(x1)
    z2 = encoder(x2)

    loss = contrastive_loss(z1, z2, label)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    if epoch % 20 == 0:
        print("Epoch:", epoch, "| Loss:", loss.item(), flush=True)


print("Generating embeddings...", flush=True)

with torch.no_grad():

    embeddings = encoder(X_tensor).numpy()

print("Embedding shape:", embeddings.shape, flush=True)


# -------------------------------------------------
# LOFO Evaluation
# -------------------------------------------------

print("Running LOFO validation...", flush=True)

logo = LeaveOneGroupOut()

scores = []

for train_idx, test_idx in logo.split(embeddings, y, groups):

    X_train = embeddings[train_idx]
    X_test = embeddings[test_idx]

    y_train = y[train_idx]
    y_test = y[test_idx]

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=4,
        random_state=42
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)

    score = f1_score(y_test, preds, average="macro")

    scores.append(score)

    fam = groups.iloc[test_idx].unique()[0]

    print(f"Family: {fam:25} | F1: {score:.3f}", flush=True)


print("\nFinal Contrastive LOFO F1:", np.mean(scores), flush=True)