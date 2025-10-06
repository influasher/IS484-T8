import unittest
import uuid
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace

try:
    from app.services import portfolio_service as mod
except Exception:
    import portfolio_service as mod  # fallback


class _DBStub:
    class session:
        @staticmethod
        def add(obj): pass
        @staticmethod
        def commit(): pass


class _Col:
    def in_(self, *a, **k): return self
    def isnot(self, *a, **k): return self
    def asc(self): return self
    def __eq__(self, other):  # allow == in filter expressions
        return True


class _TxnType:
    BUY = "BUY"
    SELL = "SELL"
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"


class _Txn:
    def __init__(self, client_uuid, type_, entity_id=None, dt=None, qty=0, amount=0.0, price=0.0):
        self.client_uuid = client_uuid
        self.type = type_
        self.entity_id = entity_id
        self.datetime = dt or datetime.now(timezone.utc)
        self.quantity = qty
        self.amount = amount
        self.price = price

    def get_total_value(self):
        if self.type in (_TxnType.BUY, _TxnType.SELL):
            return float(self.quantity or 0) * float(self.price or 0)
        return float(self.amount or 0)


class _Query:
    """Lightweight stand-in for SQLAlchemy Query supporting the methods we use."""
    def __init__(self, items):
        self._items = list(items)

    # Allow chained filter(...) and filter_by(...) without changing items unless we choose
    def filter(self, *a, **k):
        return self

    def filter_by(self, **k):
        items = self._items
        if "user_id" in k:
            items = [i for i in items if str(i.user_id) == str(k["user_id"])]
        if "entity_id" in k:
            items = [i for i in items if str(i.entity_id) == str(k["entity_id"])]
        return _Query(items)

    def order_by(self, *a, **k):
        return self

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


class _Entity:
    def __init__(self, id_, ticker, sector=None, confidence_score=0.7, sentiment_score=20):
        self.id = id_
        self.ticker = ticker
        self.sector = sector or ["Tech"]
        self.confidence_score = confidence_score
        self.sentiment_score = sentiment_score


class _CP:
    def __init__(self, user_id=None, entity_id=None, qty=0):
        self.user_id = user_id
        self.entity_id = entity_id
        self.qty = qty
        self.total_invested = 0.0
        self.first_purchase_date = None
        self.last_transaction_date = None
        self.average_cost_basis = None
        self.current_price = None
        self.current_market_value = None
        self.unrealized_pnl = None
        self.unrealized_pnl_percent = None
        self.portfolio_allocation_percent = None
        self.entity = None

    def calculate_current_values(self):
        if self.current_price and self.qty:
            self.current_market_value = float(self.qty) * float(self.current_price)
            if self.total_invested and self.total_invested > 0:
                self.unrealized_pnl = self.current_market_value - self.total_invested
                self.unrealized_pnl_percent = (self.unrealized_pnl / self.total_invested) * 100

    def calculate_portfolio_allocation(self, total):
        if self.current_market_value and total > 0:
            self.portfolio_allocation_percent = (self.current_market_value / total) * 100
            return self.portfolio_allocation_percent
        return 0.0

    def to_dict(self):
        return {"user_id": str(self.user_id), "entity_id": str(self.entity_id), "qty": self.qty}

    class query:
        items = []

        @classmethod
        def filter_by(cls, **kw):
            items = cls.items
            if "user_id" in kw:
                items = [i for i in items if str(i.user_id) == str(kw["user_id"])]
            if "entity_id" in kw:
                items = [i for i in items if str(i.entity_id) == str(kw["entity_id"])]
            return _Query(items)


class PortfolioServiceTests(unittest.TestCase):
    def setUp(self):
        self.orig = {
            "db": mod.db,
            "Transactions": mod.Transactions,
            "TransactionType": mod.TransactionType,
            "ClientPortfolio": mod.ClientPortfolio,
            "Entity": mod.Entity,
            "get_stock_price": mod.get_stock_price,
            "and_": getattr(mod, "and_", None),
        }
        # Patch module globals
        mod.db = _DBStub
        mod.TransactionType = _TxnType
        mod.ClientPortfolio = _CP
        # neutralize SQLAlchemy and_ in our stubbed expressions
        try:
            mod.and_ = lambda *clauses: True
        except Exception:
            pass
        self.entities = {}
        mod.Entity = SimpleNamespace(query=SimpleNamespace(get=lambda eid: self.entities.get(eid)))
        mod.get_stock_price = lambda t: 100.0  # deterministic price

    def tearDown(self):
        mod.db = self.orig["db"]
        mod.Transactions = self.orig["Transactions"]
        mod.TransactionType = self.orig["TransactionType"]
        mod.ClientPortfolio = self.orig["ClientPortfolio"]
        mod.Entity = self.orig["Entity"]
        mod.get_stock_price = self.orig["get_stock_price"]
        if self.orig["and_"] is not None:
            mod.and_ = self.orig["and_"]

    def _patch_txns(self, txns):
        class _TxnModel:
            # class-level, column-like attributes used in filters
            client_uuid = _Col()
            type = _Col()
            entity_id = _Col()
            datetime = _Col()
            # query fixture
            query = _Query(txns)
        mod.Transactions = _TxnModel

    def test_calculate_portfolio_from_transactions(self):
        uid = str(uuid.uuid4())
        eid = uuid.uuid4()
        self.entities[eid] = _Entity(eid, "AAA", ["Tech"])
        txns = [
            _Txn(uid, _TxnType.BUY, entity_id=eid,
                 dt=datetime.now(timezone.utc) - timedelta(days=2), qty=5, price=80.0),
            _Txn(uid, _TxnType.BUY, entity_id=eid,
                 dt=datetime.now(timezone.utc) - timedelta(days=1), qty=5, price=120.0),
            _Txn(uid, _TxnType.SELL, entity_id=eid,
                 dt=datetime.now(timezone.utc), qty=2, price=150.0),
        ]
        self._patch_txns(txns)
        svc = mod.PortfolioCalculationService()
        out = svc.calculate_portfolio_from_transactions(uid)
        self.assertEqual(out["user_id"], uid)
        self.assertGreater(out["total_portfolio_value"], 0)
        self.assertGreaterEqual(out["position_count"], 1)

    def test_get_available_cash(self):
        uid = str(uuid.uuid4())
        txns = [
            _Txn(uid, _TxnType.DEPOSIT, amount=10_000),
            _Txn(uid, _TxnType.WITHDRAWAL, amount=1_000),
        ]
        self._patch_txns(txns)
        svc = mod.PortfolioCalculationService()
        # Keep it deterministic: pretend there's 2k already invested
        svc.get_portfolio_summary = lambda _: {"total_invested": 2000.0, "total_portfolio_value": 0}
        cash = svc.get_available_cash(uid)
        self.assertEqual(cash, 7000.0)

    def test_get_sector_allocation(self):
        uid = str(uuid.uuid4())
        e1 = _Entity(uuid.uuid4(), "A", ["Tech"])
        e2 = _Entity(uuid.uuid4(), "B", ["Energy", "Energy"])
        p1 = _CP(uid, e1.id, 1); p1.current_market_value = 200.0; p1.entity = e1
        p2 = _CP(uid, e2.id, 1); p2.current_market_value = 300.0; p2.entity = e2
        _CP.query.items = [p1, p2]
        svc = mod.PortfolioCalculationService()
        alloc = svc.get_sector_allocation(uid)
        self.assertAlmostEqual(alloc.get("Tech", 0), 40.0, places=3)
        self.assertAlmostEqual(alloc.get("Energy", 0), 60.0, places=3)

    def test_refresh_portfolio_prices(self):
        uid = str(uuid.uuid4())
        e = _Entity(uuid.uuid4(), "Z", ["Tech"])
        p = _CP(uid, e.id, 2); p.entity = e
        _CP.query.items = [p]
        svc = mod.PortfolioCalculationService()
        out = svc.refresh_portfolio_prices(uid)
        self.assertEqual(out["positions_updated"], 1)
        self.assertEqual(out["total_positions"], 1)


if __name__ == "__main__":
    unittest.main()
