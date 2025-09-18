import unittest
import os
import sys
from app import create_app, db
from app.models.entity import Entity

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class EntityTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["TESTING"] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def test_create_entity(self):
        entity = Entity(
            name="Google",
            ticker="GOOG",
            summary="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            sentiment_score=0.8,
        )
        db.session.add(entity)
        db.session.commit()

        self.assertEqual(entity.name, "Google")
        self.assertEqual(entity.ticker, "GOOG")
        self.assertEqual(
            entity.summary,
            "Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
        )
        self.assertEqual(entity.sentiment_score, 0.8)

    def test_read_entity(self):
        entity = Entity(
            name="Google",
            ticker="GOOG",
            summary="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            sentiment_score=0.8,
        )
        db.session.add(entity)
        db.session.commit()

        result = Entity.query.filter_by(name="Google").first()

        self.assertEqual(result.name, "Google")
        self.assertEqual(result.ticker, "GOOG")
        self.assertEqual(
            result.summary,
            "Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
        )
        self.assertEqual(result.sentiment_score, 0.8)

    def test_update_entity(self):
        entity = Entity(
            name="Google",
            ticker="GOOG",
            summary="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            sentiment_score=0.8,
        )
        db.session.add(entity)
        db.session.commit()

        entity.sentiment_score = 0.9
        db.session.commit()

        result = Entity.query.filter_by(name="Google").first()

        self.assertEqual(result.name, "Google")
        self.assertEqual(result.ticker, "GOOG")
        self.assertEqual(
            result.summary,
            "Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
        )
        self.assertEqual(result.sentiment_score, 0.9)

    def test_delete_entity(self):
        entity = Entity(
            name="Google",
            ticker="GOOG",
            summary="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            sentiment_score=0.8,
        )
        db.session.add(entity)
        db.session.commit()

        db.session.delete(entity)
        db.session.commit()

        result = Entity.query.filter_by(name="Google").first()

        self.assertIsNone(result)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
