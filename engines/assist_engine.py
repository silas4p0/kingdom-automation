from typing import Any
from .base_engine import BaseEngine


class AssistEngine(BaseEngine):
    def preview(self, token_data: dict[str, Any]) -> bytes:
        return b""

    def render(self, project_data: dict[str, Any]) -> bytes:
        return b""

    def name(self) -> str:
        return "C AI Assist"
