import sys
import os

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from app import create_app, db
from app.models.user import User, UserRole


def seed_users():
    app = create_app()

    with app.app_context():
        # Check if users already exist
        existing_users = User.query.count()
        if existing_users > 0:
            print(f"Warning: Database already has {existing_users} users.")
            print("Run 'python clear_users.py' first to clear existing users.")
            return

        # Create RMs first
        rm1 = User(
            username='jsmith_rm',
            email='john.smith@company.com',
            first_name='John',
            last_name='Smith',
            role=UserRole.RELATIONSHIP_MANAGER
        )

        rm2 = User(
            username='sjohnson_rm',
            email='sarah.johnson@company.com',
            first_name='Sarah',
            last_name='Johnson',
            role=UserRole.RELATIONSHIP_MANAGER
        )

        # Add SentiFinance RM
        sentifinance_rm = User(
            username='sentifinance_rm',
            email='sentifinance67@gmail.com',
            first_name='SentiFinance',
            last_name='RM',
            role=UserRole.RELATIONSHIP_MANAGER
        )

        # Add RMs to session and commit to get their IDs
        db.session.add(rm1)
        db.session.add(rm2)
        db.session.add(sentifinance_rm)
        db.session.commit()

        print(f"Created RM 1: {rm1.username} (ID: {rm1.id})")
        print(f"Created RM 2: {rm2.username} (ID: {rm2.id})")
        print(f"Created SentiFinance RM: {sentifinance_rm.username} (ID: {sentifinance_rm.id})")
        
        # Clients for John Smith (RM1)
        clients_rm1 = [
            {
                "username": "mchen_client",
                "email": "michael.chen@email.com",
                "first_name": "Michael",
                "last_name": "Chen",
            },
            {
                "username": "ewilson_client",
                "email": "emma.wilson@email.com",
                "first_name": "Emma",
                "last_name": "Wilson",
            },
            {
                "username": "drodriguez_client",
                "email": "david.rodriguez@email.com",
                "first_name": "David",
                "last_name": "Rodriguez",
            },
            {
                "username": "lthompson_client",
                "email": "lisa.thompson@email.com",
                "first_name": "Lisa",
                "last_name": "Thompson",
            },
            {
                "username": "janderson_client",
                "email": "james.anderson@email.com",
                "first_name": "James",
                "last_name": "Anderson",
            },
            {
                "username": "jmartinez_client",
                "email": "jennifer.martinez@email.com",
                "first_name": "Jennifer",
                "last_name": "Martinez",
            },
        ]

        # Clients for Sarah Johnson (RM2)
        clients_rm2 = [
            {
                "username": "rtaylor_client",
                "email": "robert.taylor@email.com",
                "first_name": "Robert",
                "last_name": "Taylor",
            },
            {
                "username": "adavis_client",
                "email": "ashley.davis@email.com",
                "first_name": "Ashley",
                "last_name": "Davis",
            },
            {
                "username": "cbrown_client",
                "email": "christopher.brown@email.com",
                "first_name": "Christopher",
                "last_name": "Brown",
            },
            {
                "username": "agarcia_client",
                "email": "amanda.garcia@email.com",
                "first_name": "Amanda",
                "last_name": "Garcia",
            },
            {
                "username": "dmiller_client",
                "email": "daniel.miller@email.com",
                "first_name": "Daniel",
                "last_name": "Miller",
            },
            {
                "username": "mlee_client",
                "email": "michelle.lee@email.com",
                "first_name": "Michelle",
                "last_name": "Lee",
            },
        ]

        # Clients for SentiFinance RM
        clients_sentifinance = [
            {'username': 'sentifinance_client', 'email': 'sentifinanceclient@gmail.com', 'first_name': 'SentiFinance', 'last_name': 'Client'}
        ]
        
        # Create clients for RM1
        for client_data in clients_rm1:
            client = User(
                username=client_data['username'],
                email=client_data['email'],
                first_name=client_data['first_name'],
                last_name=client_data['last_name'],
                role=UserRole.CLIENT,
                rm_id=rm1.id,
            )
            db.session.add(client)
            print(f"Created client: {client.first_name} {client.last_name} ({client.username}) -> RM: {rm1.first_name} {rm1.last_name}")

        # Create clients for RM2
        for client_data in clients_rm2:
            client = User(
                username=client_data['username'],
                email=client_data['email'],
                first_name=client_data['first_name'],
                last_name=client_data['last_name'],
                role=UserRole.CLIENT,
                rm_id=rm2.id,
            )
            db.session.add(client)
            print(f"Created client: {client.first_name} {client.last_name} ({client.username}) -> RM: {rm2.first_name} {rm2.last_name}")

        # Create clients for SentiFinance RM
        for client_data in clients_sentifinance:
            client = User(
                username=client_data['username'],
                email=client_data['email'],
                first_name=client_data['first_name'],
                last_name=client_data['last_name'],
                role=UserRole.CLIENT,
                rm_id=sentifinance_rm.id
            )
            db.session.add(client)
            print(f"Created client: {client.first_name} {client.last_name} ({client.username}) -> RM: {sentifinance_rm.first_name} {sentifinance_rm.last_name}")
        
        # Commit all clients
        db.session.commit()

        print("\nSuccessfully created:")
        print("- 3 Relationship Managers")
        print("- 13 Clients (6 to RM1, 6 to RM2, 1 to SentiFinance RM)")
        print("\nPasswordless authentication enabled - login with email + OTP")


if __name__ == "__main__":
    seed_users()
