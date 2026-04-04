from flask import Blueprint, request, jsonify
from extensions import db
from model.user import User
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity

auth_bp = Blueprint("auth", __name__)

# --- SIGNUP ---
@auth_bp.route("/signup", methods=["POST"], strict_slashes=False)
def signup():
    """
    Signup with email and password (plain text)
    POST /api/auth/signup
    {
      "email": "user@example.com",
      "password": "password123"
    }
    """
    data = request.json
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    # Validation
    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    # Check if email already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already registered"}), 409

    try:
        # Create new user
        user = User(email=email)
        user.set_password(password)  # Plain text storage
        db.session.add(user)
        db.session.commit()

        # Create JWT token
        token = create_access_token(identity=str(user.id))

        return jsonify({
            "message": "Signup successful",
            "token": token,
            "user": {
                "id": str(user.id),
                "email": user.email
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Signup Error: {e}")
        return jsonify({"message": "Signup failed"}), 500


# --- LOGIN ---
@auth_bp.route("/login", methods=["POST"], strict_slashes=False)
def login():
    """
    Login with email and password
    POST /api/auth/login
    {
      "email": "user@example.com",
      "password": "password123"
    }
    """
    data = request.json
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()

    if not email or not password:
        return jsonify({"message": "Email and password are required"}), 400

    try:
        # Query user by email
        user = User.query.filter_by(email=email).first()

        # Verify password (plain text comparison)
        if not user or not user.check_password(password):
            return jsonify({"message": "Invalid email or password"}), 401

        # Generate JWT token
        token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "id": str(user.id),
                "email": user.email
            }
        }), 200

    except Exception as e:
        print(f"Login Error: {e}")
        return jsonify({"message": "Login failed"}), 500


# --- LOGOUT ---
@auth_bp.route("/logout", methods=["POST"], strict_slashes=False)
@jwt_required()
def logout():
    """
    Logout - client deletes token from localStorage
    POST /api/auth/logout (requires Authorization header)
    """
    return jsonify({"message": "Logout successful"}), 200


# --- GOOGLE LOGIN ---
@auth_bp.route("/google-login", methods=["POST"], strict_slashes=False)
def google_login():
    """
    Google OAuth login
    POST /api/auth/google-login
    {
      "token": "google_credential_token"
    }
    """
    data = request.json
    token = data.get("token", "").strip()

    if not token:
        return jsonify({"message": "Google token is required"}), 400

    try:
        # TODO: Verify Google token with Google API
        # For now, return a placeholder response
        return jsonify({"message": "Google Login not yet configured", "token": None}), 501

    except Exception as e:
        print(f"Google Login Error: {e}")
        return jsonify({"message": "Google Login failed"}), 500


# --- GET CURRENT USER ---
@auth_bp.route("/me", methods=["GET"], strict_slashes=False)
@jwt_required()
def get_current_user():
    """
    Get current user info
    GET /api/auth/me (requires Authorization header)
    """
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    return jsonify({
        "user": {
            "id": str(user.id),
            "email": user.email
        }
    }), 200
