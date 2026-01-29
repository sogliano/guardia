"""Raw email storage for quarantine and deferred forwarding."""

import asyncio
import hashlib
from pathlib import Path

import structlog

from app.config import settings

logger = structlog.get_logger()


class EmailStorage:
    """Stores and retrieves raw email bytes on disk.

    Used for:
    - Quarantine: retain raw email until CISO releases/deletes it.
    - Deferred forwarding: retrieve raw email to relay to Google after release.
    """

    def __init__(self, base_path: str | None = None) -> None:
        self.base_path = Path(base_path or settings.quarantine_storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _case_path(self, case_id: str) -> Path:
        """Generate storage path for a case. Uses subdirectories for performance."""
        safe_id = hashlib.sha256(case_id.encode()).hexdigest()[:8]
        subdir = self.base_path / safe_id[:2]
        subdir.mkdir(parents=True, exist_ok=True)
        return subdir / f"{case_id}.eml"

    async def store(self, case_id: str, raw_data: bytes) -> str:
        """Store raw email bytes. Returns the file path."""
        path = self._case_path(case_id)
        await asyncio.to_thread(path.write_bytes, raw_data)
        logger.info("email_stored", case_id=case_id, path=str(path), size=len(raw_data))
        return str(path)

    async def retrieve(self, case_id: str) -> bytes | None:
        """Retrieve raw email bytes. Returns None if not found."""
        path = self._case_path(case_id)
        if not await asyncio.to_thread(path.exists):
            logger.warning("email_not_found", case_id=case_id, path=str(path))
            return None
        return await asyncio.to_thread(path.read_bytes)

    async def delete(self, case_id: str) -> bool:
        """Delete raw email from storage. Returns True if deleted."""
        path = self._case_path(case_id)
        if not await asyncio.to_thread(path.exists):
            return False
        await asyncio.to_thread(path.unlink)
        logger.info("email_deleted", case_id=case_id, path=str(path))
        return True

    async def exists(self, case_id: str) -> bool:
        """Check if raw email exists in storage."""
        return await asyncio.to_thread(self._case_path(case_id).exists)
