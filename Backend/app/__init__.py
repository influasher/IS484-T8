from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_mail import Mail
from flask_migrate import Migrate


db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    app.config.from_object("app.config.Config")

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app.routes import register_routes

        register_routes(app)
        
        # Add a root route for health check
        @app.route('/')
        def health_check():
            return {"status": "SentiFinance API is running", "version": "1.0"}, 200

    return app
