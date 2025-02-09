import os
import json

from ..config import ENV_DIRS

def ensure_env_dir(env):
    """确保环境目录存在"""
    env_dir = ENV_DIRS.get(env)
    if not env_dir:
        raise ValueError(f"Invalid environment: {env}")
    os.makedirs(env_dir, exist_ok=True)
    return env_dir

def load_or_initialize_config(config_path):
    """
    加载配置文件，如果文件不存在或内容无效，则初始化默认配置。
    """
    default_config = {
        "current_version": "v1.0.0",
        "services": {
            "recomserver": [
                {
                    "port": 8080,
                    "ip": "127.0.0.1",
                    "status": "stopped",
                    "pid": None
                }
            ],
            "rewardserver": [
                {
                    "port": 9090,
                    "ip": "127.0.0.1",
                    "status": "stopped",
                    "pid": None
                }
            ]
        }
    }

    if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
        # 如果文件不存在或内容为空，生成默认配置
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config

    try:
        # 尝试读取配置文件
        with open(config_path, "r") as f:
            config = json.load(f)
        # 确保配置文件包含必要的字段
        if "services" not in config:
            config["services"] = default_config["services"]
        return config
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"Invalid config file: {e}. Generating a new one...")
        with open(config_path, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config