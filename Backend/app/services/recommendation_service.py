from typing import List, Dict, Optional
from enum import Enum
from dataclasses import dataclass
from sqlalchemy import and_

from app.models.entity import Entity
from app.models.client_preferences import ClientPreferences
from app.models.client_portfolio import ClientPortfolio
from app.models.user import User
from app.services.portfolio_service import PortfolioCalculationService
from app.services.data_ingestion_yfinance import get_stock_price


# Configuration constants
EMERGENCY_FUND_PERCENT = 10.0  # Configurable emergency reserve percentage
CASH_UTILIZATION_PERCENT = 70.0  # Max percentage of available cash to invest
MINIMUM_POSITION_AMOUNT = 500.0  # Minimum viable position size
MAX_BUY_RECOMMENDATIONS = 3  # Limit buy recommendations for practicality


class RecommendationType(Enum):
    BUY_NEW = "BUY_NEW"
    BUY_ADD = "BUY_ADD"
    SELL_SENTIMENT = "SELL_SENTIMENT"
    SELL_REBALANCE = "SELL_REBALANCE"
    SELL_RISK = "SELL_RISK"


@dataclass
class Recommendation:
    entity_id: str
    entity_name: str
    ticker: str
    action: str
    recommendation_type: RecommendationType
    sentiment_score: float
    sentiment_confidence: float
    recommendation_confidence: float
    reasoning: str
    suggested_amount: Optional[float] = None
    suggested_allocation_percent: Optional[float] = None
    current_position_value: Optional[float] = None
    current_allocation_percent: Optional[float] = None
    current_price: Optional[float] = None
    risk_level: str = "MODERATE"


class EnhancedCashCalculator:
    """Handles sophisticated cash availability calculations"""

    @staticmethod
    def get_investable_cash(portfolio_service: PortfolioCalculationService, client_id: str) -> Dict:
        """Calculate true investable cash after reserves and constraints"""
        base_available_cash = portfolio_service.get_available_cash(client_id)

        emergency_reserve = base_available_cash * (EMERGENCY_FUND_PERCENT / 100)
        max_investable = base_available_cash * (CASH_UTILIZATION_PERCENT / 100)

        investable_cash = max(0, base_available_cash - emergency_reserve)
        practical_investable = min(investable_cash, max_investable)

        return {
            'total_available_cash': base_available_cash,
            'emergency_reserve': emergency_reserve,
            'investable_cash': practical_investable,
            'reserve_reasoning': f'Maintaining {EMERGENCY_FUND_PERCENT}% emergency fund',
            'utilization_limit': f'Using max {CASH_UTILIZATION_PERCENT}% of available cash'
        }


class PositionSizingOptimizer:
    """Handles practical position sizing logic"""

    @staticmethod
    def calculate_minimum_viable_position(portfolio_value: float) -> float:
        """Calculate minimum position size based on portfolio value"""
        portfolio_based_minimum = portfolio_value * 0.01  # 1% of portfolio
        return max(MINIMUM_POSITION_AMOUNT, portfolio_based_minimum)

    @staticmethod
    def round_to_practical_amount(amount: float) -> float:
        """Round amounts to practical trading increments"""
        if amount < 1000:
            return round(amount, -2)  # Round to nearest $100
        elif amount < 10000:
            return round(amount, -3)  # Round to nearest $1000
        else:
            return round(amount, -4)  # Round to nearest $10k

    @staticmethod
    def optimize_buy_recommendations(recommendations: List[Recommendation],
                                   investable_cash: float) -> List[Recommendation]:
        """Optimize buy recommendations for practical implementation"""
        buy_recs = [r for r in recommendations if r.action == 'BUY']
        buy_recs.sort(key=lambda x: x.recommendation_confidence, reverse=True)

        # Limit to top recommendations
        buy_recs = buy_recs[:MAX_BUY_RECOMMENDATIONS]

        # If we're using less than 50% of investable cash, scale up positions
        total_suggested = sum(r.suggested_amount for r in buy_recs if r.suggested_amount)

        if total_suggested < investable_cash * 0.5 and total_suggested > 0:
            scale_factor = min(2.0, (investable_cash * 0.5) / total_suggested)
            for rec in buy_recs:
                if rec.suggested_amount:
                    rec.suggested_amount *= scale_factor
                    rec.reasoning += f" (Scaled up {scale_factor:.1f}x for practical position size)"

        return buy_recs


class SectorConcentrationChecker:
    """Handles sector concentration risk assessment"""

    @staticmethod
    def check_sector_limits(entity: Entity,
                          current_sector_allocation: Dict,
                          preferences: ClientPreferences,
                          new_position_value: float,
                          total_portfolio_value: float) -> Dict:
        """Check if adding position would exceed sector limits"""

        if not entity.sector:
            return {'allowed': True, 'reason': 'No sector classification'}

        for sector in entity.sector:
            current_sector_percent = current_sector_allocation.get(sector, 0)
            new_allocation_impact = (new_position_value / total_portfolio_value) * 100
            projected_sector_percent = current_sector_percent + new_allocation_impact

            if projected_sector_percent > preferences.max_sector_allocation_percent:
                return {
                    'allowed': False,
                    'reason': f'{sector} would exceed limit: {projected_sector_percent:.1f}% > {preferences.max_sector_allocation_percent:.1f}%',
                    'current_allocation': current_sector_percent,
                    'projected_allocation': projected_sector_percent,
                    'limit': preferences.max_sector_allocation_percent
                }

        return {'allowed': True, 'reason': 'Within sector limits'}


class RecommendationEngine:
    """Enhanced recommendation engine with MVP improvements"""

    def __init__(self):
        self.portfolio_service = PortfolioCalculationService()
        self.cash_calculator = EnhancedCashCalculator()
        self.position_optimizer = PositionSizingOptimizer()
        self.sector_checker = SectorConcentrationChecker()

    def generate_recommendations(self, client_id: str, limit: int = 10) -> List[Recommendation]:
        """Generate comprehensive recommendations with MVP enhancements"""
        client = User.query.get(client_id)
        if not client or not client.is_client():
            return []

        preferences = ClientPreferences.query.filter_by(user_id=client.id).first()
        if not preferences:
            return []

        # Enhanced cash calculation
        portfolio_summary = self.portfolio_service.get_portfolio_summary(client_id)
        cash_info = self.cash_calculator.get_investable_cash(self.portfolio_service, client_id)
        sector_allocation = self.portfolio_service.get_sector_allocation(client_id)

        total_portfolio_value = max(portfolio_summary['total_portfolio_value'], cash_info['total_available_cash'])
        minimum_position = self.position_optimizer.calculate_minimum_viable_position(total_portfolio_value)

        entities = Entity.query.filter(
            and_(
                Entity.sentiment_score.isnot(None),
                Entity.classification.isnot(None)
            )
        ).all()

        recommendations = []

        # Generate buy recommendations
        for entity in entities:
            buy_rec = self._evaluate_buy_opportunity(
                entity, preferences, portfolio_summary, cash_info,
                sector_allocation, total_portfolio_value, minimum_position
            )
            if buy_rec:
                recommendations.append(buy_rec)

        # Generate sell recommendations
        current_positions = ClientPortfolio.query.filter_by(user_id=client_id).all()
        for position in current_positions:
            sell_rec = self._evaluate_sell_opportunity(position, preferences, portfolio_summary)
            if sell_rec:
                recommendations.append(sell_rec)

        # Optimize buy recommendations for practicality
        buy_recommendations = self.position_optimizer.optimize_buy_recommendations(
            [r for r in recommendations if r.action == 'BUY'],
            cash_info['investable_cash']
        )

        sell_recommendations = [r for r in recommendations if r.action == 'SELL']

        final_recommendations = buy_recommendations + sell_recommendations
        final_recommendations.sort(key=lambda x: x.recommendation_confidence, reverse=True)

        return final_recommendations[:limit]

    def _evaluate_buy_opportunity(self, entity: Entity, preferences: ClientPreferences,
                                portfolio_summary: Dict, cash_info: Dict,
                                sector_allocation: Dict, total_portfolio_value: float,
                                minimum_position: float) -> Optional[Recommendation]:

        if not self._passes_sentiment_filter(entity):
            return None

        if not self._passes_sector_filter(entity, preferences):
            return None

        # Calculate suggested position size
        suggested_allocation = self._calculate_position_size(
            entity, preferences, total_portfolio_value, cash_info['investable_cash']
        )

        # Apply minimum position logic
        if suggested_allocation['amount'] < minimum_position:
            return None

        # Check sector concentration limits
        sector_check = self.sector_checker.check_sector_limits(
            entity, sector_allocation, preferences,
            suggested_allocation['amount'], total_portfolio_value
        )

        if not sector_check['allowed']:
            return None

        # Round to practical amount
        practical_amount = self.position_optimizer.round_to_practical_amount(
            suggested_allocation['amount']
        )

        # Check for existing position
        existing_position = ClientPortfolio.query.filter_by(
            user_id=preferences.user_id, entity_id=entity.id
        ).first()

        rec_type = RecommendationType.BUY_ADD if existing_position else RecommendationType.BUY_NEW

        confidence = self._calculate_recommendation_confidence(entity, preferences, 0.3)

        try:
            price_data = get_stock_price(entity.ticker)
            current_price = price_data.get('current_price') if price_data else None
        except Exception:
            current_price = None

        reasoning = self._build_buy_reasoning(entity, sector_check, practical_amount, minimum_position)

        return Recommendation(
            entity_id=str(entity.id),
            entity_name=entity.name,
            ticker=entity.ticker,
            action="BUY",
            recommendation_type=rec_type,
            sentiment_score=entity.sentiment_score,
            sentiment_confidence=entity.confidence_score or 0.5,
            recommendation_confidence=confidence,
            reasoning=reasoning,
            suggested_amount=practical_amount,
            suggested_allocation_percent=(practical_amount / total_portfolio_value) * 100,
            current_price=current_price,
            risk_level=self._assess_risk_level(entity)
        )

    def _evaluate_sell_opportunity(self, position: ClientPortfolio,
                                 preferences: ClientPreferences,
                                 portfolio_summary: Dict) -> Optional[Recommendation]:

        if not position.entity:
            return None

        entity = position.entity
        total_portfolio_value = portfolio_summary['total_portfolio_value']
        current_allocation = (position.current_market_value / total_portfolio_value) * 100

        # Stop loss check
        if (position.unrealized_pnl_percent and
            position.unrealized_pnl_percent < -preferences.stop_loss_tolerance):
            return self._create_sell_recommendation(
                position, entity, RecommendationType.SELL_RISK,
                f"Stop loss triggered: {position.unrealized_pnl_percent:.1f}% loss exceeds {preferences.stop_loss_tolerance:.1f}% tolerance",
                position.current_market_value, 100.0
            )

        # Bearish sentiment check
        if entity.sentiment_score < -20 and entity.confidence_score > 0.6:
            sell_amount = position.current_market_value * 0.75
            return self._create_sell_recommendation(
                position, entity, RecommendationType.SELL_SENTIMENT,
                f"Bearish sentiment ({entity.sentiment_score:.1f}) with high confidence ({entity.confidence_score:.0%})",
                sell_amount, 75.0
            )

        # Overweight position check
        if current_allocation > preferences.max_single_position_percent:
            excess_allocation = current_allocation - preferences.max_single_position_percent
            sell_amount = (excess_allocation / 100) * total_portfolio_value
            sell_percent = (sell_amount / position.current_market_value) * 100

            return self._create_sell_recommendation(
                position, entity, RecommendationType.SELL_REBALANCE,
                f"Overweight position: {current_allocation:.1f}% exceeds {preferences.max_single_position_percent:.1f}% limit",
                sell_amount, sell_percent
            )

        return None

    def _calculate_position_size(self, entity: Entity, preferences: ClientPreferences,
                               total_portfolio_value: float, investable_cash: float) -> Dict:

        base_allocation_percent = {
            'Conservative': 3.0,
            'Moderate': 5.0,
            'Aggressive': 8.0
        }.get(preferences.risk_cap, 5.0)

        sentiment_multiplier = min(1.5, max(0.5, (entity.sentiment_score + 100) / 100))
        confidence_multiplier = entity.confidence_score or 0.7

        final_allocation_percent = min(
            base_allocation_percent * sentiment_multiplier * confidence_multiplier,
            preferences.max_single_position_percent
        )

        suggested_amount = min(
            total_portfolio_value * (final_allocation_percent / 100),
            investable_cash * 0.4,  # Don't use more than 40% of investable cash per position
            total_portfolio_value * 0.1  # Max 10% of portfolio in single position
        )

        return {
            'amount': suggested_amount,
            'percent': final_allocation_percent
        }

    def _build_buy_reasoning(self, entity: Entity, sector_check: Dict,
                           practical_amount: float, minimum_position: float) -> str:

        sentiment_desc = "bullish" if entity.sentiment_score > 0 else "bearish"
        confidence_desc = f"{entity.confidence_score:.0%}" if entity.confidence_score else "moderate"

        reasoning = f"Strong {sentiment_desc} sentiment ({entity.sentiment_score:.1f}) with {confidence_desc} confidence"

        if practical_amount >= minimum_position * 2:
            reasoning += f". Meaningful position size (${practical_amount:,.0f})"

        reasoning += f". {sector_check['reason']}"

        return reasoning

    def _create_sell_recommendation(self, position: ClientPortfolio, entity: Entity,
                                  rec_type: RecommendationType, reasoning: str,
                                  sell_amount: float, sell_percent: float) -> Recommendation:

        confidence = 0.8 if rec_type == RecommendationType.SELL_RISK else 0.7
        practical_sell_amount = self.position_optimizer.round_to_practical_amount(sell_amount)

        return Recommendation(
            entity_id=str(entity.id),
            entity_name=entity.name,
            ticker=entity.ticker,
            action="SELL",
            recommendation_type=rec_type,
            sentiment_score=entity.sentiment_score,
            sentiment_confidence=entity.confidence_score or 0.5,
            recommendation_confidence=confidence,
            reasoning=reasoning,
            suggested_amount=practical_sell_amount,
            current_position_value=position.current_market_value,
            current_allocation_percent=position.portfolio_allocation_percent,
            risk_level=self._assess_risk_level(entity)
        )

    def _calculate_recommendation_confidence(self, entity: Entity, preferences: ClientPreferences,
                                          diversification_benefit: float) -> float:

        sentiment_confidence = entity.confidence_score or 0.5
        sentiment_strength = min(1.0, abs(entity.sentiment_score) / 50)

        base_confidence = (
            sentiment_confidence * 0.5 +
            sentiment_strength * 0.3 +
            diversification_benefit * 0.2
        )

        return min(0.95, max(0.3, base_confidence))

    def _passes_sentiment_filter(self, entity: Entity) -> bool:
        return entity.sentiment_score > 15 and (entity.confidence_score or 0) > 0.4

    def _passes_sector_filter(self, entity: Entity, preferences: ClientPreferences) -> bool:
        if not preferences.sectors:
            return True
        entity_sectors = entity.sector or []
        return any(sector in preferences.sectors for sector in entity_sectors)

    def _assess_risk_level(self, entity: Entity) -> str:
        confidence = entity.confidence_score or 0.5
        sentiment_volatility = abs(entity.sentiment_score) / 100

        if confidence > 0.8 and sentiment_volatility < 0.3:
            return "LOW"
        elif confidence > 0.6 and sentiment_volatility < 0.6:
            return "MODERATE"
        else:
            return "HIGH"


def get_client_recommendations(client_id: str, limit: int = 10) -> List[Dict]:
    """Get recommendations for a client with enhanced MVP features"""
    engine = RecommendationEngine()
    recommendations = engine.generate_recommendations(client_id, limit)

    return [
        {
            'entity_id': rec.entity_id,
            'entity_name': rec.entity_name,
            'ticker': rec.ticker,
            'action': rec.action,
            'recommendation_type': rec.recommendation_type.value,
            'sentiment_score': rec.sentiment_score,
            'sentiment_confidence': rec.sentiment_confidence,
            'recommendation_confidence': rec.recommendation_confidence,
            'reasoning': rec.reasoning,
            'suggested_amount': rec.suggested_amount,
            'suggested_allocation_percent': rec.suggested_allocation_percent,
            'current_position_value': rec.current_position_value,
            'current_allocation_percent': rec.current_allocation_percent,
            'current_price': rec.current_price,
            'risk_level': rec.risk_level
        }
        for rec in recommendations
    ]