"""
In-memory email ingestion queue with gradual processing.

This module provides a background queue system that processes emails gradually
at a configurable rate (default: 1 email every 5 seconds).

For production, consider migrating to Redis or RabbitMQ for persistence
and multi-worker support.
"""

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any

import structlog

from app.db.session import async_session_factory
from app.models.email import Email
from app.models.case import Case
from app.services.pipeline.orchestrator import PipelineOrchestrator

logger = structlog.get_logger()


class IngestionQueue:
    """
    FIFO queue for gradual email ingestion.

    Features:
    - Loads dataset of emails
    - Processes 1 email every N seconds (configurable)
    - Executes full pipeline for each email
    - Tracks progress and statistics
    """

    def __init__(self, interval_seconds: float = 5.0) -> None:
        self.queue: deque[dict[str, Any]] = deque()
        self.interval_seconds = interval_seconds
        self.is_running = False
        self.task: asyncio.Task | None = None
        self.stats = {
            "total": 0,
            "processed": 0,
            "failed": 0,
            "started_at": None,
            "completed_at": None,
        }

    def load_dataset(self, dataset: list[dict[str, Any]]) -> None:
        """Load email dataset into the queue."""
        self.queue.extend(dataset)
        self.stats["total"] = len(dataset)
        logger.info("dataset_loaded", count=len(dataset))

    async def start(self) -> None:
        """Start background processing of the queue."""
        if self.is_running:
            raise RuntimeError("Queue already running")

        self.is_running = True
        self.stats["started_at"] = datetime.now(timezone.utc)
        self.task = asyncio.create_task(self._process_loop())
        logger.info(
            "ingestion_started",
            total=self.stats["total"],
            interval=self.interval_seconds,
        )

    async def stop(self) -> None:
        """Stop background processing."""
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        self.stats["completed_at"] = datetime.now(timezone.utc)
        logger.info("ingestion_stopped", stats=self.stats)

    def get_stats(self) -> dict[str, Any]:
        """Return current queue statistics."""
        return {
            **self.stats,
            "queue_remaining": len(self.queue),
            "is_running": self.is_running,
        }

    async def _process_loop(self) -> None:
        """Main loop that processes emails from the queue."""
        while self.is_running and len(self.queue) > 0:
            try:
                entry = self.queue.popleft()
                await self._process_email(entry)
                self.stats["processed"] += 1

                # Wait before processing next email
                if len(self.queue) > 0:
                    await asyncio.sleep(self.interval_seconds)

            except Exception as exc:
                self.stats["failed"] += 1
                logger.error(
                    "email_processing_failed",
                    error=str(exc),
                    entry=entry.get("template_name", "unknown"),
                )

        # Mark as completed
        self.is_running = False
        self.stats["completed_at"] = datetime.now(timezone.utc)
        logger.info("ingestion_completed", stats=self.stats)

    async def _process_email(self, entry: dict[str, Any]) -> None:
        """
        Process a single email: build RFC 5322, persist, execute pipeline.

        Args:
            entry: EmailDatasetEntry with template_name, recipient, etc.
        """
        from backend.scripts.email_templates import TEMPLATES
        from app.gateway.parser import EmailParser

        # 1. Build email using template
        template_name = entry["template_name"]
        if template_name not in TEMPLATES:
            raise ValueError(f"Template not found: {template_name}")

        template_fn, _ = TEMPLATES[template_name]
        rfc_email = template_fn(recipient=entry["recipient"])

        # 2. Parse to EmailIngest
        parser = EmailParser()
        raw_bytes = rfc_email.as_bytes()
        email_dict = parser.parse_raw(
            raw_data=raw_bytes,
            envelope_from=rfc_email["From"],
            envelope_to=[entry["recipient"]],
        )

        # 3. Persist to DB
        async with async_session_factory() as session:
            email = Email(
                message_id=email_dict["message_id"],
                sender_email=email_dict["sender_email"],
                sender_name=email_dict["sender_name"],
                reply_to=email_dict["reply_to"],
                recipient_email=email_dict["recipient_email"],
                recipients_cc=email_dict["recipients_cc"],
                subject=email_dict["subject"],
                body_text=email_dict["body_text"],
                body_html=email_dict["body_html"],
                headers=email_dict["headers"],
                urls=email_dict["urls"],
                attachments=email_dict["attachments"],
                auth_results=email_dict["auth_results"],
                received_at=email_dict["received_at"],
            )
            session.add(email)
            await session.commit()
            await session.refresh(email)

            # 4. Create case
            case = Case(email_id=email.id, status="pending")
            session.add(case)
            await session.commit()
            await session.refresh(case)

            # 5. Run pipeline
            orchestrator = PipelineOrchestrator(session)
            result = await orchestrator.analyze(email.id)

            logger.info(
                "email_processed",
                email_id=str(email.id),
                case_id=str(case.id),
                verdict=result.verdict,
                score=result.final_score,
                category=entry["category"],
                template=template_name,
            )


# Singleton global queue instance
_global_queue: IngestionQueue | None = None


def get_queue() -> IngestionQueue:
    """Return the global singleton queue instance."""
    global _global_queue
    if _global_queue is None:
        _global_queue = IngestionQueue(interval_seconds=5.0)
    return _global_queue
