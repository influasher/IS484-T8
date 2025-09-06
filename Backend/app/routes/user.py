from flask import Blueprint, request

from app.models import User
from app.utils import format_response
# Remove heavy import and import directly when needed

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['GET'])
def get_users():
    db_users = User.query.all()
    users = []
    for user in db_users:
        users.append({
            "id": user.id,
            "username": user.username,
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
        "email": user.email,
        "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
        "rm_id": user.rm_id,
        "created_at": user.created_at,
    }
    return format_response(user_data, "User fetched successfully", 200)

@user_bp.route('/search', methods=['GET'])
def search_users_endpoint():
    # Import only when needed to avoid loading heavy dependencies
    from app.services.user_services import search_users
    
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = min(int(request.args.get('per_page', 20)), 100)  # Limit max results
    role_filter = request.args.get('role', 'client')  # Default to clients only
    
    try:
        result = search_users(
            query=query,
            page=page,
            per_page=per_page,
            role_filter=role_filter
        )
        return format_response(result, "Users search successful", 200)
    except Exception as e:
        return format_response(None, f"Search failed: {str(e)}", 500)