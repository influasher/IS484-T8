import unittest
from types import SimpleNamespace

try:
    from app.services import entities_service as mod
except Exception:
    import entities_service as mod  # fallback


# ---------- Minimal SQLAlchemy-like stubs ----------

class _OrderSpec:
    def __init__(self, key_func, reverse=False):
        self.key_func = key_func
        self.reverse = reverse


class _Column:
    def __init__(self, name):
        self.name = name

    def __eq__(self, other):
        return lambda obj: getattr(obj, self.name) == other

    def __gt__(self, other):
        return lambda obj: (getattr(obj, self.name) or 0) > other

    def __ge__(self, other):
        return lambda obj: (getattr(obj, self.name) or 0) >= other

    def __lt__(self, other):
        return lambda obj: (getattr(obj, self.name) or 0) < other

    def __le__(self, other):
        return lambda obj: (getattr(obj, self.name) or 0) <= other

    def ilike(self, pattern):
        needle = (pattern or "").strip("%").lower()
        return lambda obj: needle in str(getattr(obj, self.name, "")).lower()

    def asc(self):
        return _OrderSpec(key_func=lambda it: getattr(it, self.name))

    def desc(self):
        return _OrderSpec(key_func=lambda it: getattr(it, self.name), reverse=True)


def _or_(*preds):
    preds = [p for p in preds if callable(p)]
    return (lambda obj: any(p(obj) for p in preds)) if preds else (lambda obj: True)


def _asc(col):
    return _OrderSpec(key_func=lambda it: getattr(it, col.name), reverse=False)


def _desc(col):
    return _OrderSpec(key_func=lambda it: getattr(it, col.name), reverse=True)


class _FuncStub:
    @staticmethod
    def lower(col):
        class _Lower:
            def asc(self_inner):
                return _OrderSpec(
                    key_func=lambda it: str(getattr(it, col.name, "")).lower(),
                    reverse=False,
                )

            def desc(self_inner):
                return _OrderSpec(
                    key_func=lambda it: str(getattr(it, col.name, "")).lower(),
                    reverse=True,
                )
        return _Lower()


class _Paginator:
    def __init__(self, items, page, per_page):
        total = len(items)
        pages = (total + per_page - 1) // per_page if per_page else 1
        start = (page - 1) * per_page
        end = start + per_page
        self.items = items[start:end]
        self.total = total
        self.pages = pages
        self.page = page
        self.next_num = page + 1 if page < pages else None
        self.prev_num = page - 1 if page > 1 else None


class _Query:
    def __init__(self, items):
        self._items = list(items)

    def filter(self, *conds):
        items = self._items
        for c in conds:
            if callable(c):
                items = [it for it in items if c(it)]
        return _Query(items)

    def order_by(self, order_spec):
        if isinstance(order_spec, _OrderSpec):
            items = sorted(self._items, key=order_spec.key_func, reverse=order_spec.reverse)
        else:
            items = self._items
        return _Query(items)

    def paginate(self, page=1, per_page=10, error_out=False):
        return _Paginator(self._items, page, per_page)

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


# ---------- DB & Entity stubs ----------

class _DBStub:
    class session:
        commits = 0

        @staticmethod
        def commit():
            _DBStub.session.commits += 1


class _EntityObj:
    id = _Column("id")
    name = _Column("name")
    ticker = _Column("ticker")
    summary = _Column("summary")
    classification = _Column("classification")
    sentiment_score = _Column("sentiment_score")
    finbert_score = _Column("finbert_score")
    gemini_score = _Column("gemini_score")
    open_ai_score = _Column("open_ai_score")
    confidence_score = _Column("confidence_score")
    time_decay = _Column("time_decay")
    simple_average = _Column("simple_average")

    _items = []

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ---------- Tests ----------

class EntityServicesTests(unittest.TestCase):
    def setUp(self):
        # keep originals
        self.orig_db = mod.db
        self.orig_Entity = mod.Entity
        self.orig_or = mod.or_
        self.orig_func = mod.func
        self.orig_asc = mod.asc
        self.orig_desc = mod.desc

        # patch
        mod.db = _DBStub
        mod.Entity = _EntityObj
        mod.or_ = _or_
        mod.func = _FuncStub
        mod.asc = _asc
        mod.desc = _desc

        # seed
        _EntityObj._items = [
            _EntityObj(
                id=1, name="Apple Inc", ticker="AAPL",
                summary="iPhone and cloud services", classification="Bullish",
                sentiment_score=75.5, finbert_score=0.8, gemini_score=0.78, open_ai_score=0.77,
                confidence_score=0.82, time_decay=72.0, simple_average=70.0
            ),
            _EntityObj(
                id=2, name="microsoft", ticker="MSFT",
                summary="Cloud leader Azure", classification="Positive",
                sentiment_score=65.0, finbert_score=0.7, gemini_score=0.66, open_ai_score=0.64,
                confidence_score=0.75, time_decay=64.0, simple_average=65.0
            ),
            _EntityObj(
                id=3, name="Zoom Video", ticker="ZM",
                summary="Video communications", classification="Neutral",
                sentiment_score=40.0, finbert_score=0.55, gemini_score=0.5, open_ai_score=0.52,
                confidence_score=0.6, time_decay=41.0, simple_average=44.0
            ),
            _EntityObj(
                id=4, name="beta corp", ticker="BETA",
                summary="Old economy", classification="Bearish",
                sentiment_score=15.0, finbert_score=0.4, gemini_score=0.38, open_ai_score=0.39,
                confidence_score=0.55, time_decay=20.0, simple_average=18.0
            ),
            _EntityObj(
                id=5, name="Tesla", ticker="TSLA",
                summary="EV leader", classification="Bullish",
                sentiment_score=85.0, finbert_score=0.9, gemini_score=0.88, open_ai_score=0.87,
                confidence_score=0.86, time_decay=83.0, simple_average=84.0
            ),
        ]

        # --- FIX: make Entity.query a proxy object that returns a fresh _Query ---
        def _make_query_proxy():
            return SimpleNamespace(
                filter=lambda *conds: _Query(_EntityObj._items).filter(*conds),
                order_by=lambda spec: _Query(_EntityObj._items).order_by(spec),
                paginate=lambda page=1, per_page=10, error_out=False:
                    _Query(_EntityObj._items).paginate(page, per_page, error_out),
                all=lambda: list(_EntityObj._items),
                first=lambda: _Query(_EntityObj._items).first(),
            )

        mod.Entity.query = _make_query_proxy()

        # also allow filter(...) from get_ticker_by_entity/get_id_by_entity to be chained first()
        # (already handled above via proxy.filter -> _Query)

    def tearDown(self):
        mod.db = self.orig_db
        mod.Entity = self.orig_Entity
        mod.or_ = self.orig_or
        mod.func = self.orig_func
        mod.asc = self.orig_asc
        mod.desc = self.orig_desc
        _EntityObj._items = []
        _DBStub.session.commits = 0

    # ---- simple lookups ----

    def test_get_ticker_by_entity_and_id(self):
        self.assertEqual(mod.get_ticker_by_entity("Apple Inc"), "AAPL")
        self.assertIsNone(mod.get_ticker_by_entity("NoSuch"))
        self.assertEqual(mod.get_id_by_entity("Tesla"), 5)
        self.assertIsNone(mod.get_id_by_entity("Missing"))

    def test_get_all_ticker_entities(self):
        out = mod.get_all_ticker_entities()
        self.assertEqual(len(out), 5)
        self.assertIn({"ticker": "TSLA", "name": "Tesla"}, out)

    # ---- get_all_entities: sorting ----

    def test_get_all_entities_name_asc(self):
        out = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc")
        names = [e["name"] for e in out["entities"]]
        self.assertEqual(names, ["Apple Inc", "beta corp", "microsoft", "Tesla", "Zoom Video"])

    def test_get_all_entities_name_desc(self):
        out = mod.get_all_entities(page=1, per_page=10, sort_order="name-desc")
        names = [e["name"] for e in out["entities"]]
        self.assertEqual(names[0], "Zoom Video")
        self.assertEqual(names[-1], "Apple Inc")

    def test_get_all_entities_sentiment_high_low(self):
        high = mod.get_all_entities(page=1, per_page=10, sort_order="sentiment-high")
        low = mod.get_all_entities(page=1, per_page=10, sort_order="sentiment-low")
        self.assertEqual(high["entities"][0]["ticker"], "TSLA")
        self.assertEqual(high["entities"][-1]["ticker"], "BETA")
        self.assertEqual(low["entities"][0]["ticker"], "BETA")
        self.assertEqual(low["entities"][-1]["ticker"], "TSLA")

    # ---- get_all_entities: search & numeric filter ----

    def test_get_all_entities_search_term_matches_name_ticker_summary_classification(self):
        out = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", search_term="cloud")
        tickers = [e["ticker"] for e in out["entities"]]
        self.assertIn("AAPL", tickers)
        self.assertIn("MSFT", tickers)

        out2 = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", search_term="tsl")
        self.assertEqual([e["ticker"] for e in out2["entities"]], ["TSLA"])

        out3 = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", search_term="bearish")
        self.assertEqual([e["ticker"] for e in out3["entities"]], ["BETA"])

    def test_get_all_entities_numeric_filters(self):
        gt = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", filter_operator=">", filter_value="70")
        self.assertEqual(sorted([e["ticker"] for e in gt["entities"]]), ["AAPL", "TSLA"])

        ge = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", filter_operator=">=", filter_value="75.5")
        self.assertEqual(sorted([e["ticker"] for e in ge["entities"]]), ["AAPL", "TSLA"])

        eq = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", filter_operator="=", filter_value="65")
        self.assertEqual([e["ticker"] for e in eq["entities"]], ["MSFT"])

        le = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", filter_operator="<=", filter_value="40")
        self.assertEqual(sorted([e["ticker"] for e in le["entities"]]), ["BETA", "ZM"])

        lt = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", filter_operator="<", filter_value="16")
        self.assertEqual([e["ticker"] for e in lt["entities"]], ["BETA"])

    def test_get_all_entities_invalid_filter_value_is_ignored(self):
        out = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc",
                                   filter_operator=">", filter_value="not-a-number")
        self.assertEqual(out["total"], 5)

    # ---- get_all_entities: pagination & empty ----

    def test_get_all_entities_pagination(self):
        p1 = mod.get_all_entities(page=1, per_page=2, sort_order="name-asc")
        p2 = mod.get_all_entities(page=2, per_page=2, sort_order="name-asc")
        p3 = mod.get_all_entities(page=3, per_page=2, sort_order="name-asc")
        self.assertEqual(p1["total"], 5)
        self.assertEqual(p1["pages"], 3)
        self.assertEqual(len(p1["entities"]), 2)
        self.assertEqual(len(p2["entities"]), 2)
        self.assertEqual(len(p3["entities"]), 1)

    def test_get_all_entities_returns_empty_when_no_matches(self):
        out = mod.get_all_entities(page=1, per_page=10, sort_order="name-asc", search_term="no-such-term")
        self.assertEqual(out, [])

    # ---- updates & details ----

    def test_update_entity_sentiment_success_and_failure(self):
        before = _DBStub.session.commits
        ok = mod.update_entity_sentiment(
            ticker="MSFT",
            sentiment_score=77.7,
            confidence_score=0.91,
            time_decay_score=76.0,
            simple_average_score=76.5,
            classification="Upgraded"
        )
        self.assertTrue(ok)
        self.assertEqual(_DBStub.session.commits, before + 1)

        msft = [e for e in _EntityObj._items if e.ticker == "MSFT"][0]
        self.assertEqual(msft.sentiment_score, 77.7)
        self.assertEqual(msft.classification, "Upgraded")

        before = _DBStub.session.commits
        fail = mod.update_entity_sentiment(
            ticker="NONE",
            sentiment_score=10,
            confidence_score=0.1,
            time_decay_score=10,
            simple_average_score=10,
            classification="Down"
        )
        self.assertFalse(fail)
        self.assertEqual(_DBStub.session.commits, before)

    def test_get_entity_details(self):
        d = mod.get_entity_details("AAPL")
        self.assertIsInstance(d, dict)
        self.assertEqual(d["ticker"], "AAPL")
        self.assertIn("avg_score", d)
        self.assertIn("classification", d)
        self.assertIsNone(mod.get_entity_details("MISSING"))


if __name__ == "__main__":
    unittest.main()
