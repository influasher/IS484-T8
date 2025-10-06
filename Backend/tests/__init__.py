"""
Test package for IS484-T8 backend application.
This package contains comprehensive unit tests for the backend components.
"""
import os
import sys

# Ensure backend directory is in Python path
backend_dir = os.path.dirname(os.path.dirname(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
