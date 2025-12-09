import pytest
from datetime import datetime
from app.models import Company, Deal, Order, MatchConfig
from app.matching_engine import MatchingEngine


@pytest.fixture
def sample_companies():
    return [
        Company(id="comp_001", name="Test Company", created_at=datetime(2024, 1, 1))
    ]


@pytest.fixture
def sample_deals():
    return [
        Deal(
            id="deal_001",
            company_id="comp_001",
            sales_rep_id="rep_alice",
            sales_rep_name="Alice Johnson",
            amount=10000.0,
            status="Won",
            close_date=datetime(2024, 6, 1),
            created_at=datetime(2024, 5, 1)
        )
    ]


@pytest.fixture
def sample_orders():
    return [
        Order(
            id="order_001",
            company_id="comp_001",
            amount=10200.0,
            order_date=datetime(2024, 6, 15)
        )
    ]


@pytest.fixture
def matching_config():
    return MatchConfig(
        time_window_days=90,
        value_tolerance_percent=10.0,
        self_service_threshold=500.0,
        confidence_threshold=70.0
    )


def test_perfect_match(sample_companies, sample_deals, sample_orders, matching_config):
    """Test perfect temporal and value match"""
    engine = MatchingEngine(matching_config)
    matched, self_service, needs_review = engine.match_orders(
        sample_companies, sample_deals, sample_orders
    )
    
    assert len(matched) == 1
    assert len(self_service) == 0
    assert matched[0].order_id == "order_001"
    assert matched[0].deal_id == "deal_001"
    assert matched[0].sales_rep_id == "rep_alice"
    assert matched[0].confidence_score > 70.0


def test_self_service_low_value(sample_companies, sample_deals, matching_config):
    """Test self-service detection for low value orders"""
    low_value_order = [
        Order(
            id="order_002",
            company_id="comp_001",
            amount=300.0,  # Below threshold
            order_date=datetime(2024, 6, 15)
        )
    ]
    
    engine = MatchingEngine(matching_config)
    matched, self_service, needs_review = engine.match_orders(
        sample_companies, sample_deals, low_value_order
    )
    
    assert len(self_service) == 1
    assert len(matched) == 0
    assert self_service[0].attribution_method == "self_service"


def test_no_deals_for_company(sample_companies, matching_config):
    """Test self-service when company has no deals"""
    no_deals = []
    order = [
        Order(
            id="order_003",
            company_id="comp_001",
            amount=5000.0,
            order_date=datetime(2024, 6, 15)
        )
    ]
    
    engine = MatchingEngine(matching_config)
    matched, self_service, needs_review = engine.match_orders(
        sample_companies, no_deals, order
    )
    
    assert len(self_service) == 1
    assert self_service[0].attribution_method == "self_service"


def test_temporal_only_match(sample_companies, matching_config):
    """Test temporal match when value differs significantly"""
    deals = [
        Deal(
            id="deal_002",
            company_id="comp_001",
            sales_rep_id="rep_bob",
            sales_rep_name="Bob Smith",
            amount=5000.0,  # Very different from order
            status="Won",
            close_date=datetime(2024, 6, 1),
            created_at=datetime(2024, 5, 1)
        )
    ]
    
    orders = [
        Order(
            id="order_004",
            company_id="comp_001",
            amount=15000.0,  # 200% difference
            order_date=datetime(2024, 6, 15)
        )
    ]
    
    engine = MatchingEngine(matching_config)
    matched, self_service, needs_review = engine.match_orders(
        sample_companies, deals, orders
    )
    
    # Should be flagged for review due to value difference
    assert len(needs_review) >= 1 or len(matched) == 1
    if len(matched) == 1:
        assert matched[0].needs_review == True


def test_confidence_score_calculation(matching_config):
    """Test confidence score calculation logic"""
    engine = MatchingEngine(matching_config)
    
    # Test with minimal differences
    score = engine._calculate_confidence_score(
        order=None,  # Not used in calculation
        deal=None,   # Not used in calculation
        days_diff=10,
        value_diff_percent=5.0,
        total_deals=1
    )
    
    # Score should be: 100 - (10*1) - (5/5*10) + 30 = 110 (capped at 100)
    assert score == 100.0
    
    # Test with larger differences
    score = engine._calculate_confidence_score(
        order=None,
        deal=None,
        days_diff=30,
        value_diff_percent=15.0,
        total_deals=3
    )
    
    # Score should be: 100 - (30*1) - (15/5*10) = 40
    assert score == 40.0
