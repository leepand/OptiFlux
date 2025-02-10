# optiflux/models.py

from pydantic import BaseModel


class DeployRequest(BaseModel):
    env: str
    file: bytes


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str
