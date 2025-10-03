import sys
import os

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from app import create_app, db
from app.models.user import User, UserRole
from app.models.client_preferences import ClientPreferences


def create_missing_preferences():
    """Create ClientPreferences for users who don't have them."""
    app = create_app()

    with app.app_context():
        # Find all clients who don't have preferences
        clients_without_preferences = db.session.query(User).filter(
            User.role == UserRole.CLIENT,
            ~db.session.query(ClientPreferences).filter(
                ClientPreferences.user_id == User.id
            ).exists()
        ).all()

        if not clients_without_preferences:
            print("All clients already have preferences.")
            return

        print(f"Found {len(clients_without_preferences)} clients without preferences:")

        for client in clients_without_preferences:
            # Create default preferences
            preferences = ClientPreferences(
                user_id=client.id,
                holding=0.0,
                overall_pl=0.0,
                risk_cap="Moderate",
                sectors=[]
            )
            preferences.apply_risk_profile_defaults()
            db.session.add(preferences)

            print(f"Created preferences for: {client.first_name} {client.last_name} ({client.username})")

        # Commit all changes
        db.session.commit()
        print(f"\nSuccessfully created preferences for {len(clients_without_preferences)} clients.")


if __name__ == "__main__":
    create_missing_preferences()