import logging
from pathlib import Path
from typing import Dict, Type, Any, List, Optional
from .model import BaseModel
from .cache import ModelCache
from optiflux.utils.config_loader import load_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger("optiflux.ModelLibrary")

class ModelLibrary:
    """模型库：集中管理模型配置和实例"""
    def __init__(
        self,
        models: Dict[str, Type[BaseModel]],
        config_path: Optional[str] = None,
        cache_dir: str = "optiflux_cache",
        **cache_kwargs
    ):
        """
        :param models: 模型名称到模型类的映射
        :param config_path: 配置文件路径（可选）
        """
        logger.info("Initializing ModelLibrary...")
        self.models = models
        # 加载配置并填充默认值
        self.config = self._load_config_with_defaults(config_path)
        self.cache = ModelCache(cache_dir, **cache_kwargs)
        self._model_instances: Dict[str, BaseModel] = {}
        self._initialize_models()
        logger.info("ModelLibrary initialized successfully.")

    def _load_config_with_defaults(self, config_path: Optional[str]) -> Dict[str, dict]:
        """加载配置并自动填充缺失模型的默认配置"""
        loaded_config = {}
        if config_path:
            try:
                logger.info(f"Loading config from: {config_path}")
                loaded_config = load_config(config_path)
            except FileNotFoundError:
                logger.warning(f"Config file {config_path} not found, using defaults")
        else:
            logger.info("No config file provided, using defaults.")

        # 为每个模型生成最终配置（合并默认值）
        final_config = {}
        for model_name, model_cls in self.models.items():
            user_config = loaded_config.get(model_name, {})
            final_config[model_name] = user_config
            
            # 记录缺失配置警告
            if model_name not in loaded_config:
                logger.info(f"Using default config for model: {model_name}")

        return final_config

    # core/library.py
    def _initialize_models(self):
        """初始化模型实例（确保依赖模型先加载）"""
        logger.info(f"Loading {len(self.models)} models...")

        # 按依赖顺序加载模型
        loaded_models = set()
        while len(loaded_models) < len(self.models):
            progress = False  # 标记本轮是否有模型加载
            for model_name, model_cls in self.models.items():
                if model_name in loaded_models:
                    continue  # 已加载的模型跳过

                # 检查依赖是否已加载
                dependencies = getattr(model_cls, "depends", [])
                if all(dep in loaded_models for dep in dependencies):
                    logger.info(f"Loading model: {model_name}")
                    config = self.config.get(model_name, {})
                    instance = model_cls(config)

                    # 注入依赖模型
                    for dep_name in dependencies:
                        instance.add_dependency(dep_name, self._model_instances[dep_name])

                    instance.load()
                    self._model_instances[model_name] = instance
                    loaded_models.add(model_name)
                    progress = True  # 标记本轮有模型加载
                    logger.info(f"Model {model_name} loaded successfully.")
                else:
                    missing_deps = [dep for dep in dependencies if dep not in loaded_models]
                    logger.warning(f"Model {model_name} is waiting for dependencies: {missing_deps}")

            # 如果本轮没有模型加载，说明存在循环依赖
            if not progress:
                raise RuntimeError("Circular dependency detected in models.")

        logger.info("All models loaded.")

    def _initialize_models3(self):
        """初始化模型实例（自动合并默认配置）"""
        logger.info(f"Loading {len(self.models)} models...")
        for model_name, model_cls in self.models.items():
            logger.info(f"Loading model: {model_name}")
            config = self.config.get(model_name, {})
            instance = model_cls(config)
            instance.load()
            self._model_instances[model_name] = instance
            logger.info(f"Model {model_name} loaded successfully.")
        logger.info("All models loaded.")

    def _initialize_models2(self):
        """初始化所有注册的模型实例（带依赖解析）"""
        # 依赖解析逻辑（示例简化）
        initialized = set()
        for model_name in self.models:
            if model_name not in initialized:
                self._load_model(model_name, initialized)

    def _load_model(self, model_name: str, initialized: set):
        """递归加载模型及其依赖"""
        model_cls = self.models[model_name]
        deps = getattr(model_cls, "dependencies", [])

        # 先加载依赖
        for dep in deps:
            if dep not in initialized:
                self._load_model(dep, initialized)

        # 实例化当前模型
        if model_name not in self.config:
            raise ValueError(f"Missing config for {model_name}")
        
        instance = model_cls(self.config[model_name])
        
        # 注入依赖
        for dep in deps:
            instance.add_dependency(dep, self._model_instances[dep])
        
        instance.load()
        self._model_instances[model_name] = instance
        initialized.add(model_name)

    def get_model(self, name: str) -> BaseModel:
        """获取已加载的模型实例"""
        if name not in self._model_instances:
            logger.error(f"Model {name} not found in library")
            raise KeyError(f"Model {name} not loaded")
        return self._model_instances[name]

    def predict(
        self,
        model_name: str,
        input_data: Any,
        cache_key: Optional[str] = None,
        use_cache: bool = False,  # 添加此参数
        **kwargs
    ) -> Any:
        """执行预测（带缓存支持）"""
        if use_cache:
            cached_result = self.cache.get(cache_key)
            if cached_result is not None:
                return cached_result

        # 执行预测
        model = self.get_model(model_name)
        result = model.predict(input_data, **kwargs)

        if use_cache and cache_key:
            self.cache.set(cache_key, result)

        return result
    
    # 在 ModelLibrary 类中新增方法
    def predict_batch(
        self,
        model_name: str,
        inputs: List[Any],
        cache_keys: Optional[List[str]] = None,
        use_cache: bool = True,
        **kwargs
    ) -> List[Any]:
        """批量预测（带缓存支持）"""
        model = self.get_model(model_name)

        # 生成默认缓存键
        if cache_keys is None and use_cache:
            cache_keys = [f"{model_name}_{hash(str(item))}" for item in inputs]

        results = []

        # 先尝试获取缓存
        cached_results = []
        if use_cache and cache_keys:
            cached_results = [self.cache.get(key) for key in cache_keys]
        else:
            cached_results = [None] * len(inputs)

        # 筛选需要预测的索引
        need_predict_indices = [i for i, val in enumerate(cached_results) if val is None]
        need_predict_items = [inputs[i] for i in need_predict_indices]

        if need_predict_items:
            # 执行批量预测
            new_results = model.predict_batch(need_predict_items, **kwargs)

            # 存储新结果到缓存
            if use_cache and cache_keys:
                with self.cache.transact():  # 使用事务保证原子性
                    for idx, result in zip(need_predict_indices, new_results):
                        self.cache.set(cache_keys[idx], result)

            # 合并结果
            result_ptr = 0
            for i in range(len(inputs)):
                if cached_results[i] is not None:
                    results.append(cached_results[i])
                else:
                    results.append(new_results[result_ptr])
                    result_ptr += 1
        else:
            results = cached_results

        return results