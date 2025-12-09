from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from difflib import SequenceMatcher
from .models import (
    Order, Deal, Company, Attribution, 
    AttributionMethod, DealStatus
)


class MatchingConfig:
    """Configuration for matching algorithm"""
    # Temporal matching
    MAX_DAYS_BEFORE_ORDER = 90  # Deal can be up to 90 days before order
    MAX_DAYS_AFTER_ORDER = 30   # Deal can be up to 30 days after order
    
    # Value matching
    VALUE_TOLERANCE_PERCENT = 20.0  # 20% tolerance for amount differences
    
    # Confidence scoring
    CONFIDENCE_THRESHOLD_REVIEW = 70.0  # Below this, needs manual review
    
    # Self-service thresholds
    SELF_SERVICE_AMOUNT_THRESHOLD = 500.0  # Orders below this are self-service
    
    # Fuzzy matching
    COMPANY_NAME_SIMILARITY_THRESHOLD = 0.6  # 60% similarity for company names


class MatchingEngine:
    """Engine for matching orders to deals"""
    
    def __init__(self, config: MatchingConfig = None):
        self.config = config or MatchingConfig()
    
    def match_orders(
        self, 
        orders: List[Order], 
        deals: List[Deal],
        companies: List[Company]
    ) -> Tuple[List[Attribution], List[Attribution], List[Attribution]]:
        """
        Match orders to deals using multi-level matching logic
        
        Returns:
            - matched: High confidence matches
            - self_service: Orders without sales rep involvement
            - needs_review: Low confidence matches
        """
        matched = []
        self_service = []
        needs_review = []
        
        # Create lookup dictionaries
        company_dict = {c.id: c for c in companies}
        
        # Filter only Won deals
        won_deals = [d for d in deals if d.status == DealStatus.WON]
        
        for order in orders:
            # Check self-service threshold
            if order.amount < self.config.SELF_SERVICE_AMOUNT_THRESHOLD:
                self_service.append(self._create_self_service_attribution(
                    order, 
                    reason="Order amount below self-service threshold"
                ))
                continue
            
            # Find candidate deals
            candidates = self._find_candidate_deals(order, won_deals, company_dict)
            
            if not candidates:
                # No matches found
                self_service.append(self._create_self_service_attribution(
                    order,
                    reason="No suitable deal match found within time window"
                ))
                continue
            
            # Score and select best match
            best_match = self._select_best_match(order, candidates, company_dict)
            
            if best_match.confidence_score >= self.config.CONFIDENCE_THRESHOLD_REVIEW:
                matched.append(best_match)
            else:
                needs_review.append(best_match)
        
        return matched, self_service, needs_review
    
    def _find_candidate_deals(
        self, 
        order: Order, 
        deals: List[Deal],
        company_dict: Dict[str, Company]
    ) -> List[Deal]:
        """Find all deals that could potentially match this order"""
        candidates = []
        
        order_company = company_dict.get(order.company_id)
        
        for deal in deals:
            # Skip if no close date
            if not deal.close_date:
                continue
            
            # Temporal filter
            days_diff = (order.order_date - deal.close_date).days
            if not (-self.config.MAX_DAYS_BEFORE_ORDER <= days_diff <= self.config.MAX_DAYS_AFTER_ORDER):
                continue
            
            # Value filter
            value_diff_percent = abs(order.amount - deal.amount) / deal.amount * 100
            if value_diff_percent > self.config.VALUE_TOLERANCE_PERCENT:
                continue
            
            # Company matching - three strategies:
            # 1. Exact company_id match
            if order.company_id == deal.company_id:
                candidates.append(deal)
                continue
            
            # 2. Fuzzy company name match (for new companies)
            if order_company:
                deal_company = company_dict.get(deal.company_id)
                if deal_company:
                    similarity = self._calculate_company_similarity(
                        order_company.name, 
                        deal_company.name
                    )
                    if similarity >= self.config.COMPANY_NAME_SIMILARITY_THRESHOLD:
                        candidates.append(deal)
                        continue
            
            # 3. Amount-based matching (if company is new but amount matches closely)
            if value_diff_percent <= 5.0:  # Very close amount match
                candidates.append(deal)
        
        return candidates
    
    def _calculate_company_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two company names"""
        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, n1, n2).ratio()
    
    def _select_best_match(
        self, 
        order: Order, 
        candidates: List[Deal],
        company_dict: Dict[str, Company]
    ) -> Attribution:
        """Select the best matching deal from candidates"""
        if len(candidates) == 1:
            return self._create_attribution(order, candidates[0], company_dict)
        
        # Score each candidate
        scored_candidates = []
        for deal in candidates:
            score = self._calculate_match_score(order, deal, company_dict)
            scored_candidates.append((deal, score))
        
        # Sort by score (descending)
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Return best match
        best_deal, best_score = scored_candidates[0]
        return self._create_attribution(
            order, 
            best_deal, 
            company_dict,
            custom_confidence=best_score
        )
    
    def _calculate_match_score(
        self, 
        order: Order, 
        deal: Deal,
        company_dict: Dict[str, Company]
    ) -> float:
        """
        Calculate confidence score for a match
        
        New scoring system (total 100 points):
        - Product match: 50 points (most important)
        - Amount match: 30 points (second most important)
        - Temporal proximity: 15 points
        - Company match: 5 points (least important since products/amount are better indicators)
        """
        score = 0.0
        
        # Product match score (50 points max) - HIGHEST PRIORITY
        if order.products and deal.products:
            # Calculate product overlap
            order_products_set = set(p.lower().strip() for p in order.products)
            deal_products_set = set(p.lower().strip() for p in deal.products)
            
            if order_products_set and deal_products_set:
                # Calculate Jaccard similarity (intersection / union)
                intersection = len(order_products_set & deal_products_set)
                union = len(order_products_set | deal_products_set)
                product_similarity = intersection / union if union > 0 else 0
                score += product_similarity * 50.0
        elif not order.products and not deal.products:
            # If neither has products, give neutral score
            score += 25.0
        # If only one has products, give 0 points (mismatch)
        
        # Value match score (30 points max) - SECOND PRIORITY
        value_diff_percent = abs(order.amount - deal.amount) / deal.amount * 100
        if value_diff_percent <= 1.0:
            # Perfect match (within 1%)
            value_score = 30.0
        elif value_diff_percent <= 5.0:
            # Excellent match (within 5%)
            value_score = 25.0
        elif value_diff_percent <= 10.0:
            # Good match (within 10%)
            value_score = 20.0
        elif value_diff_percent <= 15.0:
            # Acceptable match (within 15%)
            value_score = 15.0
        else:
            # Poor match - linear decay
            value_score = max(0, 30 - (value_diff_percent * 1.5))
        score += value_score
        
        # Temporal proximity score (15 points max)
        if deal.close_date:
            days_diff = abs((order.order_date - deal.close_date).days)
            if days_diff <= 7:
                temporal_score = 15.0
            elif days_diff <= 14:
                temporal_score = 12.0
            elif days_diff <= 30:
                temporal_score = 8.0
            else:
                temporal_score = max(0, 15 - (days_diff / 6))  # Lose 1 point per 6 days
            score += temporal_score
        
        # Company match score (5 points max) - LOWEST PRIORITY
        if order.company_id == deal.company_id:
            score += 5.0
        else:
            order_company = company_dict.get(order.company_id)
            deal_company = company_dict.get(deal.company_id)
            if order_company and deal_company:
                similarity = self._calculate_company_similarity(
                    order_company.name,
                    deal_company.name
                )
                score += similarity * 5.0
        
        return min(100.0, score)
    
    def _create_attribution(
        self, 
        order: Order, 
        deal: Deal,
        company_dict: Dict[str, Company],
        custom_confidence: Optional[float] = None
    ) -> Attribution:
        """Create an attribution object for a matched order"""
        days_diff = abs((order.order_date - deal.close_date).days) if deal.close_date else 0
        value_diff_percent = abs(order.amount - deal.amount) / deal.amount * 100
        
        # Calculate confidence if not provided
        if custom_confidence is None:
            confidence = self._calculate_match_score(order, deal, company_dict)
        else:
            confidence = custom_confidence
        
        # Determine attribution method
        if value_diff_percent <= 5.0 and days_diff <= 14:
            method = AttributionMethod.TEMPORAL_VALUE
        else:
            method = AttributionMethod.TEMPORAL_ONLY
        
        return Attribution(
            order_id=order.id,
            deal_id=deal.id,
            sales_rep_id=deal.sales_rep_id,
            sales_rep_name=deal.sales_rep_name,
            attribution_method=method,
            confidence_score=confidence,
            needs_review=confidence < self.config.CONFIDENCE_THRESHOLD_REVIEW,
            matching_metadata={
                "days_difference": days_diff,
                "value_difference_percent": round(value_diff_percent, 2),
                "order_amount": order.amount,
                "deal_amount": deal.amount,
                "candidates_count": 1,
                "company_match": order.company_id == deal.company_id
            }
        )
    
    def _create_self_service_attribution(
        self, 
        order: Order, 
        reason: str
    ) -> Attribution:
        """Create a self-service attribution"""
        return Attribution(
            order_id=order.id,
            deal_id=None,
            sales_rep_id=None,
            sales_rep_name=None,
            attribution_method=AttributionMethod.SELF_SERVICE,
            confidence_score=100.0,
            needs_review=False,
            matching_metadata={
                "reason": reason,
                "order_amount": order.amount
            }
        )
