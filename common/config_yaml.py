import os
import yaml
from dataclasses import dataclass
from typing import Any, Dict

@dataclass
class LoadedYaml:
    data: Dict[str, Any]
    mtime: float

def load_yaml(path: str) -> LoadedYaml:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    mtime = os.path.getmtime(path)
    return LoadedYaml(data=data, mtime=mtime)
