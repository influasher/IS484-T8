import unittest

try:
    from app.services import feedback_services as mod
except Exception:
    import feedback_services as mod  # fallback

class _DBStub:
    class session:
        added = []
        @staticmethod
        def add(obj): _DBStub.session.added.append(obj)
        @staticmethod
        def commit(): pass

class _FeedbackObj:
    def __init__(self, userID, newsID, data=None):
        self.userID = userID; self.newsID = newsID; self._data = data or {}
    def to_dict(self): return {"userID": self.userID, "newsID": self.newsID, **self._data}

class _QueryStub:
    def __init__(self, items): self._items = items
    def filter(self, *exprs): return self
    def filter_by(self, **kwargs):
        items = self._items
        for k, v in kwargs.items():
            items = [it for it in items if getattr(it, k, None) == v]
        return _QueryStub(items)
    def all(self): return list(self._items)
    def first(self): return self._items[0] if self._items else None

class _FeedbackStub:
    # Column-like attributes to satisfy service expressions (Feedback.userID == ...)
    userID = object()
    newsID = object()
    items = []
    class query:
        @staticmethod
        def filter(*exprs): return _QueryStub(_FeedbackStub.items)
        @staticmethod
        def filter_by(**kwargs): return _QueryStub(_FeedbackStub.items).filter_by(**kwargs)

class FeedbackServicesTests(unittest.TestCase):
    def setUp(self):
        self.orig_db = mod.db
        self.orig_FB = mod.Feedback
        mod.db = _DBStub
        mod.Feedback = _FeedbackStub
        _FeedbackStub.items = [
            _FeedbackObj("u1", "n1", {"r": 1}),
            _FeedbackObj("u1", "n2", {"r": 2}),
            _FeedbackObj("u2", "n1", {"r": 3}),
        ]

    def tearDown(self):
        mod.db = self.orig_db
        mod.Feedback = self.orig_FB
        _DBStub.session.added.clear()

    def test_getters(self):
        lst1 = mod.get_feedback_by_userID("u1")
        self.assertGreaterEqual(len(lst1), 2)
        lst2 = mod.get_feedback_by_newsID("n1")
        self.assertGreaterEqual(len(lst2), 2)
        one = mod.get_feedback_by_userID_and_newsID("u1", "n1")
        self.assertIsInstance(one, dict)

    def test_insert_feedback(self):
        fb = _FeedbackObj("u9", "n9", {"r": 5})
        mod.insert_feedback(fb)
        self.assertIn(fb, _DBStub.session.added)

if __name__ == "__main__":
    unittest.main()
