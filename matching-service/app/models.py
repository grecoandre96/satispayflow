from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime
from enum import Enum


class DealStatus(str, Enum):
    """Deal status enum"""
    OPEN = "Open"
    WON = "Won"
    LOST = "Lost"


class AttributionMethod(str, Enum):
    """Attribution method enum"""
    TEMPORAL_VALUE = "temporal_value"
    TEMPORAL_ONLY = "temporal_only"
    SELF_SERVICE = "self_service"
    MANUAL = "manual"


class Company(BaseModel):
    """Company entity"""
    id: str
    name: str
    created_at: datetime


class Deal(BaseModel):
    """Deal entity - sales opportunity"""
    id: str
    company_id: str
    sales_rep_id: str
    sales_rep_name: str
    amount: float
    status: DealStatus
    close_date: Optional[datetime] = None
    created_at: datetime
    products: Optional[List[str]] = None  # Products/services in the deal


class Order(BaseModel):
    """Order entity - completed purchase"""
    id: str
    company_id: str
    amount: float
    order_date: datetime
    products: Optional[List[str]] = None


class Attribution(BaseModel):
    """Attribution result linking Order to Deal"""
    order_id: str
    deal_id: Optional[str] = None
    sales_rep_id: Optional[str] = None
    sales_rep_name: Optional[str] = None
    attribution_method: AttributionMethod
    confidence_score: float = Field(ge=0, le=100)
    needs_review: bool
    matching_metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class MatchRequest(BaseModel):
    """Request payload for matching endpoint"""
    companies: List[Company]
    deals: List[Deal]
    orders: List[Order]


class MatchResponse(BaseModel):
    """Response from matching endpoint"""
    matched: List[Attribution]
    self_service: List[Attribution]
    needs_review: List[Attribution]
    summary: dict
