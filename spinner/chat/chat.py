# spinner/chat.py

import json
from pathlib import Path
from typing import Callable

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from . import utils

system_prompt = """
You are the Spinner Chat, a bot that helps spinner users to analyse their HPC experiments.
The experiments are executed first using the spinner run command, it reads the spinner yaml file
with the experimental configuration (application commands, benchmark parameters) and run the benchmarks.
Then with the .pkl file that stores the experiment metadata, config, and results (a pandas dataframe),
you help the user to get informations from the metadata and config about the experimental setup.
You also helps with data analysis on the experimental results dataframe.
Please prefer short responses and you not need to explain spinner stuff all the time.
"""

_COMPARE_HELP = (
    "Usage: /compare <path/to/first.pkl> <path/to/second.pkl>\n"
    "Loads both experiments and asks the LLM to compare them."
)


def _build_experiment_context(label: str, pkl_path: str) -> str:
    """Return a text block describing one experiment for use in a comparison prompt."""
    bench = utils.load_spinner_bench(Path(pkl_path))
    if bench is None:
        return f"[{label}] Could not load {pkl_path}.\n"
    config = bench['config'].model_dump()
    metadata = bench['metadata']
    df = bench['dataframe']
    return (
        f"=== Experiment {label}: {pkl_path} ===\n"
        f"Config:\n{json.dumps(config, default=str)}\n"
        f"Metadata:\n{json.dumps(metadata, default=str)}\n"
        f"DataFrame head (30 rows):\n{df.head(30)}\n"
    )


def _build_experiment_setup(pkl_path: str) -> str:
    spinner_bench = utils.load_spinner_bench(Path(pkl_path))
    experiment_config = spinner_bench["config"].model_dump()
    experiment_metadata = spinner_bench["metadata"]
    experiment_dataframe = spinner_bench["dataframe"]
    return (
        f"The experimental .pkl file is {pkl_path}.\n"
        f"The experiment configure is\n{json.dumps(experiment_config, default=str)}\n"
        f"The experiment metadata is \n{json.dumps(experiment_metadata, default=str)}\n"
        f"Following is the header of the experiment_dataframe:\n"
        f"{experiment_dataframe.head(30)}\n"
    )


def _build_tools(pkl_path: str) -> list[Callable]:
    @tool
    def experiment_summary() -> str:
        """Return the current experiment configuration, metadata, and dataframe preview."""
        return _build_experiment_setup(pkl_path)

    @tool
    def dataframe_schema() -> str:
        """Return dataframe columns, shape, and dtypes for the current experiment."""
        spinner_bench = utils.load_spinner_bench(Path(pkl_path))
        experiment_dataframe = spinner_bench["dataframe"]
        return (
            f"Columns: {list(experiment_dataframe.columns)}\n"
            f"Shape: {experiment_dataframe.shape}\n"
            f"Dtypes:\n{experiment_dataframe.dtypes.to_string()}"
        )

    @tool
    def compare_experiments(other_path: str) -> str:
        """Compare the current experiment with another .pkl experiment file path."""
        if not other_path.strip():
            return _COMPARE_HELP
        return (
            "Please compare the two HPC experiments below.\n"
            "Highlight differences in configuration, metadata, and key performance metrics.\n"
            "Point out which experiment performed better and why.\n\n"
            f"{_build_experiment_context('A', pkl_path)}\n"
            f"{_build_experiment_context('B', other_path.strip())}"
        )

    return [experiment_summary, dataframe_schema, compare_experiments]


def _to_langchain_messages(messages: list[dict]):
    converted = []
    for message in messages:
        role = message["role"]
        content = message["content"]
        if role == "system":
            converted.append(SystemMessage(content=content))
        elif role == "assistant":
            converted.append(AIMessage(content=content))
        elif role == "tool":
            converted.append(
                ToolMessage(content=content, tool_call_id=message["tool_call_id"])
            )
        else:
            converted.append(HumanMessage(content=content))
    return converted


def _run_agent(llm, tools: list[Callable], messages: list[dict], prompt: str) -> str:
    bound_llm = llm.bind_tools(tools)
    tool_map = {tool.name: tool for tool in tools}
    conversation = [
        *_to_langchain_messages(messages),
        HumanMessage(content=prompt),
    ]
    response = bound_llm.invoke(conversation)

    while response.tool_calls:
        conversation.append(response)
        for tool_call in response.tool_calls:
            tool_instance = tool_map[tool_call["name"]]
            tool_result = tool_instance.invoke(tool_call["args"])
            conversation.append(
                ToolMessage(content=tool_result, tool_call_id=tool_call["id"])
            )
        response = bound_llm.invoke(conversation)

    return response.content if isinstance(response.content, str) else str(response.content)


def _handle_compare(parts: list[str], messages: list[dict], llm, tools: list[Callable]) -> None:
    """Handle the /compare command via the LangChain model."""
    if len(parts) != 3:
        print(_COMPARE_HELP)
        return

    _, _, pkl_b = parts
    output = _run_agent(
        llm,
        tools,
        messages,
        f"Use the compare_experiments tool with this exact path: {pkl_b}",
    )
    print("Bot:", output)
    messages.append({"role": "user", "content": " ".join(parts)})
    messages.append({"role": "assistant", "content": output})


def chat_with_data(pkl_path: str) -> None:
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": _build_experiment_setup(pkl_path)},
    ]
    llm = utils.build_langchain_model()
    tools = _build_tools(pkl_path)

    print("Welcome to Spinner Chat! You can now ask questions about your benchmark data.\n")
    print("Try: 'Which experiment had the best performance?', or 'Plot the speedup over time'.\n")
    print("Special commands:\n  /compare <first.pkl> <second.pkl>  — compare two experiments\n")

    while True:
        try:
            question = input("> ")
            stripped = question.strip()

            if stripped.lower() in {"exit", "quit"}:
                print("Exiting chat.")
                break

            if stripped.startswith("/compare"):
                _handle_compare(stripped.split(), messages, llm, tools)
                continue

            if stripped.lower() in {"/help", "help"}:
                print(_COMPARE_HELP)
                continue

            output = _run_agent(llm, tools, messages, stripped)
            print("Bot:", output)

            messages.append({"role": "user", "content": stripped})
            messages.append({"role": "assistant", "content": output})

        except KeyboardInterrupt:
            print("\nExiting chat.")
            break


def summarize_data(data) -> str:
    # Reduce the benchmark data into something small enough for prompting
    return str(data)[:2000]  # naive, but works for now
