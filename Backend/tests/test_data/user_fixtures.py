"""
User test data fixtures for comprehensive testing.
"""

# Relationship Managers
RELATIONSHIP_MANAGERS = [
    {
        'email': 'john.smith@company.com',
        'username': 'jsmith_rm',
        'full_name': 'John Smith',
        'role': 'relationship_manager',
        'password': 'SecureRM123!'
    },
    {
        'email': 'sarah.johnson@company.com',
        'username': 'sjohnson_rm',
        'full_name': 'Sarah Johnson',
        'role': 'relationship_manager',
        'password': 'SecureRM456!'
    },
    {
        'email': 'sentifinance67@gmail.com',
        'username': 'sentifinance_rm',
        'full_name': 'Sentifinance RM',
        'role': 'relationship_manager',
        'password': 'SecureRM789!'
    }
]

# Clients assigned to John Smith
JOHN_SMITH_CLIENTS = [
    {
        'email': 'michael.chen@email.com',
        'username': 'mchen_client',
        'full_name': 'Michael Chen',
        'role': 'client',
        'rm_username': 'jsmith_rm',
        'password': 'ClientPass123!'
    },
    {
        'email': 'emma.wilson@email.com',
        'username': 'ewilson_client',
        'full_name': 'Emma Wilson',
        'role': 'client',
        'rm_username': 'jsmith_rm',
        'password': 'ClientPass124!'
    },
    {
        'email': 'david.rodriguez@email.com',
        'username': 'drodriguez_client',
        'full_name': 'David Rodriguez',
        'role': 'client',
        'rm_username': 'jsmith_rm',
        'password': 'ClientPass125!'
    },
    {
        'email': 'lisa.thompson@email.com',
        'username': 'lthompson_client',
        'full_name': 'Lisa Thompson',
        'role': 'client',
        'rm_username': 'jsmith_rm',
        'password': 'ClientPass126!'
    },
    {
        'email': 'james.anderson@email.com',
        'username': 'janderson_client',
        'full_name': 'James Anderson',
        'role': 'client',
        'rm_username': 'jsmith_rm',
        'password': 'ClientPass127!'
    },
    {
        'email': 'jennifer.martinez@email.com',
        'username': 'jmartinez_client',
        'full_name': 'Jennifer Martinez',
        'role': 'client',
        'rm_username': 'jsmith_rm',
        'password': 'ClientPass128!'
    }
]

# Clients assigned to Sarah Johnson
SARAH_JOHNSON_CLIENTS = [
    {
        'email': 'robert.taylor@email.com',
        'username': 'rtaylor_client',
        'full_name': 'Robert Taylor',
        'role': 'client',
        'rm_username': 'sjohnson_rm',
        'password': 'ClientPass129!'
    },
    {
        'email': 'ashley.davis@email.com',
        'username': 'adavis_client',
        'full_name': 'Ashley Davis',
        'role': 'client',
        'rm_username': 'sjohnson_rm',
        'password': 'ClientPass130!'
    },
    {
        'email': 'christopher.brown@email.com',
        'username': 'cbrown_client',
        'full_name': 'Christopher Brown',
        'role': 'client',
        'rm_username': 'sjohnson_rm',
        'password': 'ClientPass131!'
    },
    {
        'email': 'amanda.garcia@email.com',
        'username': 'agarcia_client',
        'full_name': 'Amanda Garcia',
        'role': 'client',
        'rm_username': 'sjohnson_rm',
        'password': 'ClientPass132!'
    },
    {
        'email': 'daniel.miller@email.com',
        'username': 'dmiller_client',
        'full_name': 'Daniel Miller',
        'role': 'client',
        'rm_username': 'sjohnson_rm',
        'password': 'ClientPass133!'
    },
    {
        'email': 'michelle.lee@email.com',
        'username': 'mlee_client',
        'full_name': 'Michelle Lee',
        'role': 'client',
        'rm_username': 'sjohnson_rm',
        'password': 'ClientPass134!'
    }
]

# Clients assigned to Sentifinance RM
SENTIFINANCE_CLIENTS = [
    {
        'email': 'sentifinanceclient@gmail.com',
        'username': 'sentifinance_client',
        'full_name': 'Sentifinance Client',
        'role': 'client',
        'rm_username': 'sentifinance_rm',
        'password': 'ClientPass135!'
    }
]

# All users combined
ALL_TEST_USERS = RELATIONSHIP_MANAGERS + JOHN_SMITH_CLIENTS + SARAH_JOHNSON_CLIENTS + SENTIFINANCE_CLIENTS

def get_rm_by_username(username):
    """Get relationship manager by username."""
    return next((rm for rm in RELATIONSHIP_MANAGERS if rm['username'] == username), None)

def get_clients_for_rm(rm_username):
    """Get all clients for a specific relationship manager."""
    all_clients = JOHN_SMITH_CLIENTS + SARAH_JOHNSON_CLIENTS + SENTIFINANCE_CLIENTS
    return [client for client in all_clients if client['rm_username'] == rm_username]

def get_user_by_email(email):
    """Get user by email address."""
    return next((user for user in ALL_TEST_USERS if user['email'] == email), None)

def get_user_by_username(username):
    """Get user by username."""
    return next((user for user in ALL_TEST_USERS if user['username'] == username), None)
