#!/usr/bin/env python3
"""
Quick test script for the ingestion system.

This script tests:
1. Loading the dataset
2. Building emails from templates
3. Parsing emails
4. Basic queue operations

Run:
    python scripts/test_ingestion_system.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from scripts.email_templates import TEMPLATES
from scripts.datasets.email_dataset_50 import get_dataset, get_dataset_stats
from app.gateway.parser import EmailParser


def test_templates():
    """Test that all templates can be built."""
    print("=" * 60)
    print("Testing email templates...")
    print("=" * 60)

    success_count = 0
    failed = []

    for template_name, (template_fn, description) in TEMPLATES.items():
        try:
            email = template_fn(recipient="test@strike.sh")
            assert email is not None
            assert email["Subject"] is not None
            success_count += 1
        except Exception as e:
            failed.append((template_name, str(e)))

    print(f"\n✓ Successfully built {success_count}/{len(TEMPLATES)} templates")

    if failed:
        print("\n✗ Failed templates:")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return False

    return True


def test_dataset():
    """Test that dataset is correctly structured."""
    print("\n" + "=" * 60)
    print("Testing dataset structure...")
    print("=" * 60)

    dataset = get_dataset()
    stats = get_dataset_stats()

    print(f"\nTotal emails: {len(dataset)}")
    print("\nDistribution:")
    for category, count in sorted(stats.items()):
        pct = (count / len(dataset)) * 100
        print(f"  {category:15} {count:3d} ({pct:5.1f}%)")

    # Verify all required fields
    required_fields = [
        "template_name",
        "recipient",
        "expected_verdict",
        "expected_risk",
        "category",
        "description",
    ]

    for i, entry in enumerate(dataset):
        for field in required_fields:
            if field not in entry:
                print(f"\n✗ Missing field '{field}' in entry {i}")
                return False

    print("\n✓ All dataset entries have required fields")
    return True


def test_email_parsing():
    """Test that emails can be parsed."""
    print("\n" + "=" * 60)
    print("Testing email parsing...")
    print("=" * 60)

    parser = EmailParser()
    dataset = get_dataset()

    success_count = 0
    failed = []

    # Test first 10 emails
    for entry in dataset[:10]:
        try:
            template_fn, _ = TEMPLATES[entry["template_name"]]
            rfc_email = template_fn(recipient=entry["recipient"])
            raw_bytes = rfc_email.as_bytes()

            email_dict = parser.parse_raw(
                raw_data=raw_bytes,
                envelope_from=rfc_email["From"],
                envelope_to=[entry["recipient"]],
            )

            assert email_dict["message_id"] is not None
            assert email_dict["sender_email"] is not None
            assert email_dict["recipient_email"] is not None
            assert email_dict["subject"] is not None

            success_count += 1

        except Exception as e:
            failed.append((entry["template_name"], str(e)))

    print(f"\n✓ Successfully parsed {success_count}/10 emails")

    if failed:
        print("\n✗ Failed to parse:")
        for name, error in failed:
            print(f"  - {name}: {error}")
        return False

    return True


async def test_queue_basic():
    """Test basic queue operations."""
    print("\n" + "=" * 60)
    print("Testing queue operations...")
    print("=" * 60)

    from app.services.ingestion.queue import IngestionQueue

    queue = IngestionQueue(interval_seconds=0.1)

    # Test loading
    test_dataset = get_dataset()[:5]
    queue.load_dataset(test_dataset)

    assert queue.stats["total"] == 5
    assert len(queue.queue) == 5

    print(f"\n✓ Queue loaded {queue.stats['total']} emails")

    # Test stats
    stats = queue.get_stats()
    assert stats["is_running"] is False
    assert stats["processed"] == 0

    print("✓ Queue statistics working")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("GUARD-IA INGESTION SYSTEM TEST")
    print("=" * 60)

    results = []

    # Test templates
    results.append(("Templates", test_templates()))

    # Test dataset
    results.append(("Dataset", test_dataset()))

    # Test parsing
    results.append(("Parsing", test_email_parsing()))

    # Test queue
    results.append(("Queue", asyncio.run(test_queue_basic())))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8} {name}")

    all_passed = all(passed for _, passed in results)

    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
