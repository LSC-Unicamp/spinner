"""Cria bench_a.pkl e bench_b.pkl usando dict puro (sem classe customizada)."""
import pickle
import pandas as pd


class _DictConfig:
    """Config serializável que armazena dados como dict puro."""
    def __init__(self, data: dict):
        self._data = data

    def model_dump(self):
        return self._data


df_a = pd.DataFrame({
    "name":      ["bench_test"] * 6,
    "param":     [1, 1, 2, 2, 4, 4],
    "wall_time": [1.10, 1.12, 2.20, 2.18, 4.50, 4.55],
    "run":       [1, 2, 1, 2, 1, 2],
    "status":    ["ok"] * 6,
})

df_b = pd.DataFrame({
    "name":      ["bench_test"] * 6,
    "param":     [1, 1, 2, 2, 4, 4],
    "wall_time": [0.85, 0.87, 1.70, 1.72, 3.40, 3.38],
    "run":       [1, 2, 1, 2, 1, 2],
    "status":    ["ok"] * 6,
})

bench_a = {
    "config": _DictConfig({
        "applications": {"bench_test": {"command": "sleep {param}"}},
        "benchmarks":   {"bench_test": {"param": [1, 2, 4]}},
        "description":  "Experiment A - baseline",
        "version":      "1.0",
    }),
    "metadata": {
        "description": "Experiment A - baseline (slower)",
        "version": "1.0",
        "host": "node-01",
        "cpu": "Intel Xeon E5-2690",
    },
    "dataframe": df_a,
}

bench_b = {
    "config": _DictConfig({
        "applications": {"bench_test": {"command": "sleep {param}"}},
        "benchmarks":   {"bench_test": {"param": [1, 2, 4]}},
        "description":  "Experiment B - optimized",
        "version":      "2.0",
    }),
    "metadata": {
        "description": "Experiment B - optimized (faster)",
        "version": "2.0",
        "host": "node-02",
        "cpu": "AMD EPYC 9654",
    },
    "dataframe": df_b,
}

with open("bench_a.pkl", "wb") as f:
    pickle.dump(bench_a, f)

with open("bench_b.pkl", "wb") as f:
    pickle.dump(bench_b, f)

print("bench_a.pkl e bench_b.pkl criados com sucesso.")
