from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


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
    status: Literal["Open", "Won", "Lost"]
    close_date: Optional[datetime] = None
    created_at: datetime


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
    attribution_method: Literal[
        "temporal_value",
        "temporal_only", 
        "self_service",
        "manual"
    ]
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


class MatchConfig(BaseModel):
    """Configuration for matching algorithm"""
    time_window_days: int = Field(default=90, description="Max days between deal close and order")
    value_tolerance_percent: float = Field(default=10.0, description="Tolerance for value matching (%)")
    self_service_threshold: float = Field(default=500.0, description="Orders below this are self-service")
    confidence_threshold: float = Field(default=70.0, description="Minimum confidence for auto-attribution")
    temporal_decay_per_day: float = Field(default=1.0, description="Score penalty per day of distance")
    value_penalty_per_5_percent: float = Field(default=10.0, description="Score penalty per 5% value difference")
    unique_deal_bonus: float = Field(default=30.0, description="Bonus if only one deal in period")
