import unittest
import sys
import os
from sqlalchemy import text

# Add backend directory to Python path
backend_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, backend_dir)

try:
    from extensions import db
except ImportError:
    db = None

class DatabaseCleanupMixin:
    """Mixin to provide comprehensive database cleanup for tests."""
    
    def cleanup_database_postgresql(self):
        """Cleanup database for PostgreSQL with proper CASCADE handling."""
        try:
            with db.engine.connect() as conn:
                # Disable foreign key checks
                conn.execute(text('SET session_replication_role = replica'))
                
                # Get all table names
                result = conn.execute(text("""
                    SELECT tablename FROM pg_tables 
                    WHERE schemaname = 'public'
                """))
                tables = [row[0] for row in result]
                
                # Drop tables in reverse dependency order
                dependent_tables = ['client_portfolio', 'transactions', 'news_entities']
                main_tables = ['entity', 'news', 'user', 'client']
                
                for table in dependent_tables + main_tables:
                    if table in tables:
                        conn.execute(text(f'DROP TABLE IF EXISTS {table} CASCADE'))
                
                # Re-enable foreign key checks
                conn.execute(text('SET session_replication_role = DEFAULT'))
                conn.commit()
                
        except Exception as e:
            print(f"PostgreSQL cleanup failed: {e}")
            # Fallback: drop entire schema
            try:
                with db.engine.connect() as conn:
                    conn.execute(text('DROP SCHEMA public CASCADE'))
                    conn.execute(text('CREATE SCHEMA public'))
                    conn.commit()
            except Exception as fallback_error:
                print(f"Schema recreate failed: {fallback_error}")
    
    def cleanup_database_sqlite(self):
        """Cleanup database for SQLite."""
        try:
            # SQLite doesn't enforce foreign keys by default
            db.drop_all()
        except Exception as e:
            print(f"SQLite cleanup failed: {e}")
    
    def comprehensive_cleanup(self):
        """Perform comprehensive database cleanup."""
        if not db:
            return
            
        try:
            # Rollback any pending transactions
            db.session.rollback()
            db.session.remove()
            
            # Choose cleanup method based on database type
            if db.engine.dialect.name == 'postgresql':
                self.cleanup_database_postgresql()
            else:
                self.cleanup_database_sqlite()
                
        except Exception as e:
            print(f"Warning: Comprehensive cleanup failed: {e}")

class DatabaseCleanupTestCase(unittest.TestCase, DatabaseCleanupMixin):
    """Test case with comprehensive database cleanup."""
    
    def tearDown(self):
        """Enhanced tearDown with comprehensive cleanup."""
        self.comprehensive_cleanup()
        super().tearDown()

if __name__ == '__main__':
    unittest.main()
