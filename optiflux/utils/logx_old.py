import time
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone, timedelta
from ..config import defu_logs_fnames, LOG_DIR

SHA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


def get_bj_day_time(sec, what):
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    beijing_now = utc_now.astimezone(SHA_TZ)
    return beijing_now.timetuple()


# 初始化日志记录器
def init_logging_handlers(log_name, log_dir=LOG_DIR):
    formatter = logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S")
    handler = TimedRotatingFileHandler(
        f"{log_dir}/{log_name}", when="midnight", backupCount=7, encoding="utf-8"
    )
    handler.setFormatter(formatter)
    logger = logging.getLogger(log_name)
    logger.addHandler(handler)
    return logger


def init():
    logging.Formatter.converter = get_bj_day_time
    logging.basicConfig(level=logging.DEBUG)

    # 初始化所有日志记录器
    loggers = {}
    for log_name in defu_logs_fnames:
        loggers[log_name] = init_logging_handlers(log_name)

    # 记录初始化完成状态
    log_content = [["status", "finish_logger_init"]]
    log_server(log_content)


# 格式化日志消息为键值对格式
def format_key_value(msg):
    msg.append(["_ts", int(time.time())])
    return "&".join([f"{k}={v}" for k, v in msg])


def do_format2(msg):
    ret = ""
    msg.append(["_ts", int(time.time())])
    for i in msg:
        ret += "%s=%s," % (i[0], str(i[1]))
    return ret[:-1]


def do_format(msg):
    """通用日志消息格式化器，带时间戳，支持中文"""
    formatted = []
    for item in msg:
        if isinstance(item, (list, tuple)) and len(item) == 2:
            # 确保键和值都转换为字符串
            key = str(item[0])
            value = str(item[1])
            formatted.append(f"{key}={value}")
    formatted.append(f"_ts={int(time.time())}")
    return "|".join(formatted)


# 格式化日志消息为逗号分隔的列表，包含时间戳
def format_csv(msg):
    msg.insert(0, int(time.time()))
    return ",".join(map(str, msg))


# 专门的日志记录函数
def log_error(logger_name, error_msg):
    logger_name = f"{logger_name}_errors"
    logger = logging.getLogger(f"{logger_name}.log")
    formatted_msg = do_format(error_msg)  # format_key_value([["error", error_msg]])
    getattr(logger, "info")(formatted_msg)


def log_info(logger_name, info_msg):
    logger_name = f"{logger_name}_debugs"
    logger = logging.getLogger(f"{logger_name}.log")
    formatted_msg = do_format(info_msg)  # format_key_value([["info", info_msg]])
    getattr(logger, "info")(formatted_msg)


# 网络日志
def log_net(msg):
    net_logger = logging.getLogger("net")
    net_logger.info(msg)


# 服务器日志
def log_server(msg):
    server_logger = logging.getLogger("server")
    formatted_msg = format_key_value(msg)
    server_logger.info(formatted_msg)


init()
