# optiflux/config.py
import os
from dotenv import load_dotenv

from .utils.file_utils import ensure_dir_exists,data_dir_default


def load_config(env='dev'):
    """加载环境配置"""
    # 加载环境变量优先级：.env.<env> > .env
    loaded = load_dotenv(f".env.{env}") or load_dotenv(".env")
    
    return {
        # 基础配置
        "SERVER_HOST": os.getenv("SERVER_HOST", "0.0.0.0"),
        "SERVER_PORT": int(os.getenv("SERVER_PORT", "8912")),
        
        # 环境目录
        "ENV_DIRS": {
            "dev": os.getenv("DEV_ENV_DIR",os.path.join(os.getcwd(),"dev")),
            "preprod": os.getenv("PREPROD_ENV_DIR",os.path.join(os.getcwd(),"preprod")),
            "prod": os.getenv("PROD_ENV_DIR",os.path.join(os.getcwd(),"prod"))
        },
        # 日志配置
        "LOG_DIR": os.getenv("LOG_DIR",os.path.join(data_dir_default(),"logs")),
        
        # Flask 开发配置
        "FLASK_DEBUG": os.getenv("FLASK_DEBUG", "true").lower() == "true",
        
        # Gunicorn 生产配置
        "GUNICORN_WORKERS": int(os.getenv("GUNICORN_WORKERS", 4)),
        "GUNICORN_TIMEOUT": int(os.getenv("GUNICORN_TIMEOUT", 30)),
        "GUNICORN_LOGLEVEL": os.getenv("GUNICORN_LOGLEVEL", "info")
    }

# 全局配置对象
_config = None

def get_config(env='dev'):
    global _config
    if _config is None:
        _config = load_config(env)
    return _config

base_config = get_config("prod")

ENV_DIRS=base_config["ENV_DIRS"]
LOG_DIR=base_config["LOG_DIR"]

base_paths=[ENV_DIRS["dev"],ENV_DIRS["preprod"],ENV_DIRS["prod"],LOG_DIR]
for bp in base_paths:
    ensure_dir_exists(bp)
    
    
defu_logs_fnames = [
            "recom_errors.log",
            "reward_errors.log",
            "recom_debugs.log",
            "reward_debugs.log",
        ]

# Logs
# 创建一个空文件
for fname in defu_logs_fnames:
    log_file = os.path.join(LOG_DIR, fname)
    # Open the file in write mode
    if not os.path.exists(log_file):
        open(log_file, "a").close()  # 以追加模式打开并立即关闭