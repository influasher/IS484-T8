import unittest
import os
import sys
from app.models.news import News
from app import create_app, db

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class NewsTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["TESTING"] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def test_create_news(self):
        news = News(
            title="Google News",
            description="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            url="https://www.google.com",
            sentiment="Positive",
            publisher="google",
            published_date="2021-09-01",
            entities=["Google", "Alphabet"],
            summary="Google is a technology company.",
            score=0.5,
        )
        db.session.add(news)
        db.session.commit()

        self.assertEqual(news.title, "Google News")
        self.assertEqual(
            news.description,
            "Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
        )
        self.assertEqual(news.url, "https://www.google.com")
        self.assertEqual(news.sentiment, "Positive")
        self.assertEqual(news.publisher, "google")
        self.assertEqual(news.published_date, "2021-09-01")
        self.assertEqual(news.entities, ["Google", "Alphabet"])
        self.assertEqual(news.summary, "Google is a technology company.")
        self.assertEqual(news.score, 0.5)
        self.assertEqual(news.sentiment, "Positive")

    def test_read_news(self):
        news = News(
            title="Google News",
            description="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            url="https://www.google.com",
            sentiment="Positive",
            publisher="google",
            published_date="2021-09-01",
            entities=["Google", "Alphabet"],
            summary="Google is a technology company.",
            score=0.5,
        )
        db.session.add(news)
        db.session.commit()

        result = News.query.filter_by(title="Google News").first()

        self.assertEqual(result.title, "Google News")
        self.assertEqual(
            result.description,
            "Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
        )
        self.assertEqual(result.url, "https://www.google.com")
        self.assertEqual(result.sentiment, "Positive")
        self.assertEqual(result.publisher, "google")
        self.assertEqual(result.published_date, "2021-09-01")
        self.assertEqual(result.entities, ["Google", "Alphabet"])
        self.assertEqual(result.summary, "Google is a technology company.")
        self.assertEqual(result.score, 0.5)

    def test_update_news(self):
        news = News(
            title="Google News",
            description="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            url="https://www.google.com",
            sentiment="Positive",
            publisher="google",
            published_date="2021-09-01",
            entities=["Google", "Alphabet"],
            summary="Google is a technology company.",
        )
        db.session.add(news)
        db.session.commit()

        news.sentiment = "bad"
        db.session.commit()

        result = News.query.filter_by(title="Google News").first()

        self.assertEqual(result.title, "Google News")
        self.assertEqual(
            result.description,
            "Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
        )
        self.assertEqual(result.url, "https://www.google.com")
        self.assertEqual(result.sentiment, "Positive")
        self.assertEqual(result.publisher, "google")
        self.assertEqual(result.published_date, "2021-09-01")
        self.assertEqual(result.entities, ["Google", "Alphabet"])
        self.assertEqual(result.summary, "Google is a technology company.")

    def test_delete_news(self):
        news = News(
            title="Google News",
            description="Google LLC is an American multinational technology company that specializes in Internet-related services and products.",
            url="https://www.google.com",
            sentiment="Positive",
            publisher="google",
            published_date="2021-09-01",
            entities=["Google", "Alphabet"],
            summary="Google is a technology company.",
            score=0.5,
        )
        db.session.add(news)
        db.session.commit()

        db.session.delete(news)
        db.session.commit()

        result = News.query.filter_by(title="Google News").first()

        self.assertIsNone(result)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
