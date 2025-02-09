import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file {config_path} not found")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)