"""
Parser for .mbox email archive files.

This module provides utilities to parse .mbox files (standard Unix mailbox format)
and convert them to EmailDatasetEntry format for use with the ingestion system.

Usage:
    from backend.scripts.datasets.mbox_parser import load_mbox_dataset

    dataset = load_mbox_dataset("path/to/mailbox.mbox", max_emails=50)
"""

import mailbox
from pathlib import Path
from typing import TypedDict

from app.gateway.parser import EmailParser


class EmailDatasetEntry(TypedDict):
    """Single email entry in the dataset."""

    template_name: str
    recipient: str
    expected_verdict: str  # allowed, warned, quarantined, blocked
    expected_risk: str  # low, medium, high, critical
    category: str  # legitimate, phishing, bec, malware, scam, spear
    description: str


def load_mbox_dataset(
    mbox_path: str | Path,
    max_emails: int = 50,
    default_category: str = "legitimate",
) -> list[EmailDatasetEntry]:
    """
    Parse .mbox file and convert to EmailDatasetEntry list.

    Args:
        mbox_path: Path to .mbox file
        max_emails: Maximum number of emails to parse (default: 50)
        default_category: Default category for emails (default: "legitimate")

    Returns:
        List of EmailDatasetEntry dictionaries

    Example:
        dataset = load_mbox_dataset("mailbox.mbox", max_emails=30)
        # Use with ingestion queue
        queue.load_dataset(dataset)
    """
    mbox_path = Path(mbox_path)
    if not mbox_path.exists():
        raise FileNotFoundError(f"mbox file not found: {mbox_path}")

    mbox = mailbox.mbox(str(mbox_path))
    parser = EmailParser()
    entries: list[EmailDatasetEntry] = []

    for i, message in enumerate(mbox):
        if i >= max_emails:
            break

        try:
            # Convert mailbox.Message to bytes
            raw_bytes = message.as_bytes()

            # Parse using EmailParser
            email_data = parser.parse(raw_bytes)

            # Create dataset entry
            entry: EmailDatasetEntry = {
                "template_name": f"mbox_{i:03d}",
                "recipient": email_data.recipient_email,
                "expected_verdict": "allowed",  # Assume legitimate
                "expected_risk": "low",
                "category": default_category,
                "description": f"Real email from mbox: {email_data.subject[:50]}",
            }
            entries.append(entry)

        except Exception as exc:
            # Skip malformed emails
            print(f"Warning: Failed to parse email {i}: {exc}")
            continue

    return entries


def inspect_mbox_file(mbox_path: str | Path, limit: int = 10) -> None:
    """
    Print summary of first N emails in .mbox file.

    Useful for inspecting mbox contents before importing.

    Args:
        mbox_path: Path to .mbox file
        limit: Number of emails to inspect (default: 10)
    """
    mbox_path = Path(mbox_path)
    if not mbox_path.exists():
        raise FileNotFoundError(f"mbox file not found: {mbox_path}")

    mbox = mailbox.mbox(str(mbox_path))

    print(f"Inspecting {mbox_path}")
    print(f"Total emails in mbox: {len(mbox)}")
    print(f"\nFirst {limit} emails:\n")

    for i, message in enumerate(mbox):
        if i >= limit:
            break

        from_addr = message.get("From", "Unknown")
        to_addr = message.get("To", "Unknown")
        subject = message.get("Subject", "No subject")
        date = message.get("Date", "Unknown date")

        print(f"{i+1}. From: {from_addr}")
        print(f"   To: {to_addr}")
        print(f"   Subject: {subject}")
        print(f"   Date: {date}")
        print()
