import logging
from diskcache import Cache
from typing import Any, Optional
import os
from pathlib import Path
from ..utils.file_utils import data_dir_default
import json

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


CACHE_CONFIG = os.path.join(data_dir_default(), "cache_config.json")
# 从文件加载
with open(CACHE_CONFIG, "r", encoding="utf-8") as f:
    CACHE_DIRS = json.load(f)


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
    env: str,
    model_name: str,
    db_name: str,
    model_version: Optional[str] = None,
    default_version: str = "0.0",  # 允许配置默认版本
    use_sys_path=True,
) -> Optional[ModelCache]:
    """
    优化后的缓存创建函数，支持更健壮的路径处理和错误反馈

    Args:
        env: 环境名称 (e.g. "dev")
        model_name: 模型名称
        db_name: 数据库名称
        model_version: 模型版本 (可选)
        default_version: 默认版本号 (从配置读取更佳)

    Returns:
        ModelCache 实例或 None
    """
    try:
        # 使用 Pathlib 处理路径
        base_path: Path
        if use_sys_path:
            if model_version:
                base_path = f"{CACHE_DIRS[env]}/{model_name}/{model_version}"
            else:
                base_path = f"{CACHE_DIRS[env]}/{model_name}/{default_version}"

            # 统一构建缓存目录路径
            cache_dir = Path(base_path) / "dbs" / db_name
            logger.debug(f"最终缓存目录: {cache_dir}")

            # 确保目录结构存在
            cache_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"已创建缓存目录: {cache_dir}")

            return ModelCache(cache_dir=str(cache_dir))

        # 场景1: 有明确版本号时
        if model_version:
            fragment = f"{env}/{model_name}/{model_version}"
            found_path = find_directory_from_fragment(fragment)

            if found_path:
                base_path = Path(found_path)
                logger.debug(f"精确匹配版本路径: {base_path}")
            else:
                logger.warning(f"版本路径 {fragment} 未找到，尝试回退方案")
                raise ValueError("Version path not found")

        # 场景2: 无版本号时使用默认版本
        else:
            fragment = f"{env}/{model_name}"
            found_path = find_directory_from_fragment(fragment)

            if found_path:
                base_path = Path(found_path) / default_version
                logger.debug(f"使用默认版本路径: {base_path}")
            else:
                base_path = Path(os.getcwd()) / f"{env}/{model_name}" / default_version

        # 统一构建缓存目录路径
        cache_dir = base_path / "dbs" / db_name
        logger.debug(f"最终缓存目录: {cache_dir}")

        # 确保目录结构存在
        cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"已创建缓存目录: {cache_dir}")

        return ModelCache(cache_dir=str(cache_dir))

    except Exception as e:
        logger.error(f"创建缓存失败: {str(e)}", exc_info=True)
        return None


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
