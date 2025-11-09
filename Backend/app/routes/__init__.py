from .auth import auth_bp
from .news import news_bp
from .entities import entities_bp
from .sentiment_analysis import sentiment_bp
from .pdf import pdf_bp
from app.routes.send_pdf import send_pdf_bp
from .active_learning import active_learning_bp
from .sentiment_history import sentiment_history_bp
from .user import user_bp
from .recommendations import recommendations_bp
from .transactions import transactions_bp
from .portfolio import portfolio_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(news_bp, url_prefix="/api/news")
    app.register_blueprint(entities_bp, url_prefix="/api/entities")
    app.register_blueprint(sentiment_bp, url_prefix="/api/sentiment")
    app.register_blueprint(pdf_bp, url_prefix="/api/pdf")
    app.register_blueprint(send_pdf_bp, url_prefix="/api/send_pdf")
    app.register_blueprint(sentiment_history_bp, url_prefix="/api/sentiment_history")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(recommendations_bp, url_prefix="/api/recommendations")
    app.register_blueprint(transactions_bp, url_prefix="/api/transactions")
    app.register_blueprint(portfolio_bp, url_prefix="/api/portfolio")
    app.register_blueprint(active_learning_bp, url_prefix="/api/labeling")