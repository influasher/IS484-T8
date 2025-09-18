from dotenv import load_dotenv
import os

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_TOKEN_LOCATION = "headers"
    APP_DEBUG = os.getenv("APP_DEBUG", True)
    PORT = os.getenv("PORT", 5001)
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    FLASK_APP = os.getenv("FLASK_APP", "run.py")

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = os.getenv("MAIL_PORT", 587)
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", True)
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", False)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")  # Your email address
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")  # Your email password or app password
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_USERNAME")  # Sender's email address


class TestConfig(Config):
    """Configuration for testing environment"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"  # In-memory database for tests
    SECRET_KEY = "test-secret-key"
    JWT_SECRET_KEY = "test-jwt-secret"
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing
