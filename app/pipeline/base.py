"""Base Pipeline interface."""
from abc import ABC, abstractmethod
from typing import Any, Optional
from app.models.api import ConvertResponse


class BasePipeline(ABC):
    @abstractmethod
    def process(self, *args, **kwargs) -> ConvertResponse:
        """Process document through the pipeline and return ConvertResponse."""
        pass
