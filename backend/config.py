import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"


def load_config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))

