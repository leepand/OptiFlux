import argparse
import logging
import yaml
import os
from pathlib import Path
from .utils.file_utils import data_dir_default
import hashlib
import json
import requests
from datetime import datetime
import zipfile
import io

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

# SERVER_URL = "http://35.165.37.114:8913"

IGNORE_PATTERNS = [
    ".ipynb_checkpoints",  # 忽略 Jupyter Notebook 的检查点目录
    ".optiflux/index",     # 忽略索引文件
    ".optiflux",
    "servers.yaml"
]

class OptifluxClient:
    def __init__(self, repo_path, server_name=None):
        self.repo_path = repo_path
        self.git_dir = os.path.join(repo_path, ".optiflux")
        self.objects_dir = os.path.join(self.git_dir, "objects")
        self.head_path = os.path.join(self.git_dir, "HEAD")
        self.server_name = server_name
        self.server_info = self.load_server_info()
        self.session = requests.Session()
        os.makedirs(self.git_dir, exist_ok=True)
        os.makedirs(self.objects_dir, exist_ok=True)

    def load_session(self, server_name):
        """加载指定服务器的会话信息"""
        session_path = os.path.join(self.git_dir, f"session_{server_name}")
        if os.path.exists(session_path):
            with open(session_path, "r") as f:
                session_data = json.load(f)
                self.session.cookies.update(session_data.get("cookies", {}))
                self.user_id = session_data.get("user_id")
        else:
            self.user_id = None

    def save_session(self, server_name):
        """保存指定服务器的会话信息"""
        session_path = os.path.join(self.git_dir, f"session_{server_name}")
        session_data = {
            "cookies": dict(self.session.cookies),
            "user_id": self.user_id,
        }
        with open(session_path, "w") as f:
            json.dump(session_data, f)

    def login(self, username, password, server_name):
        """登录指定服务器并保存会话信息"""
        url = f"{self.get_server_url()}/login"
        try:
            response = self.session.post(
                url,
                data={"username": username, "password": password},
                headers={"Accept": "application/json"}  # 指定需要 JSON 响应
            )
            print(f"Response status code: {response.status_code}")
            print(f"Response content: {response.text}")
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get("status") == "success":
                        self.user_id = data.get("user_id")
                        self.save_session(server_name)
                        print(f"Login to {server_name} successful")
                    else:
                        print(f"Login failed: {data.get('message')}")
                except ValueError as e:
                    print(f"Failed to parse response as JSON: {e}")
            else:
                print(f"Login to {server_name} failed")
                self.user_id = None
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")


    def login2(self, username, password, server_name):
        """登录指定服务器并保存会话信息"""
        url = f"{self.get_server_url()}/login"
        response = self.session.post(
            url, data={"username": username, "password": password}
        )
        if response.status_code == 200:
            self.user_id = response.json().get("_user_id")
            self.save_session(server_name)
            print(f"Login to {server_name} successful")
        else:
            print(f"Login to {server_name} failed")
            self.user_id = None

    def load_server_info(self):
        """从配置文件加载服务器信息"""
        config_path = os.path.join(self.repo_path, "servers.yaml")
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Server configuration file not found: {config_path}"
            )

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if self.server_name:  # and self.server_name in config['servers']:
            return config["servers"][self.server_name]
        else:
            # 如果没有指定服务器名称，默认使用第一个服务器
            return list(config["servers"].values())[0]

    def get_server_url(self):
        """获取当前服务器的URL"""
        return self.server_info["url"]

    def get_api_key(self):
        """获取当前服务器的API Key"""
        return self.server_info["api_key"]

    def get_index_path(self):
        return os.path.join(self.git_dir, "index")

    def read_index(self):
        """读取索引文件"""
        index_path = self.get_index_path()
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return json.load(f)
        return {}

    def write_index(self, index):
        """写入索引文件"""
        index_path = self.get_index_path()
        with open(index_path, "w") as f:
            json.dump(index, f)

    def hash_object2(self, data):
        """生成对象的哈希值"""
        return hashlib.sha1(data.encode()).hexdigest()

    def hash_object(self, data):
        """生成对象的哈希值"""
        if isinstance(data, str):  # 如果是字符串，先编码为 bytes
            data = data.encode("utf-8")
        return hashlib.sha1(data).hexdigest()  # 直接计算哈希值

    def add(self, path):
        """添加文件到暂存区"""
        index = self.read_index()
        index["operations"] = []

        def should_ignore(file_path):
            """检查文件路径是否匹配忽略规则"""
            for pattern in IGNORE_PATTERNS:
                if pattern in file_path:
                    return True
            return False

        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if should_ignore(file_path):
                        print(f"Ignored {file_path}")
                        continue
                    try:
                        with open(file_path, "rb") as f:  # 以二进制模式读取
                            content = f.read()
                        file_hash = self.hash_object(content)

                        if file_path not in index:
                            # 文件新增
                            index[file_path] = file_hash
                            index["operations"].append(
                                {
                                    "type": "add",
                                    "file": file_path,
                                    "old_hash": file_hash,
                                    "new_hash": file_hash,
                                }
                            )
                            print(f"Added {file_path}")
                        elif index[file_path] != file_hash:
                            # 文件更新
                            index["operations"].append(
                                {
                                    "type": "update",
                                    "file": file_path,
                                    "old_hash": index[file_path],
                                    "new_hash": file_hash,
                                }
                            )

                            print(f"Updated {file_path}")

                    except UnicodeDecodeError:
                        print(f"Skipped binary file: {file_path}")
        else:
            if should_ignore(path):
                print(f"Ignored {path}")
                return
            try:
                with open(path, "rb") as f:  # 以二进制模式读取
                    content = f.read()
                file_hash = self.hash_object(content)

                if path not in index:
                    # 文件新增
                    index["operations"].append(
                        {
                            "type": "add",
                            "file": path,
                            "old_hash": file_hash,
                            "new_hash": file_hash,
                        }
                    )
                    print(f"Added {path}")
                elif index[path] != file_hash:
                    # 文件更新
                    index["operations"].append(
                        {
                            "type": "update",
                            "file": path,
                            "old_hash": index[path],
                            "new_hash": file_hash,
                        }
                    )

                    print(f"Updated {path}")

            except UnicodeDecodeError:
                print(f"Skipped binary file: {path}")
        self.write_index(index)

    def commit(self, message):
        """提交更改到服务端"""
        commit_data = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "files": {},
            "operations": [],  # 记录操作信息
        }

        def should_ignore(file_path):
            """检查文件路径是否匹配忽略规则"""
            for pattern in IGNORE_PATTERNS:
                if pattern in file_path:
                    return True
            return False

        index = self.read_index()
        operations = index.get("operations", [])
        commit_data["operations"] = operations
        for file_path, file_hash in list(
            index.items()
        ):  # 使用 list() 避免迭代时修改字典
            if should_ignore(file_path):
                print(f"Ignored {file_path}")
                continue
            if file_path == "operations":  # 跳过操作信息
                continue
            if os.path.exists(file_path):  # 检查文件是否存在
                with open(file_path, "rb") as f:
                    content = f.read()
                current_hash = self.hash_object(content)

                if file_hash != current_hash:
                    # 文件内容已更新
                    commit_data["files"][file_path] = current_hash
                    commit_data["operations"].append(
                        {
                            "type": "update",
                            "file": file_path,
                            "old_hash": file_hash,
                            "new_hash": current_hash,
                        }
                    )
                    index[file_path] = current_hash  # 更新索引中的哈希值
                    print(f"Updated {file_path}")
                else:
                    # 文件未更改
                    commit_data["files"][file_path] = file_hash
            else:
                # 文件已删除
                commit_data["operations"].append(
                    {
                        "type": "delete",
                        "file": file_path,
                        "old_hash": file_hash,
                    }
                )
                del index[file_path]  # 从索引中移除
                print(f"Removed non-existent file from index: {file_path}")

        # operations_info = commit_data["operations"]
        index["operations"] = commit_data["operations"]
        # 更新索引文件
        self.write_index(index)

        # 发送提交数据到服务端
        response = requests.post(
            f"{self.get_server_url()}/commit", json={"commit": commit_data}
        )
        if response.status_code == 200:
            commit_hash = response.json()["commit_hash"]
            print(f"Commit {commit_hash} created")
        else:
            print("Failed to create commit")

    def commit2(self, message):
        """提交更改到服务端"""
        commit_data = {
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "files": {},
        }

        index = self.read_index()
        for file_path, file_hash in list(
            index.items()
        ):  # 使用 list() 避免迭代时修改字典
            if os.path.exists(file_path):  # 检查文件是否存在
                with open(file_path, "rb") as f:
                    content = f.read()
                commit_data["files"][file_path] = file_hash
            else:
                # 如果文件不存在，从索引中移除
                del index[file_path]
                print(f"Removed non-existent file from index: {file_path}")

        # 更新索引文件
        self.write_index(index)

        response = requests.post(
            f"{self.get_server_url()}/commit", json={"commit": commit_data}
        )
        if response.status_code == 200:
            commit_hash = response.json()["commit_hash"]
            print(f"Commit {commit_hash} created")
        else:
            print("Failed to create commit")

    def should_ignore(self,file_path):
            """检查文件路径是否匹配忽略规则"""
            for pattern in IGNORE_PATTERNS:
                if pattern in file_path:
                    return True
            return False
    def push(self, remote, model_name, model_version):
        """打包文件并推送到服务端"""
        index = self.read_index()
        if not index:
            print("No files to push")
            return

        operations = index.get("operations", [])
        # 创建内存中的 ZIP 文件
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path, file_hash in index.items():
                if self.should_ignore(file_path):
                    print(f"Ignored {file_path}")
                    continue
                if file_path in ["operations","commit_data"]:  # 跳过操作信息
                    continue
                zipf.write(file_path, os.path.relpath(file_path, self.repo_path))
                print(f"Added to ZIP: {file_path}")

        # 重置缓冲区指针
        zip_buffer.seek(0)

        # 发送 ZIP 文件到服务端
        print(f"Pushing files to server: {list(index.keys())}")
        print(f"operations data: {operations}")
        self.load_session(server_name=self.server_name)
        response = self.session.post(
            f"{self.get_server_url()}/push",
            files={"file": (f"{model_name}_{model_version}.zip", zip_buffer)},
            data={
                "remote": remote,
                "model_name": model_name,
                "model_version": model_version,
                "remote": remote,
                "operations": json.dumps({"operations":operations}),
            },
        )
        print(f"Server response: {response.status_code}, {response.text}")
        if response.status_code == 200:
            print("Push completed")
        else:
            print("Push failed")

    def pull(self, remote, model_name, model_version):
        """从服务端拉取 ZIP 文件并解压"""
        self.load_session(server_name=self.server_name)
        response = self.session.get(
            f"{self.get_server_url()}/pull",
            params={
                "model_name": model_name,
                "model_version": model_version,
                "remote": remote,
            },
        )
        if response.status_code == 200:
            # 将响应内容写入内存中的 ZIP 文件
            zip_buffer = io.BytesIO(response.content)
            with zipfile.ZipFile(zip_buffer, "r") as zipf:
                zipf.extractall(self.repo_path)
            print("Pull completed")
        else:
            print("Pull failed")


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


def load_config():
    """加载服务器配置文件"""
    config_path = os.path.join(os.getcwd(), "servers.yaml")
    if not os.path.exists(config_path):
        return {"servers": {}}
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def save_config(config):
    """保存服务器配置文件"""
    config_path = os.path.join(os.getcwd(), "servers.yaml")
    with open(config_path, "w") as f:
        yaml.safe_dump(config, f)


def config_list(args):
    """列出所有服务器配置"""
    config = load_config()
    if not config["servers"]:
        print("No servers configured.")
        return
    for server_name, server_info in config["servers"].items():
        print(f"Server: {server_name}")
        for key, value in server_info.items():
            print(f"  {key}: {value}")


def config_add(args):
    """添加新的服务器配置"""
    config = load_config()
    if args.name in config["servers"]:
        print(f"Server '{args.name}' already exists. Use 'config update' to modify it.")
        return
    config["servers"][args.name] = {"url": args.url, "api_key": args.api_key}
    save_config(config)
    print(f"Server '{args.name}' added successfully.")


def config_update(args):
    """更新现有服务器配置"""
    config = load_config()
    if args.name not in config["servers"]:
        print(f"Server '{args.name}' does not exist. Use 'config add' to create it.")
        return
    if args.url:
        config["servers"][args.name]["url"] = args.url
    if args.api_key:
        config["servers"][args.name]["api_key"] = args.api_key
    save_config(config)
    print(f"Server '{args.name}' updated successfully.")


def config_remove(args):
    """删除服务器配置"""
    config = load_config()
    if args.name not in config["servers"]:
        print(f"Server '{args.name}' does not exist.")
        return
    del config["servers"][args.name]
    save_config(config)
    print(f"Server '{args.name}' removed successfully.")


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

    # Add command
    add_parser = subparsers.add_parser("add", help="Add files to the staging area")
    add_parser.add_argument("path", help="Path to the file or directory")
    add_parser.set_defaults(
        func=lambda args: OptifluxClient(os.getcwd()).add(args.path)
    )

    # Commit command
    commit_parser = subparsers.add_parser("commit", help="Commit changes")
    commit_parser.add_argument("-m", "--message", required=True, help="Commit message")
    commit_parser.set_defaults(
        func=lambda args: OptifluxClient(os.getcwd()).commit(args.message)
    )

    # Push command
    push_parser = subparsers.add_parser("push", help="Push changes to remote")
    push_parser.add_argument("remote", help="Remote name")
    push_parser.add_argument("model_name", help="Model name")
    push_parser.add_argument("model_version", help="Model version")
    push_parser.add_argument("--server", help="Server name to use")
    push_parser.set_defaults(
        func=lambda args: OptifluxClient(os.getcwd(), args.server).push(
            args.remote, args.model_name, args.model_version
        )
    )

    # Pull command
    pull_parser = subparsers.add_parser("pull", help="Pull changes from remote")
    pull_parser.add_argument("remote", help="Remote name")
    pull_parser.add_argument("model_name", help="Model name")
    pull_parser.add_argument("model_version", help="Model version")
    pull_parser.add_argument("--server", help="Server name to use")
    pull_parser.set_defaults(
        func=lambda args: OptifluxClient(os.getcwd(), args.server).pull(
            args.remote, args.model_name, args.model_version
        )
    )

    # 登录子命令
    login_parser = subparsers.add_parser("login", help="Login to the server")
    login_parser.add_argument("username", help="Username")
    login_parser.add_argument("password", help="Password")
    login_parser.add_argument("--server", help="Server name to use")
    login_parser.set_defaults(
        func=lambda args: OptifluxClient(os.getcwd(), args.server).login(
            args.username, args.password,args.server
        )
    )

    # Config 子命令
    config_parser = subparsers.add_parser("config", help="Manage server configurations")
    config_subparsers = config_parser.add_subparsers(
        title="config commands", dest="config_command"
    )

    # config list 子命令
    config_list_parser = config_subparsers.add_parser(
        "list", help="List all server configurations"
    )
    config_list_parser.set_defaults(func=config_list)

    # config add 子命令
    config_add_parser = config_subparsers.add_parser(
        "add", help="Add a new server configuration"
    )
    config_add_parser.add_argument("name", help="Server name")
    config_add_parser.add_argument("url", help="Server URL")
    config_add_parser.add_argument("api_key", help="Server API key")
    config_add_parser.set_defaults(func=config_add)

    # config update 子命令
    config_update_parser = config_subparsers.add_parser(
        "update", help="Update an existing server configuration"
    )
    config_update_parser.add_argument("name", help="Server name")
    config_update_parser.add_argument("--url", help="New server URL")
    config_update_parser.add_argument("--api_key", help="New server API key")
    config_update_parser.set_defaults(func=config_update)

    # config remove 子命令
    config_remove_parser = config_subparsers.add_parser(
        "remove", help="Remove a server configuration"
    )
    config_remove_parser.add_argument("name", help="Server name")
    config_remove_parser.set_defaults(func=config_remove)

    # Parse arguments and execute the corresponding function
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
