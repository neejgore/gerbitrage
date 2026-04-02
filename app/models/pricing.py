import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class WinePricing(Base):
    __tablename__ = "wine_pricing"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    wine_id: Mapped[str] = mapped_column(
        String(100), ForeignKey("wines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    vintage: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    min_price: Mapped[float | None] = mapped_column()
    max_price: Mapped[float | None] = mapped_column()
    avg_price: Mapped[float | None] = mapped_column()
    median_price: Mapped[float | None] = mapped_column()
    num_listings: Mapped[int | None] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    raw_data: Mapped[dict | None] = mapped_column(JSON)


class AnalysisLog(Base):
    __tablename__ = "analysis_log"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    menu_text: Mapped[str] = mapped_column(Text, nullable=False)
    menu_price: Mapped[float | None] = mapped_column()
    identified_wine_id: Mapped[str | None] = mapped_column(String(100), index=True)
    confidence_score: Mapped[float | None] = mapped_column()
    fairness_score: Mapped[int | None] = mapped_column(Integer)
    verdict: Mapped[str | None] = mapped_column(String(50))
    venue_id: Mapped[str | None] = mapped_column(String(255), index=True)
    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), index=True
    )
