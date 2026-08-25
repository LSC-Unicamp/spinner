import json
import os
import pickle
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import dotenv
import numpy as np
import pandas as pd
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from openai import AzureOpenAI, OpenAI
from pydantic import BaseModel, Field

dotenv.load_dotenv()

# ---------------------------------------------------------------------------
# Provider selection — set LLM_PROVIDER in your .env
#
#   Ollama cloud (free):
#     LLM_PROVIDER=ollama
#     OLLAMA_BASE_URL=https://ollama.com/api     # cloud
#     OLLAMA_MODEL=gemma4:31b
#     OLLAMA_API_KEY=<your ollama key>
#
#   Ollama local (no key needed):
#     LLM_PROVIDER=ollama
#     OLLAMA_BASE_URL=http://localhost:11434/v1
#     OLLAMA_MODEL=llama3.2
#
#   OpenAI:
#     LLM_PROVIDER=openai
#     OPENAI_API_KEY=sk-...
#     OPENAI_MODEL=gpt-4o
#
#   Azure OpenAI (original default):
#     LLM_PROVIDER=azure  (or unset)
#     AZURE_ENDPOINT_URL=...
#     AZURE_DEPLOYMENT_NAME=...
#     AZURE_OPENAI_API_KEY=...
#     AZURE_API_VERSION=2025-01-01-preview
# ---------------------------------------------------------------------------

_provider = os.getenv("LLM_PROVIDER", "azure").lower()
_ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

# Detect Ollama cloud vs local based on the base URL
_ollama_is_cloud = _ollama_base_url.startswith("https://ollama.com")

if _provider == "ollama" and _ollama_is_cloud:
    # Ollama cloud uses its own native HTTP API (not OpenAI-compatible)
    deployment = os.getenv("OLLAMA_MODEL", "gemma4:31b")
    _ollama_api_key = os.getenv("OLLAMA_API_KEY", "")

    class _OllamaCloudClient:
        """Thin wrapper that mimics the openai client interface for Ollama cloud."""

        class _Completions:
            def __init__(self, model, api_key):
                self._model = model
                self._api_key = api_key

            def create(self, model, messages, temperature=0, top_p=1,
                       frequency_penalty=0, presence_penalty=0, stop=None, stream=False, **kwargs):
                payload = json.dumps({
                    "model": model,
                    "messages": messages,
                    "stream": False,
                }).encode()

                last_err = None
                for attempt in range(3):
                    req = urllib.request.Request(
                        "https://ollama.com/api/chat",
                        data=payload,
                        headers={
                            "Authorization": f"Bearer {self._api_key}",
                            "Content-Type": "application/json",
                        },
                        method="POST",
                    )
                    try:
                        with urllib.request.urlopen(req, timeout=120) as r:
                            data = json.loads(r.read())
                        break  # success
                    except urllib.error.HTTPError as e:
                        last_err = e
                        if e.code in (429, 503):
                            import time
                            wait = 3 * (attempt + 1)
                            print(f"Ollama cloud returned {e.code}, retrying in {wait}s...")
                            time.sleep(wait)
                        else:
                            raise
                else:
                    raise last_err

                content = data["message"]["content"]

                # Return an object that matches the openai response shape
                class _Choice:
                    class _Message:
                        pass
                    message = _Message()

                choice = _Choice()
                choice.message.content = content

                class _Response:
                    choices = [choice]

                return _Response()

        class _Chat:
            def __init__(self, model, api_key):
                self.completions = _OllamaCloudClient._Completions(model, api_key)

        def __init__(self, model, api_key):
            self.chat = _OllamaCloudClient._Chat(model, api_key)

    client = _OllamaCloudClient(deployment, _ollama_api_key)

elif _provider == "ollama":
    # Local Ollama — uses OpenAI-compatible /v1 endpoint
    deployment = os.getenv("OLLAMA_MODEL", "llama3.2")
    client = OpenAI(
        base_url=_ollama_base_url,
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
    )
elif _provider == "openai":
    deployment = os.getenv("OPENAI_MODEL", "gpt-4o")
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY", "PASTE_YOUR_OPENAI_KEY"),
    )
else:  # azure (default)
    deployment = os.getenv("AZURE_DEPLOYMENT_NAME", "PASTE_YOUR_DEPLOYMENT_NAME")
    client = AzureOpenAI(
        azure_endpoint=os.getenv("AZURE_ENDPOINT_URL", "PASTE_YOUR_ENDPOINT_URL"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "PASTE_YOUR_AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2025-01-01-preview"),
    )


def build_langchain_model():
    if _provider == "ollama" and _ollama_is_cloud:
        raise RuntimeError(
            "LangChain chat integration is not supported with Ollama cloud. "
            "Use local Ollama, OpenAI, or Azure OpenAI."
        )
    if _provider == "ollama":
        return ChatOpenAI(
            model=deployment,
            base_url=_ollama_base_url,
            api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
            temperature=0,
        )
    if _provider == "openai":
        return ChatOpenAI(
            model=deployment,
            api_key=os.getenv("OPENAI_API_KEY", "PASTE_YOUR_OPENAI_KEY"),
            temperature=0,
        )
    return AzureChatOpenAI(
        azure_deployment=deployment,
        azure_endpoint=os.getenv("AZURE_ENDPOINT_URL", "PASTE_YOUR_ENDPOINT_URL"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY", "PASTE_YOUR_AZURE_OPENAI_KEY"),
        api_version=os.getenv("AZURE_API_VERSION", "2025-01-01-preview"),
        temperature=0,
    )

class VegaLiteLayer(BaseModel):
    mark: Dict[str, Any] | str
    encoding: Dict[str, Any] | str

class VegaLiteSpec(BaseModel):
    schema_: str = Field(..., alias="$schema")
    description: Optional[str]
    layer: List[VegaLiteLayer]
    data: Dict[Literal["values"], List[dict]]

class _DictConfig:
    """Fallback config class for .pkl files created outside spinner."""

    def __init__(self, data: dict):
        self._data = data

    def model_dump(self):
        return self._data


class _FlexUnpickler(pickle.Unpickler):
    """Resolve config classes that were pickled from __main__ or external modules."""

    # Names that should map to _DictConfig regardless of origin module
    _ALIASES = {"BenchConfig", "_DictConfig", "FakeConfig"}

    def find_class(self, module, name):
        if name in self._ALIASES:
            return _DictConfig
        try:
            return super().find_class(module, name)
        except (AttributeError, ModuleNotFoundError):
            pass
        # Walk sys.modules as last resort
        for mod in sys.modules.values():
            obj = getattr(mod, name, None)
            if obj is not None:
                return obj
        return super().find_class(module, name)


def load_spinner_bench(bench_data: Path) -> tuple[pd.DataFrame, dict]:
    try:
        with bench_data.open("rb") as data:
            bench_dict = _FlexUnpickler(data).load()
            return bench_dict
    except Exception as e:
        print(f"Error trying to open file {bench_data}: {e}")

def vegalite_to_pdf(vega_lite_json: str, filepath: Path):
    pdf_data = vlc.vegalite_to_pdf(vega_lite_json)
    with filepath.open("wb") as file:
        file.write(pdf_data)
