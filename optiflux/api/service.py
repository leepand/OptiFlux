import fastapi
from typing import Any, Dict, List, Optional
import uvicorn
import logging
from optiflux.core.library import ModelLibrary
from ..core.model import Model

# 配置日志
logger = logging.getLogger("optiflux.APIService")


class ModelkitAPIRouter(fastapi.APIRouter):
    def __init__(
        self,
        # ModelLibrary arguments
        model: Dict,
        **kwargs,
    ) -> None:
        # add custom startup/shutdown events
        super().__init__(**kwargs)

        self.lib = ModelLibrary(models=model, size_limit=5 * 1024**3)  # 5GB 缓存)


class ModelkitAutoAPIRouter(ModelkitAPIRouter):
    def __init__(
        self,
        # ModelLibrary arguments
        model: Dict,
        # paths overrides change the configuration key into a path
        route_paths: Optional[Dict[str, str]] = None,
        api_prefix: str = "",
        # APIRouter arguments
        **kwargs,
    ) -> None:
        super().__init__(
            model=model,
            **kwargs,
        )

        route_paths = route_paths or {}
        model_name = list(model.keys())[0]
        path = route_paths.get(model_name, f"{api_prefix}/predict/" + model_name)
        batch_path = route_paths.get(
            model_name, f"{api_prefix}/predict/batch/" + model_name
        )

        summary = ""
        description = ""
        m = model.get(model_name)
        if m.__doc__:
            doclines = m.__doc__.strip().split("\n")
            summary = doclines[0]
            if len(doclines) > 1:
                description = "".join(doclines[1:])

        logger.info(f"Adding model: {model_name}")
        # item_type = m._item_type or Any

        self.add_api_route(
            path,
            self._make_model_endpoint_fn(m, model_name),
            methods=["POST"],
            description=description,
            summary=summary,
            tags=[str(type(m).__module__)],
        )
        self.add_api_route(
            batch_path,
            self._make_batch_model_endpoint_fn(m, model_name),
            methods=["POST"],
            description=description,
            summary=summary,
            tags=[str(type(m).__module__)],
        )
        logger.info(f"Added model to service: {model_name}, path: {path}")

    def _make_model_endpoint_fn(self, model, model_name):
        if isinstance(model, Model):

            async def _aendpoint(
                item=fastapi.Body(...),
                model=fastapi.Depends(lambda: self.lib.get_model(model_name)),
            ):
                return await model._predict(item)

            return _aendpoint

        def _endpoint(
            item=fastapi.Body(...),
            model=fastapi.Depends(lambda: self.lib.get_model(model_name)),
        ):
            return model._predict(item)

        return _endpoint

    def _make_batch_model_endpoint_fn(self, model, model_name):
        if isinstance(model, Model):

            async def _aendpoint(
                item: List = fastapi.Body(...),
                model=fastapi.Depends(lambda: self.lib.get_model(model_name)),
            ):
                return await model._predict_batch(item)

            return _aendpoint

        def _endpoint(
            item: List = fastapi.Body(...),
            model=fastapi.Depends(lambda: self.lib.get_model(model_name)),
        ):
            return model._predict_batch(item)

        return _endpoint


def create_optiflux_app(model: Dict, **config):
    title = config.get("title")
    if title is None:
        title = "Optiflux API"
    version = "1.0"
    enable_docs = True
    app = fastapi.FastAPI(
        title=title, version=version, docs_url="/docs" if enable_docs else None
    )
    router = ModelkitAutoAPIRouter(model=model, **config)
    app.include_router(router)
    return app


def serve(model, host: str = "0.0.0.0", port: int = 8000, **config):
    """
    Run a library as a service.

    Run an HTTP server with specified models using FastAPI
    """
    app = create_optiflux_app(model=model, **config)
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
