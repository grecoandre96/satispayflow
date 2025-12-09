# 🎯 Matching Logic Documentation

## Overview

The matching engine uses a **multi-level cascade strategy** to attribute Orders to Deals with varying levels of confidence.

---

## Matching Levels

### Level 1: Temporal + Value Match ⭐⭐⭐
**Highest Confidence**

#### Criteria
1. **Temporal**: Order date is AFTER Deal close date
2. **Temporal Window**: Order within 90 days of Deal close
3. **Value Match**: Order amount within ±10% of Deal amount

#### Example
```
Deal:
  - ID: deal_001
  - Company: TechCorp
  - Amount: €10,000
  - Close Date: 2024-06-01
  - Sales Rep: Alice

Order:
  - ID: order_001
  - Company: TechCorp
  - Amount: €10,200 (2% difference)
  - Order Date: 2024-06-15 (14 days after)

Result: ✅ MATCH
  - Method: temporal_value
  - Confidence: 96%
  - Attribution: Alice
```

#### Confidence Calculation
```python
base_score = 100

# Temporal penalty: -1 point per day
days_diff = 14
temporal_penalty = 14 * 1 = 14

# Value penalty: -10 points per 5% difference
value_diff_percent = 2%
value_penalty = (2 / 5) * 10 = 4

# Bonus: +30 if only one deal in period
unique_deal_bonus = 30

final_score = 100 - 14 - 4 + 30 = 112
capped_score = min(112, 100) = 100
```

---

### Level 2: Temporal Only Match ⭐⭐
**Medium Confidence - Always Flagged for Review**

#### Criteria
1. **Temporal**: Order date is AFTER Deal close date
2. **Temporal Window**: Order within 90 days of Deal close
3. **Value**: Does NOT match (>10% difference)

#### Example
```
Deal:
  - ID: deal_002
  - Amount: €5,000
  - Close Date: 2024-06-01

Order:
  - ID: order_002
  - Amount: €15,000 (200% difference!)
  - Order Date: 2024-06-15

Result: ⚠️ MATCH (needs review)
  - Method: temporal_only
  - Confidence: 56% (after 20% penalty)
  - Needs Review: TRUE
```

#### Why Flag for Review?
- Large value discrepancy suggests:
  - Deal amount was estimated incorrectly
  - Order includes additional products
  - Multiple deals combined into one order
  - Wrong deal being matched

#### Confidence Calculation
```python
base_score = 100
temporal_penalty = 14
value_penalty = (200 / 5) * 10 = 400 (capped)

score = 100 - 14 - 400 = -314 (floored to 0)

# Apply temporal-only penalty (20%)
final_score = 70 * 0.8 = 56%
```

---

### Level 3: Self-Service Detection 🤖
**No Sales Rep Attribution**

#### Criteria (Any of these)
1. **Low Value**: Order amount < €500
2. **No Deals**: Company has no Won deals
3. **No Temporal Match**: No deals within 90-day window

#### Examples

**Example 1: Low Value**
```
Order:
  - ID: order_003
  - Amount: €350
  - Company: SmallBiz

Result: 🤖 SELF-SERVICE
  - Reason: "Order amount below self-service threshold"
  - Confidence: 100%
  - Sales Rep: None
```

**Example 2: No Deals**
```
Order:
  - ID: order_004
  - Amount: €5,000
  - Company: NewCompany (no deals in CRM)

Result: 🤖 SELF-SERVICE
  - Reason: "No Won deals found for this company"
  - Confidence: 100%
  - Sales Rep: None
```

**Example 3: Old Deal**
```
Deal:
  - Close Date: 2024-01-01

Order:
  - Order Date: 2024-12-01 (11 months later)

Result: 🤖 SELF-SERVICE
  - Reason: "No Won deals found within time window"
  - Confidence: 100%
  - Sales Rep: None
```

---

## Configuration Parameters

### Default Values
```python
time_window_days = 90              # Max days between deal close and order
value_tolerance_percent = 10.0     # ±10% tolerance for value matching
self_service_threshold = 500.0     # Orders below €500 are self-service
confidence_threshold = 70.0        # Min confidence for auto-attribution
temporal_decay_per_day = 1.0       # Score penalty per day distance
value_penalty_per_5_percent = 10.0 # Score penalty per 5% value diff
unique_deal_bonus = 30.0           # Bonus if only one deal in period
```

### Customization
These can be adjusted based on:
- **Industry**: B2B vs B2C
- **Sales Cycle**: Short vs long
- **Deal Size**: Small vs enterprise
- **Business Model**: Transactional vs subscription

---

## Edge Cases

### Case 1: Multiple Deals in Period
```
Company: TechCorp

Deals:
  - deal_001: €10,000, closed 2024-06-01 (Alice)
  - deal_002: €12,000, closed 2024-06-15 (Bob)

Order:
  - order_001: €11,500, ordered 2024-06-20

Solution:
  - Calculate confidence for BOTH deals
  - Choose deal with HIGHEST confidence
  - In this case: deal_002 (Bob) - more recent + closer value
```

### Case 2: Deal After Order
```
Deal:
  - Close Date: 2024-07-01

Order:
  - Order Date: 2024-06-15 (BEFORE deal close)

Result: ❌ NOT MATCHED
  - Orders must come AFTER deal close
  - Marked as self-service or flagged for review
```

### Case 3: Exact Same Amount, Different Dates
```
Deals:
  - deal_001: €10,000, closed 2024-05-01 (90 days ago)
  - deal_002: €10,000, closed 2024-07-01 (10 days ago)

Order:
  - order_001: €10,000, ordered 2024-07-15

Solution:
  - Both match on value
  - deal_002 wins due to temporal proximity
  - Confidence: Higher for deal_002
```

### Case 4: No Clear Winner
```
Scenario:
  - Multiple deals with similar confidence scores
  - Difference < 5 points

Solution:
  - Flag for manual review
  - Include ALL candidate deals in metadata
  - Let human decide based on context
```

---

## Confidence Score Breakdown

### Score Components

| Component | Impact | Example |
|-----------|--------|---------|
| **Base Score** | +100 | Starting point |
| **Temporal Penalty** | -1 per day | 30 days = -30 |
| **Value Penalty** | -10 per 5% diff | 15% diff = -30 |
| **Unique Deal Bonus** | +30 | Only one deal |
| **Temporal-Only Penalty** | -20% | Value mismatch |

### Score Ranges

| Range | Interpretation | Action |
|-------|---------------|--------|
| **90-100** | Excellent match | Auto-attribute |
| **70-89** | Good match | Auto-attribute |
| **50-69** | Uncertain | Flag for review |
| **0-49** | Poor match | Flag for review |

---

## Decision Tree

```
START: New Order
│
├─ Is amount < €500?
│  └─ YES → SELF-SERVICE
│
├─ Does company have Won deals?
│  └─ NO → SELF-SERVICE
│
├─ Any deals closed before order date?
│  └─ NO → SELF-SERVICE
│
├─ Any deals within 90-day window?
│  └─ NO → SELF-SERVICE
│
├─ Filter deals in time window
│
├─ Any deals with matching value (±10%)?
│  ├─ YES → Calculate confidence
│  │        ├─ Score ≥ 70? → MATCH (temporal_value)
│  │        └─ Score < 70? → NEEDS REVIEW
│  │
│  └─ NO → Try temporal-only match
│           ├─ Most recent deal exists?
│           │  └─ YES → NEEDS REVIEW (temporal_only)
│           └─ NO → SELF-SERVICE
│
END
```

---

## Metadata Captured

For each attribution, we store:

```json
{
  "order_id": "order_001",
  "deal_id": "deal_001",
  "sales_rep_id": "rep_alice",
  "sales_rep_name": "Alice Johnson",
  "attribution_method": "temporal_value",
  "confidence_score": 96.5,
  "needs_review": false,
  "matching_metadata": {
    "days_difference": 14,
    "value_difference_percent": 2.0,
    "order_amount": 10200.0,
    "deal_amount": 10000.0,
    "candidates_count": 1,
    "timestamp": "2024-12-09T16:00:00Z"
  }
}
```

---

## Testing Scenarios

### Scenario 1: Perfect Match
- ✅ Same company
- ✅ Order 10 days after deal close
- ✅ Value within 5%
- **Expected**: High confidence match

### Scenario 2: Value Mismatch
- ✅ Same company
- ✅ Order 15 days after deal close
- ❌ Value differs by 50%
- **Expected**: Temporal-only match, flagged for review

### Scenario 3: Time Gap
- ✅ Same company
- ❌ Order 120 days after deal close
- ✅ Value matches
- **Expected**: Self-service (outside time window)

### Scenario 4: Multiple Deals
- ✅ Same company
- ✅ Two deals in time window
- ✅ Order matches both
- **Expected**: Match to most recent deal

### Scenario 5: New Customer
- ❌ No deals in CRM
- ✅ Order amount > €500
- **Expected**: Self-service

---

## Performance Optimization

### Current Implementation
- **Time Complexity**: O(n * m) where n = orders, m = deals
- **Space Complexity**: O(n + m)

### Optimizations for Scale
1. **Indexing**: Index deals by company_id and close_date
2. **Caching**: Cache company-deal mappings
3. **Batch Processing**: Process orders in batches
4. **Parallel Processing**: Use multiprocessing for large datasets
5. **Database Queries**: Use SQL joins instead of in-memory filtering

---

## Audit Trail

Every attribution decision is logged with:
- Input data (order, deals considered)
- Matching method used
- Confidence score calculation
- Final decision
- Timestamp
- User who triggered (if manual)

This enables:
- Debugging incorrect attributions
- Improving algorithm over time
- Compliance and transparency
- Performance analysis
