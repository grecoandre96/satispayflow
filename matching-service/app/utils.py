from datetime import datetime
from typing import Dict


def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO string"""
    return dt.isoformat()


def calculate_percentage_difference(value1: float, value2: float) -> float:
    """Calculate percentage difference between two values"""
    if value2 == 0:
        return 100.0 if value1 != 0 else 0.0
    return abs(value1 - value2) / value2 * 100


def create_summary_stats(matched: list, self_service: list, needs_review: list) -> Dict:
    """Create summary statistics for matching results"""
    
    total = len(matched) + len(self_service) + len(needs_review)
    
    if total == 0:
        return {
            'total_orders': 0,
            'matched_count': 0,
            'self_service_count': 0,
            'needs_review_count': 0,
            'match_rate_percent': 0.0,
            'average_confidence': 0.0
        }
    
    # Calculate average confidence for matched orders
    avg_confidence = 0.0
    if matched:
        avg_confidence = sum(a.confidence_score for a in matched) / len(matched)
    
    return {
        'total_orders': total,
        'matched_count': len(matched),
        'self_service_count': len(self_service),
        'needs_review_count': len(needs_review),
        'match_rate_percent': round((len(matched) / total) * 100, 2),
        'average_confidence': round(avg_confidence, 2),
        'attribution_methods': {
            'temporal_value': len([a for a in matched if a.attribution_method == 'temporal_value']),
            'temporal_only': len([a for a in matched if a.attribution_method == 'temporal_only']),
            'self_service': len(self_service)
        }
    }
