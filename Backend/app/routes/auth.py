import random
from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.helpers import format_response, password_rule_checker
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from app.models.user import User, UserRole
from app.models.user_otp import UserOTP
from app.services.email_service import EmailService
from app.utils.helpers import format_response
from app import db

auth_bp = Blueprint("auth", __name__)

# Blacklist set to store JWT tokens
blacklist = set()

# ** Email Login - Step 1: Send OTP
@auth_bp.route('/login', methods=['POST'])
def send_otp():
    data = request.json
    email = data.get('email')

    if not email:
        return format_response(None, "Email is required", 400)

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return format_response(None, "User not found. Please contact your administrator.", 404)

    # Additional validation for clients only
    if user.is_client() and not user.rm_id:
        return format_response(None, "Access denied. Please contact your Relationship Manager.", 403)

    # Generate 6-digit OTP
    otp_code = f"{random.randint(100000, 999999)}"

    # Create new OTP (this will deactivate any existing active OTPs)
    UserOTP.create_new_otp(user_id=user.id, otp_code=otp_code)

    # Send OTP via Azure Communication Services Email
    try:
        email_service = EmailService()
        email_sent = email_service.send_otp_email(
            recipient_email=email,
            otp_code=otp_code,
            user_name=f"{user.first_name} {user.last_name}"
        )

        if email_sent:
            return format_response(
                {"message": f"OTP sent to {email}"},
                "OTP sent successfully",
                200
            )
        else:
            return format_response(
                None,
                "Failed to send OTP email. Please try again.",
                500
            )

    except Exception as e:
        print(f"Error sending OTP email: {str(e)}")
        return format_response(
            None,
            "Failed to send OTP email. Please try again.",
            500
        )

# ** Verify OTP - Step 2: Complete Login
@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    otp_code = data.get('otp_code')

    if not otp_code:
        return format_response(None, "OTP code is required", 400)

    # Find valid OTP (since OTP is unique and we only allow one active OTP per user)
    otp_record = UserOTP.query.filter_by(
        otp_code=otp_code,
        is_used=False
    ).first()

    if not otp_record:
        return format_response(None, "Invalid OTP code", 401)

    if otp_record.is_expired():
        return format_response(None, "OTP has expired", 401)

    # Get the user associated with this OTP
    user = otp_record.user

    # Mark OTP as used
    otp_record.mark_as_used()

    # Create access token with user role
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role.value,
            "email": user.email,
            "username": user.username
        }
    )

    # Return success with user info and token
    return format_response(
        {
            "access_token": access_token,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value
            }
        },
        "Login successful",
        200
    )


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
