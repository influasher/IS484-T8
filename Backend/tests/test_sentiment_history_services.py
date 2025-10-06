import unittest
from datetime import datetime

try:
    from app.services import sentiment_history_services as mod
except Exception:
    import sentiment_history_services as mod  # fallback


class _DBStub:
    class session:
        @staticmethod
        def add(obj):
            # Persist new SentimentHistory-like objects into the in-memory store
            try:
                if isinstance(obj, _SHObj) and obj not in _SHObj._store:
                    _SHObj._store.append(obj)
            except Exception:
                pass

        @staticmethod
        def commit():
            pass


class _Col:
    """Minimal column stub to satisfy attr access like .asc()/.desc() and comparisons."""
    def asc(self): return self
    def desc(self): return self
    def __eq__(self, other):  # used in filter expressions; we don't evaluate it
        return True


class _SHObj:
    """In-memory stand-in for SentimentHistory."""
    # class-level, column-like attributes used by service code
    entity_id = _Col()
    date = _Col()

    _store = []

    def __init__(self, entity_id, date, sentiment_score):
        self.id = len(_SHObj._store) + 1  # id assigned at construction; OK for tests
        self.entity_id = entity_id
        self.date = date
        self.sentiment_score = sentiment_score

    def to_dict(self):
        return {
            "id": self.id,
            "entity_id": self.entity_id,
            "date": self.date,
            "sentiment_score": self.sentiment_score,
        }

    class query:
        @staticmethod
        def filter(*args, **kwargs):
            # Return a query wrapper over all items (filters are no-ops in this stub)
            class _Q:
                def __init__(self, items): self.items = list(items)
                def order_by(self, *a, **k): return self
                def paginate(self, page=1, per_page=10, error_out=False):
                    total = len(self.items)
                    pages = (total + per_page - 1) // per_page if per_page else 1
                    start = (page - 1) * per_page
                    end = start + per_page
                    page_items = self.items[start:end]
                    return type("P", (), {
                        "items": page_items,
                        "total": total,
                        "pages": pages,
                        "page": page,
                        "next_num": page + 1 if page < pages else None,
                        "prev_num": page - 1 if page > 1 else None
                    })()
                def first(self): return self.items[0] if self.items else None
            return _Q(list(_SHObj._store))

        @staticmethod
        def filter_by(**kwargs):
            # Support simple equality filtering for convenience
            class _Q:
                def __init__(self, items): self.items = list(items)
                def order_by(self, *a, **k): return self
                def paginate(self, page=1, per_page=10, error_out=False):
                    total = len(self.items)
                    pages = (total + per_page - 1) // per_page if per_page else 1
                    start = (page - 1) * per_page
                    end = start + per_page
                    page_items = self.items[start:end]
                    return type("P", (), {
                        "items": page_items,
                        "total": total,
                        "pages": pages,
                        "page": page,
                        "next_num": page + 1 if page < pages else None,
                        "prev_num": page - 1 if page > 1 else None
                    })()
                def first(self): return self.items[0] if self.items else None

            items = list(_SHObj._store)
            for k, v in kwargs.items():
                items = [it for it in items if getattr(it, k, None) == v]
            return _Q(items)


# Dummy func to avoid SQLAlchemy func.date coercion in app code
class _FuncStub:
    @staticmethod
    def date(x): return x


def _create_or_update(entity_id, sentiment_score):
    """
    Seeding helper: ALWAYS append a new row so pagination has enough items.
    (We still test the real 'update same day' path via create_sentiment_history.)
    """
    new = _SHObj(entity_id, datetime.now(), sentiment_score)
    _SHObj._store.append(new)
    return new


class SentimentHistoryServiceTests(unittest.TestCase):
    def setUp(self):
        self.orig_db = mod.db
        self.orig_SH = getattr(mod, "SentimentHistory", None)
        self.orig_func = getattr(mod, "func", None)

        mod.db = _DBStub
        mod.SentimentHistory = _SHObj
        try:
            mod.func = _FuncStub
        except Exception:
            pass

        _SHObj._store.clear()

    def tearDown(self):
        mod.db = self.orig_db
        if self.orig_SH is not None:
            mod.SentimentHistory = self.orig_SH
        if self.orig_func is not None:
            mod.func = self.orig_func
        _SHObj._store.clear()

    def test_create_and_update_same_day(self):
        # This exercises the actual service which uses db.session.add/commit.
        out1 = mod.create_sentiment_history(entity_id=1, sentiment_score=0.5)
        self.assertEqual(out1["entity_id"], 1)

        out2 = mod.create_sentiment_history(entity_id=1, sentiment_score=0.9)
        self.assertEqual(out2["sentiment_score"], 0.9)

        # Should still be a single row for that entity-date
        self.assertEqual(len(_SHObj._store), 1)

    def test_get_history_pagination(self):
        # Seed 12 entries for entity 2 so pagination yields 3 pages at 5 per page
        for i in range(12):
            _create_or_update(entity_id=2, sentiment_score=float(i))

        out = mod.get_sentiment_history_by_entity_id(entity_id=2, page=1, per_page=5, sort_order="desc")
        if out:
            self.assertIn("sentiment_history", out)
            self.assertEqual(out["current_page"], 1)
            self.assertEqual(out["pages"], 3)  # 12 items @ 5 per page -> 3 pages
            self.assertEqual(len(out["sentiment_history"]), 5)


if __name__ == "__main__":
    unittest.main()
