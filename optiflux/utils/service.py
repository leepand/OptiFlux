import os
import stat
import subprocess
import time
import psutil
import signal
import json
from ..config import ENV_DIRS
import traceback
import socket


def get_port_status(port):
    """
    检查端口状态。
    :param port: 端口号
    :return: 端口状态（running/failed/error）
    """
    try:
        process = subprocess.run(
            ["lsof", "-i", f":{port}"], capture_output=True, text=True
        )
        stdout = process.stdout
        stderr = process.stderr

        if "PID" in stdout:
            return "running"
        else:
            return "failed"
    except Exception:
        return f"Error: {traceback.format_exc()}"


def is_port_in_use(port):
    """
    检查端口是否被占用。
    :param port: 端口号
    :return: True 如果端口被占用，否则 False
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex(("localhost", port)) == 0


def start_service(script, timeout=240):
    """
    启动服务。
    :param script: 脚本路径
    :param timeout: 超时时间（秒）
    :return: 执行结果
    """
    try:
        process = subprocess.run(
            script,
            shell=True,
            preexec_fn=os.setsid,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True,
        )
        return (
            process.stdout or process.stderr or "Your script is processed successfully."
        )
    except subprocess.CalledProcessError as e:
        return f"Error: {e}"
    except subprocess.TimeoutExpired:
        return "Command execution timed out."


def wait_until_port_used(port, max_wait_sec=15, interval_sec=0.5):
    """
    等待端口被占用。
    :param port: 端口号
    :param max_wait_sec: 最大等待时间（秒）
    :param interval_sec: 检查间隔（秒）
    :return: 是否成功
    """
    curr_wait_sec = 0
    while curr_wait_sec < max_wait_sec:
        if get_port_status(port) == "running":
            return True
        curr_wait_sec += interval_sec
        time.sleep(interval_sec)
    return False


def generate_start_services_script(env, model_name, model_version):
    """
    生成 start_services.sh 脚本，并按端口生成独立的服务启动脚本。
    :param env: 环境（dev/preprod/prod）
    :param model_name: 模型名称
    :param model_version: 模型版本
    """
    # 构建模型目录
    model_dir = os.path.join(ENV_DIRS.get(env), model_name)
    model_version_dir = os.path.join(ENV_DIRS.get(env), model_name, model_version)
    start_script_path = os.path.join(model_version_dir, "start_services.sh")

    # 如果 start_services.sh 已存在，则跳过
    if os.path.exists(start_script_path):
        print(f"start_services.sh already exists at {start_script_path}")
        # return

    # 读取 config.json
    config_path = os.path.join(model_dir, "config.json")
    with open(config_path, "r") as f:
        config = json.load(f)

    # 生成 start_services.sh 内容
    script_content = """#!/bin/bash

# 启动所有服务
"""

    # 生成 recomserver 启动脚本
    for recom_config in config.get("recomserver", []):
        script_path = generate_service_script(
            env, model_name, model_version, "recomserver", recom_config
        )
        script_content += f"sh {script_path} &\n"

    # 生成 rewardserver 启动脚本
    for reward_config in config.get("rewardserver", []):
        script_path = generate_service_script(
            env, model_name, model_version, "rewardserver", reward_config
        )
        script_content += f"sh {script_path} &\n"

    script_content += """
# 等待所有服务启动
wait
"""

    # 写入 start_services.sh 文件
    with open(start_script_path, "w") as f:
        f.write(script_content)

    # 赋予脚本执行权限
    st = os.stat(start_script_path)
    os.chmod(start_script_path, st.st_mode | stat.S_IEXEC)

    print(f"Generated start_services.sh at {start_script_path}")


def restart_services_handle(env, model_name, model_version):
    """
    重启 recomserver 和 rewardserver 服务。
    :param env: 环境（dev/preprod/prod）
    :param model_name: 模型名称
    :param model_version: 模型版本
    :return: 重启结果
    """
    try:
        # 构建 config.json 文件路径
        config_path = os.path.join(ENV_DIRS.get(env), model_name, "config.json")
        if not os.path.exists(config_path):
            return {"status": "error", "message": "Config file not found"}

        with open(config_path, "r") as f:
            config = json.load(f)

        # 重启 recomserver 服务
        recom_ports = []
        for recom_config in config.get("recomserver", []):
            script_path = generate_service_script(
                env, model_name, model_version, "recomserver", recom_config
            )
            if start_service_with_nohup(script_path):
                recom_ports.append(recom_config.get("port"))
            time.sleep(5)  # 每个服务启动后停留 5 秒

        # 重启 rewardserver 服务
        reward_ports = []
        for reward_config in config.get("rewardserver", []):
            script_path = generate_service_script(
                env, model_name, model_version, "rewardserver", reward_config
            )
            if start_service_with_nohup(script_path):
                reward_ports.append(reward_config.get("port"))
            time.sleep(5)  # 每个服务启动后停留 5 秒

        return {
            "status": "success",
            "message": "Services restarted successfully",
            "recom_ports": recom_ports,
            "reward_ports": reward_ports,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def start_service_with_nohup(script_path):
    """
    使用 nohup 启动服务。
    :param script_path: 脚本文件路径
    :return: 是否启动成功
    """
    try:
        # 使用 nohup 执行脚本
        subprocess.Popen(
            ["nohup", script_path, "&"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        print(f"Started service with script: {script_path}")
        return True
    except Exception as e:
        print(f"Failed to start service with script {script_path}: {e}")
        return False


def generate_service_script(env, model_name, model_version, service_type, config):
    """
    生成启动单个服务的脚本文件。
    :param env: 环境（dev/preprod/prod）
    :param model_name: 模型名称
    :param model_version: 模型版本
    :param service_type: 服务类型（recomserver/rewardserver）
    :param config: 服务配置（包含 port, workers 等信息）
    :return: 脚本文件路径
    """
    port = config.get("port")
    workers = config.get("workers", 1)  # 默认 1 个 worker
    log_file = f"{service_type}_{port}.log"
    log_path = os.path.join(
        ENV_DIRS.get(env), model_name, model_version, "logs", log_file
    )
    project_root = os.path.join(ENV_DIRS.get(env), model_name, model_version)

    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # 获取项目根目录
    # project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # 脚本内容
    script_content = f"""#!/bin/bash

# 启动 gunicorn
gunicorn --workers {workers} \\
         --bind :{port} \\
         --worker-class uvicorn.workers.UvicornWorker \\
         --preload \\
         --chdir {project_root} \\
         src.{service_type}:app \\
         --log-file {log_path} \\
         --log-level info
"""

    # 脚本文件路径
    script_name = f"{service_type}_{port}.sh"
    script_path = os.path.join(
        ENV_DIRS.get(env), model_name, model_version, "scripts", script_name
    )

    # 确保脚本目录存在
    os.makedirs(os.path.dirname(script_path), exist_ok=True)

    # 写入脚本文件
    with open(script_path, "w") as f:
        f.write(script_content)

    # 赋予脚本执行权限
    st = os.stat(script_path)
    os.chmod(script_path, st.st_mode | stat.S_IEXEC)

    return script_path


def kill_process_by_port(port):
    """
    根据端口号杀掉相关进程。
    """
    for proc in psutil.process_iter(["pid", "name", "connections"]):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    proc.kill()
                    break
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue


def start_gunicorn_service(env, model_name, model_version, service_type, config):
    """
    启动 gunicorn 服务。
    :param env: 环境（dev/preprod/prod）
    :param model_name: 模型名称
    :param model_version: 模型版本
    :param service_type: 服务类型（recomserver/rewardserver）
    :param config: 服务配置（包含 port, workers 等信息）
    :return: 服务端口
    """
    port = config.get("port")
    workers = config.get("workers", 1)  # 默认 1 个 worker
    log_file = f"{service_type}_{port}.log"
    log_path = os.path.join(
        ENV_DIRS.get(env), model_name, model_version, "logs", log_file
    )

    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # 如果端口被占用，杀掉占用端口的进程
    for proc in psutil.process_iter(["pid", "name", "connections"]):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    print(f"Killing process {proc.pid} using port {port}")
                    os.kill(proc.pid, signal.SIGTERM)
                    time.sleep(1)  # 等待进程终止
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # 启动 gunicorn 服务
    command = [
        "gunicorn",
        "--workers",
        str(workers),
        "--bind",
        f":{port}",
        "--worker-class",
        "uvicorn.workers.UvicornWorker",
        "--preload",
        f"src.{service_type}:app",
        "--log-file",
        log_path,
        "--log-level",
        "info",
        "--daemon",  # 后台运行
    ]

    try:
        subprocess.run(command, check=True)
        print(f"Started {service_type} on port {port}")
        return port
    except subprocess.CalledProcessError as e:
        print(f"Failed to start {service_type} on port {port}: {e}")
        return None
