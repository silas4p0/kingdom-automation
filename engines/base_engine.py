from abc import ABC, abstractmethod
from typing import Any


class BaseEngine(ABC):
    @abstractmethod
    def preview(self, token_data: dict[str, Any]) -> bytes:
        ...

    @abstractmethod
    def render(self, project_data: dict[str, Any]) -> bytes:
        ...

    @abstractmethod
    def name(self) -> str:
        ...
