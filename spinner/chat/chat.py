# spinner/chat.py

from pathlib import Path
import json

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


def chat_with_data(pkl_path: str) -> None:

    spinner_bench = utils.load_spinner_bench(Path(pkl_path))

    experiment_config = spinner_bench['config'].model_dump()
    experiment_metadata = spinner_bench['metadata']
    experiment_dataframe = spinner_bench['dataframe']

    experiment_setup = (
        f"The experimental .pkl file is {pkl_path}.\n"
        f"The experiment configure is\n{json.dumps(experiment_config, default=str)}\n"
        f"The experiment metadata is \n{json.dumps(experiment_metadata, default=str)}\n"
        f"Following is the header of the experiment_dataframe:\n{experiment_dataframe.head(30)}\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {'role': "user", "content": experiment_setup}
    ]

    # Example: format data for prompting
    # summary = summarize_data(data)

    print("🧠 Welcome to Spinner Chat! You can now ask questions about your benchmark data.\n")
    print("Try: 'Which experiment had the best performance?', or 'Plot the speedup over time'.\n")

    while True:
        try:
            question = input("💬 > ")
            if question.strip().lower() in {"exit", "quit"}:
                print("👋 Exiting chat.")
                break

            # Example call to OpenAI
            # response = openai.ChatCompletion.create(
            #     model="gpt-4o",
            #     messages=[
            #         {"role": "system", "content": "You are a benchmark analysis assistant."},
            #         {"role": "user", "content": f"Here is the data summary:\n{summary}"},
            #         {"role": "user", "content": question},
            #     ],
            # )
            # print("🤖", response["choices"][0]["message"]["content"].strip())

            messages.append({"role": "user", "content": question})

            completion = utils.client.chat.completions.create(
                model=utils.deployment,
                messages=messages,
                temperature=0,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None,
                stream=False
            )

            response = completion.choices[0].message.content
            print("🤖", response)

            messages.append({"role": "assistant", "content": response})

            # print("🤖", "Chat will be available soon!")
        except KeyboardInterrupt:
            print("\n👋 Exiting chat.")
            break

def summarize_data(data) -> str:
    # Reduce the benchmark data into something small enough for prompting
    return str(data)[:2000]  # naive, but works for now
