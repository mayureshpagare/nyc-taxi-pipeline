from pathlib import Path
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = PROJECT_ROOT / "config" / "pipeline.yaml"

def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def layer_path(config: dict, layer:str) -> Path:
    paths = config["paths"]
    return PROJECT_ROOT / paths["lake_root"] / paths[layer]