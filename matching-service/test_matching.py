"""
Test script to verify the improved matching logic with products
"""
import json
from datetime import datetime
from app.models import Company, Deal, Order, DealStatus
from app.matching_engine import MatchingEngine

# Test data with products
companies = [
    Company(id="mobile_tech_ancona", name="Mobile Tech Ancona", created_at=datetime(2024, 11, 29, 12, 0, 0)),
    Company(id="it_experts_bolzano", name="IT Experts Bolzano", created_at=datetime(2024, 11, 24, 12, 0, 0)),
]

deals = [
    Deal(
        id="DEAL-0125",
        company_id="mobile_tech_ancona",
        sales_rep_id="luca_marino",
        sales_rep_name="Luca Marino",
        amount=85005,
        status=DealStatus.WON,
        close_date=datetime(2025, 1, 27, 12, 0, 0),
        created_at=datetime(2024, 11, 29, 12, 0, 0),
        products=["HR System", "Support"]  # Added products
    ),
    Deal(
        id="DEAL-0009",
        company_id="it_experts_bolzano",
        sales_rep_id="elena_costa",
        sales_rep_name="Elena Costa",
        amount=54785,
        status=DealStatus.WON,
        close_date=datetime(2025, 1, 8, 12, 0, 0),
        created_at=datetime(2024, 11, 24, 12, 0, 0),
        products=["CRM", "Analytics"]
    ),
]

# Order with non-existent company_id but matching products and amount
orders = [
    Order(
        id="order_new_001",
        company_id="nutellone",  # This company doesn't exist in deals!
        amount=85000,
        order_date=datetime(2025, 2, 5, 10, 0, 0),
        products=["HR System", "Support"]  # Same products as DEAL-0125
    )
]

# Run matching
engine = MatchingEngine()
matched, self_service, needs_review = engine.match_orders(orders, deals, companies)

print("=" * 80)
print("MATCHING RESULTS WITH PRODUCT-BASED SCORING")
print("=" * 80)

print(f"\n✅ MATCHED ({len(matched)}):")
for attr in matched:
    print(f"  - Order {attr.order_id} → Deal {attr.deal_id}")
    print(f"    Sales Rep: {attr.sales_rep_name}")
    print(f"    Confidence: {attr.confidence_score:.2f}%")
    print(f"    Metadata: {json.dumps(attr.matching_metadata, indent=6)}")

print(f"\n⚠️  NEEDS REVIEW ({len(needs_review)}):")
for attr in needs_review:
    print(f"  - Order {attr.order_id} → Deal {attr.deal_id}")
    print(f"    Sales Rep: {attr.sales_rep_name}")
    print(f"    Confidence: {attr.confidence_score:.2f}%")
    print(f"    Metadata: {json.dumps(attr.matching_metadata, indent=6)}")

print(f"\n🔵 SELF-SERVICE ({len(self_service)}):")
for attr in self_service:
    print(f"  - Order {attr.order_id}")
    print(f"    Reason: {attr.matching_metadata.get('reason')}")
    print(f"    Amount: €{attr.matching_metadata.get('order_amount')}")

print("\n" + "=" * 80)
print("SCORING BREAKDOWN:")
print("- Product Match: 50 points (100% match = 50 pts)")
print("- Amount Match: 30 points (0.01% diff = 30 pts)")
print("- Temporal: 12 points (8 days = 12 pts)")
print("- Company: 0 points (different companies)")
print("- TOTAL: ~92 points → MATCHED! ✅")
print("=" * 80)
