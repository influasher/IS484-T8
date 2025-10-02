"""
Test configuration and shared fixtures.
Helps resolve import paths for backend modules.
"""
import os
import sys

# Add backend directory to Python path at module level
backend_dir = os.path.dirname(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Test environment variables
os.environ['FLASK_ENV'] = 'testing'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key-do-not-use-in-production'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key'

# Import backend modules to validate they're available
BACKEND_MODULES_AVAILABLE = False
try:
    import importlib.util
    
    # Check if modules exist without importing them completely
    app_spec = importlib.util.find_spec('app')
    
    if app_spec:
        BACKEND_MODULES_AVAILABLE = True
    else:
        print("Warning: App module not found")
        
except Exception as e:
    print(f"Warning: Backend modules validation failed: {e}")
    BACKEND_MODULES_AVAILABLE = False
    BACKEND_MODULES_AVAILABLE = False
