import os
import json
import pickle
from pathlib import Path
from typing import Literal, Optional, List, Dict, Any

import rich
from openai import AzureOpenAI
from pydantic import BaseModel, Field

import vl_convert as vlc
import pandas as pd
import numpy as np

import dotenv

dotenv.load_dotenv()

endpoint = os.getenv("AZURE_ENDPOINT_URL", "PASTE_YOUR_ENDPOINT_URL")
deployment = os.getenv("AZURE_DEPLOYMENT_NAME", "PASTE_YOUR_DEPLOYMENT_NAME")
subscription_key = os.getenv("AZURE_OPENAI_API_KEY", "PASTE_YOUR_AZURE_OPENAI_KEY")
api_version = os.getenv("AZURE_API_VERSION", "2025-01-01-preview")

# Initialize Azure OpenAI client with key-based authentication
client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=subscription_key,
    api_version=api_version,
)

class VegaLiteLayer(BaseModel):
    mark: Dict[str, Any] | str
    encoding: Dict[str, Any] | str

class VegaLiteSpec(BaseModel):
    schema_: str = Field(..., alias="$schema")
    description: Optional[str]
    layer: List[VegaLiteLayer]
    data: Dict[Literal["values"], List[dict]]

def load_spinner_bench(bench_data: Path) -> tuple[pd.DataFrame, dict]:
    try:
        with bench_data.open("rb") as data:
            bench_dict = pickle.load(data)
            return bench_dict
    except Exception as e:
        print(f"Error trying to open file {bench_data}: {e}")

def vegalite_to_pdf(vega_lite_json: str, filepath: Path):
    pdf_data = vlc.vegalite_to_pdf(vega_lite_json)
    with filepath.open("wb") as file:
        file.write(pdf_data)
