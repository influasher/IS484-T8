from flask import Blueprint, request
import uuid

from app.models import User, ClientPreferences
from app import db
from app.utils import format_response

user_bp = Blueprint("user", __name__)

@user_bp.route("/clients", methods=["GET"])
def get_clients():
    db_users = User.query.filter_by(role="CLIENT").all()
    users = []
    for user in db_users:
        users.append({
            "id": str(user.id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "rm_id": user.rm_id,
            "created_at": user.created_at,
        })
    return format_response(users, "Clients fetched successfully", 200)

@user_bp.route("/<id>", methods=["GET"])
def get_user(id):
    try:
        user_uuid = uuid.UUID(id)
    except ValueError:
        return format_response(None, "Invalid user ID format", 400)
    user = User.query.get(user_uuid)
    if user is None:
        return format_response(None, "User not found", 404)
    user_data = {
        "id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "rm_id": user.rm_id,
        "created_at": user.created_at,
    }
    return format_response(user_data, "User fetched successfully", 200)

@user_bp.route('/create-clients', methods=['POST'])
def create_client():
    data = request.get_json()

    # Use provided id if present, else generate new UUID
    user_id = data.get("id")
    if user_id:
        try:
            user_id = uuid.UUID(user_id)
        except ValueError:
            return format_response(None, "Invalid user ID format", 400)
    else:
        user_id = uuid.uuid4()

    user_data = {
        "id": user_id,
        "username": data.get("username"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "email": data.get("email"),
        "role": "CLIENT",
        "rm_id": data.get("rm_id"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }

    # Create User
    user = User(**user_data)
    db.session.add(user)
    db.session.flush()  # To get user.id before commit

    # Create ClientPreferences
    preferences = ClientPreferences(
        user_id=user.id,
        holding=data.get("holding", 0.0),
        overall_pl=data.get("overall_pl", 0.0),
        stop_loss_tolerance=data.get("stop_loss_tolerance"),
        risk_cap=data.get("risk_cap"),
        sectors=data.get("sectors"),
    )
    db.session.add(preferences)
    db.session.commit()

    user_response = {
        "id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "rm_id": user.rm_id,
        "created_at": user.created_at,
        "updated_at": user.updated_at if hasattr(user, "updated_at") else None,
    }

    preferences_response = preferences.to_dict() if preferences else None

    return format_response(
        {"user": user_response, "preferences": preferences_response},
        "CLIENT and preferences created successfully",
        200
    )

@user_bp.route('/<id>/preferences', methods=['GET'])
def get_client_preferences(id):
    """Fetch client preferences for a given user id (UUID)."""
    try:
        user_uuid = uuid.UUID(id)
    except ValueError:
        return format_response(None, "Invalid user ID format", 400)
    preferences = ClientPreferences.query.filter_by(user_id=user_uuid).first()
    if not preferences:
        return format_response(None, "Preferences not found", 404)
    return format_response(preferences.to_dict(), "Preferences fetched successfully", 200)