import sys
import os

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from app import create_app, db
from app.models.user import User


def clear_users():
    app = create_app()

    with app.app_context():
        # Check if users exist
        user_count = User.query.count()

        if user_count == 0:
            print("No users found in database.")
            return

        print(f"Found {user_count} users in database.")

        # Clear all users
        try:
            User.query.delete()
            db.session.commit()
            print(f"Successfully deleted all {user_count} users from database.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting users: {e}")


if __name__ == "__main__":
    clear_users()
