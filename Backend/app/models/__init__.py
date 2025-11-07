# Import db from parent app package to re-export it
# This allows `from app.models import db, News, Entity` to work
from app import db

# Import all model classes
from .user import User
from .user_otp import UserOTP
from .client_preferences import ClientPreferences
from .entity import Entity
from .news import News
from .feedback import Feedback
from .sentiment_history import SentimentHistory
from .transactions import Transactions, TransactionType
from .client_portfolio import ClientPortfolio
from .client_performance import ClientPerformance

# Explicitly export all models and db
__all__ = [
    'db',
    'User',
    'UserOTP',
    'ClientPreferences',
    'Entity',
    'News',
    'Feedback',
    'SentimentHistory',
    'Transactions',
    'TransactionType',
    'ClientPortfolio',
    'ClientPerformance'
]
