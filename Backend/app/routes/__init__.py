from .auth import auth_bp
from .news import news_bp
from .entities import entities_bp
from .sentiment_analysis import sentiment_bp
from .pdf import pdf_bp
from app.routes.send_pdf import send_pdf_bp
from app.routes.feedback import feedback_bp
from .sentiment_history import sentiment_history_bp
from .user import user_bp
from .transactions import transactions_bp
from .portfolio import portfolio_bp


def register_routes(app):
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(news_bp, url_prefix="/news")
    app.register_blueprint(entities_bp, url_prefix="/entities")
    app.register_blueprint(sentiment_bp, url_prefix="/sentiment")
    app.register_blueprint(pdf_bp, url_prefix="/pdf")
    app.register_blueprint(send_pdf_bp, url_prefix="/send_pdf")
    app.register_blueprint(feedback_bp, url_prefix="/feedback")
    app.register_blueprint(sentiment_history_bp, url_prefix="/sentiment_history")
    app.register_blueprint(user_bp, url_prefix="/user")
    app.register_blueprint(transactions_bp)
    app.register_blueprint(portfolio_bp)
