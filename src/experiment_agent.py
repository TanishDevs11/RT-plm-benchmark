import json
from datetime import datetime

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier

from train_lofo_model import run_lofo_validation
from feature_engineering import engineer_features


def run_experiment(model_name, model):

    print(f"\nRunning experiment: {model_name}")

    X, y, groups = engineer_features()

    score = run_lofo_validation(model, X, y, groups)

    return score


def main():

    experiments = {}

    models = {

        "RandomForest_default": RandomForestClassifier(
            n_estimators=200,
            random_state=42
        ),

        "RandomForest_shallow": RandomForestClassifier(
            n_estimators=200,
            max_depth=5,
            random_state=42
        ),

        "LogisticRegression": LogisticRegression(
            max_iter=1000
        ),

        "XGBoost": XGBClassifier(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=4,
            eval_metric="logloss"
        )
    }

    for name, model in models.items():

        score = run_experiment(name, model)

        experiments[name] = score

    print("\nExperiment Results")

    for model, score in experiments.items():
        print(model, ":", score)

    best_model = max(experiments, key=experiments.get)

    print("\nBest model:", best_model)
    print("Best LOFO F1:", experiments[best_model])

    log = {
        "timestamp": str(datetime.now()),
        "results": experiments,
        "best_model": best_model
    }

    with open("experiments_log.json", "w") as f:
        json.dump(log, f, indent=4)


if __name__ == "__main__":
    main()