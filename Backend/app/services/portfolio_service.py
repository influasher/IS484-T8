from typing import Dict, List, Optional
from sqlalchemy import func, and_
from app import db
from app.models.transactions import Transactions, TransactionType
from app.models.client_portfolio import ClientPortfolio
from app.models.client_preferences import ClientPreferences
from app.models.entity import Entity
from app.models.user import User
from app.services.data_ingestion_yfinance import get_stock_price


class PortfolioCalculationService:
    """Service for calculating portfolio metrics from transaction data"""

    def calculate_portfolio_from_transactions(self, user_id: str) -> Dict:
        """
        Calculate complete portfolio from transaction history
        Returns portfolio summary and updates ClientPortfolio records
        """
        transactions = self._get_stock_transactions(user_id)
        portfolio_positions = self._aggregate_positions(transactions)

        total_portfolio_value = 0
        updated_positions = []

        for entity_id, position_data in portfolio_positions.items():
            portfolio_record = self._update_portfolio_record(
                user_id, entity_id, position_data
            )
            if portfolio_record and portfolio_record.current_market_value:
                total_portfolio_value += portfolio_record.current_market_value
                updated_positions.append(portfolio_record)

        # Update allocation percentages
        for position in updated_positions:
            position.calculate_portfolio_allocation(total_portfolio_value)

        db.session.commit()

        return {
            'user_id': user_id,
            'total_portfolio_value': total_portfolio_value,
            'position_count': len(updated_positions),
            'positions': [pos.to_dict() for pos in updated_positions]
        }

    def _get_stock_transactions(self, user_id: str) -> List[Transactions]:
        """Get all stock buy/sell transactions for a user"""
        return Transactions.query.filter(
            and_(
                Transactions.client_uuid == user_id,
                Transactions.type.in_([TransactionType.BUY, TransactionType.SELL]),
                Transactions.entity_id.isnot(None)
            )
        ).order_by(Transactions.datetime.asc()).all()

    def _aggregate_positions(self, transactions: List[Transactions]) -> Dict:
        """Aggregate transactions into current positions"""
        positions = {}

        for txn in transactions:
            entity_id = str(txn.entity_id)

            if entity_id not in positions:
                positions[entity_id] = {
                    'total_quantity': 0,
                    'total_cost': 0,
                    'transactions': [],
                    'first_purchase_date': None,
                    'last_transaction_date': None
                }

            pos = positions[entity_id]
            pos['transactions'].append(txn)
            pos['last_transaction_date'] = txn.datetime

            if txn.type == TransactionType.BUY:
                pos['total_quantity'] += txn.quantity or 0
                pos['total_cost'] += txn.get_total_value()
                if not pos['first_purchase_date']:
                    pos['first_purchase_date'] = txn.datetime

            elif txn.type == TransactionType.SELL:
                sell_quantity = txn.quantity or 0
                if pos['total_quantity'] > 0:
                    # Calculate proportional cost reduction
                    cost_per_share = pos['total_cost'] / pos['total_quantity']
                    pos['total_cost'] -= cost_per_share * sell_quantity

                pos['total_quantity'] -= sell_quantity

        # Filter out positions with zero or negative quantity
        return {k: v for k, v in positions.items() if v['total_quantity'] > 0}

    def _update_portfolio_record(self, user_id: str, entity_id: str, position_data: Dict) -> Optional[ClientPortfolio]:
        """Update or create ClientPortfolio record"""
        portfolio = ClientPortfolio.query.filter_by(
            user_id=user_id, entity_id=entity_id
        ).first()

        if not portfolio:
            portfolio = ClientPortfolio(
                user_id=user_id,
                entity_id=entity_id,
                qty=0
            )
            db.session.add(portfolio)

        # Update calculated fields
        portfolio.qty = int(position_data['total_quantity'])
        portfolio.total_invested = position_data['total_cost']
        portfolio.first_purchase_date = position_data['first_purchase_date']
        portfolio.last_transaction_date = position_data['last_transaction_date']

        if portfolio.total_invested and portfolio.qty > 0:
            portfolio.average_cost_basis = portfolio.total_invested / portfolio.qty

        # Get current market price
        entity = Entity.query.get(entity_id)
        if entity and entity.ticker:
            try:
                price_data = get_stock_price(entity.ticker)
                if price_data:
                    portfolio.current_price = price_data.get('current_price')
                    portfolio.calculate_current_values()
            except Exception:
                pass  # Handle price fetch failures gracefully

        return portfolio

    def get_portfolio_summary(self, user_id: str) -> Dict:
        """Get current portfolio summary without recalculating"""
        portfolio_positions = ClientPortfolio.query.filter_by(user_id=user_id).all()

        total_value = sum(pos.current_market_value or 0 for pos in portfolio_positions)
        total_invested = sum(pos.total_invested or 0 for pos in portfolio_positions)
        total_pnl = sum(pos.unrealized_pnl or 0 for pos in portfolio_positions)

        return {
            'user_id': user_id,
            'total_portfolio_value': total_value,
            'total_invested': total_invested,
            'total_unrealized_pnl': total_pnl,
            'total_unrealized_pnl_percent': (total_pnl / total_invested * 100) if total_invested > 0 else 0,
            'position_count': len(portfolio_positions),
            'positions': [pos.to_dict() for pos in portfolio_positions]
        }

    def get_available_cash(self, user_id: str) -> float:
        """Calculate available cash from deposit/withdrawal transactions"""
        cash_transactions = Transactions.query.filter(
            and_(
                Transactions.client_uuid == user_id,
                Transactions.type.in_([TransactionType.DEPOSIT, TransactionType.WITHDRAWAL])
            )
        ).all()

        total_deposits = sum(
            float(txn.amount) for txn in cash_transactions
            if txn.type == TransactionType.DEPOSIT
        )
        total_withdrawals = sum(
            float(txn.amount) for txn in cash_transactions
            if txn.type == TransactionType.WITHDRAWAL
        )

        portfolio_summary = self.get_portfolio_summary(user_id)
        total_invested = portfolio_summary['total_invested']

        return total_deposits - total_withdrawals - total_invested

    def get_sector_allocation(self, user_id: str) -> Dict:
        """Calculate portfolio allocation by sector"""
        portfolio_positions = ClientPortfolio.query.filter_by(user_id=user_id).all()
        sector_allocation = {}
        total_value = 0

        for position in portfolio_positions:
            if position.current_market_value and position.entity:
                entity_sectors = position.entity.sector or []
                position_value = position.current_market_value
                total_value += position_value

                # If entity has multiple sectors, split allocation
                sectors_count = len(entity_sectors) if entity_sectors else 1
                value_per_sector = position_value / sectors_count

                if entity_sectors:
                    for sector in entity_sectors:
                        sector_allocation[sector] = sector_allocation.get(sector, 0) + value_per_sector
                else:
                    sector_allocation['Other'] = sector_allocation.get('Other', 0) + position_value

        # Convert to percentages
        if total_value > 0:
            sector_allocation = {
                sector: (value / total_value) * 100
                for sector, value in sector_allocation.items()
            }

        return sector_allocation

    def refresh_portfolio_prices(self, user_id: str) -> Dict:
        """Refresh current market prices for all positions"""
        portfolio_positions = ClientPortfolio.query.filter_by(user_id=user_id).all()
        updated_count = 0

        for position in portfolio_positions:
            if position.entity and position.entity.ticker:
                try:
                    price_data = get_stock_price(position.entity.ticker)
                    if price_data:
                        position.current_price = price_data.get('current_price')
                        position.calculate_current_values()
                        updated_count += 1
                except Exception:
                    continue

        db.session.commit()

        return {
            'user_id': user_id,
            'positions_updated': updated_count,
            'total_positions': len(portfolio_positions)
        }


# Convenience functions
def calculate_client_portfolio(user_id: str) -> Dict:
    """Calculate portfolio for a client"""
    service = PortfolioCalculationService()
    return service.calculate_portfolio_from_transactions(user_id)

def get_client_portfolio_summary(user_id: str) -> Dict:
    """Get portfolio summary for a client"""
    service = PortfolioCalculationService()
    return service.get_portfolio_summary(user_id)

def get_client_available_cash(user_id: str) -> float:
    """Get available cash for a client"""
    service = PortfolioCalculationService()
    return service.get_available_cash(user_id)


class PortfolioHealthAssessment:
    """Service for assessing portfolio health relative to client preferences"""

    def __init__(self):
        self.portfolio_service = PortfolioCalculationService()

    def get_portfolio_health(self, user_id: str) -> Dict:
        """Assess portfolio health relative to client preferences"""
        from app.models.client_preferences import ClientPreferences

        preferences = ClientPreferences.query.filter_by(user_id=user_id).first()
        if not preferences:
            return {'error': 'Client preferences not found'}

        portfolio_summary = self.portfolio_service.get_portfolio_summary(user_id)
        sector_allocation = self.portfolio_service.get_sector_allocation(user_id)
        cash_info = self._get_cash_analysis(user_id, preferences)
        position_analysis = self._analyze_position_sizes(user_id, preferences)
        risk_analysis = self._analyze_risk_exposure(user_id, preferences, portfolio_summary)

        overall_score = self._calculate_health_score(
            cash_info, position_analysis, risk_analysis, sector_allocation, preferences
        )

        return {
            'user_id': user_id,
            'overall_health_score': overall_score,
            'cash_analysis': cash_info,
            'position_analysis': position_analysis,
            'risk_analysis': risk_analysis,
            'sector_analysis': self._analyze_sector_concentration(sector_allocation, preferences),
            'recommendations': self._generate_health_recommendations(
                cash_info, position_analysis, risk_analysis, sector_allocation, preferences
            )
        }

    def _get_cash_analysis(self, user_id: str, preferences: ClientPreferences) -> Dict:
        """Analyze cash position relative to preferences"""
        available_cash = self.portfolio_service.get_available_cash(user_id)
        portfolio_summary = self.portfolio_service.get_portfolio_summary(user_id)
        total_value = portfolio_summary['total_portfolio_value'] + available_cash

        cash_percent = (available_cash / total_value * 100) if total_value > 0 else 0
        min_cash_required = preferences.min_cash_reserve_percent or 10.0

        return {
            'available_cash': available_cash,
            'cash_percent': cash_percent,
            'min_required_percent': min_cash_required,
            'surplus_deficit': cash_percent - min_cash_required,
            'status': 'healthy' if cash_percent >= min_cash_required else 'low_cash'
        }

    def _analyze_position_sizes(self, user_id: str, preferences: ClientPreferences) -> Dict:
        """Analyze individual position sizes relative to limits"""
        from app.models.client_portfolio import ClientPortfolio

        positions = ClientPortfolio.query.filter_by(user_id=user_id).all()
        max_single_position = preferences.max_single_position_percent or 15.0

        oversized_positions = []
        total_positions = len(positions)

        for position in positions:
            if position.portfolio_allocation_percent and position.portfolio_allocation_percent > max_single_position:
                oversized_positions.append({
                    'entity_name': position.entity.name if position.entity else 'Unknown',
                    'current_allocation': position.portfolio_allocation_percent,
                    'limit': max_single_position,
                    'excess': position.portfolio_allocation_percent - max_single_position
                })

        return {
            'total_positions': total_positions,
            'oversized_count': len(oversized_positions),
            'oversized_positions': oversized_positions,
            'max_position_limit': max_single_position,
            'status': 'healthy' if len(oversized_positions) == 0 else 'oversized_positions'
        }

    def _analyze_risk_exposure(self, user_id: str, preferences: ClientPreferences, portfolio_summary: Dict) -> Dict:
        """Analyze overall risk exposure"""
        from app.models.client_portfolio import ClientPortfolio

        positions = ClientPortfolio.query.filter_by(user_id=user_id).all()
        total_unrealized_pnl_percent = portfolio_summary.get('total_unrealized_pnl_percent', 0)
        stop_loss_tolerance = preferences.stop_loss_tolerance or -10.0

        positions_at_risk = []
        for position in positions:
            if (position.unrealized_pnl_percent and
                position.unrealized_pnl_percent < stop_loss_tolerance):
                positions_at_risk.append({
                    'entity_name': position.entity.name if position.entity else 'Unknown',
                    'unrealized_pnl_percent': position.unrealized_pnl_percent,
                    'stop_loss_tolerance': stop_loss_tolerance
                })

        return {
            'total_unrealized_pnl_percent': total_unrealized_pnl_percent,
            'stop_loss_tolerance': stop_loss_tolerance,
            'positions_at_risk': positions_at_risk,
            'risk_status': 'high' if len(positions_at_risk) > 0 else 'acceptable'
        }

    def _analyze_sector_concentration(self, sector_allocation: Dict, preferences: ClientPreferences) -> Dict:
        """Analyze sector concentration relative to limits"""
        max_sector_allocation = preferences.max_sector_allocation_percent or 40.0

        overconcentrated_sectors = []
        for sector, allocation_percent in sector_allocation.items():
            if allocation_percent > max_sector_allocation:
                overconcentrated_sectors.append({
                    'sector': sector,
                    'current_allocation': allocation_percent,
                    'limit': max_sector_allocation,
                    'excess': allocation_percent - max_sector_allocation
                })

        return {
            'sector_allocation': sector_allocation,
            'max_sector_limit': max_sector_allocation,
            'overconcentrated_sectors': overconcentrated_sectors,
            'status': 'healthy' if len(overconcentrated_sectors) == 0 else 'overconcentrated'
        }

    def _calculate_health_score(self, cash_info: Dict, position_analysis: Dict,
                              risk_analysis: Dict, sector_allocation: Dict,
                              preferences: ClientPreferences) -> float:
        """Calculate overall portfolio health score (0-100)"""
        score = 100.0

        # Cash position scoring (20% weight)
        if cash_info['status'] == 'low_cash':
            score -= min(20, abs(cash_info['surplus_deficit']) * 2)

        # Position size scoring (30% weight)
        if position_analysis['oversized_count'] > 0:
            penalty = min(30, position_analysis['oversized_count'] * 10)
            score -= penalty

        # Risk exposure scoring (30% weight)
        if risk_analysis['risk_status'] == 'high':
            penalty = min(30, len(risk_analysis['positions_at_risk']) * 15)
            score -= penalty

        # Sector concentration scoring (20% weight)
        sector_analysis = self._analyze_sector_concentration(sector_allocation, preferences)
        if sector_analysis['status'] == 'overconcentrated':
            penalty = min(20, len(sector_analysis['overconcentrated_sectors']) * 10)
            score -= penalty

        return max(0, score)

    def _generate_health_recommendations(self, cash_info: Dict, position_analysis: Dict,
                                       risk_analysis: Dict, sector_allocation: Dict,
                                       preferences: ClientPreferences) -> List[str]:
        """Generate actionable health recommendations"""
        recommendations = []

        if cash_info['status'] == 'low_cash':
            recommendations.append(f"Increase cash reserves to {cash_info['min_required_percent']:.1f}% (currently {cash_info['cash_percent']:.1f}%)")

        if position_analysis['oversized_count'] > 0:
            for pos in position_analysis['oversized_positions']:
                recommendations.append(f"Reduce {pos['entity_name']} position by {pos['excess']:.1f}% to meet size limits")

        if risk_analysis['risk_status'] == 'high':
            for pos in risk_analysis['positions_at_risk']:
                recommendations.append(f"Consider stop-loss for {pos['entity_name']} (currently {pos['unrealized_pnl_percent']:.1f}% loss)")

        sector_analysis = self._analyze_sector_concentration(sector_allocation, preferences)
        if sector_analysis['status'] == 'overconcentrated':
            for sector in sector_analysis['overconcentrated_sectors']:
                recommendations.append(f"Reduce {sector['sector']} allocation by {sector['excess']:.1f}% to meet sector limits")

        if not recommendations:
            recommendations.append("Portfolio health is good - all metrics within acceptable ranges")

        return recommendations


def get_client_portfolio_health(user_id: str) -> Dict:
    """Get portfolio health assessment for a client"""
    service = PortfolioHealthAssessment()
    return service.get_portfolio_health(user_id)