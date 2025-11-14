import uuid
import unittest
from dataclasses import dataclass
from typing import List, Dict
from unittest.mock import patch

# Import under either layout
try:
    from app.services import recommendation_service as svc
except Exception:
    import recommendation_service as svc  # noqa: F401, F403


# ----------------- Simple stubs for ORM-like querying -----------------

class _FakeQuery:
    def __init__(self, first=None, all_=None, get_=None):
        """
        first: value to return from .first()
        all_: list to return from .all()
        get_: a callable(id)->obj OR a dict {id: obj} OR a direct object
        """
        self._first = first
        self._all = all_ if all_ is not None else []
        self._get = get_

    def filter_by(self, **kw):
        return self

    def filter(self, *args, **kw):
        return self

    def first(self):
        return self._first

    def all(self):
        return self._all

    def get(self, _id):
        # Resolve to the underlying object/value
        if callable(self._get):
            return self._get(_id)
        if isinstance(self._get, dict):
            return self._get.get(_id)
        return self._get


# A column-like stub so expressions like Entity.sentiment_score.isnot(None) work
class _Col:
    def isnot(self, _):
        # Return a dummy SQLAlchemy-compatible object for filter expressions
        class DummyClause:
            def __bool__(self):
                return True
        return DummyClause()


# ----------------- Entities & Positions -----------------

@dataclass
class _Entity:
    id: uuid.UUID
    name: str
    ticker: str
    sentiment_score: float
    confidence_score: float
    classification: str = "EQUITY"
    sector: List[str] = None


@dataclass
class _Position:
    user_id: str
    entity: _Entity
    current_market_value: float
    portfolio_allocation_percent: float = 0.0
    unrealized_pnl_percent: float = 0.0


@dataclass
class _Prefs:
    user_id: str
    risk_cap: str = "Moderate"
    max_sector_allocation_percent: float = 40.0
    max_single_position_percent: float = 15.0
    stop_loss_tolerance: float = 12.0
    sectors: List[str] = None


# ----------------- Fake Portfolio service -----------------

class _PortfolioSvc:
    def __init__(self, total=100_000.0, cash=20_000.0, sectors=None):
        self._total = total
        self._cash = cash
        self._sectors = sectors or {"Tech": 10.0, "Energy": 5.0}

    def get_available_cash(self, client_id):
        return self._cash

    def get_portfolio_summary(self, client_id):
        return {"total_portfolio_value": self._total}

    def get_sector_allocation(self, client_id):
        return dict(self._sectors)


class RecommendationServiceHelperTests(unittest.TestCase):
    def test_cash_calculator(self):
        calc = svc.EnhancedCashCalculator()
        out = calc.get_investable_cash(_PortfolioSvc(), "cid")
        self.assertGreater(out["total_available_cash"], 0)
        self.assertIn("emergency_reserve", out)
        self.assertLessEqual(out["investable_cash"], out["total_available_cash"])

    def test_position_sizing_and_rounding(self):
        opt = svc.PositionSizingOptimizer()
        self.assertEqual(opt.round_to_practical_amount(840), 800)
        self.assertEqual(opt.round_to_practical_amount(4300), 4000)
        # Python round(26500, -4) -> 30000 (nearest 10k), not 20000
        self.assertEqual(opt.round_to_practical_amount(26500), 30000)
        self.assertEqual(opt.calculate_minimum_viable_position(30_000), 500.0)   # 1% is 300 -> min 500
        self.assertEqual(opt.calculate_minimum_viable_position(120_000), 1200.0)

        # scaling behavior when total < 50% investable cash
        r1 = svc.Recommendation(entity_id="e1", entity_name="A", ticker="A", action="BUY",
                                recommendation_type=svc.RecommendationType.BUY_NEW,
                                sentiment_score=25, sentiment_confidence=0.7,
                                recommendation_confidence=0.6, reasoning="x",
                                suggested_amount=500.0)
        r2 = svc.Recommendation(entity_id="e2", entity_name="B", ticker="B", action="BUY",
                                recommendation_type=svc.RecommendationType.BUY_NEW,
                                sentiment_score=30, sentiment_confidence=0.8,
                                recommendation_confidence=0.7, reasoning="y",
                                suggested_amount=600.0)
        scaled = svc.PositionSizingOptimizer.optimize_buy_recommendations([r1, r2], investable_cash=5000.0)
        # scaled up but capped by 2.0x
        self.assertGreaterEqual(scaled[0].suggested_amount, 500 * 1.5)
        self.assertGreaterEqual(scaled[1].suggested_amount, 600 * 1.5)

    def test_sector_concentration_checker(self):
        checker = svc.SectorConcentrationChecker()
        ent = _Entity(id=uuid.uuid4(), name="Acme", ticker="ACM", sentiment_score=30, confidence_score=0.8, sector=["Tech"])
        prefs = _Prefs(user_id="u1", max_sector_allocation_percent=20.0)
        ok = checker.check_sector_limits(ent, {"Tech": 5.0}, prefs, new_position_value=2000, total_portfolio_value=100_000)
        self.assertTrue(ok["allowed"])
        bad = checker.check_sector_limits(ent, {"Tech": 19.5}, prefs, new_position_value=2000, total_portfolio_value=100_000)
        self.assertFalse(bad["allowed"])

    def test_engine_internal_helpers(self):
        eng = svc.RecommendationEngine()
        # sentiment filter
        e1 = _Entity(id=uuid.uuid4(), name="X", ticker="X", sentiment_score=16, confidence_score=0.5)
        e2 = _Entity(id=uuid.uuid4(), name="Y", ticker="Y", sentiment_score=10, confidence_score=0.9)
        self.assertTrue(eng._passes_sentiment_filter(e1))
        self.assertFalse(eng._passes_sentiment_filter(e2))
        # risk
        e_low = _Entity(id=uuid.uuid4(), name="L", ticker="L", sentiment_score=5, confidence_score=0.9)
        self.assertEqual(eng._assess_risk_level(e_low), "LOW")
        e_high = _Entity(id=uuid.uuid4(), name="H", ticker="H", sentiment_score=90, confidence_score=0.3)
        self.assertEqual(eng._assess_risk_level(e_high), "HIGH")
        # confidence compute boundaries
        conf = eng._calculate_recommendation_confidence(e1, _Prefs(user_id="u1"), 0.3)
        self.assertGreaterEqual(conf, 0.3)
        self.assertLessEqual(conf, 0.95)


class RecommendationEndToEndTests(unittest.TestCase):
    def test_get_client_recommendations_buy_and_sell_flows(self):
        client_id = str(uuid.uuid4())

        # Client object with is_client()
        class _UserObj:
            def __init__(self, id_):
                self.id = id_
            def is_client(self):
                return True

        # Client present & is client
        class _UserCls:
            query = _FakeQuery(get_=lambda _id: _UserObj(_id))

        # Preferences present
        prefs = _Prefs(user_id=client_id, risk_cap="Moderate",
                       max_single_position_percent=20.0, sectors=["Tech", "Energy"])
        class _PrefsCls:
            query = _FakeQuery(first=prefs)

        # Entities to buy (pass filters)
        e_buy_ok = _Entity(id=uuid.uuid4(), name="Acme", ticker="ACM",
                           sentiment_score=35.0, confidence_score=0.7, sector=["Tech"])
        e_buy_no_conf = _Entity(id=uuid.uuid4(), name="Low", ticker="LOW",
                                sentiment_score=12.0, confidence_score=0.9, sector=["Energy"])  # filtered out by sentiment

        class _EntityCls:
            # Provide class-level "columns" compatible with .isnot(None)
            sentiment_score = _Col()
            classification = _Col()
            query = _FakeQuery(all_=[e_buy_ok, e_buy_no_conf])

        # Positions to sell:
        # 1) risk stop-loss
        pos_risk = _Position(user_id=client_id, entity=e_buy_ok,
                             current_market_value=10_000.0, unrealized_pnl_percent=-20.0)
        # 2) overweight rebalance
        e_sell = _Entity(id=uuid.uuid4(), name="Globex", ticker="GBX",
                         sentiment_score=5.0, confidence_score=0.5, sector=["Energy"])
        pos_over = _Position(user_id=client_id, entity=e_sell,
                             current_market_value=30_000.0, portfolio_allocation_percent=30.0)
        class _PortCls:
            query = _FakeQuery(all_=[pos_risk, pos_over])

        # Portfolio service + prices
        port = _PortfolioSvc(total=120_000.0, cash=30_000.0,
                             sectors={"Tech": 10.0, "Energy": 5.0})

        with patch.object(svc, "User", _UserCls), \
             patch.object(svc, "ClientPreferences", _PrefsCls), \
             patch.object(svc, "Entity", _EntityCls), \
             patch.object(svc, "ClientPortfolio", _PortCls), \
             patch.object(svc, "PortfolioCalculationService", return_value=port), \
             patch.object(svc, "get_stock_price", return_value=123.45), \
             patch.object(svc, "and_", lambda *clauses: True):
            out = svc.get_client_recommendations(client_id, limit=10)

        # Expect at least one BUY (Acme) and both SELLs (risk + rebalance)
        actions = {o["action"] for o in out}
        self.assertIn("BUY", actions)
        self.assertIn("SELL", actions)
        types = {o["recommendation_type"] for o in out}
        self.assertTrue({"SELL_RISK", "SELL_REBALANCE"}.issubset(types))
        # ensure suggested_amount is rounded to practical increments (ends with '00')
        for o in out:
            self.assertTrue(str(int(o["suggested_amount"])).endswith("00"))

    def test_no_client_or_no_prefs_yields_empty(self):
        cid = str(uuid.uuid4())

        # User missing entirely
        class _UserNone:
            query = _FakeQuery(get_=lambda _id: None)
        class _PrefsNone:
            query = _FakeQuery(first=None)
        class _EntityEmpty:
            sentiment_score = _Col()
            classification = _Col()
            query = _FakeQuery(all_=[])

        with patch.object(svc, "User", _UserNone), \
             patch.object(svc, "ClientPreferences", _PrefsNone), \
             patch.object(svc, "Entity", _EntityEmpty), \
             patch.object(svc, "and_", lambda *clauses: True):
            out1 = svc.get_client_recommendations(cid, limit=5)
            self.assertEqual(out1, [])

        # client present but prefs missing
        class _UserObj:
            def __init__(self, id_):
                self.id = id_
            def is_client(self):
                return True
        class _UserOK:
            query = _FakeQuery(get_=lambda _id: _UserObj(_id))

        with patch.object(svc, "User", _UserOK), \
             patch.object(svc, "ClientPreferences", _PrefsNone), \
             patch.object(svc, "Entity", _EntityEmpty), \
             patch.object(svc, "and_", lambda *clauses: True):
            out2 = svc.get_client_recommendations(cid, limit=5)
            self.assertEqual(out2, [])


if __name__ == "__main__":
    unittest.main()
