"""
Unit tests for email ingestion queue.

Tests the gradual ingestion system that processes emails from a dataset
at a configurable rate.
"""

import asyncio

import pytest

from app.services.ingestion.queue import IngestionQueue
from scripts.datasets.email_dataset_50 import DATASET_50, get_by_category


@pytest.mark.asyncio
async def test_queue_loads_dataset():
    """Test that queue correctly loads a dataset."""
    queue = IngestionQueue()
    queue.load_dataset(DATASET_50)

    assert queue.stats["total"] == 50
    assert len(queue.queue) == 50


@pytest.mark.asyncio
async def test_queue_loads_filtered_dataset():
    """Test that queue correctly loads a filtered dataset."""
    queue = IngestionQueue()
    phishing_emails = get_by_category("phishing")
    queue.load_dataset(phishing_emails)

    assert queue.stats["total"] == len(phishing_emails)
    assert len(queue.queue) == len(phishing_emails)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires database connection")
async def test_queue_processes_emails(db_session):
    """Test that queue processes emails and tracks statistics."""
    queue = IngestionQueue(interval_seconds=0.1)  # Fast for testing

    # Use only first 3 emails for speed
    test_dataset = DATASET_50[:3]
    queue.load_dataset(test_dataset)

    # Start processing
    await queue.start()

    # Wait for completion (0.1s * 3 emails + buffer)
    await asyncio.sleep(1)

    stats = queue.get_stats()
    assert stats["processed"] == 3
    assert stats["failed"] == 0
    assert stats["is_running"] is False
    assert stats["started_at"] is not None
    assert stats["completed_at"] is not None


@pytest.mark.asyncio
async def test_queue_can_be_stopped():
    """Test that queue can be stopped mid-processing."""
    queue = IngestionQueue(interval_seconds=1.0)  # Slow to allow stopping

    # Use 10 emails
    queue.load_dataset(DATASET_50[:10])

    # Start processing
    await queue.start()

    # Wait a bit then stop
    await asyncio.sleep(0.5)
    await queue.stop()

    stats = queue.get_stats()
    assert stats["is_running"] is False
    assert stats["processed"] < 10  # Should not have processed all
    assert stats["queue_remaining"] > 0


@pytest.mark.asyncio
async def test_queue_cannot_start_twice():
    """Test that queue raises error if started while already running."""
    queue = IngestionQueue()
    queue.load_dataset(DATASET_50[:5])

    await queue.start()

    with pytest.raises(RuntimeError, match="already running"):
        await queue.start()

    await queue.stop()


@pytest.mark.asyncio
async def test_queue_stats_updates():
    """Test that queue statistics update correctly during processing."""
    queue = IngestionQueue(interval_seconds=0.1)
    queue.load_dataset(DATASET_50[:3])

    initial_stats = queue.get_stats()
    assert initial_stats["total"] == 3
    assert initial_stats["processed"] == 0
    assert initial_stats["queue_remaining"] == 3

    await queue.start()
    await asyncio.sleep(0.15)  # Let one email process

    mid_stats = queue.get_stats()
    assert mid_stats["processed"] >= 1
    assert mid_stats["queue_remaining"] < 3

    await asyncio.sleep(1)  # Let all finish

    final_stats = queue.get_stats()
    assert final_stats["processed"] == 3
    assert final_stats["queue_remaining"] == 0
