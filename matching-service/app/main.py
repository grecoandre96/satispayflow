from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from .models import MatchRequest, MatchResponse, MatchConfig, Attribution
from .matching_engine import MatchingEngine
from .config import get_settings
from .utils import create_summary_stats

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Initialize FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Automated Deal-to-Order attribution system for Sales Rep commission tracking"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "match_orders": "/match-orders",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from datetime import datetime
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/match-orders", response_model=MatchResponse)
async def match_orders(request: MatchRequest):
    """
    Match orders to deals using multi-level matching logic
    
    Returns categorized attributions:
    - matched: High confidence matches
    - self_service: Orders without sales rep involvement
    - needs_review: Low confidence matches requiring manual review
    """
    try:
        logger.info(f"Received match request: {len(request.orders)} orders, {len(request.deals)} deals")
        
        # Create matching config from settings
        config = MatchConfig(
            time_window_days=settings.time_window_days,
            value_tolerance_percent=settings.value_tolerance_percent,
            self_service_threshold=settings.self_service_threshold,
            confidence_threshold=settings.confidence_threshold,
            temporal_decay_per_day=settings.temporal_decay_per_day,
            value_penalty_per_5_percent=settings.value_penalty_per_5_percent,
            unique_deal_bonus=settings.unique_deal_bonus
        )
        
        # Initialize matching engine
        engine = MatchingEngine(config)
        
        # Perform matching
        matched, self_service, needs_review = engine.match_orders(
            companies=request.companies,
            deals=request.deals,
            orders=request.orders
        )
        
        # Create summary statistics
        summary = create_summary_stats(matched, self_service, needs_review)
        
        logger.info(f"Matching complete: {summary}")
        
        return MatchResponse(
            matched=matched,
            self_service=self_service,
            needs_review=needs_review,
            summary=summary
        )
    
    except Exception as e:
        logger.error(f"Error during matching: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")


@app.get("/attribution/{order_id}")
async def get_attribution(order_id: str):
    """
    Get attribution details for a specific order
    
    Note: This is a placeholder endpoint. In production, this would
    query a database to retrieve stored attribution results.
    """
    # TODO: Implement database lookup
    return {
        "message": "This endpoint would retrieve attribution from database",
        "order_id": order_id,
        "note": "Not yet implemented - use /match-orders for batch processing"
    }


@app.get("/config")
async def get_config():
    """Get current matching configuration"""
    return {
        "time_window_days": settings.time_window_days,
        "value_tolerance_percent": settings.value_tolerance_percent,
        "self_service_threshold": settings.self_service_threshold,
        "confidence_threshold": settings.confidence_threshold,
        "temporal_decay_per_day": settings.temporal_decay_per_day,
        "value_penalty_per_5_percent": settings.value_penalty_per_5_percent,
        "unique_deal_bonus": settings.unique_deal_bonus
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
