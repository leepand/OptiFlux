import argparse
import logging
import yaml
import os
from pathlib import Path
from .utils.file_utils import data_dir_default


# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


log_base_path = os.path.join(data_dir_default(), "logs")

DEFAULT_ENV_TEMPLATE = f"""# OptiFlux 环境配置
# 服务器基础配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8912

# 模型目录配置
DEV_ENV_DIR=./models/dev
PREPROD_ENV_DIR=./models/preprod
PROD_ENV_DIR=./models/prod

# 日志配置
LOG_DIR={log_base_path}

# Flask 开发模式配置
FLASK_DEBUG=true

# Gunicorn 生产模式配置
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=30
GUNICORN_LOGLEVEL=info
"""


def init_command(args):
    """处理 init 命令"""
    file_name = args.file
    force = args.force

    # 检查文件是否存在
    if Path(file_name).exists() and not force:
        print(f"⚠️  文件 {file_name} 已存在，使用 --force 覆盖")
        return

    # 写入文件
    with open(file_name, "w") as f:
        f.write(DEFAULT_ENV_TEMPLATE)

    # 创建示例目录结构
    Path("./models/dev").mkdir(parents=True, exist_ok=True)
    Path("./logs").mkdir(exist_ok=True)

    print(f"✅ 已生成默认环境文件: {file_name}")
    print("👉 请根据需求修改以下目录配置：")
    print(f"   - 开发环境模型目录: ./models/dev")
    print(f"   - 生产环境模型目录: ./models/prod")
    print(f"   - 日志目录: {log_base_path}")


def create_directories(base_dir, src_dir, utils_dir):
    """创建项目所需的目录"""
    try:
        utils_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"成功创建目录: {utils_dir}")
    except FileExistsError:
        logging.warning(f"目录 {utils_dir} 已存在")
    except PermissionError:
        logging.error(f"没有权限创建目录: {utils_dir}")
    except Exception as e:
        logging.error(f"创建目录 {utils_dir} 时出现错误: {e}")


def write_files(files):
    """写入项目所需的文件"""
    for path, content in files.items():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                f.write(content)
            logging.info(f"成功创建文件: {path}")
        except PermissionError:
            logging.error(f"没有权限创建文件: {path}")
        except Exception as e:
            logging.error(f"创建文件 {path} 时出现错误: {e}")


def create_gitignore(model_name):
    """创建 .gitignore 文件"""
    gitignore_path = Path(model_name) / ".gitignore"
    try:
        with open(gitignore_path, "w") as f:
            f.write("__pycache__/\n*.pyc\n*.pyo\n*.pyd\n")
        logging.info(f"成功创建 .gitignore 文件: {gitignore_path}")
    except PermissionError:
        logging.error(f"没有权限创建 .gitignore 文件: {gitignore_path}")
    except Exception as e:
        logging.error(f"创建 .gitignore 文件时出现错误: {e}")


# def create_project(model_name: str, version: str = "0.0"):
def create_project(args):
    """生成统一的项目结构"""
    model_name = args.name
    version = args.version
    base_dir = Path(model_name) / version
    src_dir = base_dir / "src"
    utils_dir = src_dir / "utils"

    # 创建目录
    create_directories(base_dir, src_dir, utils_dir)

    # 创建核心文件
    files = {
        base_dir / "config.yml": "# 模型配置\n",
        base_dir / "requirements.txt": "# 项目依赖\n",
        base_dir / "README.md": f"# {model_name}\n\n## 版本 {version}\n",
        src_dir / "__init__.py": "# 核心模型模块\n",
        src_dir / "decision_module.py": "# 决策模块\n",
        src_dir / "strategy_module.py": "# 策略模块\n",
        src_dir
        / "model.py": f"""from optiflux.core import BaseModel
import logging

logger = logging.getLogger("optiflux.{model_name}")

class {model_name.title()}Model(BaseModel):
    DEFAULT_CONFIG = {{
        "model_path": "models/{model_name}_v1.pt",
        "threshold": 0.5
    }}

    def load(self):
        logger.info("Loading {model_name} model...")
        # 加载模型逻辑

    def predict(self, input_data):
        logger.debug("Predicting with {model_name} model...")
        # 预测逻辑
""",
        src_dir
        / "recomserver.py": f"""from optiflux import BaseModel, ModelLibrary, make
from optiflux.utils.logx import log_recom_error, log_recom_debug
from optiflux import make

import traceback
import numpy as np
import os
import json

from utils import MODEL_ENV, VERSION


class RecomServer(BaseModel):
    def _load(self):
        self.model_name = f"{model_name}"
  
        self.model_db = make(
            f"cache/{{self.model_name}}-v{{VERSION}}",
            db_name="{model_name}.db",
            env=MODEL_ENV,
        )

    def _predict(self, items):
        uid = items.get("uid")
        request_id = items.get("request_id")
        try:
            print("business and model process")

            return items
        except:
            # 将异常堆栈信息写入错误日志文件
            error_content = [
                f"{{self.model_name}}:{{request_id}}-error",
                str(traceback.format_exc()),
            ]
            log_recom_error([error_content])
            return items

# 初始化模型库
library = ModelLibrary(
    models={{"recomserver": RecomServer}},
    #config_path="config.yml",
    #cache_dir=".prod_cache",
    size_limit=5*1024**3  # 5GB 缓存
)

# 创建 API 应用
api_config={{
        "title": "Production Recomserver API",
        "api_prefix": "",
        "enable_docs": True
    }}
api_service = create_optiflux_app(
    library,
    **api_config
)
app = api_service.app  # ✅ 关键：导出 FastAPI 实例
""",
        src_dir
        / "rewardserver.py": f"""from optiflux import BaseModel, ModelLibrary, make
from optiflux.utils.logx import log_reward_error, log_reward_debug
from optiflux.api import create_optiflux_app


import traceback
import numpy as np
import os
import json

from utils import MODEL_ENV, VERSION


class RewardServer(BaseModel):
    def _load(self):
        self.model_name = f"{model_name}"
  
        self.model_db = make(
            f"cache/{{self.model_name}}-v{{VERSION}}",
            db_name="{model_name}.db",
            env=MODEL_ENV,
        )

    def _predict(self, items):
        uid = items.get("uid")
        request_id = items.get("request_id")
        try:
            print("business and model process")

            return items
        except:
            # 将异常堆栈信息写入错误日志文件
            error_content = [
                f"{{self.model_name}}:{{request_id}}-error",
                str(traceback.format_exc()),
            ]
            log_reward_error([error_content])
            return items

# 初始化模型库
library = ModelLibrary(
    models={{"rewardserver": RewardServer}},
    #config_path="config.yml",
    #cache_dir=".prod_cache",
    size_limit=5*1024**3  # 5GB 缓存
)

# 创建 API 应用
api_config={{
        "title": "Production Rewardserver API",
        "api_prefix": "",
        "enable_docs": True
    }}
api_service = create_optiflux_app(
    library,
    **api_config
)
app = api_service.app  # ✅ 关键：导出 FastAPI 实例
""",
        utils_dir / "__init__.py": "# 工具模块\n",
        utils_dir
        / "config_loader.py": """import yaml
from pathlib import Path

def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)
""",
        utils_dir
        / "validation.py": """from typing import Any

def validate_input(data: Any) -> bool:
    return isinstance(data, (str, list, dict))
""",
    }

    # 写入文件
    write_files(files)

    # 创建 .gitignore
    create_gitignore(model_name)

    logging.info(f"项目 {model_name} 已生成，版本 {version}。")


def main():
    parser = argparse.ArgumentParser(description="Optiflux MLOps")
    subparsers = parser.add_subparsers(title="commands", dest="command")

    # init 子命令
    init_parser = subparsers.add_parser("init", help="初始化环境配置")
    init_parser.add_argument(
        "-f", "--file", default=".env", help="生成的环境文件名 (默认: .env)"
    )
    init_parser.add_argument("--force", action="store_true", help="强制覆盖已存在文件")
    init_parser.set_defaults(func=init_command)

    # 创建模型项目 子命令
    create_parser = subparsers.add_parser("create-project", help="创建模型项目")

    create_parser.add_argument(
        "--name", default="mymodel", required=True, help="模型名称"
    )
    create_parser.add_argument("--version", default="0.0", help="版本号")
    create_parser.set_defaults(func=create_project)
    # args = parser.parse_args()

    # create_project(args.name, args.version)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
