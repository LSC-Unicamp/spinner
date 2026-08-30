import os
import json
import pickle
from pathlib import Path
from typing import Literal, Optional, List, Dict, Any

import vl_convert as vlc
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from langchain_openai import AzureChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


class VegaLiteLayer(BaseModel):
    mark: Dict[str, Any] | str
    encoding: Dict[str, Any] | str


class VegaLiteSpec(BaseModel):
    schema_: str = Field(..., alias="$schema")
    description: Optional[str]
    layer: List[VegaLiteLayer]
    data: Dict[Literal["values"], List[dict]]


def _build_llm() -> AzureChatOpenAI:
    return AzureChatOpenAI(
        azure_endpoint=os.getenv("ENDPOINT_URL", "PASTE_YOUR_ENDPOINT_URL"),
        azure_deployment=os.getenv("DEPLOYMENT_NAME", "PASTE_YOUR_DEPLOYMENT_NAME"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "PASTE_YOUR_AZURE_OPENAI_KEY"),
        api_version="2024-05-01-preview",
        temperature=0,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )


def load_spinner_bench(bench_data: Path) -> dict:
    try:
        with bench_data.open("rb") as data:
            return pickle.load(data)
    except Exception as e:
        print(f"Error trying to open file {bench_data}: {e}")


def vegalite_to_pdf(vega_lite_json: str, filepath: Path):
    pdf_data = vlc.vegalite_to_pdf(vega_lite_json)
    with filepath.open("wb") as file:
        file.write(pdf_data)


def run_ai_exporter(spinner_pkl_path: Path, figure_path: Path):
    system_prompt = (
        "You are a VegaLite expert that write Vega Lite JSONs.\n"
        "Do not include explanations or extra text. Use the schema 'https://vega.github.io/schema/vega-lite/v5.json'.\n"
        "When it makes sense, please use different colors and markers shapes for each line on the plot.\n"
        "Please prefer the use of Vega Lite layers instead of single view specification.\n"
        "If no hue is defined by the user the plot do not need a legend.\n"
        "If there is a user-defined hue, ensure that the plot will have legend combining both colors and labels of each plot in one label.\n"
        "Try to use Vega Scales to group the values in the hue column indicated by the user. "
        "Write the scale.domain field as a array of the values of the user-defined hue column. "
        "That field need to be written in the color and shape fields of the layer plot. "
        "Also the scale field can help with the unique labels in the platform legend.\n"
        "Assume the data and columns described by the user are in the user-provided dataset.\n"
        "Please, use only the values in the markdown dataset."
    )

    llm = _build_llm()
    spinner_bench = load_spinner_bench(spinner_pkl_path)

    apps = spinner_bench['config'].applications
    for app in apps:
        plot = apps[app].plot[0]

        instruction = (
            f"Write a Vega Lite JSON that plots a lineplot showing the {plot.y_axis} (y) per {plot.x_axis} (x) "
            f"also agregate the {plot.y_axis} (y axis) using the mean of the samples and plot the error bars of that mean.\n"
            f"The title of the figure must be '{plot.title}'\n"
            "The dataset is the following:\n"
            f"{spinner_bench['dataframe'].to_markdown(index=False)}"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=instruction),
        ]

        try:
            response = llm.invoke(messages)
            vega_lite_json = response.content
            vegalite_to_pdf(vega_lite_json, figure_path)
        except Exception as e:
            print(e)
