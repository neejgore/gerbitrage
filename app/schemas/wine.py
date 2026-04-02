from typing import Optional

from pydantic import BaseModel


class WineBase(BaseModel):
    id: str
    name: str
    producer: str
    region: Optional[str] = None
    country: Optional[str] = None
    appellation: Optional[str] = None
    varietal: Optional[str] = None
    wine_type: str
    avg_retail_price: Optional[float] = None
    price_tier: Optional[str] = None


class WineDetail(WineBase):
    aliases: list[str] = []
    description: Optional[str] = None


class WineSearchResult(WineBase):
    match_score: float


class WineSearchResponse(BaseModel):
    query: str
    results: list[WineSearchResult]
    total: int
