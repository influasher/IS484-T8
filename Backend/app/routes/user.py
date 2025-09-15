from flask import Blueprint, request

from app.models import User
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
# @jwt_required
def create_client():
    data = request.get_json()
    user = User(**data)
    user.role = "client"
    db.session.add(user)
    db.session.commit()
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
    return format_response(user_data, "CLIENT created successfully", 200)
