from contextlib import contextmanager
from app import create_test_app, db

@contextmanager
def test_db(app=None):
    """
    Context manager to set up and tear down a temporary test database.
    
    Usage:
        with test_db() as client:
            client.get('/some-route')
    """
    # Create test app if not provided
    app = app or create_test_app()
    
    # Push app context
    ctx = app.app_context()
    ctx.push()
    
    try:
        # Create all tables
        db.create_all()
        yield app.test_client()  # yield the test client to run requests
    finally:
        # Rollback and drop all tables
        db.session.remove()
        db.drop_all()
        ctx.pop()
