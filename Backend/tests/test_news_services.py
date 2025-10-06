import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace

try:
    from app.services import news_services as mod
except Exception:
    import news_services as mod  # fallback


# ---------- Minimal SQLAlchemy-like column/query stubs ----------

class _OrderSpec:
    def __init__(self, col, direction):
        self.col = col
        self.direction = direction  # 'asc' or 'desc'


class _Column:
    """Column stub that can produce predicates and order specs."""
    def __init__(self, name):
        self.name = name

    # Comparisons -> return predicate callables
    def __ge__(self, other):
        return lambda obj: getattr(obj, self.name) >= other

    # array helpers for entities list
    def any(self, val):
        return lambda obj: val in (getattr(obj, self.name, []) or [])

    def contains(self, arr):
        # arr expected to be a list (after cast)
        return lambda obj: all(x in (getattr(obj, self.name, []) or []) for x in arr)

    # text matching for title/summary/description
    def ilike(self, pattern):
        term = (pattern or "").strip("%").lower()
        return lambda obj: term in (str(getattr(obj, self.name, "")).lower())

    # ordering
    def asc(self): return _OrderSpec(self.name, "asc")
    def desc(self): return _OrderSpec(self.name, "desc")


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
        self._order = None

    # Accepts any number of predicate callables; ignores non-callables
    def filter(self, *conds, **k):
        items = self._items
        for c in conds:
            if callable(c):
                items = [it for it in items if c(it)]
        return _Query(items)

    def order_by(self, order_spec):
        if isinstance(order_spec, _OrderSpec):
            reverse = order_spec.direction == "desc"
            items = sorted(self._items, key=lambda it: getattr(it, order_spec.col), reverse=reverse)
        else:
            items = self._items
        return _Query(items)

    def paginate(self, page=1, per_page=10, error_out=False):
        return _Paginator(self._items, page, per_page)

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


# ---------- In-memory News model stub ----------

class _NewsObj:
    # Class-level column descriptors used by production code
    published_date = _Column("published_date")
    entities = _Column("entities")
    title = _Column("title")
    summary = _Column("summary")
    description = _Column("description")

    # Backing store
    _items = []

    def __init__(
        self, id, published_date=None, description="",
        publisher="Pub", summary="", title="", url="",
        entities=None, score=0.0, finbert_score=0.0, second_model_score=0.0,
        third_model_score=0.0, sentiment="Neutral", tags=None,
        confidence=0.0, agreement_rate=0.0, company_names=None,
        regions=None, sectors=None
    ):
        self.id = id
        self.published_date = published_date or datetime.now()
        self.description = description
        self.publisher = publisher
        self.summary = summary
        self.title = title
        self.url = url
        self.entities = entities or []
        self.score = score
        self.finbert_score = finbert_score
        self.second_model_score = second_model_score
        self.third_model_score = third_model_score
        self.sentiment = sentiment
        self.tags = tags or []
        self.confidence = confidence
        self.agreement_rate = agreement_rate
        self.company_names = company_names or []
        self.regions = regions or []
        self.sectors = sectors or []

    class query:
        @classmethod
        def filter(cls, *conds, **k):
            return _Query(_NewsObj._items).filter(*conds, **k)

        @classmethod
        def paginate(cls, page=1, per_page=10, error_out=False):
            return _Query(_NewsObj._items).paginate(page, per_page, error_out)

        @classmethod
        def all(cls):
            return list(_NewsObj._items)

        @classmethod
        def get(cls, nid):
            for it in _NewsObj._items:
                if it.id == nid:
                    return it
            return None


# ---------- Lightweight stubs for SQLA helpers used by all_news/news_by_name ----------

def _or_(*preds):
    # Combine predicate callables with OR; ignore non-callables
    preds = [p for p in preds if callable(p)]
    return (lambda obj: any(p(obj) for p in preds)) if preds else (lambda obj: True)

def _cast(val, _=None):
    return val

_ARRAY = object()
_VARCHAR = object()


# ---------- DB stub (track commits/rollbacks for sanity) ----------

class _DBStub:
    class session:
        commits = 0
        rollbacks = 0

        @staticmethod
        def commit():
            _DBStub.session.commits += 1

        @staticmethod
        def rollback():
            _DBStub.session.rollbacks += 1


# ---------- The Tests ----------

class NewsServicesTests(unittest.TestCase):
    def setUp(self):
        # Save originals
        self.orig_db = mod.db
        self.orig_News = mod.News
        self.orig_sleep = mod.time.sleep
        self.orig_or = getattr(mod, "or_", None)
        self.orig_any = getattr(mod, "any_", None)
        self.orig_cast = getattr(mod, "cast", None)
        self.orig_ARRAY = getattr(mod, "ARRAY", None)
        self.orig_VARCHAR = getattr(mod, "VARCHAR", None)
        self.orig_interpreter = getattr(mod, "news_interpreter", None)

        # Patch module symbols
        mod.db = _DBStub
        mod.News = _NewsObj
        mod.time.sleep = lambda *a, **k: None  # avoid delays
        mod.or_ = _or_
        mod.any_ = lambda col: None  # ignored by _or_ (we rely on title/summary/description ilike)
        mod.cast = _cast
        mod.ARRAY = _ARRAY
        mod.VARCHAR = _VARCHAR
        mod.news_interpreter = lambda text, limit: {
            "metadata": {"companies": ["ACME"], "regions": ["US"], "sectors": ["Tech"]}
        }

        # Seed in-memory data
        now = datetime.now()
        _NewsObj._items = [
            _NewsObj(
                id=1,
                published_date=now - timedelta(hours=3),
                description="Strong earnings, outlook raised.",
                publisher="Alpha",
                summary="Earnings beat",
                title="Apple earnings beat expectations",
                url="http://n/1",
                entities=["AAPL", "Apple Inc"],
                tags=["results", "earnings"],
            ),
            _NewsObj(
                id=2,
                published_date=now - timedelta(hours=30),
                description="New product line announced.",
                publisher="Beta",
                summary="Launch event",
                title="Apple unveils new device",
                url="http://n/2",
                entities=["AAPL"],
                tags=["launch"],
            ),
            _NewsObj(
                id=3,
                published_date=now - timedelta(days=8),
                description="Older news beyond 7d window",
                publisher="Gamma",
                summary="Old",
                title="Last week wrap",
                url="http://n/3",
                entities=["MSFT"],
                tags=["wrap"],
            ),
            _NewsObj(
                id=4,
                published_date=now - timedelta(hours=10),
                description="Macro slowdown fears",
                publisher="Delta",
                summary="Earnings softness",
                title="Sector earnings weakness",
                url="http://n/4",
                entities=["SPY"],
                tags=["macro", "earnings"],
            ),
        ]

        # Reset commit/rollback counters
        _DBStub.session.commits = 0
        _DBStub.session.rollbacks = 0

    def tearDown(self):
        # Restore originals
        mod.db = self.orig_db
        mod.News = self.orig_News
        mod.time.sleep = self.orig_sleep
        if self.orig_or is not None:
            mod.or_ = self.orig_or
        if self.orig_any is not None:
            mod.any_ = self.orig_any
        if self.orig_cast is not None:
            mod.cast = self.orig_cast
        if self.orig_ARRAY is not None:
            mod.ARRAY = self.orig_ARRAY
        if self.orig_VARCHAR is not None:
            mod.VARCHAR = self.orig_VARCHAR
        if self.orig_interpreter is not None:
            mod.news_interpreter = self.orig_interpreter
        _NewsObj._items = []

    # ---------- resync_news_data ----------

    def test_resync_news_data_updates_recent_only(self):
        out = mod.resync_news_data()
        # Only ids 1,2,4 are within last 48h
        self.assertEqual(out.get("total"), 3)
        self.assertEqual(out.get("updated"), 3)
        self.assertEqual(out.get("failed"), 0)
        self.assertGreaterEqual(_DBStub.session.commits, 3)
        # Check metadata applied
        for nid in (1, 2, 4):
            it = _NewsObj.query.get(nid)
            self.assertEqual(it.company_names, ["ACME"])
            self.assertEqual(it.regions, ["US"])
            self.assertEqual(it.sectors, ["Tech"])
        # Ensure old item untouched
        old = _NewsObj.query.get(3)
        self.assertEqual(old.company_names, [])

    # ---------- news_by_ticker ----------

    def test_news_by_ticker_filter_48h_sort_desc_pagination(self):
        out = mod.news_by_ticker("AAPL", page=1, per_page=1, sort_order="desc", filter_time="48")
        self.assertEqual(out["total"], 2)  # ids 1 and 2
        self.assertEqual(out["pages"], 2)
        self.assertEqual(out["current_page"], 1)
        # newest first -> id 1 on page 1
        self.assertEqual(out["news"][0]["id"], 1)

        # page 2 returns the older one
        out2 = mod.news_by_ticker("AAPL", page=2, per_page=1, sort_order="desc", filter_time="48")
        self.assertEqual(out2["news"][0]["id"], 2)

    def test_news_by_ticker_no_results_returns_empty_list(self):
        out = mod.news_by_ticker("TSLA", page=1, per_page=5, sort_order="desc", filter_time="all")
        self.assertEqual(out, [])

    # ---------- news_by_name (ARRAY contains + cast) ----------

    def test_news_by_name_contains_cast(self):
        # Only id 1 has "Apple Inc" in entities list
        out = mod.news_by_name("Apple Inc", page=1, per_page=5, sort_order="desc", filter_time="all")
        self.assertEqual(out["total"], 1)
        self.assertEqual(out["news"][0]["id"], 1)

    # ---------- news_by_id ----------

    def test_news_by_id_found_and_missing(self):
        one = mod.news_by_id(2)
        self.assertIsInstance(one, dict)
        self.assertEqual(one["id"], 2)
        missing = mod.news_by_id(999)
        self.assertIsNone(missing)

    # ---------- all_news (sorting, filtering, search_term) ----------

    def test_all_news_24h_and_sort_asc(self):
        out = mod.all_news(page=1, per_page=10, filter_time="24", sort_order="asc")
        # Within 24h -> ids 1 and 4
        self.assertEqual(out["total"], 2)
        self.assertEqual([n["id"] for n in out["news"]], [4, 1])  # asc by date (older first)

    def test_all_news_search_term_uses_ilike(self):
        # "earnings" appears in id 1 title/summary and id 4 tags/summary/title,
        # but our or_ stub only evaluates ilike against title/summary/description.
        out = mod.all_news(page=1, per_page=10, filter_time="all", sort_order="desc", search_term="earnings")
        ids = [n["id"] for n in out["news"]]
        # id 1 (title: "...earnings..."), id 4 (summary/title include 'earnings')
        self.assertIn(1, ids)
        self.assertIn(4, ids)
        self.assertNotIn(2, ids)  # no "earnings" in title/summary/description
        self.assertNotIn(3, ids)

    def test_all_news_pagination(self):
        out = mod.all_news(page=1, per_page=2, filter_time="all", sort_order="desc")
        self.assertEqual(out["pages"], 2)
        self.assertEqual(len(out["news"]), 2)
        out2 = mod.all_news(page=2, per_page=2, filter_time="all", sort_order="desc")
        self.assertEqual(len(out2["news"]), 2)


if __name__ == "__main__":
    unittest.main()
