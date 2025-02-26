import logging
from diskcache import Cache
from typing import Any, Optional
import os
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ModelCache:
    def __init__(self, cache_dir: str, size_limit: int = int(100e9), **kwargs):
        """
        初始化缓存实例。

        Args:
            cache_dir (str): 缓存目录路径。
            size_limit (int): 缓存大小限制，默认为 1GB。
            **kwargs: 传递给 `diskcache.Cache` 的其他参数。
        """
        self.cache = Cache(cache_dir, size_limit=size_limit, **kwargs)
        logger.info(f"初始化缓存，目录: {cache_dir}，大小限制: {size_limit} bytes")

    def get(self, key: str) -> Optional[Any]:
        """
        从缓存中获取值。

        Args:
            key (str): 缓存的键。

        Returns:
            Optional[Any]: 如果键存在则返回对应的值，否则返回 None。
        """
        value = self.cache.get(key)
        # logger.debug(f"从缓存中获取键 '{key}'，值: {value}")
        return value

    def set(self, key: str, value: Any, expire: int = 3600):
        """
        将值存储到缓存中。

        Args:
            key (str): 缓存的键。
            value (Any): 要缓存的值。
            expire (int): 缓存过期时间（秒），默认为 1 小时。
        """
        self.cache.set(key, value, expire=expire)
        # logger.debug(f"将键 '{key}' 存储到缓存中，值: {value}，过期时间: {expire} 秒")

    def clear(self):
        """清空缓存。"""
        self.cache.clear()
        logger.info("缓存已清空")


def find_directory_from_fragment(fragment: str) -> Optional[str]:
    """
    根据当前代码文件的位置和给定的片段查找目录。

    Args:
        fragment (str): 目录片段（例如 "m/0.0"）。

    Returns:
        Optional[str]: 如果找到匹配的目录则返回路径，否则返回 None。
    """
    # 获取当前代码文件的绝对路径
    current_file_path = Path(__file__).resolve()
    logger.debug(f"当前代码文件路径: {current_file_path}")

    # 获取当前文件所在的目录路径
    current_dir = current_file_path.parent
    logger.debug(f"当前目录路径: {current_dir}")

    # 将当前目录路径拆分为部分
    parts = current_dir.parts

    # 将片段拆分为部分
    fragment_parts = fragment.split("/")

    # 查找片段在路径中的位置
    try:
        # 查找片段的第一部分在路径中的索引
        start_index = parts.index(fragment_parts[0])
        logger.debug(f"片段 '{fragment_parts[0]}' 在路径中的索引: {start_index}")

        # 检查路径中的后续部分是否与片段匹配
        for i, part in enumerate(fragment_parts):
            if parts[start_index + i] != part:
                logger.warning(f"片段 '{part}' 不匹配路径 '{parts[start_index + i]}'")
                raise ValueError("片段不匹配")

        # 构建并返回新目录路径
        new_dir = Path(*parts[: start_index + len(fragment_parts)])
        logger.info(f"根据片段 '{fragment}' 找到目录: {new_dir}")
        return str(new_dir)

    except (ValueError, IndexError) as e:
        logger.warning(f"无法根据片段 '{fragment}' 找到目录: {e}")
        return None


def make(
    env: str, model_name: str, db_name, model_version: Optional[str] = None
) -> Optional[ModelCache]:
    """
    根据环境和模型信息创建缓存实例。

    Args:
        env (str): 环境名称（例如 "dev"）。
        model_name (str): 模型名称。
        model_version (Optional[str]): 模型版本，可选。

    Returns:
        Optional[ModelCache]: 如果成功则返回缓存实例，否则返回 None。
    """
    # 构建片段路径
    if model_version is not None:
        db0 = False
        fragment_path = f"{env}/{model_name}/{model_version}"
    else:
        db0 = True
        fragment_path = f"{env}/{model_name}"

    logger.debug(f"构建片段路径: {fragment_path}")

    # 查找目录
    db_path = find_directory_from_fragment(fragment_path)
    if not db_path:
        logger.error(f"无法找到片段路径 '{fragment_path}' 对应的目录")
        return None

    # 构建缓存目录路径
    if db0:
        db_path_formake = os.path.join(db_path, "0.0/dbs")
    else:
        db_path_formake = os.path.join(db_path, "dbs")

    logger.debug(f"缓存目录路径: {db_path_formake}")

    # 确保目标目录存在
    os.makedirs(os.path.dirname(db_path_formake), exist_ok=True)
    logger.info(f"创建目录: {os.path.dirname(db_path_formake)}")

    # 初始化缓存实例
    db_name_path = f"{db_path_formake}/{db_name}"
    db_cache = ModelCache(cache_dir=db_name_path)
    logger.info(f"初始化缓存实例，目录: {db_name_path}")

    return db_cache


# 示例用法
"""if __name__ == "__main__":
    # 示例参数
    env = "dev"
    model_name = "model1"
    model_version = "1.0"

    # 创建缓存实例
    cache = make(env, model_name, model_version)
    if cache:
        # 使用缓存
        cache.set("key1", "value1")
        value = cache.get("key1")
        print(f"从缓存中获取的值: {value}")
    else:
        print("无法创建缓存实例")
"""
