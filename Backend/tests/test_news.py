import unittest
import os
import sys
import uuid
import random
import string
from datetime import datetime
from app.models.news import News
from app import create_app, db

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class BaseTestCase(unittest.TestCase):
    """Base test case with app context and database setup."""

    def setUp(self):
        """Set up test environment."""
        self.app = create_app()
        self.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
        self.app.config["TESTING"] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        """Clean up after tests with proper cascade handling."""
        try:
            # Clear all sessions and rollback transactions
            db.session.rollback()
            db.session.remove()
            
            # Handle PostgreSQL foreign key constraints
            if db.engine.dialect.name == 'postgresql':
                with db.engine.connect() as conn:
                    # Use text() for raw SQL execution
                    from sqlalchemy import text
                    conn.execute(text('DROP TABLE IF EXISTS client_portfolio CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS transactions CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS news CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS entity CASCADE'))
                    conn.execute(text('DROP TABLE IF EXISTS user CASCADE'))
                    conn.commit()
            else:
                # For SQLite
                db.drop_all()
                
        except Exception as e:
            print(f"Warning: Error during news test teardown: {e}")
        finally:
            super().tearDown()


class NewsTestCase(BaseTestCase):
    """Test cases for news functionality."""
    
    def setUp(self):
        """Set up test environment."""
        super().setUp()
        self.test_counter = 0
        
    def generate_unique_url(self):
        """Generate a unique URL for testing."""
        self.test_counter += 1
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        return f"https://test-news-{self.test_counter}-{random_suffix}.example.com"
    
    def create_test_news(self, **kwargs):
        """Create a test news item with unique constraints."""
        default_data = {
            'id': uuid.uuid4(),
            'publisher': f'test_publisher_{self.test_counter}',
            'description': f'Test news description {self.test_counter}',
            'published_date': datetime.now().strftime('%Y-%m-%d'),
            'title': f'Test News {self.test_counter} {uuid.uuid4().hex[:8]}',
            'url': self.generate_unique_url(),
            'entities': [f'TestEntity_{self.test_counter}'],
            'score': 0.7,
            'sentiment': 'Positive',
            'summary': f'Test news summary {self.test_counter}'
        }
        default_data.update(kwargs)
        
        try:
            from app.models.news import News
            news = News(**default_data)
            db.session.add(news)
            db.session.commit()
            return news
        except ImportError:
            self.skipTest("News model not available")
    
    def test_create_news(self):
        """Test creating news"""
        news = self.create_test_news()
        
        self.assertIsNotNone(news)
        self.assertIsNotNone(news.title)
        self.assertIsNotNone(news.url)

    def test_read_news(self):
        """Test reading news"""
        # Create news with unique data
        unique_title = f'Test Read News {uuid.uuid4().hex[:8]}'
        news = self.create_test_news(title=unique_title)
        
        try:
            from app.models.news import News
            # Read the news from database
            found_news = News.query.filter_by(title=unique_title).first()
            
            self.assertIsNotNone(found_news)
            self.assertEqual(found_news.title, unique_title)
            
        except ImportError:
            self.skipTest("News model not available")

    def test_update_news(self):
        """Test updating news"""
        # Create news with unique data
        original_title = f'Original Title {uuid.uuid4().hex[:8]}'
        news = self.create_test_news(title=original_title)
        
        try:
            from app.models.news import News
            
            # Update the news
            updated_title = f'Updated Title {uuid.uuid4().hex[:8]}'
            news.title = updated_title
            news.sentiment = 'Negative'
            db.session.commit()
            
            # Verify update
            updated_news = News.query.get(news.id)
            self.assertEqual(updated_news.title, updated_title)
            self.assertEqual(updated_news.sentiment, 'Negative')
            
        except ImportError:
            self.skipTest("News model not available")

    def test_delete_news(self):
        """Test deleting news"""
        # Create news with unique data
        news = self.create_test_news()
        news_id = news.id
        
        try:
            from app.models.news import News
            
            # Delete the news
            db.session.delete(news)
            db.session.commit()
            
            # Verify deletion
            deleted_news = News.query.get(news_id)
            self.assertIsNone(deleted_news)
            
        except ImportError:
            self.skipTest("News model not available")

    def test_news_unique_url_constraint(self):
        """Test that URLs must be unique"""
        unique_url = self.generate_unique_url()
        
        # Create first news item
        news1 = self.create_test_news(
            title='First News',
            url=unique_url
        )
        
        # Try to create second news item with same URL
        try:
            from app.models.news import News
            
            news2 = News(
                id=uuid.uuid4(),
                title='Second News',
                url=unique_url,  # Same URL should cause constraint violation
                publisher='test_publisher_2',
                description='Another test description',
                published_date=datetime.now().strftime('%Y-%m-%d'),
                sentiment='Neutral'
            )
            
            db.session.add(news2)
            
            # This should raise an IntegrityError
            with self.assertRaises(Exception):
                db.session.commit()
                
        except ImportError:
            self.skipTest("News model not available")
        finally:
            # Clean up the session
            db.session.rollback()
    
    def test_news_serialization(self):
        """Test news model serialization"""
        news = self.create_test_news(
            title='Serialization Test',
            url=self.generate_unique_url()
        )
        
        # Test to_dict method if available
        if hasattr(news, 'to_dict'):
            news_dict = news.to_dict()
            self.assertIsInstance(news_dict, dict)
            self.assertEqual(news_dict['title'], 'Serialization Test')
            self.assertIn('id', news_dict)
            self.assertIn('url', news_dict)
