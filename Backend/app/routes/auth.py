from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.utils.helpers import format_response, password_rule_checker
from app import db

auth_bp = Blueprint("auth", __name__)

# Blacklist set to store JWT tokens
blacklist = set()


# ** User Registration
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return format_response(None, "Username, email, and password are required", 400)
    if User.query.filter_by(email=email).first():
        return format_response(None, "Email already exists", 400)

    # Check if password meets all requirements
    is_valid, message = password_rule_checker(password)
    if not is_valid:
        return format_response(None, message, 400)

    # Hash the password
    hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

    # Create a new user
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return format_response(None, "User created successfully", 201)


# ** User Login
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return format_response(None, "Email and password are required", 400)

    user = User.query.filter_by(email=email).first()

    # Check if user exists and password is correct
    if not user or not check_password_hash(user.password, password):
        return format_response(None, "Invalid email or password", 401)

    # Create a new access token
    access_token = create_access_token(identity=str(user.id))

    # Return the access token
    return format_response({"access_token": access_token}, "Login successful", 200)


# ** Protected Route (Example)
@auth_bp.route("/protected", methods=["GET"])
@jwt_required()
def protected():
    # Get the current user_id from the JWT token
    user_id = get_jwt_identity()

    # check if JWT token is blacklisted
    jti = get_jwt()["jti"]
    if jti in blacklist:
        return format_response(None, "Token has been revoked", 401)

    # Get the user from the database
    current_user = User.query.filter(User.id == int(user_id)).first()

    # Check if user exists
    if not current_user:
        return format_response(None, "User not found", 404)

    # User data to be returned
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }

    return format_response(user_data, f"Hello {user_data['username']}", 200)


# User Logout (Optional if using client-side token management)
@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    # Blacklist the current access token
    jti = get_jwt()["jti"]
    blacklist.add(jti)

    return format_response(None, "Logged out successfully", 200)
