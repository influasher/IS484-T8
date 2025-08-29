from flask import Blueprint

from app.models import User
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
            "email": user.email,
            "role": user.role,
            "rm_id": user.rm_id,
            "created_at": user.created_at,
        })
    return format_response(users, "Users fetched successfully", 200)
    # return "User route is working"