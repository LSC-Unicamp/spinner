# io-testbed

![Logo](spinner.svg)

## Setting up environment

```sh
python3 -m virtualenv .venv
pip install -r spinner/requirements.txt
source .venv/bin/activate
```

## Running
```sh
python3 spinner/main.py -b F -r T -c spinner/bench_settings.json -e F
```
