import pandas as pd
import json

cols = {
    'handcrafted': pd.read_csv('data/handcrafted_features.csv').columns.tolist(),
    'structure': pd.read_csv('data/structure_features.csv').columns.tolist(),
    'topology': pd.read_csv('data/topology_features.csv').columns.tolist() if __import__('os').path.exists('data/topology_features.csv') else []
}

with open('cols.json', 'w') as f:
    json.dump(cols, f, indent=4)
