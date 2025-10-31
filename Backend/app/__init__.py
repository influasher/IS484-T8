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
    app = Flask(__name__, static_folder="../frontend-build", static_url_path="/")
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
    app.config.from_object("app.config.Config")

    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from app.routes import register_routes

        # Register all blueprints via the central register_routes function.
        register_routes(app)

        # API health check route
        @app.route('/api')
        def health_check():
            return {"status": "SentiFinance API is running", "version": "1.0"}, 200

        # Serve React frontend at root
        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve(path):
            if path and (path.startswith('api/') or path.startswith('static/')):
                # Let Flask handle API routes and static files normally
                from flask import abort
                abort(404)
            try:
                return app.send_static_file('index.html')
            except:
                return {"error": "Frontend not built. Please build the React app first."}, 404

    return app
