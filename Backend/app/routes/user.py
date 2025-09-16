from flask import Blueprint, request

from app.models import User, ClientPreferences
from app import db
from app.utils import format_response

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['GET'])
def get_users():
    db_users = User.query.all()
    users = []
    for user in db_users:
        users.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "rm_id": user.rm_id,
            "created_at": user.created_at,
        })
    return format_response(users, "Users fetched successfully", 200)

@user_bp.route('/clients', methods=['GET'])
def get_clients():
    db_users = User.query.filter_by(role='CLIENT').all()
    users = []
    for user in db_users:
        users.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "rm_id": user.rm_id,
            "created_at": user.created_at,
        })
    return format_response(users, "Clients fetched successfully", 200)

@user_bp.route('/<id>', methods=['GET'])
def get_user(id):
    user = User.query.get(id)
    if user is None:
        return format_response(None, "User not found", 404)
    user_data = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "rm_id": user.rm_id,
        "created_at": user.created_at,
    }
    return format_response(user_data, "User fetched successfully", 200)

@user_bp.route('/create-clients', methods=['POST'])
def create_client():
    data = request.get_json()

    user_data = {
        "username": data.get("username"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": data.get("email"),
        "role": "client",
        "rm_id": data.get("rm_id"),
        "created_at": data.get("created_at"),
    }

    # Create User
    user = User(**user_data)
    db.session.add(user)
    db.session.flush()  # To get user.id before commit

    # Create ClientPreferences
    preferences = ClientPreferences(
        user_id=user.id,
        holding=0.0,
        overall_pl=0.0,
        stop_loss_tolerance=data.get("stop_loss_tolerance"),
        risk_cap=data.get("risk_cap"),
        sectors=data.get("sectors"),
    )
    db.session.add(preferences)
    db.session.commit()

    user_response = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "rm_id": user.rm_id,
        "created_at": user.created_at,
    }

    preferences_response = preferences.to_dict() if preferences else None

    return format_response(
        {"user": user_response, "preferences": preferences_response},
        "CLIENT and preferences created successfully",
        200
    )
