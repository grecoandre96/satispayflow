from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from datetime import datetime

from .models import MatchRequest, MatchResponse, Attribution
from .matching_engine import MatchingEngine, MatchingConfig

# Initialize FastAPI app
app = FastAPI(
    title="SatispayFlow Matching Service",
    description="Automated Deal-to-Order attribution system for Sales Rep commission tracking",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize matching engine
matching_engine = MatchingEngine()


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "SatispayFlow Matching Service",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "match_orders": "/match-orders",
            "config": "/config",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "matching-service"
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
        # Perform matching
        matched, self_service, needs_review = matching_engine.match_orders(
            orders=request.orders,
            deals=request.deals,
            companies=request.companies
        )
        
        # Calculate summary statistics
        total_orders = len(request.orders)
        matched_count = len(matched)
        self_service_count = len(self_service)
        needs_review_count = len(needs_review)
        
        # Calculate match rate
        match_rate = (matched_count / total_orders * 100) if total_orders > 0 else 0
        
        # Calculate average confidence for matched orders
        avg_confidence = (
            sum(a.confidence_score for a in matched) / matched_count
            if matched_count > 0 else 0
        )
        
        # Count attribution methods
        all_attributions = matched + self_service + needs_review
        attribution_methods = {}
        for attr in all_attributions:
            method = attr.attribution_method.value
            attribution_methods[method] = attribution_methods.get(method, 0) + 1
        
        summary = {
            "total_orders": total_orders,
            "matched_count": matched_count,
            "self_service_count": self_service_count,
            "needs_review_count": needs_review_count,
            "match_rate_percent": round(match_rate, 2),
            "average_confidence": round(avg_confidence, 2),
            "attribution_methods": attribution_methods
        }
        
        return MatchResponse(
            matched=matched,
            self_service=self_service,
            needs_review=needs_review,
            summary=summary
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Matching error: {str(e)}")


@app.get("/attribution/{order_id}")
async def get_attribution(order_id: str):
    """
    Get attribution details for a specific order
    
    Note: This is a placeholder endpoint. In production, this would
    query a database to retrieve stored attribution results.
    """
    return {
        "message": "Attribution lookup not implemented",
        "order_id": order_id,
        "note": "In production, this would query a database"
    }


@app.get("/config")
async def get_config():
    """Get current matching configuration"""
    config = matching_engine.config
    return {
        "temporal_matching": {
            "max_days_before_order": config.MAX_DAYS_BEFORE_ORDER,
            "max_days_after_order": config.MAX_DAYS_AFTER_ORDER
        },
        "value_matching": {
            "tolerance_percent": config.VALUE_TOLERANCE_PERCENT
        },
        "confidence": {
            "review_threshold": config.CONFIDENCE_THRESHOLD_REVIEW
        },
        "self_service": {
            "amount_threshold": config.SELF_SERVICE_AMOUNT_THRESHOLD
        },
        "fuzzy_matching": {
            "company_name_similarity_threshold": config.COMPANY_NAME_SIMILARITY_THRESHOLD
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
