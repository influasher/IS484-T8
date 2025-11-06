import uuid
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import User, ClientPreferences
from app import db
from app.utils import format_response

user_bp = Blueprint("user", __name__)

@user_bp.route("/clients", methods=["GET"])
@jwt_required()
def get_clients():
    # Get current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.filter(User.id == uuid.UUID(current_user_id)).first()

    if not current_user:
        return format_response(None, "User not found", 404)

    # Only RMs can access this endpoint, and they should only see their own clients
    if not current_user.is_rm():
        return format_response(None, "Access denied. Only Relationship Managers can view clients.", 403)

    # Filter clients by the current RM's ID
    db_users = User.query.filter_by(role="CLIENT", rm_id=current_user.id).all()
    users = []
    for user in db_users:
        users.append({
            "id": str(user.id),
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
            "rm_id": str(user.rm_id) if user.rm_id else None,
            "created_at": user.created_at,
        })
    return format_response(users, "Clients fetched successfully", 200)

@user_bp.route("/<id>", methods=["GET"])
@jwt_required()
def get_user(id):
    # Get current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.filter(User.id == uuid.UUID(current_user_id)).first()

    if not current_user:
        return format_response(None, "User not found", 404)

    try:
        user_uuid = uuid.UUID(id)
    except ValueError:
        return format_response(None, "Invalid user ID format", 400)

    user = User.query.get(user_uuid)
    if user is None:
        return format_response(None, "User not found", 404)

    # Access control: RMs can only view their own clients or themselves, clients can only view themselves
    if current_user.is_rm():
        if user.is_client() and user.rm_id != current_user.id and user.id != current_user.id:
            return format_response(None, "Access denied. You can only view your own clients.", 403)
        elif user.is_rm() and user.id != current_user.id:
            return format_response(None, "Access denied. You can only view your own profile.", 403)
    elif current_user.is_client():
        if user.id != current_user.id:
            return format_response(None, "Access denied. You can only view your own profile.", 403)
    else:
        return format_response(None, "Access denied.", 403)

    user_data = {
        "id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, "value") else str(user.role),
        "rm_id": str(user.rm_id) if user.rm_id else None,
        "created_at": user.created_at,
    }
    return format_response(user_data, "User fetched successfully", 200)

@user_bp.route('/create-clients', methods=['POST'])
@jwt_required()
def create_client():
    # Get current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.filter(User.id == uuid.UUID(current_user_id)).first()

    if not current_user:
        return format_response(None, "User not found", 404)

    # Only RMs can create clients
    if not current_user.is_rm():
        return format_response(None, "Access denied. Only Relationship Managers can create clients.", 403)

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
        "rm_id": current_user.id,  # Automatically assign the current RM as the client's RM
        "created_at": data.get("created_at"),
        # "updated_at": data.get("updated_at"),
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
        max_single_position_percent=data.get("max_single_position_percent"),
        max_sector_allocation_percent=data.get("max_sector_allocation_percent"),
        min_cash_reserve_percent=data.get("min_cash_reserve_percent"),
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

@user_bp.route('/<id>', methods=['PUT'])
@jwt_required()
def update_client(id):
    data = request.get_json()

    # Find user
    user = User.query.filter_by(id=id).first()
    if not user:
        return format_response(None, "User not found", 404)

    # Update User fields (only if provided in body)
    if "username" in data: 
        user.username = data["username"]
    if "first_name" in data:
        user.first_name = data["first_name"]
    if "last_name" in data:
        user.last_name = data["last_name"]
    if "email" in data:
        user.email = data["email"]
    if "rm_id" in data:
        user.rm_id = data["rm_id"]
    user.updated_at = data.get("updated_at")

    # Update ClientPreferences
    preferences = ClientPreferences.query.filter_by(user_id=user.id).first()
    if preferences:
        if "holding" in data:
            preferences.holding = data["holding"]
        if "overall_pl" in data:
            preferences.overall_pl = data["overall_pl"]
        if "stop_loss_tolerance" in data:
            preferences.stop_loss_tolerance = data["stop_loss_tolerance"]
        if "risk_cap" in data:
            preferences.risk_cap = data["risk_cap"]
        if "sectors" in data:
            preferences.sectors = data["sectors"]

    db.session.commit()

    # Response
    user_response = {
        "id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "rm_id": user.rm_id,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }

    preferences_response = preferences.to_dict() if preferences else None

    return format_response(
        {"user": user_response, "preferences": preferences_response},
        "CLIENT and preferences updated successfully",
        200
    )

@user_bp.route('/<id>/preferences', methods=['GET', 'PUT'])
@jwt_required()
def client_preferences(id):
    """Fetch or update client preferences for a given user id (UUID)."""
    # Get current user from JWT token
    current_user_id = get_jwt_identity()
    current_user = User.query.filter(User.id == uuid.UUID(current_user_id)).first()

    if not current_user:
        return format_response(None, "User not found", 404)

    try:
        user_uuid = uuid.UUID(id)
    except ValueError:
        return format_response(None, "Invalid user ID format", 400)

    # Get the client whose preferences are being requested
    client = User.query.get(user_uuid)
    if not client:
        return format_response(None, "Client not found", 404)

    # Only RMs can access client preferences, and only for their own clients
    if current_user.is_rm():
        if client.rm_id != current_user.id:
            return format_response(None, "Access denied. You can only access preferences for your own clients.", 403)
    elif current_user.is_client():
        # Clients can only access their own preferences
        if client.id != current_user.id:
            return format_response(None, "Access denied. You can only access your own preferences.", 403)
    else:
        return format_response(None, "Access denied.", 403)

    if request.method == 'GET':
        preferences = ClientPreferences.query.filter_by(user_id=user_uuid).first()
        if not preferences:
            # Auto-create default preferences if they don't exist
            preferences = ClientPreferences(
                user_id=user_uuid,
                holding=0.0,
                overall_pl=0.0,
                risk_cap="Moderate",
                sectors=[]
            )
            preferences.apply_risk_profile_defaults()
            db.session.add(preferences)
            db.session.commit()

        # Get current portfolio data to replace static holding/overall_pl values
        from app.services.portfolio_service import get_client_portfolio_summary
        try:
            portfolio_summary = get_client_portfolio_summary(str(user_uuid))
            preferences_dict = preferences.to_dict()
            # Replace static values with calculated portfolio values
            preferences_dict['holding'] = portfolio_summary.get('total_portfolio_value', 0.0)
            preferences_dict['overall_pl'] = portfolio_summary.get('total_unrealized_pnl', 0.0)
        except Exception:
            # If portfolio calculation fails, use static values
            preferences_dict = preferences.to_dict()

        return format_response(preferences_dict, "Preferences fetched successfully", 200)

    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return format_response(None, "No data provided", 400)

        preferences = ClientPreferences.query.filter_by(user_id=user_uuid).first()
        if not preferences:
            # Create new preferences if they don't exist
            preferences = ClientPreferences(user_id=user_uuid)
            db.session.add(preferences)

        # Update preferences with provided data
        for field in ['holding', 'overall_pl', 'stop_loss_tolerance', 'risk_cap', 'sectors',
                     'max_single_position_percent', 'max_sector_allocation_percent', 'min_cash_reserve_percent']:
            if field in data:
                setattr(preferences, field, data[field])

        db.session.commit()
        return format_response(preferences.to_dict(), "Preferences updated successfully", 200)
