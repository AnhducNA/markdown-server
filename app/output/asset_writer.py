"""Asset writer module for extracted images and charts."""
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.document import Asset
from app.output.writer import sanitize_filename


class AssetWriter:
    """Writes extracted document assets (images, figures) to disk."""

    def __init__(
        self,
        base_asset_dir: Optional[Path] = None,
        overwrite: Optional[bool] = None,
    ):
        self.base_asset_dir = Path(base_asset_dir) if base_asset_dir else settings.asset_output_dir
        self.overwrite = settings.output_overwrite if overwrite is None else overwrite

    def get_asset_dir(self, document_id: str, tenant: Optional[str] = None) -> Path:
        """Get destination directory for document assets."""
        safe_id = sanitize_filename(document_id)
        if tenant:
            return self.base_asset_dir / sanitize_filename(tenant) / safe_id
        return self.base_asset_dir / safe_id

    def write_assets(
        self,
        document_id: str,
        assets: List[Asset],
        tenant: Optional[str] = None,
    ) -> List[Path]:
        """Save raw asset data into the document's asset folder."""
        saved_paths: List[Path] = []
        if not assets:
            return saved_paths

        target_dir = self.get_asset_dir(document_id, tenant)
        target_dir.mkdir(parents=True, exist_ok=True)

        for asset in assets:
            if asset.data:
                safe_name = sanitize_filename(asset.name)
                dest = target_dir / safe_name
                dest.write_bytes(asset.data)
                saved_paths.append(dest)
                logger.debug(f"Saved asset {asset.name} to {dest}")

        return saved_paths
