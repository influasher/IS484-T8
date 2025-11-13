# Import db from parent app package to re-export it
# This allows `from app.models import db, News, Entity` to work
from app import db

# Import all model classes
from .user import User
from .user_otp import UserOTP
from .client_preferences import ClientPreferences
from .entity import Entity
from .news import News
from .sentiment_history import SentimentHistory
from .transactions import Transactions, TransactionType
from .client_portfolio import ClientPortfolio
from .client_performance import ClientPerformance
from .active_learning import LabelingQueue, UserVote, AggregatedLabel, UserStats, ModelRun, FinalSentiment, QueueStatus, SentimentVote

# Explicitly export all models and db
__all__ = [
    'db',
    'User',
    'UserOTP',
    'ClientPreferences',
    'Entity',
    'News',
    'SentimentHistory',
    'Transactions',
    'TransactionType',
    'ClientPortfolio',
    'ClientPerformance',
    'LabelingQueue',
    'UserVote',
    'AggregatedLabel',
    'UserStats',
    'ModelRun',
    'FinalSentiment',
    'QueueStatus',
    'SentimentVote',
    # do new sentiment analysis models 
]
