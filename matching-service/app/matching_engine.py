from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

from .models import Company, Deal, Order, Attribution, MatchConfig


class MatchingEngine:
    """
    Core matching engine for attributing Orders to Deals
    
    Uses multi-level matching strategy:
    1. Temporal + Value match (highest confidence)
    2. Temporal only match (medium confidence)
    3. Self-service detection (no sales rep)
    """
    
    def __init__(self, config: MatchConfig):
        self.config = config
        logger.info(f"MatchingEngine initialized with config: {config.dict()}")
    
    def match_orders(
        self,
        companies: List[Company],
        deals: List[Deal],
        orders: List[Order]
    ) -> Tuple[List[Attribution], List[Attribution], List[Attribution]]:
        """
        Match orders to deals and return categorized results
        
        Returns:
            Tuple of (matched, self_service, needs_review)
        """
        logger.info(f"Starting matching: {len(orders)} orders, {len(deals)} deals, {len(companies)} companies")
        
        # Convert to DataFrames for easier manipulation
        df_deals = pd.DataFrame([d.dict() for d in deals])
        df_orders = pd.DataFrame([o.dict() for o in orders])
        
        # Filter only Won deals
        df_deals = df_deals[df_deals['status'] == 'Won'].copy()
        logger.info(f"Filtered to {len(df_deals)} Won deals")
        
        matched = []
        self_service = []
        needs_review = []
        
        for order in orders:
            attribution = self._match_single_order(order, df_deals)
            
            if attribution.attribution_method == "self_service":
                self_service.append(attribution)
            elif attribution.needs_review:
                needs_review.append(attribution)
            else:
                matched.append(attribution)
        
        logger.info(f"Matching complete: {len(matched)} matched, {len(self_service)} self-service, {len(needs_review)} need review")
        
        return matched, self_service, needs_review
    
    def _match_single_order(self, order: Order, df_deals: pd.DataFrame) -> Attribution:
        """Match a single order to the best deal"""
        
        # Check if self-service (low value)
        if order.amount < self.config.self_service_threshold:
            return self._create_self_service_attribution(
                order,
                reason="Order amount below self-service threshold"
            )
        
        # Get deals for this company
        company_deals = df_deals[df_deals['company_id'] == order.company_id].copy()
        
        if len(company_deals) == 0:
            return self._create_self_service_attribution(
                order,
                reason="No Won deals found for this company"
            )
        
        # Filter deals that closed before the order
        company_deals = company_deals[
            company_deals['close_date'] < order.order_date
        ].copy()
        
        if len(company_deals) == 0:
            return self._create_self_service_attribution(
                order,
                reason="No Won deals found before order date"
            )
        
        # Try Level 1: Temporal + Value match
        best_match = self._find_temporal_value_match(order, company_deals)
        if best_match is not None:
            return best_match
        
        # Try Level 2: Temporal only match
        best_match = self._find_temporal_match(order, company_deals)
        if best_match is not None:
            return best_match
        
        # No good match found
        return self._create_self_service_attribution(
            order,
            reason="No suitable deal match found within time window"
        )
    
    def _find_temporal_value_match(
        self,
        order: Order,
        company_deals: pd.DataFrame
    ) -> Optional[Attribution]:
        """Level 1: Match based on time proximity AND value similarity"""
        
        candidates = []
        
        for _, deal in company_deals.iterrows():
            # Check time window
            days_diff = (order.order_date - deal['close_date']).days
            if days_diff > self.config.time_window_days or days_diff < 0:
                continue
            
            # Check value similarity
            value_diff_percent = abs(order.amount - deal['amount']) / deal['amount'] * 100
            if value_diff_percent > self.config.value_tolerance_percent:
                continue
            
            # Calculate confidence score
            score = self._calculate_confidence_score(
                order,
                deal,
                days_diff,
                value_diff_percent,
                len(company_deals)
            )
            
            candidates.append({
                'deal': deal,
                'score': score,
                'days_diff': days_diff,
                'value_diff_percent': value_diff_percent
            })
        
        if not candidates:
            return None
        
        # Get best candidate
        best = max(candidates, key=lambda x: x['score'])
        deal = best['deal']
        
        return Attribution(
            order_id=order.id,
            deal_id=deal['id'],
            sales_rep_id=deal['sales_rep_id'],
            sales_rep_name=deal['sales_rep_name'],
            attribution_method="temporal_value",
            confidence_score=best['score'],
            needs_review=best['score'] < self.config.confidence_threshold,
            matching_metadata={
                'days_difference': int(best['days_diff']),
                'value_difference_percent': round(best['value_diff_percent'], 2),
                'order_amount': order.amount,
                'deal_amount': float(deal['amount']),
                'candidates_count': len(candidates)
            }
        )
    
    def _find_temporal_match(
        self,
        order: Order,
        company_deals: pd.DataFrame
    ) -> Optional[Attribution]:
        """Level 2: Match based on time proximity only (most recent deal)"""
        
        # Filter by time window
        max_date = order.order_date - timedelta(days=self.config.time_window_days)
        recent_deals = company_deals[company_deals['close_date'] >= max_date].copy()
        
        if len(recent_deals) == 0:
            return None
        
        # Get most recent deal
        recent_deals = recent_deals.sort_values('close_date', ascending=False)
        deal = recent_deals.iloc[0]
        
        days_diff = (order.order_date - deal['close_date']).days
        value_diff_percent = abs(order.amount - deal['amount']) / deal['amount'] * 100
        
        score = self._calculate_confidence_score(
            order,
            deal,
            days_diff,
            value_diff_percent,
            len(company_deals)
        )
        
        # Penalize temporal-only matches
        score = score * 0.8  # 20% penalty for not matching value
        
        return Attribution(
            order_id=order.id,
            deal_id=deal['id'],
            sales_rep_id=deal['sales_rep_id'],
            sales_rep_name=deal['sales_rep_name'],
            attribution_method="temporal_only",
            confidence_score=score,
            needs_review=True,  # Always flag temporal-only for review
            matching_metadata={
                'days_difference': int(days_diff),
                'value_difference_percent': round(value_diff_percent, 2),
                'order_amount': order.amount,
                'deal_amount': float(deal['amount']),
                'reason': 'Temporal match only - value differs significantly'
            }
        )
    
    def _calculate_confidence_score(
        self,
        order: Order,
        deal: pd.Series,
        days_diff: int,
        value_diff_percent: float,
        total_deals: int
    ) -> float:
        """Calculate confidence score for a match"""
        
        score = 100.0
        
        # Temporal penalty: -1 point per day
        score -= days_diff * self.config.temporal_decay_per_day
        
        # Value penalty: -10 points per 5% difference
        score -= (value_diff_percent / 5.0) * self.config.value_penalty_per_5_percent
        
        # Bonus if this is the only deal in the period
        if total_deals == 1:
            score += self.config.unique_deal_bonus
        
        # Ensure score is in valid range
        return max(0.0, min(100.0, score))
    
    def _create_self_service_attribution(
        self,
        order: Order,
        reason: str
    ) -> Attribution:
        """Create a self-service attribution (no sales rep)"""
        
        return Attribution(
            order_id=order.id,
            deal_id=None,
            sales_rep_id=None,
            sales_rep_name=None,
            attribution_method="self_service",
            confidence_score=100.0,  # High confidence it's self-service
            needs_review=False,
            matching_metadata={
                'reason': reason,
                'order_amount': order.amount
            }
        )
