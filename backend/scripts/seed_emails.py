"""
Unified email seeding script for Guard-IA testing.

This script consolidates seed_test_emails.py and seed_extra_20.py into a single
configurable tool for generating test emails.

Usage:
    # Use email templates (16 emails)
    python -m scripts.seed_emails --mode templates

    # Use extra dataset (20 emails)
    python -m scripts.seed_emails --mode extra

    # Use both (36 emails total)
    python -m scripts.seed_emails --mode all

    # Specify custom count
    python -m scripts.seed_emails --mode templates --count 10
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime
from uuid import uuid4

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.email import Email
from app.models.case import Case
from app.services.pipeline.orchestrator import PipelineOrchestrator
from scripts.email_templates import TEMPLATES


# Extra emails dataset (from seed_extra_20.py)
EXTRA_EMAILS = [
    {
        "sender": "cfo@legitimate-corp.com",
        "recipient": "security@strike.sh",
        "subject": "Q4 Budget Review",
        "body": "Please review the attached budget proposal for Q4.",
    },
    {
        "sender": "support@paypal-secure.xyz",
        "recipient": "user@strike.sh",
        "subject": "Verify Your Account Immediately",
        "body": "Your PayPal account has been locked. Click here to verify: http://paypal-secure.xyz/verify",
    },
    {
        "sender": "admin@strike.sh",
        "recipient": "team@strike.sh",
        "subject": "Weekly Team Meeting",
        "body": "Don't forget our weekly sync tomorrow at 2 PM.",
    },
    {
        "sender": "invoice@amazon-aws.scam",
        "recipient": "billing@strike.sh",
        "subject": "Urgent: AWS Payment Failed",
        "body": "Your AWS payment failed. Update your credit card immediately to avoid service suspension.",
    },
    {
        "sender": "hr@strike.sh",
        "recipient": "employee@strike.sh",
        "subject": "PTO Request Approved",
        "body": "Your PTO request for next week has been approved.",
    },
    {
        "sender": "noreply@microsoft-365.phish",
        "recipient": "admin@strike.sh",
        "subject": "Action Required: Office 365 License Expiring",
        "body": "Your Office 365 license expires in 24 hours. Renew now: http://microsoft-365.phish/renew",
    },
    {
        "sender": "ceo@strike.sh",
        "recipient": "finance@strike.sh",
        "subject": "Urgent Wire Transfer Needed",
        "body": "Please wire $50,000 to this account immediately for the new acquisition. Details in attachment.",
    },
    {
        "sender": "notifications@github.com",
        "recipient": "dev@strike.sh",
        "subject": "New PR: Fix authentication bug",
        "body": "A new pull request has been opened on your repository.",
    },
    {
        "sender": "alerts@fake-bank.com",
        "recipient": "customer@strike.sh",
        "subject": "Suspicious Activity Detected",
        "body": "We detected suspicious activity on your account. Verify your identity: http://fake-bank.com/verify",
    },
    {
        "sender": "partner@vendor.com",
        "recipient": "procurement@strike.sh",
        "subject": "Invoice #12345",
        "body": "Please find attached invoice for last month's services.",
    },
    {
        "sender": "security@apple-id.scam",
        "recipient": "iphone-user@strike.sh",
        "subject": "Your Apple ID Has Been Locked",
        "body": "For security reasons, your Apple ID has been locked. Unlock it here: http://apple-id.scam/unlock",
    },
    {
        "sender": "marketing@strike.sh",
        "recipient": "team@strike.sh",
        "subject": "New Blog Post Published",
        "body": "Check out our latest blog post on email security best practices.",
    },
    {
        "sender": "winner@lottery.scam",
        "recipient": "lucky@strike.sh",
        "subject": "Congratulations! You Won $1,000,000",
        "body": "You have been selected as the winner of our international lottery. Claim your prize now!",
    },
    {
        "sender": "it@strike.sh",
        "recipient": "all@strike.sh",
        "subject": "Scheduled Maintenance Tonight",
        "body": "Our systems will be down for maintenance tonight from 10 PM to 2 AM.",
    },
    {
        "sender": "phishing@evil.com",
        "recipient": "victim@strike.sh",
        "subject": "Your Package Could Not Be Delivered",
        "body": "We attempted to deliver your package but failed. Reschedule delivery: http://evil.com/delivery",
    },
    {
        "sender": "sales@partner.com",
        "recipient": "business@strike.sh",
        "subject": "Partnership Proposal",
        "body": "We would like to discuss a potential partnership opportunity. Are you available for a call next week?",
    },
    {
        "sender": "alerts@netflix-billing.phish",
        "recipient": "subscriber@strike.sh",
        "subject": "Your Netflix Payment Failed",
        "body": "We couldn't process your payment. Update your billing info: http://netflix-billing.phish/update",
    },
    {
        "sender": "legal@strike.sh",
        "recipient": "management@strike.sh",
        "subject": "Contract Review Needed",
        "body": "Please review the attached contract before our meeting tomorrow.",
    },
    {
        "sender": "refund@fake-amazon.com",
        "recipient": "shopper@strike.sh",
        "subject": "Amazon Refund Pending",
        "body": "Your refund of $299 is pending. Confirm your bank details to receive it: http://fake-amazon.com/refund",
    },
    {
        "sender": "support@strike.sh",
        "recipient": "customer@company.com",
        "subject": "Ticket #789 Resolved",
        "body": "Your support ticket has been resolved. Please let us know if you need further assistance.",
    },
]


async def seed_from_templates(session, count: int | None = None):
    """Seed emails using email_templates.py"""
    templates = TEMPLATES[:count] if count else TEMPLATES

    print(f"\n📧 Seeding {len(templates)} emails from templates...")

    for idx, template in enumerate(templates, 1):
        email = Email(
            id=uuid4(),
            sender=template["sender"],
            recipient=template["recipient"],
            subject=template["subject"],
            body=template["body"],
            received_at=datetime.utcnow(),
        )
        session.add(email)

    await session.commit()
    print(f"✅ Created {len(templates)} template emails")


async def seed_from_extra(session, count: int | None = None):
    """Seed emails using EXTRA_EMAILS dataset"""
    emails = EXTRA_EMAILS[:count] if count else EXTRA_EMAILS

    print(f"\n📧 Seeding {len(emails)} emails from extra dataset...")

    for idx, email_data in enumerate(emails, 1):
        email = Email(
            id=uuid4(),
            sender=email_data["sender"],
            recipient=email_data["recipient"],
            subject=email_data["subject"],
            body=email_data["body"],
            received_at=datetime.utcnow(),
        )
        session.add(email)

    await session.commit()
    print(f"✅ Created {len(emails)} extra emails")


async def run_pipeline_on_emails(session):
    """Run detection pipeline on all emails without cases"""
    orchestrator = PipelineOrchestrator(session)

    # Find emails without cases
    query = select(Email).outerjoin(Case, Email.id == Case.email_id).where(Case.id.is_(None))
    result = await session.execute(query)
    emails = result.scalars().all()

    if not emails:
        print("\n⚠️  No emails without cases found")
        return

    print(f"\n🔄 Running pipeline on {len(emails)} emails...")

    results = {"success": 0, "failed": 0}

    for email in emails:
        try:
            # Create case
            case = Case(email_id=email.id, status="pending")
            session.add(case)
            await session.commit()
            await session.refresh(case)

            # Run pipeline
            await orchestrator.run_pipeline(case.id)
            results["success"] += 1
            print(f"  ✓ Processed email from {email.sender}")

        except Exception as e:
            results["failed"] += 1
            print(f"  ✗ Failed to process email from {email.sender}: {e}")
            await session.rollback()

    print(f"\n📊 Pipeline Results:")
    print(f"  Success: {results['success']}")
    print(f"  Failed: {results['failed']}")


async def main():
    parser = argparse.ArgumentParser(
        description="Seed test emails for Guard-IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--mode",
        choices=["templates", "extra", "all"],
        default="all",
        help="Email dataset to use (default: all)",
    )
    parser.add_argument(
        "--count",
        type=int,
        help="Number of emails to seed (default: all)",
    )
    parser.add_argument(
        "--no-pipeline",
        action="store_true",
        help="Skip running detection pipeline",
    )

    args = parser.parse_args()

    async with AsyncSessionLocal() as session:
        if args.mode in ["templates", "all"]:
            await seed_from_templates(session, args.count)

        if args.mode in ["extra", "all"]:
            await seed_from_extra(session, args.count)

        if not args.no_pipeline:
            await run_pipeline_on_emails(session)

    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
