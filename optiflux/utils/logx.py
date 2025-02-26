import time
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone, timedelta
from ..config import defu_logs_fnames, LOG_DIR

SHA_TZ = timezone(timedelta(hours=8), name="Asia/Shanghai")


class LoggerManager:
    def __init__(self):
        self.loggers = {}
        self.init_logging()

    @staticmethod
    def get_bj_day_time(sec, what):
        utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
        beijing_now = utc_now.astimezone(SHA_TZ)
        return beijing_now.timetuple()

    def init_logging(self):
        # 设置日志时间转换器
        logging.Formatter.converter = self.get_bj_day_time

        # 创建日志目录（如果不存在）
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        # 初始化所有日志记录器
        for log_name in defu_logs_fnames:
            self.loggers[log_name] = self.init_logging_handler(log_name)

        # 记录初始化完成状态
        self.log_server([["status", "finish_logger_init"]])

    def init_logging_handler(self, log_name, log_dir=LOG_DIR):
        # 创建日志记录器
        logger = logging.getLogger(f"{log_name}")
        logger.setLevel(logging.DEBUG)  # 设置日志级别为 DEBUG

        # 创建文件处理器
        handler = TimedRotatingFileHandler(
            f"{log_dir}/{log_name}", when="midnight", backupCount=7, encoding="utf-8"
        )
        handler.setLevel(logging.DEBUG)  # 设置处理器级别为 DEBUG

        # 设置日志格式
        formatter = logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

        # 避免重复添加处理器
        if not logger.handlers:
            logger.addHandler(handler)

        return logger

    def format_log_message(self, msg, format_type="key_value"):
        msg.append(["_ts", int(time.time())])
        if format_type == "key_value":
            return "&".join([f"{k}={v}" for k, v in msg])
        elif format_type == "csv":
            return ",".join(map(str, msg))
        elif format_type == "pipe":
            return "|".join([f"{k}={v}" for k, v in msg])
        else:
            raise ValueError("Unsupported format type")

    def log(self, logger_name, msg, level="info", format_type="key_value"):
        logger = self.loggers.get(f"{logger_name}.log")
        if not logger:
            logger = self.init_logging_handler(logger_name)
            self.loggers[logger_name] = logger

        formatted_msg = self.format_log_message(msg, format_type)
        getattr(logger, level)(formatted_msg)

    def log_error(self, logger_name, error_msg, format_type="key_value"):
        self.log(f"{logger_name}_errors", [["error", error_msg]], "error", format_type)

    def log_info(self, logger_name, info_msg, format_type="key_value"):
        self.log(f"{logger_name}_debugs", [["info", info_msg]], "info", format_type)

    def log_net(self, msg, format_type="key_value"):
        self.log("net", msg, "info", format_type)

    def log_server(self, msg, format_type="key_value"):
        self.log("server", msg, "info", format_type)


"""# 初始化日志管理器
logger_manager = LoggerManager()

# 示例用法
logger_manager.log_info("example", [["key1", "value1"], ["key2", "value2"]])
logger_manager.log_error("example", [["error", "An error occurred"]])
logger_manager.log_net([["request", "GET /api/data"], ["response", "200 OK"]])
logger_manager.log_server([["status", "server_started"], ["port", "8080"]])
"""
