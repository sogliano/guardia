"""
Simple import tests for ingestion system that don't require database.

These tests verify that all modules can be imported and basic
functionality works without database connection.
"""

import pytest


def test_dataset_import():
    """Test that dataset can be imported and has correct structure."""
    from scripts.datasets.email_dataset_50 import (
        DATASET_50,
        get_dataset,
        get_by_category,
        get_dataset_stats,
    )

    assert len(DATASET_50) == 50
    assert len(get_dataset()) == 50

    # Test category filtering
    phishing = get_by_category("phishing")
    assert len(phishing) > 0
    assert all(e["category"] == "phishing" for e in phishing)

    # Test stats
    stats = get_dataset_stats()
    assert "legitimate" in stats
    assert "phishing" in stats
    assert sum(stats.values()) == 50


def test_templates_import():
    """Test that all email templates can be imported."""
    from scripts.email_templates import TEMPLATES

    assert len(TEMPLATES) == 50

    # Test that a template can be called
    template_fn, description = TEMPLATES["clean"]
    email = template_fn(recipient="test@strike.sh")

    assert email is not None
    assert email["Subject"] is not None
    assert email["From"] is not None
    assert email["To"] == "test@strike.sh"


def test_queue_import():
    """Test that queue can be imported and basic operations work."""
    from app.services.ingestion.queue import IngestionQueue, get_queue
    from scripts.datasets.email_dataset_50 import get_dataset

    # Test queue creation
    queue = IngestionQueue(interval_seconds=1.0)
    assert queue.interval_seconds == 1.0
    assert queue.is_running is False

    # Test loading dataset
    dataset = get_dataset()[:5]  # Only 5 emails
    queue.load_dataset(dataset)

    assert queue.stats["total"] == 5
    assert len(queue.queue) == 5

    # Test stats
    stats = queue.get_stats()
    assert stats["total"] == 5
    assert stats["processed"] == 0
    assert stats["is_running"] is False

    # Test singleton
    queue2 = get_queue()
    assert queue2 is not None


def test_api_schemas_import():
    """Test that API schemas can be imported."""
    from app.api.v1.ingestion import (
        StartIngestionRequest,
        IngestionStatusResponse,
        DatasetStatsResponse,
    )

    # Test schema creation
    request = StartIngestionRequest(interval_seconds=5.0)
    assert request.interval_seconds == 5.0
    assert request.category is None

    # Test with category
    request2 = StartIngestionRequest(category="phishing", interval_seconds=3.0)
    assert request2.category == "phishing"
    assert request2.interval_seconds == 3.0


def test_email_parsing():
    """Test that emails can be built and basic structure is correct."""
    from scripts.email_templates import TEMPLATES

    # Test a few different templates
    test_templates = ["clean", "phishing", "bec", "malware"]

    for template_name in test_templates:
        template_fn, description = TEMPLATES[template_name]
        email = template_fn(recipient="test@strike.sh")

        # Verify basic structure
        assert email["Subject"] is not None
        assert email["From"] is not None
        assert email["To"] == "test@strike.sh"
        assert email["Message-ID"] is not None
        assert email["Date"] is not None

        # Verify realistic headers
        assert "Authentication-Results" in email
        assert "X-Google-SMTP-Source" in email
        assert "Return-Path" in email

        # Verify email can be serialized
        email_bytes = email.as_bytes()
        assert len(email_bytes) > 0
