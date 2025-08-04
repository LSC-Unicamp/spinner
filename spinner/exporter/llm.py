import json
import os
import pickle
from typing import Literal, Optional, List, Dict, Any
from pathlib import Path

from pydantic import BaseModel

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.deepseek import DeepSeekProvider

import pandas as pd
import numpy as np
import rich

# class CityLocation(BaseModel):
#     city: str
#     country: str


# ollama_model = OpenAIModel(
#     model_name='qwen2.5-coder:32b', provider=OpenAIProvider(base_url='http://enqii.lsc.ic.unicamp.br:11434/v1')
# )
# agent = Agent(ollama_model, output_type=CityLocation)

# result = agent.run_sync('Where were the olympics held in 2012?')
# print(result.output)
# #> city='London' country='United Kingdom'
# print(result.usage())
# #> Usage(requests=1, request_tokens=57, response_tokens=8, total_tokens=65)

def load_data(bench_data: Path) -> tuple[pd.DataFrame, dict]:
    try:
        with bench_data.open("rb") as data:
            bench_dict = pickle.load(data)
            metadata = bench_dict["metadata"]
            df = pd.DataFrame(bench_dict["dataframe"]).T.drop_duplicates().T
            df.rename(columns={'lookups': 'lookup_size'}, inplace=True)
            return df, metadata
    except Exception as e:
        print(f"Error trying to open file {bench_data}: {e}")

def process_df(all_df):
    all_df['sys'] = all_df['name'].apply(lambda x: 'mpi' if 'mpi' in x else 'mpp')
    all_df['accl'] = all_df['version'].apply(lambda x: 'h100' if 'h100' in x else 'mi300a')
    if {'dlist', 'workers'} in set(all_df.columns):
        all_df['devices_per_worker'] = all_df['dlist'].apply(lambda x: len(x.split(',')))
        all_df['devices'] = all_df['workers'] * all_df['devices_per_worker']
    elif 'workers' in all_df.columns:
        all_df['devices'] = all_df['workers'] * 1
    else:
        all_df['devices'] = 10
    all_df['sched'] = all_df['version'].apply(lambda x: 'sched' if 'sched' in x else 'no')
    all_df['impl'] = all_df['version'].apply(lambda x: 'mpich' if 'mpich' in x else 'ompi')
    if 'hht' in all_df.columns:
        # all_df['hht'] = all_df['hht'].fillna(10)
        # all_df['hht'] = all_df['hht'].astype(int)
        # all_df['hht'] =  all_df['hht'].apply(lambda x: x if type(x) != np.nan else 10)
        all_df['hht'] = 10
    else:
        all_df['hht'] = 10
    if 'radix' not in all_df.columns:
        all_df['radix'] = 5
    all_df.drop(columns=['name', 'kernel',  'hosts', 'time'], inplace=True)
    return all_df


# Load your DataFrame
bench_path = Path("/home/cl3t0/workspace/ompc/sscad-2025/paper/pkl/ws_mpich_stencil_10x10_h100_290725.pkl")
df, _ = load_data(bench_path)

df = process_df(df)

agg_all_df = df.groupby(by=['sys', 'accl', 'devices', 'hht', 'type', 'radix', 'output', 'size', 'total_flops', 'total_tasks', 'sched', 'impl']).agg(
    runtime_mean=('wall_time', 'mean'),
    runtime_std=('wall_time', 'std')
).reset_index()

agg_all_df['tflops_per_sec'] = agg_all_df['total_flops'] * np.pow(1/10, 12) / agg_all_df['runtime_mean']
agg_all_df['flops_per_task'] = agg_all_df['total_flops'] / agg_all_df['total_tasks']
agg_all_df_max_flops_per_device = agg_all_df.groupby(
    by=['accl', 'devices', 'hht', 'type', 'radix', 'output', 'sched', 'impl'], as_index=False
)['tflops_per_sec'].max()
agg_all_df_max_flops_per_device.rename(columns={'tflops_per_sec': 'max_tflops_per_sec'}, inplace=True)
agg_all_df = agg_all_df.merge(agg_all_df_max_flops_per_device, on=['accl', 'devices', 'hht', 'type', 'radix', 'output', 'sched', 'impl'])
agg_all_df['efficiency'] = agg_all_df['tflops_per_sec'] * 100 / agg_all_df['max_tflops_per_sec']
agg_all_df['task_granularity'] = agg_all_df['runtime_mean'] * agg_all_df['devices'] * np.pow(10, 3) / agg_all_df['total_tasks']

agg_all_df['config'] = (
    agg_all_df['sys'].str.upper() + "-" + agg_all_df['accl'].str.upper() + "-" + agg_all_df['impl'].str.upper() + "-" + agg_all_df['sched'].str.upper()
)

# Define schema of VegaLite spec (simplified for example)
class VegaLiteSpec(BaseModel):
    vega_schema: str
    description: Optional[str]
    mark: str
    encoding: Dict[str, Any]
    data: Dict[Literal["values"], List[dict]]

# Prepare the data as dicts for VegaLite
df_filtered = agg_all_df[['config', 'devices', 'runtime_mean']].query('devices % 2 == 0')

data_values = df_filtered.to_markdown(index=False)

# Sample display
print("DataFrame Preview:")
print(df_filtered.head())

system_prompt = (
    "You are a data analyst. Generate only a valid VegaLite v5 JSON spec that plots the data passed to you. "
    "Do not include explanations or extra text. Use the schema 'https://vega.github.io/schema/vega-lite/v5.json'. "
    "Assume the data and coluns described by the user are in the user-provided dataset."
)

ollama_model = OpenAIModel(
    model_name='qwen3:32b',
    provider=OpenAIProvider(base_url='http://enqii.lsc.ic.unicamp.br:11434/v1')
)
agent = Agent(
    ollama_model,
    system_prompt=system_prompt,
    output_type=VegaLiteSpec,
    tools=[],
    toolsets=[],
    retries=4
)

# Instruction: what kind of chart do you want?
# instruction = "Plot a bar chart showing average salary per department"
instruction = (
    "Plot a lineplot showing the runtime_mean (y) per devices (x) using the config as a hue. "
    "Please, use only the values in the markdown dataset."
    "the dataset is the following:\n"
    f"{data_values}"
    "You also need to pass the data in the json file using the \"data\" field of vega-lite, the vega-lite compiler does not have it"
)
# print(data_values)
# print(system_prompt)

# Run the agent
response = agent.run_sync(
    instruction,
)

# Print and save result
rich.print("VegaLite Spec:")
rich.print(json.dumps(response.output.model_dump(), indent=2))

# Optionally save to file
with open("chart.json", "w") as f:
    json.dump(response.output.model_dump(), f, indent=2)
