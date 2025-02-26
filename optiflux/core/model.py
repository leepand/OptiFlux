from abc import ABC, abstractmethod
from typing import Any, Dict, List
import logging

# 配置日志
logger = logging.getLogger("optiflux.Model")


class Model(ABC):
    # 类属性：定义默认配置（子类可覆盖）
    """模型基类（支持依赖注入）"""
    DEFAULT_CONFIG: Dict[str, Any] = {}
    depends: List[str] = []  # 声明依赖的模型名称（子类可覆盖）

    def __init__(self, config: Dict[str, Any]):
        """
        :param config: 用户提供的配置（优先使用）
        """
        logger.info(f"Initializing model with config: {config}")
        # 合并默认配置和用户配置
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}
        self._depends: Dict[str, "Model"] = {}  # 初始化依赖字典

    def add_dependency(self, name: str, model: "Model"):
        self._depends[name] = model

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def _predict(self, input_data: Any) -> Any:
        pass

    def _predict_batch(self, inputs: List[Any]) -> List[Any]:
        """批量预测（默认实现为循环调用单条预测，可重写优化）"""
        return [self._predict(item) for item in inputs]
