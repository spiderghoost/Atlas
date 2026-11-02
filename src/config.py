from pathlib import Path

import yaml


def load_config(path: str = "configs/default.yaml") -> dict:
    with open(path) as fh:
        return yaml.safe_load(fh)


def ensure_dirs(config: dict) -> None:
    results = Path(config["outputs"]["results_dir"])
    results.mkdir(parents=True, exist_ok=True)
    processed = Path(config["data"]["processed_path"]).parent
    processed.mkdir(parents=True, exist_ok=True)
