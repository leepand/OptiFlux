# optiflux/server/server.py
import traceback  # 导入 traceback 模块
import os
from datetime import datetime
import json
import pytz  # 需要安装pytz库：pip install pytz

import time
import psutil

from .routes import (
    handle_deploy,
    handle_logs,
    get_model_versions,
    get_log_files,
    get_log_content,
    scan_model_versions,
    scan_model_names,convert_to_beijing_time,generate_default_config
)
# from ..config import SERVER_HOST, SERVER_PORT,ENV_DIRS
from ..config import ENV_DIRS
from ..utils.env import load_or_initialize_config
from ..utils.service import generate_service_script,wait_until_port_used,start_service,kill_process_by_port,is_port_in_use
from ..utils.file_utils import ensure_dir_exists

import sys
import argparse
from .gunicorn_apps import GunicornApp


from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import desc

from functools import wraps

from flask import (
    Flask,
    jsonify,
    render_template,
    redirect,
    flash,
    request,
    url_for,
    session
)

from datetime import timedelta
from sqlalchemy.exc import (
    IntegrityError,
    DataError,
    DatabaseError,
    InterfaceError,
    InvalidRequestError,
)
from werkzeug.routing import BuildError


from flask_bcrypt import Bcrypt,generate_password_hash, check_password_hash

from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    logout_user,
    login_required,
)

from .app import create_app,db,login_manager,bcrypt
from .models import User,OperationLog
from .manage import deploy

from sqlalchemy.orm import Session as SessionSQL
import diskcache

# 配置 diskcache
cache_dir = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(cache_dir, exist_ok=True)
cache = diskcache.Cache(cache_dir)


#deploy()

@login_manager.user_loader
def load_user(user_id):
    #return SessionSQL().get(User, int(user_id))

    #sqlalchemy_session = SessionSQL()  # 创建 SQLAlchemy Session
    #user = sqlalchemy_session.get(User, user_id)  # 查询用户
    #sqlalchemy_session.close()  # 关闭 Session
    return db.session.get(User, int(user_id))


    # return User.query.get(int(user_id))

app = create_app()

@app.before_request
def session_handler():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=60*24*7)

# 添加日志的辅助函数
def add_log(action, details=None, user_id=None):
    """记录操作日志"""
    log = OperationLog(action=action, details=details, user_id=user_id)
    db.session.add(log)
    db.session.commit()

# 注册路由
# app.add_url_rule("/deploy", "deploy", handle_deploy, methods=["POST"])
# app.add_url_rule("/logs/<env>", "logs", handle_logs, methods=["GET"])

# app.add_url_rule('/model_versions', 'model_versions', get_model_versions, methods=['GET'])

# app.add_url_rule('/logs', 'logs', get_logs, methods=['GET'])
app.add_url_rule("/log_files", "log_files", get_log_files, methods=["GET"])
app.add_url_rule("/log_content", "log_content", get_log_content, methods=["GET"])


def get_user_name(session):
    try:
        uid=int(session["_user_id"])
        # print(uid,type(uid))
        user = db.session.get(User, int(uid))
        
        return user.username
    except:
        return "session_nouser"
@app.route("/profile")
def profile():
    if "_user_id" not in session:
        return redirect(url_for("login"))
    
    user =db.session.get(User, int(session["_user_id"]))   #User.query.get(session["_user_id"])
    if user is None:
        flash("用户不存在，请重新登录")
        return redirect(url_for("logout"))
    
    return render_template("profile.html", user=user)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "_user_id" not in session:  # 检查用户是否登录
            print("User not logged in, redirecting to login page...",session,request.cookies)
            return redirect(url_for("login"))  # 重定向到登录页面
        return f(*args, **kwargs)
    return decorated_function

@app.route("/deploy", methods=["POST"])
@login_required
def deploy():
    """处理代码部署请求"""
    try:
        print("Received deployment request")  # 调试信息

        # 获取表单数据
        model_registry=[]
        env = request.form.get('env', 'dev')
        model_name = request.form.get('model_name')
        model_version = request.form.get('model_version')
        upload_type = request.form.get('uploadType', 'file')  # 获取上传类型
        
        # 构建模型目录
        model_dir = os.path.join(ENV_DIRS.get(env), model_name)
        os.makedirs(model_dir, exist_ok=True)

        # 构建 config.json 文件路径
        config_path = os.path.join(model_dir, 'config.json')

        # 如果 config.json 不存在，则生成默认配置
        if not os.path.exists(config_path):
            default_config = generate_default_config(env, model_name, model_version)
            with open(config_path, 'w') as f:
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
        if upload_type == 'file':
            if 'file' not in request.files:
                print("No file uploaded")  # 调试信息
                return jsonify({"status": "error", "message": "No file uploaded."}), 400

            file = request.files['file']
            file_path = os.path.join(target_dir, file.filename)
            print(f"Saving file to: {file_path}")  # 调试信息
            file.save(file_path)

            # 如果是zip文件，解压
            if file.filename.endswith('.zip'):
                print("File is a zip file, extracting...")  # 调试信息
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    zipf.extractall(target_dir)
                print("Extraction complete")  # 调试信息
                os.remove(file_path)  # 解压后删除zip文件

        # 处理文件夹上传
        else:
            if 'folder' not in request.files:
                print("No folder uploaded")  # 调试信息
                return jsonify({"status": "error", "message": "No folder uploaded."}), 400

            files = request.files.getlist('folder')
            for file in files:
                # 去除最外层文件夹的名称
                file_path = file.filename.split('/', 1)[-1]  # 去除最外层文件夹名称
                file_path = os.path.join(target_dir, file_path)

                # 确保目标目录存在
                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                # 保存文件
                print(f"Saving file to: {file_path}")  # 调试信息
                file.save(file_path)

        # 注册模型版本信息
        model_registry.append({
            "env": env,
            "model_name": model_name,
            "model_version": model_version,
            "target_dir": target_dir,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        user_id = session.get("_user_id")
        # print(user_id,"user_id")
        if user_id:
            username=get_user_name(session)
            add_log("部署模型", f"用户:{username} 部署了新模型:{model_name}-{model_version}", user_id)

        return jsonify({"status": "success", "message": f"Code deployed to {env}/{model_name}/{model_version}."})
    except Exception as e:
        # 打印异常信息和堆栈跟踪
        print(f"Error during deployment: {str(e)}")
        traceback.print_exc()  # 打印堆栈跟踪
        # 返回详细的错误信息
        return jsonify({"status": "error", "message": str(e)}), 500



# 用户登录
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            session["_user_id"] = user.id  # 设置 Session 数据
            session.permanent = True  # 标记会话为永久
            session.modified = True  # 显式标记会话已修改

            add_log("用户登陆", f"{username}:登陆成功", user.id)
            flash('Logged in successfully.')
            return redirect(url_for("index"))
        flash("用户名或密码错误")
    # 清理无效会话
    if "user_id" in session:
        # user = User.query.get(session["user_id"])
        user=db.session.get(User, int(session["_user_id"]))
        if user is None:
            session.pop("user_id", None)
    return render_template("login.html")


@app.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    # flash("已注销")
    # add_log("用户登出", f"{username}:登陆成功", user.id)
    return redirect(url_for("login"))


# 用户注册
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if User.query.filter_by(username=username).first():
            flash("用户名已存在")
        else:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("注册成功，请登录")
            add_log("用户注册", f"{username}:注册成功", user.id)
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/operation_records2", methods=["GET"])
def get_operation_records2():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "未登录"}), 401

    logs = OperationLog.query.filter_by(user_id=user_id).order_by(desc(OperationLog.timestamp)).all()
    logs_data = [{"id": log.id, "action": log.action, "details": log.details, "timestamp": log.timestamp} for log in logs]
    return jsonify({"status": "success", "logs": logs_data}), 200

@app.route("/operation_records", methods=["GET"])
def get_operation_records():
    # 鉴权验证
    user_id = session.get("user_id")
    #if not user_id:
    #    return jsonify({"status": "error", "message": "未登录"}), 401
    
    try:
        # 获取分页参数（带默认值）
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        if page < 1 or per_page < 1:
            raise ValueError
    except ValueError:
        return jsonify({"status": "error", "message": "非法分页参数"}), 400

    # 构造分页查询
    #query = OperationLog.query.filter_by(user_id=user_id)
    # query = OperationLog.query.order_by(OperationLog.timestamp.desc()).all()
    query = OperationLog.query.order_by(OperationLog.timestamp.desc())

    total = query.count()  # 总记录数
    
    # 获取当前页数据（使用desc排序）
    pagination = query.order_by(desc(OperationLog.timestamp)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # 构造响应数据
    logs = pagination.items
    response_data = {
        "status": "success",
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pagination.pages,
        "logs": [{
            "id": log.id,
            "action": log.action,
            "details": log.details,
            "timestamp": convert_to_beijing_time(log.timestamp).isoformat()  
        } for log in logs]
    }
    
    return jsonify(response_data), 200


@app.route("/product")
@login_required
def index():
    print("Session:", session)
    print("Cookies:", request.cookies)
    uid = int(session["_user_id"])
    print("User ID:", uid)
    user = db.session.get(User, uid)
    print("User:", user)
    if user is None:
        print("User not found, redirecting to logout...")
        return redirect(url_for("logout"))

    return render_template("index.html", user=user)

@app.route('/')
def loading_page():
    return render_template('loading_page.html')

@app.route('/model_names', methods=['GET'])
def get_model_names():
    """
    获取某个环境下的模型名称列表，包含当前服役版本及其端口状态，支持分页。
    """
    env = request.args.get('env')
    page = int(request.args.get('page', 1))  # 默认第一页
    per_page = int(request.args.get('per_page', 10))  # 默认每页 10 条

    cache_key = f'get_model_names_{env}_{page}_{per_page}'
    cached_result = cache.get(cache_key)
    if cached_result:
        return jsonify(cached_result)

    if not env or env not in ENV_DIRS:
        return jsonify({"status": "error", "message": "Invalid environment"}), 400

    try:
        # 构建环境目录
        env_dir = ENV_DIRS.get(env)
        model_names = []

        # 一次性读取目录内容
        all_models = os.listdir(env_dir)
        beijing_tz = pytz.timezone('Asia/Shanghai')

        for model_name in all_models:
            model_dir = os.path.join(env_dir, model_name)
            if os.path.isdir(model_dir):
                config_path = os.path.join(model_dir, 'config.json')
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        config = json.load(f)

                    current_version = config.get('current_version')
                    versions = [v for v in os.listdir(model_dir) if os.path.isdir(os.path.join(model_dir, v))]
                    version_count = len(versions)
                    max_version = max(versions, default='None')
                    #total_size = sum(os.path.getsize(os.path.join(model_dir, f)) for f in os.listdir(model_dir) if os.path.isfile(os.path.join(model_dir, f)))
                    total_size = 0

                    # 计算文件大小
                    for root, dirs, files in os.walk(model_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.isfile(file_path):
                                try:
                                    file_size = os.path.getsize(file_path)
                                    total_size += file_size
                                    print(f"File: {file_path}, Size: {file_size}")
                                except Exception as e:
                                    print(f"Error getting size for file {file_path}: {e}")

                    latest_timestamp = os.path.getmtime(model_dir)
                    beijing_time = datetime.fromtimestamp(latest_timestamp, tz=beijing_tz).strftime('%Y-%m-%d %H:%M:%S')

                    recomserver = [{'port': rc['port'], 'status': check_service_status(rc['port'])} for rc in config.get('recomserver', [])]
                    rewardserver = [{'port': rw['port'], 'status': check_service_status(rw['port'])} for rw in config.get('rewardserver', [])]

                    model_names.append({
                        'model_name': model_name,
                        'version_count': version_count,
                        'max_version': max_version,
                        'total_size': total_size,
                        'latest_timestamp': beijing_time,
                        'serving_version': current_version,
                        'recomserver': recomserver,
                        'rewardserver': rewardserver,
                    })

        # 根据时间戳排序，最新的排在前面
        model_names.sort(key=lambda x: x['timestamp'], reverse=True)

        # 分页逻辑
        start = (page - 1) * per_page
        end = start + per_page
        paginated_model_names = model_names[start:end]

        response_data = {
            "status": "success",
            "model_names": paginated_model_names,
            "total": len(model_names),
            "page": page,
            "per_page": per_page,
        }

        # 缓存结果
        # cache.set(cache_key, response_data, expire=60)  # 缓存 60 秒

        return jsonify(response_data)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route("/model_names22", methods=["GET"])
def get_model_names22():
    """
    获取某个环境下的所有 model_name，支持分页。
    """
    env = request.args.get("env")
    page = int(request.args.get('page', 1))  # 默认第一页
    per_page = int(request.args.get('per_page', 10))  # 默认每页 10 条

    if not env or env not in ENV_DIRS:
        return jsonify({"status": "error", "message": "Invalid environment"}), 400

    result = scan_model_names(env, page=page, per_page=per_page)

    return jsonify({"status": "success", **result})


@app.route('/model_versions_new', methods=['GET'])
def get_model_versions_new():
    env = request.args.get('env')
    model_name = request.args.get('model_name')

    if not env or not model_name:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 获取模型版本信息
        model_versions = scan_model_versions(env, model_name)

        # 检查端口状态
        for version in model_versions:
            if version.get('is_serving'):
                # 调用 check_service_status_api 获取端口状态
                status_response = check_service_status_api(env, model_name, version['model_version'])
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    version['recom_status'] = status_data.get('recom_status', {})
                    version['reward_status'] = status_data.get('reward_status', {})
                else:
                    version['recom_status'] = {}
                    version['reward_status'] = {}

        return jsonify({"status": "success", "model_versions": model_versions})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/model_versions_1", methods=["GET"])
def get_model_versions1():
    """按 Environment 查询模型版本信息"""
    try:
        env = request.args.get('env')
        model_name = request.args.get('model_name')

        if not env:
            return (
                jsonify(
                    {"status": "error", "message": "Environment parameter is required."}
                ),
                400,
            )

        # 扫描文件系统，获取模型版本信息
        model_versions = scan_model_versions(env, model_name)
        return jsonify({"status": "success", "model_versions": model_versions})
    except Exception as e:
        traceback.print_exc()  # 打印堆栈跟踪
        return jsonify({"status": "error", "message": str(e)}), 500
@app.route('/model_versions', methods=['GET'])
def get_model_versions_nn():
    """
    获取某个环境下的模型版本信息，区分当前服役版本和其他版本。
    """
    env = request.args.get('env')
    model_name = request.args.get('model_name')

    if not env or not model_name:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建模型目录
        model_dir = os.path.join(ENV_DIRS.get(env), model_name)

        # 读取 config.json 文件
        config_path = os.path.join(model_dir, 'config.json')
        with open(config_path, 'r') as f:
            config = json.load(f)

        # 获取当前服役版本
        current_version = config.get('current_version')

        # 扫描模型版本目录
        model_versions = []
        for version in os.listdir(model_dir):
            version_dir = os.path.join(model_dir, version)
            if os.path.isdir(version_dir):
                version_info = {
                    'model_name': model_name,
                    'model_version': version,
                    'is_serving': version == current_version,
                    'timestamp': os.path.getmtime(version_dir),
                    'size': get_directory_size(version_dir),
                }

                # 如果是当前服役版本，添加端口状态信息
                if version == current_version:
                    version_info['recomserver'] = []
                    for recom_config in config.get('recomserver', []):
                        version_info['recomserver'].append({
                            'port': recom_config.get('port'),
                            'status': check_service_status(recom_config.get('port')),
                        })

                    version_info['rewardserver'] = []
                    for reward_config in config.get('rewardserver', []):
                        version_info['rewardserver'].append({
                            'port': reward_config.get('port'),
                            'status': check_service_status(reward_config.get('port')),
                        })

                model_versions.append(version_info)

        # 按版本号从大到小排序
        model_versions.sort(key=lambda x: x['model_version'], reverse=True)

        return jsonify({
            "status": "success",
            "model_versions": model_versions,
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

def check_service_status222(port):
    """
    检查服务端口状态。
    :param port: 端口号
    :return: 状态（Running/Stopped）
    """
    if not port:
        return "Stopped"

    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    return "Running"
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return "Stopped"

import socket

def check_service_status( port,host="0.0.0.0"):
    """
    检查服务端口状态。
    :param host: 主机地址
    :param port: 端口号
    :return: 状态（Running/Stopped）
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1)  # 设置超时时间为 1 秒
        result = sock.connect_ex((host, port))
        return "Running" if result == 0 else "Stopped"


def get_directory_size(directory):
    """
    计算目录大小。
    :param directory: 目录路径
    :return: 目录大小（字节）
    """
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

@app.route('/restart_version', methods=['POST'])
def restart_version():
    """
    重启指定版本的服务实例。
    """
    env = request.args.get('env')
    model_name = request.args.get('model_name')
    model_version = request.args.get('model_version')
    service_name = request.args.get('service')  # 可选参数，指定重启的服务
    instance_index = request.args.get('instance_index', type=int)  # 可选参数，指定重启的实例索引

    if not env or not model_name or not model_version:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建 config.json 文件路径
        config_dir = os.path.join(ENV_DIRS.get(env), model_name)
        config_path = os.path.join(config_dir, "config.json")

        # 如果目录不存在，则创建目录
        os.makedirs(config_dir, exist_ok=True)

        # 加载或初始化配置
        config = load_or_initialize_config(config_path)

        # 更新当前服务中的版本
        config["current_version"] = model_version

        # 重启服务实例
        if service_name:
            if service_name not in config["services"]:
                return jsonify({"status": "error", "message": f"Service {service_name} not found"}), 404

            if instance_index is not None:
                # 重启指定实例
                if instance_index < 0 or instance_index >= len(config["services"][service_name]):
                    return jsonify({"status": "error", "message": f"Invalid instance index {instance_index}"}), 400
                restart_service_instance(env, model_name, model_version, service_name, instance_index, config)
            else:
                # 重启所有实例
                for index in range(len(config["services"][service_name])):
                    restart_service_instance(env, model_name, model_version, service_name, index, config)
        else:
            # 重启所有服务的所有实例
            for service in config["services"]:
                for index in range(len(config["services"][service])):
                    restart_service_instance(env, model_name, model_version, service, index, config)

        # 保存更新后的配置
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        return jsonify({"status": "success", "message": "Version restarted successfully"})
    except Exception as e:
        traceback.print_exc()  # 打印堆栈跟踪
        return jsonify({"status": "error", "message": str(e)}), 500


def restart_service_instance(env, model_name, model_version, service_name, instance_index, config):
    """
    重启指定服务的某个实例。
    """
    try:
        service_instances = config["services"][service_name]
        instance_config = service_instances[instance_index]

        # 停止当前实例
        if instance_config["status"] == "running" and instance_config["pid"]:
            os.kill(instance_config["pid"], signal.SIGTERM)  # 终止进程
            instance_config["status"] = "stopped"
            instance_config["pid"] = None

        # 启动实例
        pid = start_service_process(env, model_name, model_version, service_name, instance_config)
        instance_config["status"] = "running"
        instance_config["pid"] = pid

        print(f"Service {service_name} instance {instance_index} restarted successfully with PID {pid}")
    except Exception as e:
        traceback.print_exc()  # 打印堆栈跟踪
        print(f"Error restarting service {service_name} instance {instance_index}: {e}")
        instance_config["status"] = "error"
        instance_config["pid"] = None

@app.route('/service_instance_status', methods=['GET'])
def service_instance_status():
    """
    查询指定服务实例的状态。
    """
    env = request.args.get('env')
    model_name = request.args.get('model_name')
    service_name = request.args.get('service_name')
    instance_index = request.args.get('instance_index', type=int)

    if not env or not model_name or not service_name or instance_index is None:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建 config.json 文件路径
        config_dir = os.path.join(ENV_DIRS.get(env), model_name)
        config_path = os.path.join(config_dir, "config.json")

        # 加载或初始化配置
        config = load_or_initialize_config(config_path)

        if service_name not in config["services"]:
            return jsonify({"status": "error", "message": f"Service {service_name} not found"}), 404

        service_instances = config["services"][service_name]
        if instance_index < 0 or instance_index >= len(service_instances):
            return jsonify({"status": "error", "message": f"Invalid instance index {instance_index}"}), 400

        instance_config = service_instances[instance_index]
        return jsonify({"status": "success", "instance_status": instance_config})
    except Exception as e:
        traceback.print_exc()  # 打印堆栈跟踪
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/model_files', methods=['GET'])
def get_model_files():
    """
    获取某个版本下的文件/目录列表。
    """
    env = request.args.get('env')
    model_name = request.args.get('model_name')
    model_version = request.args.get('model_version')
    path = request.args.get('path', '')  # 默认为根目录

    if not env or not model_name or not model_version:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建模型版本的根目录
        base_dir = os.path.join(ENV_DIRS.get(env), model_name, model_version)
        target_dir = os.path.join(base_dir, path)

        if not os.path.exists(target_dir):
            return jsonify({"status": "error", "message": "Path not found"}), 404

        # 获取文件/目录列表
        files = []
        for item in os.listdir(target_dir):
            item_path = os.path.join(target_dir, item)
            item_info = {
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path),
                "last_modified": os.path.getmtime(item_path)
            }
            files.append(item_info)

        return jsonify({"status": "success", "files": files})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/model_file_content', methods=['GET'])
def get_model_file_content():
    """
    获取某个文件的内容。
    """
    env = request.args.get('env')
    model_name = request.args.get('model_name')
    model_version = request.args.get('model_version')
    path = request.args.get('path')

    if not env or not model_name or not model_version or not path:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建文件路径
        file_path = os.path.join(ENV_DIRS.get(env), model_name, model_version, path)

        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return jsonify({"status": "error", "message": "File not found"}), 404

        # 读取文件内容
        with open(file_path, "r") as f:
            content = f.read()

        return jsonify({"status": "success", "content": content})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/get_config', methods=['GET'])
def get_config():
    """
    获取配置文件内容。
    """
    env = request.args.get('env')
    model_name = request.args.get('model_name')

    if not env or not model_name:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建 config.json 文件路径
        config_path = os.path.join(ENV_DIRS.get(env), model_name, 'config.json')
        if not os.path.exists(config_path):
            return jsonify({"status": "error", "message": "Config file not found"}), 404

        with open(config_path, 'r') as f:
            config = json.load(f)
        return jsonify({"status": "success", "config": config})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/update_config', methods=['POST'])
@login_required
def update_config():
    """
    更新配置文件内容。
    """
    env = request.json.get('env')
    model_name = request.json.get('model_name')
    new_config = request.json.get('config')

    if not env or not model_name or not new_config:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建 config.json 文件路径
        config_path = os.path.join(ENV_DIRS.get(env), model_name, 'config.json')
        if not os.path.exists(config_path):
            return jsonify({"status": "error", "message": "Config file not found"}), 404

        # 保存配置文件
        with open(config_path, 'w') as f:
            json.dump(new_config, f, indent=4)
        user_id = session.get("_user_id")
        if user_id:
            username=get_user_name(session)
            add_log("更新配置", f"用户:{username} 更新了配置文件:{model_name}", user_id)

        return jsonify({"status": "success", "message": "Config updated successfully"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500

def check_service_status2(port):
    """
    检查指定端口的服务是否在运行。
    :param port: 服务端口
    :return: True 如果服务在运行，否则 False
    """
    for proc in psutil.process_iter(['pid', 'name', 'connections']):
        try:
            for conn in proc.connections():
                if conn.laddr.port == port:
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False

def get_final_script(script,log_file):
    run_cmd_contents = f"nohup sh {script} > {log_file} 2>&1 &"
    return run_cmd_contents

@app.route('/restart_services', methods=['POST'])
@login_required
def restart_services():
    """
    重启服务。
    """
    data = request.get_json()
    env = data.get('env')
    model_name = data.get('model_name')
    model_version = data.get('model_version')

    if not env or not model_name or not model_version:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建模型目录
        model_version_dir = os.path.join(ENV_DIRS.get(env), model_name, model_version)

        # 检查 start_services.sh 是否存在
        #start_script_path = os.path.join(model_version_dir, 'start_services.sh')
        # 生成 start_services.sh 脚本
        #generate_start_services_script(env, model_name, model_version)
        #if not os.path.exists(start_script_path):
        #    return jsonify({"status": "error", "message": "start_services.sh not found"}), 404

        # 执行 start_services.sh 脚本
        #result = start_service(start_script_path)
        #if "Error" in result:
        #    return jsonify({"status": "error", "message": result}), 500

        # 检查端口状态
        model_dir = os.path.join(ENV_DIRS.get(env), model_name)
        config_path = os.path.join(model_dir, 'config.json')
        

        with open(config_path, 'r') as f:
            config = json.load(f)

        # 更新当前服务中的版本
        config["current_version"] = model_version
         # 保存更新后的配置
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)

        # 逐个启动服务
        for service_type in ['recomserver', 'rewardserver']:
            for service_config in config.get(service_type, []):
                port = service_config.get('port')
                if not port:
                    continue

                # 检查端口是否被占用
                if is_port_in_use(port):
                    print(f"Port {port} is in use. Killing the process...")
                    kill_process_by_port(port)
                    time.sleep(1)  # 等待进程终止

                # 启动服务
                script_path = generate_service_script(env, model_name, model_version, service_type, service_config)
                log_file=f"run_{service_type}_{port}.log"
                log_path = os.path.join(ENV_DIRS.get(env), model_name, model_version, 'logs', log_file)
                result = start_service(get_final_script(script_path,log_path))
                if "Error" in result:
                    return jsonify({"status": "error", "message": result}), 500

                print(f"Started {service_type} on port {port}")
                time.sleep(3)  # 每个服务启动后等待 3 秒

        user_id = session.get("_user_id")
        if user_id:
            username=get_user_name(session)
            add_log("重启服务", f"用户:{username} 重启了服务：{model_name}-{model_version}", user_id)
        return jsonify({"status": "success", "message": "Services restarted successfully!"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500



@app.route('/check_service_status', methods=['GET'])
def check_service_status_api():
    """
    检查服务的运行状态。
    """
    env = request.args.get('env')
    model_name = request.args.get('model_name')
    model_version = request.args.get('model_version')

    if not env or not model_name or not model_version:
        return jsonify({"status": "error", "message": "Missing parameters"}), 400

    try:
        # 构建 config.json 文件路径
        config_path = os.path.join(ENV_DIRS.get(env), model_name, 'config.json')
        if not os.path.exists(config_path):
            return jsonify({"status": "error", "message": "Config file not found"}), 404

        with open(config_path, 'r') as f:
            config = json.load(f)

        # 检查 recomserver 服务状态
        recom_status = {}
        for recom_config in config.get('recomserver', []):
            port = recom_config.get('port')
            is_running = check_service_status(port)
            recom_status[port] = is_running

        # 检查 rewardserver 服务状态
        reward_status = {}
        for reward_config in config.get('rewardserver', []):
            port = reward_config.get('port')
            is_running = check_service_status(port)
            reward_status[port] = is_running

        return jsonify({
            "status": "success",
            "recom_status": recom_status,
            "reward_status": reward_status
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "message": str(e)}), 500


def main2():
    """命令行入口点"""
    app.run(host=SERVER_HOST, port=SERVER_PORT)

def main():
    """命令行入口点"""
    parser = argparse.ArgumentParser(description='OptiFlux Server')
    parser.add_argument('--env', 
                       choices=['dev', 'prod'],
                       default='dev',
                       help='运行环境: dev（开发）或 prod（生产）')
    parser.add_argument('--gunicorn',  # 新增参数
                        '-g',
                       action='store_true',
                       help='使用生产模式（Gunicorn）启动')
    args = parser.parse_args()

    # 加载对应环境配置
    from optiflux.config import get_config
    config = get_config(args.env)
    app.config.update({
        'ENV': args.env,
        'ENV_DIRS': config['ENV_DIRS']
    })

    if args.gunicorn:  # 生产模式
        gunicorn_options = {
            'bind': f"{config['SERVER_HOST']}:{config['SERVER_PORT']}",
            'workers': int(config.get('GUNICORN_WORKERS', 4)),
            'timeout': int(config.get('GUNICORN_TIMEOUT', 30)),
            'accesslog': '-',  # 访问日志输出到stdout
            'errorlog': '-',   # 错误日志输出到stderr
            'loglevel': 'info'
        }
        print(f"Starting PROD server (Gunicorn) on {gunicorn_options['bind']}")
        GunicornApp(app, gunicorn_options).run()
    else:  # 开发模式
        print(f"Starting DEV server (Flask) on {config['SERVER_HOST']}:{config['SERVER_PORT']}")
        app.run(
            host=config['SERVER_HOST'],
            port=config['SERVER_PORT'],
            debug=config.get('FLASK_DEBUG', True)
        )

if __name__ == "__main__":
    main()
