from datetime import datetime

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class Wine(Base):
    __tablename__ = "wines"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    producer: Mapped[str] = mapped_column(String(255), nullable=False)
    region: Mapped[str | None] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100))
    appellation: Mapped[str | None] = mapped_column(String(255))
    varietal: Mapped[str | None] = mapped_column(String(255))
    wine_type: Mapped[str] = mapped_column(String(50), nullable=False)
    avg_retail_price: Mapped[float | None] = mapped_column()
    price_tier: Mapped[str | None] = mapped_column(String(20))
    aliases: Mapped[list] = mapped_column(JSON, default=list)
    description: Mapped[str | None] = mapped_column(Text)
    normalized_name: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now())
