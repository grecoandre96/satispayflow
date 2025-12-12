# 🛠️ SatispayFlow - Development Guide

## Table of Contents
1. [Technology Stack](#technology-stack)
2. [Architecture Overview](#architecture-overview)
3. [Core Components](#core-components)
4. [Matching Algorithm Deep Dive](#matching-algorithm-deep-dive)
5. [API Endpoints](#api-endpoints)
6. [Critical Points & Edge Cases](#critical-points--edge-cases)
7. [Performance Considerations](#performance-considerations)
8. [Extension Points](#extension-points)

---

## Technology Stack

### Core Framework
```yaml
Framework: FastAPI 0.115.0
- Modern async-capable Python web framework
- Automatic OpenAPI/Swagger documentation
- Built-in request/response validation via Pydantic
- High performance (comparable to NodeJS and Go)

Server: Uvicorn 0.32.1
- ASGI server implementation
- Production-ready with uvloop and httptools
- Supports HTTP/1.1 and WebSockets
```

### Data Validation & Serialization
```yaml
Pydantic: 2.9.2
- Runtime type checking
- Data validation with custom validators
- JSON schema generation
- Enum support for type safety
```

### Dependencies
```yaml
httpx: 0.28.1          # HTTP client for external calls
pandas: 2.2.3          # Data processing (if needed)
python-dateutil: 2.9.0 # Date/time utilities
```

### Deployment
```yaml
Platform: Render (Free Tier)
- Auto-deploy from Git
- Environment variables support
- Health check monitoring
- SSL/TLS certificates included
```

---

## Architecture Overview

### Project Structure
```
matching-service/
├── app/
│   ├── __init__.py           # Package initializer
│   ├── main.py               # FastAPI app & endpoints (158 lines)
│   ├── matching_engine.py    # Core matching logic (317 lines)
│   └── models.py             # Pydantic models (77 lines)
├── requirements.txt          # Python dependencies
└── Procfile                  # Render deployment config
```

### Architectural Patterns

#### 1. **Layered Architecture**
```
┌─────────────────────────────────────┐
│   API Layer (main.py)               │  ← HTTP endpoints, validation
├─────────────────────────────────────┤
│   Business Logic (matching_engine)  │  ← Core algorithm
├─────────────────────────────────────┤
│   Data Models (models.py)           │  ← Type definitions
└─────────────────────────────────────┘
```

#### 2. **Dependency Injection**
```python
# main.py
matching_engine = MatchingEngine()  # Singleton instance

@app.post("/match-orders")
async def match_orders(request: MatchRequest):
    # Engine is injected at module level
    matched, self_service, needs_review = matching_engine.match_orders(...)
```

#### 3. **Strategy Pattern** (Implicit)
```python
# Different attribution methods based on match quality
if value_diff_percent <= 5.0 and days_diff <= 14:
    method = AttributionMethod.TEMPORAL_VALUE
else:
    method = AttributionMethod.TEMPORAL_ONLY
```

---

## Core Components

### 1. Data Models (`models.py`)

#### **Company Model**
```python
class Company(BaseModel):
    """Represents a customer company"""
    id: str                    # Unique identifier
    name: str                  # Company name (used for fuzzy matching)
    created_at: datetime       # Registration timestamp
```

**Purpose**: Provides company context for matching. The `name` field enables fuzzy matching when company IDs don't match exactly.

---

#### **Deal Model**
```python
class Deal(BaseModel):
    """Sales opportunity - represents a potential sale"""
    id: str                           # Unique deal identifier
    company_id: str                   # Link to company
    sales_rep_id: str                 # BD who owns the deal
    sales_rep_name: str               # BD name (for display)
    amount: float                     # Deal value in currency
    status: DealStatus                # OPEN | WON | LOST
    close_date: Optional[datetime]    # When deal was won/lost
    created_at: datetime              # Deal creation date
    products: Optional[List[str]]     # Products/services in deal
```

**Critical Fields**:
- `status`: Only `WON` deals are considered for matching
- `close_date`: Used for temporal proximity scoring
- `products`: **Most important** for matching (50% weight)
- `amount`: Second most important (30% weight)

---

#### **Order Model**
```python
class Order(BaseModel):
    """Completed purchase - needs attribution to a deal"""
    id: str                        # Unique order identifier
    company_id: str                # Link to company
    amount: float                  # Order value
    order_date: datetime           # Purchase timestamp
    products: Optional[List[str]]  # Products purchased
```

**Key Characteristics**:
- **No owner**: Orders don't have a sales rep directly
- **Attribution target**: We need to find which deal this came from
- **Products field**: Critical for accurate matching

---

#### **Attribution Model**
```python
class Attribution(BaseModel):
    """Result of matching - links Order to Deal"""
    order_id: str                              # Which order
    deal_id: Optional[str]                     # Which deal (None for self-service)
    sales_rep_id: Optional[str]                # BD who gets credit
    sales_rep_name: Optional[str]              # BD name
    attribution_method: AttributionMethod      # How it was matched
    confidence_score: float                    # 0-100 confidence
    needs_review: bool                         # Manual review required?
    matching_metadata: dict                    # Debug/audit info
    timestamp: datetime                        # When attribution was made
```

**Confidence Score Interpretation**:
```python
90-100: Excellent match (exact products + amount + timing)
70-89:  Good match (likely correct, auto-approved)
50-69:  Uncertain match (needs manual review)
0-49:   Poor match (likely incorrect, needs review)
```

---

#### **Enums for Type Safety**
```python
class DealStatus(str, Enum):
    """Deal lifecycle states"""
    OPEN = "Open"    # Still negotiating
    WON = "Won"      # Deal closed successfully (only these are matched)
    LOST = "Lost"    # Deal lost to competitor

class AttributionMethod(str, Enum):
    """How the attribution was determined"""
    TEMPORAL_VALUE = "temporal_value"    # Time + amount match
    TEMPORAL_ONLY = "temporal_only"      # Only time-based
    SELF_SERVICE = "self_service"        # No deal match
    MANUAL = "manual"                    # Human override
```

---

### 2. Matching Engine (`matching_engine.py`)

#### **Configuration Class**
```python
class MatchingConfig:
    """Tunable parameters for matching algorithm"""
    
    # Temporal Matching
    MAX_DAYS_BEFORE_ORDER = 90   # Deal can close up to 90 days before order
    MAX_DAYS_AFTER_ORDER = 30    # Deal can close up to 30 days after order
    
    # Value Matching
    VALUE_TOLERANCE_PERCENT = 20.0  # ±20% tolerance on amount
    
    # Confidence Thresholds
    CONFIDENCE_THRESHOLD_REVIEW = 70.0  # Below this → manual review
    
    # Self-Service Detection
    SELF_SERVICE_AMOUNT_THRESHOLD = 500.0  # Orders < €500 → self-service
    
    # Fuzzy Matching
    COMPANY_NAME_SIMILARITY_THRESHOLD = 0.6  # 60% name similarity required
```

**Why These Values?**
- **90 days before**: Sales cycle can be long, order might come months after deal
- **30 days after**: Allows for deals closed slightly after order (retroactive)
- **20% tolerance**: Accounts for discounts, add-ons, currency fluctuations
- **70% confidence**: Balance between automation and accuracy
- **€500 threshold**: Small orders likely self-service (no BD involvement)

---

#### **Main Matching Flow**
```python
def match_orders(
    self, 
    orders: List[Order], 
    deals: List[Deal],
    companies: List[Company]
) -> Tuple[List[Attribution], List[Attribution], List[Attribution]]:
    """
    Main entry point for matching algorithm
    
    Returns:
        matched: High confidence matches (>= 70%)
        self_service: Orders without BD involvement
        needs_review: Low confidence matches (< 70%)
    """
```

**Algorithm Flow**:
```
For each Order:
    │
    ├─→ Is amount < €500?
    │   └─→ YES: Mark as SELF_SERVICE
    │
    ├─→ Find candidate deals (temporal + value filters)
    │   │
    │   ├─→ No candidates found?
    │   │   └─→ Mark as SELF_SERVICE
    │   │
    │   └─→ Candidates found
    │       │
    │       ├─→ Score each candidate (multi-factor)
    │       │
    │       └─→ Select best match
    │           │
    │           ├─→ Confidence >= 70%?
    │           │   └─→ Add to MATCHED
    │           │
    │           └─→ Confidence < 70%?
    │               └─→ Add to NEEDS_REVIEW
```

---

### 3. Matching Algorithm Deep Dive

#### **Step 1: Find Candidate Deals**
```python
def _find_candidate_deals(
    self, 
    order: Order, 
    deals: List[Deal],
    company_dict: Dict[str, Company]
) -> List[Deal]:
    """
    Apply filters to find potentially matching deals
    
    Filters applied (in order):
    1. Temporal window
    2. Value tolerance
    3. Company matching (3 strategies)
    """
    candidates = []
    
    for deal in deals:
        # Filter 1: Temporal Window
        days_diff = (order.order_date - deal.close_date).days
        if not (-90 <= days_diff <= 30):
            continue  # Deal too far in past or future
        
        # Filter 2: Value Tolerance
        value_diff_percent = abs(order.amount - deal.amount) / deal.amount * 100
        if value_diff_percent > 20.0:
            continue  # Amount too different
        
        # Filter 3: Company Matching (3 strategies)
        # Strategy A: Exact ID match
        if order.company_id == deal.company_id:
            candidates.append(deal)
            continue
        
        # Strategy B: Fuzzy name match
        order_company = company_dict.get(order.company_id)
        deal_company = company_dict.get(deal.company_id)
        if order_company and deal_company:
            similarity = SequenceMatcher(
                None, 
                order_company.name.lower(), 
                deal_company.name.lower()
            ).ratio()
            if similarity >= 0.6:  # 60% similarity
                candidates.append(deal)
                continue
        
        # Strategy C: Very close amount (< 5% diff)
        if value_diff_percent <= 5.0:
            candidates.append(deal)
    
    return candidates
```

**Critical Point**: Company matching has 3 fallback strategies to handle:
- New companies (different IDs, same company)
- Typos in company names
- Edge cases where amount is the best indicator

---

#### **Step 2: Scoring System**
```python
def _calculate_match_score(
    self, 
    order: Order, 
    deal: Deal,
    company_dict: Dict[str, Company]
) -> float:
    """
    Multi-factor scoring (total: 100 points)
    
    Weight Distribution:
    - Products: 50 points (HIGHEST PRIORITY)
    - Amount:   30 points
    - Timing:   15 points
    - Company:   5 points (LOWEST PRIORITY)
    """
    score = 0.0
    
    # ═══════════════════════════════════════════════════════
    # FACTOR 1: Product Match (50 points max)
    # ═══════════════════════════════════════════════════════
    if order.products and deal.products:
        # Normalize product names (lowercase, strip whitespace)
        order_products = set(p.lower().strip() for p in order.products)
        deal_products = set(p.lower().strip() for p in deal.products)
        
        # Calculate Jaccard similarity: |intersection| / |union|
        intersection = len(order_products & deal_products)
        union = len(order_products | deal_products)
        
        if union > 0:
            product_similarity = intersection / union
            score += product_similarity * 50.0
        
        # Example:
        # Order: ["CRM", "Support"]
        # Deal:  ["CRM", "Support", "Training"]
        # Intersection: 2, Union: 3
        # Similarity: 2/3 = 0.667
        # Score: 0.667 * 50 = 33.3 points
    
    elif not order.products and not deal.products:
        # Neither has products → neutral score
        score += 25.0
    
    # If only one has products → 0 points (mismatch)
    
    # ═══════════════════════════════════════════════════════
    # FACTOR 2: Amount Match (30 points max)
    # ═══════════════════════════════════════════════════════
    value_diff_percent = abs(order.amount - deal.amount) / deal.amount * 100
    
    if value_diff_percent <= 1.0:
        value_score = 30.0      # Perfect match (within 1%)
    elif value_diff_percent <= 5.0:
        value_score = 25.0      # Excellent (within 5%)
    elif value_diff_percent <= 10.0:
        value_score = 20.0      # Good (within 10%)
    elif value_diff_percent <= 15.0:
        value_score = 15.0      # Acceptable (within 15%)
    else:
        # Linear decay: lose 1.5 points per % difference
        value_score = max(0, 30 - (value_diff_percent * 1.5))
    
    score += value_score
    
    # ═══════════════════════════════════════════════════════
    # FACTOR 3: Temporal Proximity (15 points max)
    # ═══════════════════════════════════════════════════════
    if deal.close_date:
        days_diff = abs((order.order_date - deal.close_date).days)
        
        if days_diff <= 7:
            temporal_score = 15.0    # Within 1 week
        elif days_diff <= 14:
            temporal_score = 12.0    # Within 2 weeks
        elif days_diff <= 30:
            temporal_score = 8.0     # Within 1 month
        else:
            # Decay: lose 1 point per 6 days
            temporal_score = max(0, 15 - (days_diff / 6))
        
        score += temporal_score
    
    # ═══════════════════════════════════════════════════════
    # FACTOR 4: Company Match (5 points max)
    # ═══════════════════════════════════════════════════════
    if order.company_id == deal.company_id:
        score += 5.0  # Exact match
    else:
        # Fuzzy match
        order_company = company_dict.get(order.company_id)
        deal_company = company_dict.get(deal.company_id)
        
        if order_company and deal_company:
            similarity = SequenceMatcher(
                None,
                order_company.name.lower(),
                deal_company.name.lower()
            ).ratio()
            score += similarity * 5.0
    
    # Cap at 100 points
    return min(100.0, score)
```

**Scoring Examples**:

**Example 1: Perfect Match**
```python
Order:  amount=€50,000, products=["CRM", "Support"], date=Jan 20
Deal:   amount=€50,000, products=["CRM", "Support"], close=Jan 15

Products: 100% match → 50 points
Amount:   0% diff    → 30 points
Timing:   5 days     → 15 points
Company:  Exact      → 5 points
TOTAL: 100 points ✅
```

**Example 2: Good Match**
```python
Order:  amount=€52,000, products=["CRM", "Support"], date=Jan 25
Deal:   amount=€50,000, products=["CRM", "Training"], close=Jan 10

Products: 50% match (1/2) → 25 points
Amount:   4% diff         → 25 points
Timing:   15 days         → 12 points
Company:  Exact           → 5 points
TOTAL: 67 points → NEEDS_REVIEW ⚠️
```

**Example 3: Poor Match**
```python
Order:  amount=€85,000, products=["HR System"], date=Feb 1
Deal:   amount=€50,000, products=["CRM"], close=Jan 5

Products: 0% match    → 0 points
Amount:   70% diff    → 0 points (too different)
Timing:   27 days     → 8 points
Company:  Exact       → 5 points
TOTAL: 13 points → NEEDS_REVIEW ⚠️
```

---

#### **Step 3: Select Best Match**
```python
def _select_best_match(
    self, 
    order: Order, 
    candidates: List[Deal],
    company_dict: Dict[str, Company]
) -> Attribution:
    """
    Choose the best deal from multiple candidates
    """
    # Single candidate → no need to score
    if len(candidates) == 1:
        return self._create_attribution(order, candidates[0], company_dict)
    
    # Multiple candidates → score and rank
    scored_candidates = []
    for deal in candidates:
        score = self._calculate_match_score(order, deal, company_dict)
        scored_candidates.append((deal, score))
    
    # Sort by score (highest first)
    scored_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Return best match
    best_deal, best_score = scored_candidates[0]
    return self._create_attribution(
        order, 
        best_deal, 
        company_dict,
        custom_confidence=best_score
    )
```

**Critical Point**: When multiple deals match, we **always** pick the highest scoring one. This ensures deterministic behavior.

---

#### **Step 4: Create Attribution**
```python
def _create_attribution(
    self, 
    order: Order, 
    deal: Deal,
    company_dict: Dict[str, Company],
    custom_confidence: Optional[float] = None
) -> Attribution:
    """
    Build the final attribution object with metadata
    """
    days_diff = abs((order.order_date - deal.close_date).days)
    value_diff_percent = abs(order.amount - deal.amount) / deal.amount * 100
    
    # Calculate or use provided confidence
    confidence = custom_confidence or self._calculate_match_score(
        order, deal, company_dict
    )
    
    # Determine attribution method
    if value_diff_percent <= 5.0 and days_diff <= 14:
        method = AttributionMethod.TEMPORAL_VALUE  # High quality match
    else:
        method = AttributionMethod.TEMPORAL_ONLY   # Time-based only
    
    return Attribution(
        order_id=order.id,
        deal_id=deal.id,
        sales_rep_id=deal.sales_rep_id,
        sales_rep_name=deal.sales_rep_name,
        attribution_method=method,
        confidence_score=confidence,
        needs_review=confidence < 70.0,  # Threshold for manual review
        matching_metadata={
            "days_difference": days_diff,
            "value_difference_percent": round(value_diff_percent, 2),
            "order_amount": order.amount,
            "deal_amount": deal.amount,
            "candidates_count": 1,
            "company_match": order.company_id == deal.company_id
        }
    )
```

---

### 4. API Layer (`main.py`)

#### **Main Endpoint: POST /match-orders**
```python
@app.post("/match-orders", response_model=MatchResponse)
async def match_orders(request: MatchRequest):
    """
    Match orders to deals using multi-level matching logic
    
    Request Body:
    {
        "companies": [...],
        "deals": [...],
        "orders": [...]
    }
    
    Response:
    {
        "matched": [...],           # High confidence (>= 70%)
        "self_service": [...],      # No BD involvement
        "needs_review": [...],      # Low confidence (< 70%)
        "summary": {...}            # Statistics
    }
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
        
        # Match rate
        match_rate = (matched_count / total_orders * 100) if total_orders > 0 else 0
        
        # Average confidence for matched orders
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
```

**Response Example**:
```json
{
  "matched": [
    {
      "order_id": "order_001",
      "deal_id": "DEAL-125",
      "sales_rep_id": "luca_marino",
      "sales_rep_name": "Luca Marino",
      "attribution_method": "temporal_value",
      "confidence_score": 95.5,
      "needs_review": false,
      "matching_metadata": {
        "days_difference": 5,
        "value_difference_percent": 0.0,
        "order_amount": 85000,
        "deal_amount": 85000,
        "company_match": true
      }
    }
  ],
  "self_service": [],
  "needs_review": [],
  "summary": {
    "total_orders": 1,
    "matched_count": 1,
    "self_service_count": 0,
    "needs_review_count": 0,
    "match_rate_percent": 100.0,
    "average_confidence": 95.5,
    "attribution_methods": {
      "temporal_value": 1
    }
  }
}
```

---

#### **Configuration Endpoint: GET /config**
```python
@app.get("/config")
async def get_config():
    """
    Expose current matching configuration
    
    Useful for:
    - Understanding matching behavior
    - Debugging unexpected results
    - Tuning parameters
    """
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
```

---

## Critical Points & Edge Cases

### 🔴 Critical Point 1: Division by Zero
```python
# Location: matching_engine.py, line 111
value_diff_percent = abs(order.amount - deal.amount) / deal.amount * 100

# RISK: If deal.amount == 0, this will crash!
# MITIGATION: Add validation in Deal model
```

**Fix**:
```python
class Deal(BaseModel):
    amount: float = Field(gt=0)  # Must be greater than 0
```

---

### 🔴 Critical Point 2: Empty Product Lists
```python
# Location: matching_engine.py, line 199-204
if order.products and deal.products:
    # Calculate Jaccard similarity
    intersection = len(order_products_set & deal_products_set)
    union = len(order_products_set | deal_products_set)
    product_similarity = intersection / union if union > 0 else 0

# RISK: What if products = []? (empty list is truthy!)
```

**Current Behavior**:
```python
order.products = []  # Empty list
deal.products = []   # Empty list

# Both are truthy, so we enter the if block
# union = 0, so product_similarity = 0
# Score: 0 points (correct behavior)
```

**Edge Case Handled**: ✅ Empty lists are handled correctly.

---

### 🔴 Critical Point 3: Tie-Breaking
```python
# Location: matching_engine.py, line 165
scored_candidates.sort(key=lambda x: x[1], reverse=True)

# SCENARIO: Two deals with identical scores
# Deal A: score = 85.0
# Deal B: score = 85.0

# QUESTION: Which one is selected?
```

**Current Behavior**: Python's sort is **stable**, so the first deal in the original list wins.

**Potential Issue**: Non-deterministic if deal order changes.

**Recommended Fix**:
```python
# Add secondary sort key (e.g., most recent deal)
scored_candidates.sort(
    key=lambda x: (x[1], x[0].close_date),  # Score, then date
    reverse=True
)
```

---

### 🟡 Edge Case 1: Deal Closed After Order
```python
# Scenario:
Order Date:  Jan 15, 2025
Deal Close:  Jan 20, 2025  (5 days AFTER order)

# Is this valid?
```

**Current Behavior**: ✅ YES, allowed up to 30 days after order.

**Rationale**: Deals might be retroactively closed after order is placed (admin delay).

---

### 🟡 Edge Case 2: Multiple Deals, Same Company, Same Day
```python
# Scenario:
Company: TechCorp
Deal 1: amount=€50k, close=Jan 15, products=["CRM"]
Deal 2: amount=€50k, close=Jan 15, products=["HR"]
Order:  amount=€50k, date=Jan 20, products=["CRM"]

# Which deal wins?
```

**Current Behavior**: Deal 1 wins (product match: 100% vs 0%).

**Score Breakdown**:
```
Deal 1:
- Products: 100% match → 50 points
- Amount: perfect → 30 points
- Timing: 5 days → 15 points
- Company: exact → 5 points
TOTAL: 100 points ✅

Deal 2:
- Products: 0% match → 0 points
- Amount: perfect → 30 points
- Timing: 5 days → 15 points
- Company: exact → 5 points
TOTAL: 50 points
```

**Conclusion**: Product matching correctly disambiguates.

---

### 🟡 Edge Case 3: Fuzzy Company Matching
```python
# Scenario:
Order Company: "TechCorp SRL"
Deal Company:  "Tech Corp S.R.L."

# Are these the same company?
```

**Current Behavior**:
```python
similarity = SequenceMatcher(None, "techcorp srl", "tech corp s.r.l.").ratio()
# similarity ≈ 0.75 (75%)

# Threshold: 0.6 (60%)
# Result: ✅ MATCH
```

**Potential Issue**: False positives (e.g., "TechCorp" vs "TechCore").

**Mitigation**: Threshold of 60% is conservative. Could be raised to 70-80%.

---

### 🟢 Edge Case 4: Self-Service Threshold
```python
# Scenario:
Order: amount = €499

# Is this self-service?
```

**Current Behavior**: ✅ YES (< €500 threshold).

**Rationale**: Small orders unlikely to have BD involvement.

**Tunable**: Adjust `SELF_SERVICE_AMOUNT_THRESHOLD` in config.

---

## Performance Considerations

### Time Complexity Analysis

#### **Overall Algorithm**: O(n × m)
```python
# n = number of orders
# m = number of deals

for order in orders:              # O(n)
    for deal in deals:            # O(m)
        # Filtering and scoring
```

**Worst Case**: 1000 orders × 1000 deals = 1,000,000 iterations.

**Mitigation Strategies**:

#### 1. **Pre-filter Won Deals**
```python
# Before main loop
won_deals = [d for d in deals if d.status == DealStatus.WON]  # O(m)

# Reduces m by ~70% (assuming 30% win rate)
```

#### 2. **Index by Company**
```python
# Build index: O(m)
deals_by_company = defaultdict(list)
for deal in won_deals:
    deals_by_company[deal.company_id].append(deal)

# Lookup: O(1) instead of O(m)
for order in orders:
    candidates = deals_by_company[order.company_id]  # Much smaller subset!
```

**Improvement**: O(n × m) → O(n × k), where k = avg deals per company (~10).

#### 3. **Parallel Processing**
```python
from concurrent.futures import ThreadPoolExecutor

def match_single_order(order):
    # Match logic for one order
    ...

with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(match_single_order, orders)
```

**Improvement**: 4x speedup on multi-core systems.

---

### Memory Considerations

#### **Current Memory Usage**:
```python
# Assuming:
# - 1000 orders
# - 1000 deals
# - 100 companies

# Memory per object:
Order:       ~200 bytes
Deal:        ~300 bytes
Company:     ~150 bytes
Attribution: ~400 bytes

# Total:
Orders:      1000 × 200 = 200 KB
Deals:       1000 × 300 = 300 KB
Companies:   100 × 150  = 15 KB
Attributions: 1000 × 400 = 400 KB

TOTAL: ~1 MB (negligible)
```

**Conclusion**: Memory is not a concern for typical use cases (<10K orders).

---

## Extension Points

### 1. Add Database Persistence
```python
# models.py
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class AttributionDB(Base):
    __tablename__ = "attributions"
    
    id = Column(String, primary_key=True)
    order_id = Column(String, index=True)
    deal_id = Column(String, index=True)
    sales_rep_id = Column(String, index=True)
    confidence_score = Column(Float)
    created_at = Column(DateTime)
    # ...

# main.py
@app.post("/match-orders")
async def match_orders(request: MatchRequest, db: Session = Depends(get_db)):
    matched, self_service, needs_review = matching_engine.match_orders(...)
    
    # Save to database
    for attr in matched:
        db.add(AttributionDB(**attr.dict()))
    db.commit()
    
    return MatchResponse(...)
```

---

### 2. Add Caching
```python
from functools import lru_cache
import hashlib
import json

def cache_key(order: Order, deals: List[Deal]) -> str:
    """Generate cache key for matching result"""
    data = {
        "order": order.dict(),
        "deals": [d.dict() for d in deals]
    }
    return hashlib.md5(json.dumps(data, sort_keys=True).encode()).hexdigest()

@lru_cache(maxsize=1000)
def match_order_cached(order_json: str, deals_json: str) -> Attribution:
    order = Order.parse_raw(order_json)
    deals = [Deal.parse_raw(d) for d in json.loads(deals_json)]
    return matching_engine.match_single_order(order, deals)
```

---

### 3. Add Webhooks
```python
# main.py
@app.post("/match-orders")
async def match_orders(request: MatchRequest):
    matched, self_service, needs_review = matching_engine.match_orders(...)
    
    # Send webhook for high-value matches
    for attr in matched:
        if attr.confidence_score >= 90 and order.amount > 10000:
            await send_webhook(
                url="https://your-crm.com/webhooks/attribution",
                data=attr.dict()
            )
    
    return MatchResponse(...)

async def send_webhook(url: str, data: dict):
    async with httpx.AsyncClient() as client:
        await client.post(url, json=data)
```

---

### 4. Add Machine Learning
```python
# Future enhancement: Learn from manual corrections

class MLMatchingEngine(MatchingEngine):
    def __init__(self):
        super().__init__()
        self.model = load_trained_model()  # scikit-learn, TensorFlow, etc.
    
    def _calculate_match_score(self, order, deal, company_dict):
        # Extract features
        features = self._extract_features(order, deal)
        
        # Predict confidence
        ml_score = self.model.predict([features])[0]
        
        # Combine with rule-based score
        rule_score = super()._calculate_match_score(order, deal, company_dict)
        
        # Weighted average
        return 0.7 * ml_score + 0.3 * rule_score
    
    def _extract_features(self, order, deal):
        return [
            order.amount,
            deal.amount,
            abs(order.amount - deal.amount),
            len(order.products or []),
            len(deal.products or []),
            # ... more features
        ]
```

---

### 5. Add A/B Testing
```python
# Test different scoring weights

class ABTestConfig:
    VARIANT_A = {  # Current
        "product_weight": 50,
        "amount_weight": 30,
        "temporal_weight": 15,
        "company_weight": 5
    }
    
    VARIANT_B = {  # More emphasis on amount
        "product_weight": 40,
        "amount_weight": 40,
        "temporal_weight": 15,
        "company_weight": 5
    }

@app.post("/match-orders")
async def match_orders(request: MatchRequest, variant: str = "A"):
    config = ABTestConfig.VARIANT_A if variant == "A" else ABTestConfig.VARIANT_B
    engine = MatchingEngine(config)
    
    matched, self_service, needs_review = engine.match_orders(...)
    
    # Log results for analysis
    log_ab_test_result(variant, matched, self_service, needs_review)
    
    return MatchResponse(...)
```

---

## Testing Recommendations

### Unit Tests
```python
# tests/test_matching_engine.py
import pytest
from app.matching_engine import MatchingEngine
from app.models import Order, Deal, Company, DealStatus

def test_perfect_match():
    """Test that identical order and deal score 100%"""
    engine = MatchingEngine()
    
    order = Order(
        id="order_1",
        company_id="company_1",
        amount=50000,
        order_date=datetime(2025, 1, 20),
        products=["CRM", "Support"]
    )
    
    deal = Deal(
        id="deal_1",
        company_id="company_1",
        sales_rep_id="rep_1",
        sales_rep_name="John Doe",
        amount=50000,
        status=DealStatus.WON,
        close_date=datetime(2025, 1, 15),
        products=["CRM", "Support"]
    )
    
    company = Company(
        id="company_1",
        name="TechCorp",
        created_at=datetime(2024, 1, 1)
    )
    
    score = engine._calculate_match_score(order, deal, {"company_1": company})
    
    assert score == 100.0, f"Expected 100.0, got {score}"

def test_no_match_different_products():
    """Test that different products result in low score"""
    # Similar to above, but with different products
    # Expected score: ~50 (no product match)
    ...

def test_self_service_threshold():
    """Test that small orders are marked as self-service"""
    # Order with amount < 500
    # Expected: self_service attribution
    ...
```

---

### Integration Tests
```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_match_orders_endpoint():
    """Test full matching flow via API"""
    payload = {
        "companies": [
            {
                "id": "company_1",
                "name": "TechCorp",
                "created_at": "2024-01-01T00:00:00Z"
            }
        ],
        "deals": [
            {
                "id": "deal_1",
                "company_id": "company_1",
                "sales_rep_id": "rep_1",
                "sales_rep_name": "John Doe",
                "amount": 50000,
                "status": "Won",
                "close_date": "2025-01-15T00:00:00Z",
                "created_at": "2024-12-01T00:00:00Z",
                "products": ["CRM", "Support"]
            }
        ],
        "orders": [
            {
                "id": "order_1",
                "company_id": "company_1",
                "amount": 50000,
                "order_date": "2025-01-20T00:00:00Z",
                "products": ["CRM", "Support"]
            }
        ]
    }
    
    response = client.post("/match-orders", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["matched"]) == 1
    assert data["matched"][0]["deal_id"] == "deal_1"
    assert data["matched"][0]["confidence_score"] == 100.0
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Dependencies pinned in requirements.txt
- [ ] Environment variables documented
- [ ] Health check endpoint working
- [ ] CORS configured correctly

### Deployment
- [ ] Deploy to staging first
- [ ] Run smoke tests
- [ ] Monitor logs for errors
- [ ] Check response times
- [ ] Verify /docs endpoint

### Post-Deployment
- [ ] Monitor error rates
- [ ] Check memory usage
- [ ] Verify all endpoints responding
- [ ] Test with production-like data
- [ ] Set up alerts for downtime

---

## Troubleshooting Guide

### Issue: Low Match Rate
```
Symptom: Most orders going to self_service or needs_review
```

**Diagnosis**:
1. Check `/config` endpoint - are thresholds too strict?
2. Inspect `matching_metadata` - what's failing? (products, amount, timing?)
3. Review deal data - are close_dates populated?

**Solutions**:
- Increase `VALUE_TOLERANCE_PERCENT` (e.g., 20% → 30%)
- Increase `MAX_DAYS_BEFORE_ORDER` (e.g., 90 → 120)
- Lower `CONFIDENCE_THRESHOLD_REVIEW` (e.g., 70 → 60)

---

### Issue: Wrong Matches
```
Symptom: Orders matched to incorrect deals
```

**Diagnosis**:
1. Check confidence scores - are they high despite being wrong?
2. Review product data - are product names inconsistent?
3. Check for duplicate deals

**Solutions**:
- Normalize product names (e.g., "CRM System" vs "CRM")
- Add product aliases/synonyms
- Increase product weight in scoring (50% → 60%)

---

### Issue: Slow Performance
```
Symptom: Requests taking > 5 seconds
```

**Diagnosis**:
1. Check input size - how many orders/deals?
2. Profile code to find bottleneck
3. Check for N+1 queries (if using database)

**Solutions**:
- Implement company indexing (see Performance section)
- Add caching for repeated requests
- Use async processing for large batches

---

## Conclusion

This development guide covers the complete technical implementation of the SatispayFlow matching service. The system uses a sophisticated multi-factor scoring algorithm to accurately attribute orders to deals, enabling fair commission calculation for Business Developers.

**Key Strengths**:
- Robust scoring system with configurable weights
- Handles edge cases and ambiguous matches
- Provides transparency via confidence scores and metadata
- Scalable architecture with clear extension points

**Next Steps**:
1. Add comprehensive test suite
2. Implement database persistence
3. Add monitoring and alerting
4. Consider ML enhancements for improved accuracy

---

**Document Version**: 1.0  
**Last Updated**: December 2025  
**Maintainer**: Development Team
