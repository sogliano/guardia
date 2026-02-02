import pytest
from sqlalchemy import select
from app.models.email import Email
from app.models.case import Case
from app.models.analysis import Analysis

# Check if psycopg2 is available (required for testcontainers)
try:
    import psycopg2
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not PSYCOPG2_AVAILABLE,
    reason="psycopg2 not installed (required for testcontainers PostgreSQL)"
)


class TestDatabaseIntegration:
    """Integration tests using real PostgreSQL database via testcontainers."""

    @pytest.mark.asyncio
    async def test_email_creation_and_persistence(self, db_session):
        """Test that emails are correctly persisted to database."""
        email = Email(
            sender_email="test@example.com",
            recipient_email="user@strike.sh",
            subject="Test Subject",
            body_text="Test body",
            message_id="test-123",
            auth_results={"spf": "pass", "dkim": "pass", "dmarc": "pass"},
        )

        db_session.add(email)
        await db_session.commit()
        await db_session.refresh(email)

        assert email.id is not None
        assert email.sender_email == "test@example.com"
        assert email.created_at is not None

    @pytest.mark.asyncio
    async def test_case_email_relationship(self, db_session):
        """Test SQLAlchemy relationship between Case and Email."""
        email = Email(
            sender_email="test@example.com",
            recipient_email="user@strike.sh",
            subject="Test",
            body_text="Test",
        )
        db_session.add(email)
        await db_session.flush()

        case = Case(
            email_id=email.id,
            case_number="CASE-001",
            final_score=0.5,
            risk_level="medium",
            verdict="warn",
        )
        db_session.add(case)
        await db_session.commit()

        await db_session.refresh(email, ["case"])
        await db_session.refresh(case, ["email"])

        assert email.case is not None
        assert email.case.id == case.id
        assert case.email.id == email.id

    @pytest.mark.asyncio
    async def test_analysis_relationships(self, db_session):
        """Test Analysis relationship with Case."""
        email = Email(
            sender_email="test@example.com",
            recipient_email="user@strike.sh",
            subject="Test",
            body_text="Test",
        )
        db_session.add(email)
        await db_session.flush()

        case = Case(
            email_id=email.id,
            case_number="CASE-002",
            final_score=0.7,
            risk_level="high",
            verdict="quarantined",
        )
        db_session.add(case)
        await db_session.flush()

        analysis = Analysis(
            case_id=case.id,
            stage="heuristic",
            score=0.7,
            evidences=[
                {"type": "auth_failure", "severity": "high", "detail": "SPF failed"}
            ],
        )
        db_session.add(analysis)
        await db_session.commit()

        await db_session.refresh(case, ["analyses"])

        assert len(case.analyses) == 1
        assert case.analyses[0].stage == "heuristic"
        assert case.analyses[0].score == 0.7

    @pytest.mark.asyncio
    async def test_filter_cases_by_risk_level(self, db_session):
        """Test filtering cases by risk level."""
        for i, risk in enumerate(["low", "medium", "high"]):
            email = Email(
                sender_email=f"sender{i}@example.com",
                recipient_email="user@strike.sh",
                subject=f"Test {i}",
                body_text="Test",
            )
            db_session.add(email)
            await db_session.flush()

            case = Case(
                email_id=email.id,
                case_number=f"CASE-{i:03d}",
                final_score=0.1 + (i * 0.3),
                risk_level=risk,
                verdict="allowed",
            )
            db_session.add(case)

        await db_session.commit()

        result = await db_session.execute(select(Case).where(Case.risk_level == "high"))
        high_cases = result.scalars().all()

        assert len(high_cases) == 1
        assert high_cases[0].risk_level == "high"

    @pytest.mark.asyncio
    async def test_filter_cases_by_verdict(self, db_session):
        """Test filtering cases by verdict."""
        for i, verdict in enumerate(["allowed", "warn", "quarantined"]):
            email = Email(
                sender_email=f"sender{i}@example.com",
                recipient_email="user@strike.sh",
                subject=f"Test {i}",
                body_text="Test",
            )
            db_session.add(email)
            await db_session.flush()

            case = Case(
                email_id=email.id,
                case_number=f"CASE-V{i:03d}",
                final_score=0.2 + (i * 0.3),
                risk_level="medium",
                verdict=verdict,
            )
            db_session.add(case)

        await db_session.commit()

        result = await db_session.execute(
            select(Case).where(Case.verdict == "quarantined")
        )
        quarantined = result.scalars().all()

        assert len(quarantined) == 1
        assert quarantined[0].verdict == "quarantined"

    @pytest.mark.asyncio
    async def test_unique_constraint_message_id(self, db_session):
        """Test that message_id unique constraint is enforced."""
        email1 = Email(
            sender_email="test@example.com",
            recipient_email="user@strike.sh",
            subject="Test",
            body_text="Test",
            message_id="duplicate-123",
        )
        db_session.add(email1)
        await db_session.commit()

        email2 = Email(
            sender_email="test2@example.com",
            recipient_email="user@strike.sh",
            subject="Test 2",
            body_text="Test 2",
            message_id="duplicate-123",
        )
        db_session.add(email2)

        with pytest.raises(Exception):
            await db_session.commit()

    @pytest.mark.asyncio
    async def test_cascade_delete(self, db_session):
        """Test cascade delete behavior."""
        email = Email(
            sender_email="test@example.com",
            recipient_email="user@strike.sh",
            subject="Test",
            body_text="Test",
        )
        db_session.add(email)
        await db_session.flush()

        case = Case(
            email_id=email.id,
            case_number="CASE-DEL",
            final_score=0.5,
            risk_level="medium",
            verdict="warn",
        )
        db_session.add(case)
        await db_session.commit()

        case_id = case.id

        await db_session.delete(email)
        await db_session.commit()

        result = await db_session.execute(select(Case).where(Case.id == case_id))
        deleted_case = result.scalar_one_or_none()

        assert deleted_case is None
