# optiflux/server/routes.py

from flask import request, jsonify, session
import zipfile  # 确保导入 zipfile 模块

import os
from ..utils.file_utils import unzip_file, ensure_dir_exists
from ..config import ENV_DIRS, LOG_DIR

import traceback  # 导入 traceback 模块
import time
from datetime import datetime
import json
import pytz  # 需要安装pytz库：pip install pytz
from dateutil import parser, tz


def convert_to_beijing_time(utc_time):
    if not utc_time:
        return None
    try:
        # 首先将UTC时间转换为aware时间
        utc_timestamp = utc_time.replace(tzinfo=tz.gettz("UTC"))
        # 获取北京时区
        beijing_tz = tz.gettz("Asia/Shanghai")
        # 将时间转换为北京时区
        beijing_timestamp = utc_timestamp.astimezone(beijing_tz)
        return beijing_timestamp
    except Exception as e:
        print(f"时间转换错误：{str(e)}")
        return utc_time


def generate_default_config(env, model_name, model_version):
    """
    生成默认的 config.json 文件。
    :param env: 环境（dev/preprod/prod）
    :param model_name: 模型名称
    :param model_version: 模型版本
    :return: 默认配置
    """
    default_config = {
        "recomserver": [{"port": 8001, "workers": 2}],
        "rewardserver": [{"port": 8002, "workers": 2}],
        "current_version": model_version,
    }
    return default_config


def scan_model_names(env, page=1, per_page=10):
    """
    扫描指定 Environment 的目录结构，提取所有 model_name 及其额外信息。
    按最新修改时间排序，并支持分页。

    :param env: 环境名称（例如：dev、preprod、prod）
    :param page: 当前页码
    :param per_page: 每页显示的条目数
    :return: 包含额外信息的 model_name 列表及分页信息
    """
    model_names = []
    env_dir = ENV_DIRS.get(env)
    if not env_dir or not os.path.exists(env_dir):
        return {"model_names": [], "total": 0, "page": page, "per_page": per_page}

    # 遍历第一层目录（model_name）
    for model_name in os.listdir(env_dir):
        if model_name == ".ipynb_checkpoints":  # 排除 .ipynb_checkpoints 目录
            continue
        model_dir = os.path.join(env_dir, model_name)
        if not os.path.isdir(model_dir):
            continue

        # 获取版本信息
        versions = []
        total_size = 0
        latest_timestamp = None
        for model_version in os.listdir(model_dir):
            if model_version == ".ipynb_checkpoints":  # 排除 .ipynb_checkpoints 目录
                continue
            version_dir = os.path.join(model_dir, model_version)
            if not os.path.isdir(version_dir):
                continue

            # 获取目录的修改时间
            timestamp = os.path.getmtime(version_dir)
            # 转换为北京时间
            beijing_tz = pytz.timezone("Asia/Shanghai")
            timestamp = datetime.fromtimestamp(timestamp, tz=pytz.utc).astimezone(
                beijing_tz
            )
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

            # 获取目录大小
            size = sum(
                os.path.getsize(os.path.join(version_dir, f))
                for f in os.listdir(version_dir)
                if os.path.isfile(os.path.join(version_dir, f))
            )

            versions.append(
                {"model_version": model_version, "timestamp": timestamp, "size": size}
            )

            # 更新总大小和最新时间戳
            total_size += size
            if not latest_timestamp or timestamp > latest_timestamp:
                latest_timestamp = timestamp

        # 获取最大版本
        max_version = (
            max(versions, key=lambda x: x["model_version"])["model_version"]
            if versions
            else "N/A"
        )

        # 获取 Recomserver 和 Rewardserver 的生产端口及运行状态（示例代码）
        recomserver_port, recomserver_status = get_server_info(
            env, model_name, "Recomserver"
        )
        rewardserver_port, rewardserver_status = get_server_info(
            env, model_name, "Rewardserver"
        )

        # 添加到 model_name 列表
        model_names.append(
            {
                "model_name": model_name,
                "version_count": len(versions),
                "max_version": max_version,
                "total_size": total_size,
                "latest_timestamp": latest_timestamp,
                "recomserver_port": recomserver_port,
                "recomserver_status": recomserver_status,
                "rewardserver_port": rewardserver_port,
                "rewardserver_status": rewardserver_status,
            }
        )

    # 按最新修改时间排序
    model_names.sort(key=lambda x: x["latest_timestamp"], reverse=True)

    # 分页逻辑
    total = len(model_names)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_model_names = model_names[start:end]

    return {
        "model_names": paginated_model_names,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def get_server_info(env, model_name, server_type):
    """
    获取 Recomserver 或 Rewardserver 的生产端口及运行状态（示例代码）。

    :param env: 环境名称
    :param model_name: 模型名称
    :param server_type: 服务器类型（Recomserver 或 Rewardserver）
    :return: (port, status)
    """
    # 示例：从配置文件中读取端口和状态
    # 这里假设配置文件路径为 /path/to/{env}/{model_name}/config.json
    config_path = os.path.join(ENV_DIRS.get(env), model_name, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                port = config.get(f"{server_type.lower()}_port", "N/A")
                status = config.get(f"{server_type.lower()}_status", "N/A")
                return port, status
        except Exception as e:
            print(f"Error reading config file: {e}")
    return "N/A", "N/A"


def scan_model_versions(env, model_name):
    """
    扫描指定 Environment 和 model_name 的版本信息。
    返回包含额外信息的版本列表。

    :param env: 环境名称（例如：dev、preprod、prod）
    :param model_name: 模型名称
    :return: 版本信息列表
    """
    model_versions = []
    env_dir = ENV_DIRS.get(env)
    if not env_dir or not os.path.exists(env_dir):
        return model_versions

    model_dir = os.path.join(env_dir, model_name)
    if not os.path.isdir(model_dir):
        return model_versions

    # 获取当前服务中的版本
    current_version = get_current_serving_version(env, model_name)

    # 遍历版本目录
    for model_version in os.listdir(model_dir):
        if model_version == ".ipynb_checkpoints":  # 排除 .ipynb_checkpoints 目录
            continue
        version_dir = os.path.join(model_dir, model_version)
        if not os.path.isdir(version_dir):
            continue

        # 获取目录的修改时间
        timestamp = os.path.getmtime(version_dir)
        # 转换为北京时间
        beijing_tz = pytz.timezone("Asia/Shanghai")
        timestamp = datetime.fromtimestamp(timestamp, tz=pytz.utc).astimezone(
            beijing_tz
        )
        timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # 获取目录大小
        size = sum(
            os.path.getsize(os.path.join(version_dir, f))
            for f in os.listdir(version_dir)
            if os.path.isfile(os.path.join(version_dir, f))
        )

        # 获取 recomserver 和 rewardserver 的端口
        recomserver_port, rewardserver_port = get_server_ports(
            env, model_name, model_version
        )

        # 添加到版本列表
        model_versions.append(
            {
                "model_name": model_name,
                "model_version": model_version,
                "timestamp": timestamp,
                "size": size,
                "recomserver_port": recomserver_port,
                "rewardserver_port": rewardserver_port,
                "is_serving": model_version == current_version,  # 是否正在服务中
            }
        )

    # 按最大版本排序（降序）
    model_versions.sort(key=lambda x: x["model_version"], reverse=True)

    return model_versions


def get_current_serving_version(env, model_name):
    """
    获取当前服务中的版本。

    :param env: 环境名称
    :param model_name: 模型名称
    :return: 当前服务中的版本号
    """
    # 示例：从配置文件中读取当前服务中的版本
    config_path = os.path.join(ENV_DIRS.get(env), model_name, "config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("current_version", "N/A")
        except Exception as e:
            print(f"Error reading config file: {e}")
    return "N/A"


def get_server_ports(env, model_name, model_version):
    """
    获取 recomserver 和 rewardserver 的端口。

    :param env: 环境名称
    :param model_name: 模型名称
    :param model_version: 版本号
    :return: (recomserver_port, rewardserver_port)
    """
    # 示例：从配置文件中读取端口
    config_path = os.path.join(
        ENV_DIRS.get(env), model_name, model_version, "config.json"
    )
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                return config.get("recomserver_port", "N/A"), config.get(
                    "rewardserver_port", "N/A"
                )
        except Exception as e:
            print(f"Error reading config file: {e}")
    return "N/A", "N/A"


# 模型注册表（临时存储）
model_registry = []


def handle_deploy():
    """处理代码部署请求"""
    try:
        print("Received deployment request")  # 调试信息

        # 获取表单数据
        env = request.form.get("env", "dev")
        model_name = request.form.get("model_name")
        model_version = request.form.get("model_version")
        upload_type = request.form.get("uploadType", "file")  # 获取上传类型

        # 构建模型目录
        model_dir = os.path.join(ENV_DIRS.get(env), model_name)
        os.makedirs(model_dir, exist_ok=True)

        # 构建 config.json 文件路径
        config_path = os.path.join(model_dir, "config.json")

        # 如果 config.json 不存在，则生成默认配置
        if not os.path.exists(config_path):
            default_config = generate_default_config(env, model_name, model_version)
            with open(config_path, "w") as f:
                json.dump(default_config, f, indent=4)
            print(f"Generated default config.json at {config_path}")
        else:
            print(f"Config file already exists at {config_path}")

        # 检查环境是否有效
        if env not in ENV_DIRS:
            print(f"Invalid environment: {env}")  # 调试信息
            return jsonify({"status": "error", "message": "Invalid environment."}), 400

        # 创建目标目录
        target_dir = os.path.join(ENV_DIRS[env], model_name, model_version)
        ensure_dir_exists(target_dir)

        # 处理文件上传
        if upload_type == "file":
            if "file" not in request.files:
                print("No file uploaded")  # 调试信息
                return jsonify({"status": "error", "message": "No file uploaded."}), 400

            file = request.files["file"]
            file_path = os.path.join(target_dir, file.filename)
            print(f"Saving file to: {file_path}")  # 调试信息
            file.save(file_path)

            # 如果是zip文件，解压
            if file.filename.endswith(".zip"):
                print("File is a zip file, extracting...")  # 调试信息
                with zipfile.ZipFile(file_path, "r") as zipf:
                    zipf.extractall(target_dir)
                print("Extraction complete")  # 调试信息
                os.remove(file_path)  # 解压后删除zip文件

        # 处理文件夹上传
        else:
            if "folder" not in request.files:
                print("No folder uploaded")  # 调试信息
                return (
                    jsonify({"status": "error", "message": "No folder uploaded."}),
                    400,
                )

            files = request.files.getlist("folder")
            for file in files:
                # 去除最外层文件夹的名称
                file_path = file.filename.split("/", 1)[-1]  # 去除最外层文件夹名称
                file_path = os.path.join(target_dir, file_path)

                # 确保目标目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # 保存文件
                print(f"Saving file to: {file_path}")  # 调试信息
                file.save(file_path)

        # 注册模型版本信息
        model_registry.append(
            {
                "env": env,
                "model_name": model_name,
                "model_version": model_version,
                "target_dir": target_dir,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        user_id = session.get("_user_id")
        print(user_id, "user_id")
        if user_id:

            def get_user_name(session):
                try:
                    uid = int(session["_user_id"])
                    # print(uid,type(uid))
                    user = User.query.get(uid)
                    return user.username
                except:
                    return "session_nouser"

            username = get_user_name(session)
            add_log("部署模型", f"用户:{username} 部署了新模型", user_id)

        return jsonify(
            {
                "status": "success",
                "message": f"Code deployed to {env}/{model_name}/{model_version}.",
            }
        )
    except Exception as e:
        # 打印异常信息和堆栈跟踪
        print(f"Error during deployment: {str(e)}")
        traceback.print_exc()  # 打印堆栈跟踪
        # 返回详细的错误信息
        return jsonify({"status": "error", "message": str(e)}), 500


def handle_deploy2():
    """处理代码部署请求"""
    try:
        print("Received deployment request")  # 调试信息

        # 检查文件上传
        if "file" not in request.files:
            print("No file uploaded")  # 调试信息
            return jsonify({"status": "error", "message": "No file uploaded."}), 400

        file = request.files["file"]
        env = request.form.get("env", "dev")
        version_info = request.form.get("version_info", "{}")  # 获取版本信息

        print(f"Environment: {env}")  # 调试信息
        print(f"Uploaded file: {file.filename}")  # 调试信息
        print(f"Version info: {version_info}")  # 调试信息

        # 检查环境是否有效
        if env not in ENV_DIRS:
            print(f"Invalid environment: {env}")  # 调试信息
            return jsonify({"status": "error", "message": "Invalid environment."}), 400

        # 保存上传的文件
        env_dir = ENV_DIRS[env]
        ensure_dir_exists(env_dir)

        file_path = os.path.join(env_dir, file.filename)
        print(f"Saving file to: {file_path}")  # 调试信息
        file.save(file_path)

        # 如果是zip文件，解压
        if file.filename.endswith(".zip"):
            print("File is a zip file, extracting...")  # 调试信息
            with zipfile.ZipFile(file_path, "r") as zipf:
                zipf.extractall(env_dir)
            print("Extraction complete")  # 调试信息
            os.remove(file_path)  # 解压后删除zip文件

        # 注册模型版本信息
        model_registry.append(
            {
                "env": env,
                "version_info": version_info,
                "file_path": file_path,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        return jsonify(
            {"status": "success", "message": f"Code deployed to {env} environment."}
        )
    except Exception as e:
        # 打印异常信息和堆栈跟踪
        print(f"Error during deployment: {str(e)}")
        traceback.print_exc()  # 打印堆栈跟踪
        # 返回详细的错误信息
        return jsonify({"status": "error", "message": str(e)}), 500


def get_model_versions():
    """获取模型版本信息"""
    return jsonify({"status": "success", "model_versions": model_registry})


def handle_logs(env):
    """获取指定环境的日志"""
    try:
        log_dir = os.path.join(ENV_DIRS.get(env, ""), "logs")
        if not os.path.exists(log_dir):
            return (
                jsonify({"status": "error", "message": "Log directory not found."}),
                404,
            )

        logs = []
        for log_file in os.listdir(log_dir):
            with open(os.path.join(log_dir, log_file), "r") as f:
                logs.append(f.read())
        return jsonify({"status": "success", "logs": logs})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def get_log_files():
    """获取日志文件列表，包括文件名、修改时间（北京时间）和文件大小"""
    try:
        log_files = []
        if os.path.exists(LOG_DIR):
            for file in os.listdir(LOG_DIR):
                if file.endswith(".log"):
                    file_path = os.path.join(LOG_DIR, file)
                    file_stat = os.stat(file_path)
                    # 获取文件修改时间（UTC时间）
                    modified_time_utc = datetime.utcfromtimestamp(file_stat.st_mtime)
                    # 转换为北京时间
                    beijing_tz = pytz.timezone("Asia/Shanghai")
                    modified_time_beijing = modified_time_utc.replace(
                        tzinfo=pytz.utc
                    ).astimezone(beijing_tz)
                    # 格式化时间为字符串
                    modified_time_str = modified_time_beijing.strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    # 获取文件大小（转换为MB或KB）
                    file_size = file_stat.st_size
                    if file_size > 1024 * 1024:  # 大于1MB
                        file_size = f"{file_size / (1024 * 1024):.2f} MB"
                    else:
                        file_size = f"{file_size / 1024:.2f} KB"
                    # 添加到日志文件列表
                    log_files.append(
                        {
                            "name": file,
                            "modified_time": modified_time_str,
                            "size": file_size,
                        }
                    )
        return jsonify({"status": "success", "log_files": log_files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def get_log_content():
    """获取日志文件内容"""
    try:
        file_name = request.args.get("file")  # 获取文件名
        lines = int(request.args.get("lines", 7000))  # 获取行数，默认 100 行

        if not file_name:
            return (
                jsonify({"status": "error", "message": "File name is required."}),
                400,
            )

        file_path = os.path.join(LOG_DIR, file_name)
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": "File not found."}), 404

        # 读取最新的 N 行日志
        with open(file_path, "r") as f:
            lines_list = f.readlines()[-lines:]  # 获取最后 N 行
            content = "".join(lines_list)

        return jsonify({"status": "success", "content": content})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
