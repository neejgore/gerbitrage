from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PricingSource(BaseModel):
    name: str
    avg_price: Optional[float] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    num_listings: Optional[int] = None
    url: Optional[str] = None


class PricingBreakdown(BaseModel):
    avg_retail: Optional[float] = None
    min_retail: Optional[float] = None
    max_retail: Optional[float] = None
    median_retail: Optional[float] = None
    estimated_wholesale: Optional[float] = None
    vintage: Optional[int] = None
    currency: str = "USD"
    source: str = "aggregated"
    last_updated: Optional[datetime] = None
    sources: list[PricingSource] = []
    # low / medium / high – reflects how many real data points we have
    data_confidence: str = "medium"


class WinePricingResponse(BaseModel):
    wine_id: str
    name: str
    vintage: Optional[int] = None
    pricing: PricingBreakdown
