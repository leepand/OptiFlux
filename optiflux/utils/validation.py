from typing import Any, Callable
from pydantic import BaseModel

def validate_input(
    schema: Callable[[Any], bool] = None,
    error_msg: str = "Invalid input"
):
    def decorator(func):
        def wrapper(*args, **kwargs):
            data = kwargs.get('input_data') or args[1]
            if schema and not schema(data):
                raise ValueError(error_msg)
            return func(*args, **kwargs)
        return wrapper
    return decorator