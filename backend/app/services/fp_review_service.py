"""False positive review service: manage FP reviews on cases."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fp_review import FPReview


class FPReviewService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_reviews(self, case_id: UUID) -> list[FPReview]:
        """List all FP reviews for a case."""
        stmt = (
            select(FPReview)
            .where(FPReview.case_id == case_id)
            .order_by(FPReview.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create_review(
        self,
        case_id: UUID,
        reviewer_id: UUID,
        decision: str,
        notes: str | None = None,
    ) -> FPReview:
        """Create an FP review record."""
        review = FPReview(
            case_id=case_id,
            reviewer_id=reviewer_id,
            decision=decision,
            notes=notes,
        )
        self.db.add(review)
        await self.db.flush()
        return review
