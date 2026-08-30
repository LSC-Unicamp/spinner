import json
import os
import pickle
from typing import Literal, Optional, List, Dict, Any
from pathlib import Path

import pandas as pd
import numpy as np
import vl_convert as vlc
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_data(bench_data: Path) -> tuple[pd.DataFrame, dict]:
    try:
        with bench_data.open("rb") as data:
            bench_dict = pickle.load(data)
            metadata = bench_dict["metadata"]
            df = pd.DataFrame(bench_dict["dataframe"]).T.drop_duplicates().T
            df.rename(columns={"lookups": "lookup_size"}, inplace=True)
            return df, metadata
    except Exception as e:
        print(f"Error trying to open file {bench_data}: {e}")


def process_df(all_df: pd.DataFrame) -> pd.DataFrame:
    all_df["sys"] = all_df["name"].apply(lambda x: "mpi" if "mpi" in x else "mpp")
    all_df["accl"] = all_df["version"].apply(lambda x: "h100" if "h100" in x else "mi300a")
    if {"dlist", "workers"}.issubset(set(all_df.columns)):
        all_df["devices_per_worker"] = all_df["dlist"].apply(lambda x: len(x.split(",")))
        all_df["devices"] = all_df["workers"] * all_df["devices_per_worker"]
    elif "workers" in all_df.columns:
        all_df["devices"] = all_df["workers"] * 1
    else:
        all_df["devices"] = 10
    all_df["sched"] = all_df["version"].apply(lambda x: "sched" if "sched" in x else "no")
    all_df["impl"] = all_df["version"].apply(lambda x: "mpich" if "mpich" in x else "ompi")
    all_df["hht"] = 10
    if "radix" not in all_df.columns:
        all_df["radix"] = 5
    all_df.drop(columns=["name", "kernel", "hosts", "time"], inplace=True)
    return all_df


# ---------------------------------------------------------------------------
# VegaLite output schema
# ---------------------------------------------------------------------------

class VegaLiteSpec(BaseModel):
    vega_schema: str
    description: Optional[str]
    mark: str
    encoding: Dict[str, Any]
    data: Dict[Literal["values"], List[dict]]


# ---------------------------------------------------------------------------
# LangChain / LangGraph deep agent
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a VegaLite expert that writes Vega Lite JSONs. "
    "Do not include explanations or extra text. "
    "Use the schema 'https://vega.github.io/schema/vega-lite/v5.json'. "
    "Assume the data and columns described by the user are in the user-provided dataset. "
    "Return only a valid JSON object — no markdown fences, no prose."
)


def _build_llm() -> ChatOpenAI:
    """Return a LangChain ChatOpenAI pointed at the local Ollama endpoint."""
    return ChatOpenAI(
        model="qwen2.5-coder:14b",
        base_url="http://enqii.lsc.ic.unicamp.br:11434/v1",
        api_key="ollama",
        temperature=0,
    )


def run_vegalite_agent(data_markdown: str, instruction: str) -> dict:
    """
    Run a LangGraph ReAct deep agent that generates a VegaLite JSON spec.

    The agent receives the dataset as context and the user instruction,
    then iterates (deep-agent loop) until it produces a valid JSON spec.

    Returns the parsed VegaLite spec as a dict.
    """
    llm = _build_llm()
    memory = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=[],
        checkpointer=memory,
        state_modifier=SYSTEM_PROMPT,
    )

    full_instruction = (
        f"{instruction}\n"
        "The dataset is the following:\n"
        f"{data_markdown}"
    )

    config = {"configurable": {"thread_id": "vegalite-agent"}}
    result = agent.invoke(
        {"messages": [HumanMessage(content=full_instruction)]},
        config=config,
    )

    raw_json = result["messages"][-1].content

    if raw_json.strip().startswith("```"):
        raw_json = raw_json.strip().lstrip("`").split("\n", 1)[-1]
        raw_json = raw_json.rsplit("```", 1)[0]

    return json.loads(raw_json)


# ---------------------------------------------------------------------------
# Entry point (example usage)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    bench_path = Path(
        "/home/cl3t0/workspace/ompc/sscad-2025/paper/pkl/ws_mpich_stencil_10x10_h100_290725.pkl"
    )
    df, _ = load_data(bench_path)
    df = process_df(df)

    agg = df.groupby(
        by=["sys", "accl", "devices", "hht", "type", "radix", "output",
            "size", "total_flops", "total_tasks", "sched", "impl"]
    ).agg(
        runtime_mean=("wall_time", "mean"),
        runtime_std=("wall_time", "std"),
    ).reset_index()

    agg["tflops_per_sec"] = agg["total_flops"] * np.pow(1 / 10, 12) / agg["runtime_mean"]
    agg["config"] = (
        agg["sys"].str.upper() + "-" + agg["accl"].str.upper()
        + "-" + agg["impl"].str.upper() + "-" + agg["sched"].str.upper()
    )

    df_filtered = agg.query("size == 20 & output == 16")[["config", "devices", "runtime_mean"]]
    data_markdown = df_filtered.to_markdown(index=False)

    print("DataFrame Preview:")
    print(df_filtered.head())

    instruction = (
        "Write a vega-lite V5 JSON that plots a lineplot showing the runtime_mean (y) "
        "per devices (x) using the config as a hue.\n"
        "Please use the colors green and purple and use markers in the lines on the plot.\n"
        "Please replace the config values in the data field to MPI-H100 or MPP-H100, "
        "and in the legend use Platform instead of config."
    )

    spec = run_vegalite_agent(data_markdown, instruction)

    with open("chart.json", "w") as f:
        json.dump(spec, f, indent=2)

    pdf_data = vlc.vegalite_to_pdf(vl_spec=spec)
    with open("chart.pdf", "wb") as f:
        f.write(pdf_data)
