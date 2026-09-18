"""Abstract base parser interface."""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from app.models.document import UnifiedDocument


class BaseParser(ABC):
    """Base parser interface that all format adapters must implement."""

    @abstractmethod
    def parse(
        self,
        source: Union[Path, str],
        document_id: Optional[str] = None,
        force_ocr: bool = False,
        tenant: Optional[str] = None,
        **kwargs,
    ) -> UnifiedDocument:
        """Parse source file or URL into a UnifiedDocument instance."""
        pass
