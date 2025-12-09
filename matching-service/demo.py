"""
Test script to demonstrate the matching engine with sample data
Run this to see the matching logic in action
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models import Company, Deal, Order, MatchConfig
from app.matching_engine import MatchingEngine
from app.utils import create_summary_stats


def load_json_data(filename: str):
    """Load JSON data from file"""
    data_path = Path(__file__).parent.parent / "data" / filename
    with open(data_path, 'r') as f:
        return json.load(f)


def parse_datetime(dt_str):
    """Parse ISO datetime string"""
    if dt_str is None:
        return None
    return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))


def main():
    print("=" * 80)
    print("🚀 SatispayFlow - Deal Attribution Demo")
    print("=" * 80)
    print()
    
    # Load data
    print("📂 Loading sample data...")
    companies_data = load_json_data("companies.json")
    deals_data = load_json_data("deals.json")
    orders_data = load_json_data("orders.json")
    
    # Parse into models
    companies = [
        Company(
            id=c['id'],
            name=c['name'],
            created_at=parse_datetime(c['created_at'])
        )
        for c in companies_data
    ]
    
    deals = [
        Deal(
            id=d['id'],
            company_id=d['company_id'],
            sales_rep_id=d['sales_rep_id'],
            sales_rep_name=d['sales_rep_name'],
            amount=d['amount'],
            status=d['status'],
            close_date=parse_datetime(d['close_date']),
            created_at=parse_datetime(d['created_at'])
        )
        for d in deals_data
    ]
    
    orders = [
        Order(
            id=o['id'],
            company_id=o['company_id'],
            amount=o['amount'],
            order_date=parse_datetime(o['order_date']),
            products=o.get('products')
        )
        for o in orders_data
    ]
    
    print(f"✅ Loaded {len(companies)} companies, {len(deals)} deals, {len(orders)} orders")
    print()
    
    # Create matching config
    config = MatchConfig(
        time_window_days=90,
        value_tolerance_percent=10.0,
        self_service_threshold=500.0,
        confidence_threshold=70.0
    )
    
    print("⚙️  Matching Configuration:")
    print(f"   - Time window: {config.time_window_days} days")
    print(f"   - Value tolerance: ±{config.value_tolerance_percent}%")
    print(f"   - Self-service threshold: €{config.self_service_threshold}")
    print(f"   - Confidence threshold: {config.confidence_threshold}%")
    print()
    
    # Run matching
    print("🔄 Running matching engine...")
    engine = MatchingEngine(config)
    matched, self_service, needs_review = engine.match_orders(companies, deals, orders)
    
    # Create summary
    summary = create_summary_stats(matched, self_service, needs_review)
    
    print()
    print("=" * 80)
    print("📊 RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total Orders:        {summary['total_orders']}")
    print(f"✅ Matched:          {summary['matched_count']} ({summary['match_rate_percent']}%)")
    print(f"🤖 Self-Service:     {summary['self_service_count']}")
    print(f"⚠️  Needs Review:     {summary['needs_review_count']}")
    print(f"📈 Avg Confidence:   {summary['average_confidence']}%")
    print()
    
    # Show matched orders
    if matched:
        print("=" * 80)
        print("✅ MATCHED ORDERS")
        print("=" * 80)
        for attr in matched:
            print(f"\nOrder: {attr.order_id}")
            print(f"  → Deal: {attr.deal_id}")
            print(f"  → Sales Rep: {attr.sales_rep_name} ({attr.sales_rep_id})")
            print(f"  → Method: {attr.attribution_method}")
            print(f"  → Confidence: {attr.confidence_score:.1f}%")
            print(f"  → Metadata: {attr.matching_metadata}")
    
    # Show self-service orders
    if self_service:
        print()
        print("=" * 80)
        print("🤖 SELF-SERVICE ORDERS")
        print("=" * 80)
        for attr in self_service:
            print(f"\nOrder: {attr.order_id}")
            print(f"  → Reason: {attr.matching_metadata.get('reason')}")
            print(f"  → Amount: €{attr.matching_metadata.get('order_amount')}")
    
    # Show orders needing review
    if needs_review:
        print()
        print("=" * 80)
        print("⚠️  ORDERS NEEDING MANUAL REVIEW")
        print("=" * 80)
        for attr in needs_review:
            print(f"\nOrder: {attr.order_id}")
            print(f"  → Suggested Deal: {attr.deal_id}")
            print(f"  → Suggested Rep: {attr.sales_rep_name}")
            print(f"  → Confidence: {attr.confidence_score:.1f}%")
            print(f"  → Reason: {attr.matching_metadata}")
    
    print()
    print("=" * 80)
    print("✨ Demo Complete!")
    print("=" * 80)
    
    # Save results
    output_path = Path(__file__).parent.parent / "data" / "attributions.json"
    all_attributions = matched + self_service + needs_review
    
    with open(output_path, 'w') as f:
        json.dump(
            [attr.dict() for attr in all_attributions],
            f,
            indent=2,
            default=str
        )
    
    print(f"\n💾 Results saved to: {output_path}")


if __name__ == "__main__":
    main()
