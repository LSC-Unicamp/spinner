"""Script que cria dois .pkl de teste e roda a comparação via Ollama cloud."""
import json
import pickle
import sys
from pathlib import Path

import dotenv
import pandas as pd

dotenv.load_dotenv(".env")

sys.path.insert(0, ".")
from spinner.chat import utils


# ---------------------------------------------------------------------------
# Classe de config serializável (definida no módulo para pickle funcionar)
# ---------------------------------------------------------------------------
class BenchConfig:
    def __init__(self, description, version):
        self._data = {
            "applications": {"bench_test": {"command": "sleep {param}"}},
            "benchmarks": {"bench_test": {"param": [1, 2, 4]}},
            "description": description,
            "version": version,
        }

    def model_dump(self):
        return self._data


# ---------------------------------------------------------------------------
# Cria bench_a.pkl  — baseline (mais lento, Intel Xeon)
# ---------------------------------------------------------------------------
df_a = pd.DataFrame({
    "name":      ["bench_test"] * 6,
    "param":     [1, 1, 2, 2, 4, 4],
    "wall_time": [1.10, 1.12, 2.20, 2.18, 4.50, 4.55],
    "run":       [1, 2, 1, 2, 1, 2],
    "status":    ["ok"] * 6,
})
bench_a = {
    "config": BenchConfig("Experiment A - baseline", "1.0"),
    "metadata": {
        "description": "Experiment A - baseline (slower)",
        "version": "1.0",
        "host": "node-01",
        "cpu": "Intel Xeon E5-2690",
    },
    "dataframe": df_a,
}
with open("bench_a.pkl", "wb") as f:
    pickle.dump(bench_a, f)

# ---------------------------------------------------------------------------
# Cria bench_b.pkl  — optimized (mais rápido, AMD EPYC)
# ---------------------------------------------------------------------------
df_b = pd.DataFrame({
    "name":      ["bench_test"] * 6,
    "param":     [1, 1, 2, 2, 4, 4],
    "wall_time": [0.85, 0.87, 1.70, 1.72, 3.40, 3.38],
    "run":       [1, 2, 1, 2, 1, 2],
    "status":    ["ok"] * 6,
})
bench_b = {
    "config": BenchConfig("Experiment B - optimized", "2.0"),
    "metadata": {
        "description": "Experiment B - optimized (faster)",
        "version": "2.0",
        "host": "node-02",
        "cpu": "AMD EPYC 9654",
    },
    "dataframe": df_b,
}
with open("bench_b.pkl", "wb") as f:
    pickle.dump(bench_b, f)

print("bench_a.pkl e bench_b.pkl criados.")


# ---------------------------------------------------------------------------
# Monta contexto de cada experimento
# ---------------------------------------------------------------------------
def build_context(label: str, pkl_path: str) -> str:
    bench = utils.load_spinner_bench(Path(pkl_path))
    config = bench["config"].model_dump()
    metadata = bench["metadata"]
    df = bench["dataframe"]
    return (
        f"=== Experiment {label}: {pkl_path} ===\n"
        f"Config:\n{json.dumps(config, default=str)}\n"
        f"Metadata:\n{json.dumps(metadata, default=str)}\n"
        f"DataFrame:\n{df.to_string(index=False)}\n"
    )


ctx_a = build_context("A", "bench_a.pkl")
ctx_b = build_context("B", "bench_b.pkl")

compare_prompt = (
    "Please compare the two HPC experiments below.\n"
    "Highlight differences in configuration, metadata, and key performance metrics "
    "(mean wall_time per param value).\n"
    "Point out which experiment performed better and why.\n\n"
    f"{ctx_a}\n{ctx_b}"
)

system_prompt = (
    "You are the Spinner Chat, a bot that helps spinner users to analyse their HPC experiments. "
    "Please prefer short, direct responses."
)

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user",   "content": compare_prompt},
]

# ---------------------------------------------------------------------------
# Chama o LLM
# ---------------------------------------------------------------------------
print(f"\nProvider : {utils._provider}")
print(f"Model    : {utils.deployment}")
print("Enviando comparacao para o LLM...\n")
print("=" * 60)

completion = utils.client.chat.completions.create(
    model=utils.deployment,
    messages=messages,
    temperature=0,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
    stop=None,
    stream=False,
)

print(completion.choices[0].message.content)
print("=" * 60)
