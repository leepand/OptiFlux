# OptiFlux

OptiFlux 是一个轻量级的 MLOps 工具，专为代码部署、日志记录和版本管理而设计。

## 安装

您可以使用 pip 安装 OptiFlux：

```bash
pip install .


## 更新目录结构
```py
OptiFlux/
├── optiflux/
│   ├── client/          # 客户端相关代码
│   ├── server/          # 服务器相关代码
│   ├── utils/           # 实用工具和辅助函数
│   ├── __init__.py      # 初始化文件
│   ├── config.py        # 配置文件
│   └── models.py        # 数据模型
├── templates/           # 存放 HTML 文件
│   └── index.html       # 主页模板
├── static/              # 存放静态文件（CSS/JS）
│   ├── css/
│   │   └── styles.css   # 样式表
│   └── js/
│       └── scripts.js   # JavaScript 文件
├── setup.py             # 安装脚本
├── README.md            # 项目说明文档
└── requirements.txt     # 项目依赖
```

## 使用方法

### OptiFlux 提供了一个命令行工具，可以通过以下命令使用：

```bash
optiflux <command> [options]
```

#### 可用命令

init

初始化环境配置。

```bash
optiflux init [-f FILE] [--force]
```
- -f, --file: 生成的环境文件名 (默认: .env)。
- --force: 强制覆盖已存在文件。

示例：

```bash
optiflux init --file .env --force
```
create-project

创建模型项目。

```bash
optiflux create-project --name <model_name> [--version <version>]
```
- --name: 模型名称 (必需)。
- --version: 版本号 (默认: 0.0)。
示例：

```bash
optiflux create-project --name mymodel --version 1.0
```
#### 示例工作流程
1. 初始化环境配置：
```bash
optiflux init --file .env --force
```
2. 创建模型项目：
```bash
optiflux create-project --name mymodel --version 1.0
```

**项目结构**

生成的模型项目结构如下：

```bash
mymodel/
├── 0.1/
│   ├── config.yml
│   ├── requirements.txt
│   ├── README.md
│   └── src/
│       ├── __init__.py
│       ├── decision_module.py
│       ├── strategy_module.py
│       ├── model.py
│       ├── recomserver.py
│       ├── rewardserver.py
│       └── utils/
│           ├── __init__.py
│           ├── config_loader.py
│           └── validation.py
└── .gitignore
```
**配置文件**

生成的 .env 文件包含以下默认配置：

```bash
# OptiFlux 环境配置
# 服务器基础配置
SERVER_HOST=0.0.0.0
SERVER_PORT=8912

# 模型目录配置
DEV_ENV_DIR=./models/dev
PREPROD_ENV_DIR=./models/preprod
PROD_ENV_DIR=./models/prod

# 日志配置
LOG_DIR=./logs

# Flask 开发模式配置
FLASK_DEBUG=true

# Gunicorn 生产模式配置
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=30
GUNICORN_LOGLEVEL=info
```

这将生成一个包含默认目录结构和配置文件的项目。

## 启动前端管理-服务
optiflux-server
python -m optiflux.server.server --env prod  -g
python -m optiflux.server.server --env dev

### Deploy Code

optiflux-client --path /path/to/code --env dev

## License

This project is licensed under the MIT License.



