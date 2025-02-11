from gunicorn.app.base import BaseApplication  # 新增


class GunicornApp(BaseApplication):  # 新增：Gunicorn 适配器
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {
            key: value
            for key, value in self.options.items()
            if key in self.cfg.settings and value is not None
        }
        for key, value in config.items():
            self.cfg.set(key, value)

    def load(self):
        return self.application
