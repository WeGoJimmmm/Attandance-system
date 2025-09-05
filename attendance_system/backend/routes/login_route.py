from flask import Blueprint, request, jsonify
from flask_cors import CORS, cross_origin
from firebase_admin import firestore
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for login routes
login_bp = Blueprint('login', __name__)

# Store db reference (will be set from app.py)
db = None

def init_db(db_instance):
    global db
    db = db_instance

@login_bp.route('/api/login', methods=['POST', 'OPTIONS'])
@cross_origin()
def login():
    """
    Handle user login by checking username/email and password in Firestore
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = jsonify({"success": True})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST')
            return response
            
        # Get login data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        # Validate input
        if not email or not password:
            return jsonify({
                "success": False,
                "message": "Email and password are required"
            }), 400
        
        # Check if database is connected
        if not db:
            return jsonify({
                "success": False,
                "message": "Database connection error"
            }), 500
        
        # Find user by email in Firestore users collection
        try:
            users_ref = db.collection('users')
            query = users_ref.where('email', '==', email).limit(1)
            results = query.get()
            
            if len(results) == 0:
                logger.warning(f"User not found with email: {email}")
                return jsonify({
                    "success": False,
                    "message": "Invalid email or password"
                }), 401
            
            # Get the user document
            user_doc = results[0]
            user_data = user_doc.to_dict()
            stored_password = user_data.get('password', '')
            
            # Debug logging
            logger.info(f"User found: {user_data.get('email')}")
            logger.info(f"Stored password: {stored_password}")
            logger.info(f"Provided password: {password}")
            
            # Verify password (direct comparison since it's plain text in your DB)
            if password != stored_password:
                logger.warning(f"Password mismatch for user: {email}")
                return jsonify({
                    "success": False,
                    "message": "Invalid email or password"
                }), 401
            
            # Get user info
            role = user_data.get('role', 'Unknown')
            name = user_data.get('name', 'User')
            
            logger.info(f"Login successful for user: {email}, role: {role}")
            
            # Prepare response data
            response_data = {
                "success": True,
                "message": "Login successful",
                "user": {
                    "uid": user_doc.id,
                    "email": email,
                    "name": name,
                    "role": role
                }
            }
            
            return jsonify(response_data), 200
            
        except Exception as firestore_error:
            logger.error(f"Firestore query error: {str(firestore_error)}")
            return jsonify({
                "success": False,
                "message": "Database error during login"
            }), 500
                
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred"
        }), 500

@login_bp.route('/api/update-password', methods=['POST', 'OPTIONS'])
@cross_origin()
def update_password():
    """
    Update user password in Firestore
    Expected JSON payload:
    {
        "uid": "user_id",
        "new_password": "new_password123"
    }
    """
    try:
        # Handle preflight OPTIONS request
        if request.method == 'OPTIONS':
            response = jsonify({"success": True})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
            response.headers.add('Access-Control-Allow-Methods', 'POST')
            return response
            
        # Get data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        uid = data.get('uid')
        new_password = data.get('new_password')
        
        # Validate input
        if not uid or not new_password:
            return jsonify({
                "success": False,
                "message": "User ID and new password are required"
            }), 400
        
        # Check if database is connected
        if not db:
            return jsonify({
                "success": False,
                "message": "Database connection error"
            }), 500
        
        # Update password in Firestore
        try:
            user_ref = db.collection('users').document(uid)
            user_ref.update({
                'password': new_password
            })
            
            logger.info(f"Password updated successfully for user: {uid}")
            
            return jsonify({
                "success": True,
                "message": "Password updated successfully"
            }), 200
            
        except Exception as firestore_error:
            logger.error(f"Firestore update error: {str(firestore_error)}")
            return jsonify({
                "success": False,
                "message": "Database error during password update"
            }), 500
                
    except Exception as e:
        logger.error(f"Unexpected error during password update: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred"
        }), 500