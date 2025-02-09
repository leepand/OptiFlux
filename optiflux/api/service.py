from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import uvicorn
import logging
from optiflux.core.library import ModelLibrary

# 配置日志
logger = logging.getLogger("optiflux.APIService")


class APIService:
    def __init__(
        self,
        library: ModelLibrary,
        title: str = "Optiflux API",
        version: str = "1.0",
        api_prefix: str = "/api/v1",
        enable_docs: bool = True
    ):
        logger.info("Initializing APIService...")
        self.app = FastAPI(title=title, version=version, docs_url="/docs" if enable_docs else None)
        self.library = library
        self.api_prefix = api_prefix
        self._register_routes()
        logger.info("APIService initialized successfully.")

    def _register_routes(self):
        # 定义请求体模型
        class PredictRequest(BaseModel):
            data: Any
            cache_key: Optional[str] = None
            use_cache: Optional[bool] = True  # 添加可选参数

        # 修改预测端点
        @self.app.post(f"{self.api_prefix}/predict/{{model_name}}")
        async def predict_endpoint(
            model_name: str,
            request: PredictRequest  # 使用新的请求模型
        ) -> Dict[str, Any]:
            try:
                result = self.library.predict(
                    model_name=model_name,
                    input_data=request.data,
                    cache_key=request.cache_key,
                    use_cache=request.use_cache  # 正确传递参数
                )
                return result
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # 在 APIService 类中新增批量预测端点
        @self.app.get("/health")
        def health_check():
            return {"status": "healthy"}

        # 添加批量请求模型
        class BatchPredictRequest(BaseModel):
            items: List[Any]
            cache_keys: Optional[List[str]] = None
            use_cache: Optional[bool] = True

        # 添加批量预测端点
        @self.app.post(f"{self.api_prefix}/batch_predict/{{model_name}}")
        async def batch_predict(
            model_name: str,
            request: BatchPredictRequest
        ) -> Dict[str, Any]:
            try:
                results = self.library.predict_batch(
                    model_name=model_name,
                    inputs=request.items,
                    cache_keys=request.cache_keys,
                    use_cache=request.use_cache
                )
                return results
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Batch prediction failed: {str(e)}"
                )

        for model_name in self.library.models:
            self._add_model_endpoint(model_name)

    def _add_model_endpoint(self, model_name: str):
        class RequestBody(BaseModel):
            data: Any
            cache_key: Optional[str] = None

        @self.app.post(f"{self.api_prefix}/predict/{model_name}")
        async def predict(
            request: RequestBody,
            use_cache: bool = True
        ) -> Dict[str, Any]:
            try:
                result = self.library.predict(
                    model_name=model_name,
                    input_data=request.data,
                    cache_key=request.cache_key,
                    use_cache=use_cache
                )
                return {"result": result, "cached": False}
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=str(e)
                )

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        logger.info(f"Starting API server on {host}:{port}")
        uvicorn.run(self.app, host=host, port=port, **kwargs)


def create_optiflux_app(library: ModelLibrary, **config) -> APIService:
    return APIService(library=library, **config)


 
