from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
# Add after other imports
from backend.routes.admin_routes import init_admin_routes
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the absolute path to the frontend directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')

logger.info(f"Base directory: {BASE_DIR}")
logger.info(f"Frontend directory: {FRONTEND_DIR}")

# Initialize Firebase Admin SDK
def initialize_firebase():
    try:
        if not firebase_admin._apps:
            cred_path = os.path.join(BASE_DIR, "serviceAccountKey.json")
            if not os.path.exists(cred_path):
                logger.error(f"Service account key file not found: {cred_path}")
                return False
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Error initializing Firebase: {str(e)}")
        return False

firebase_initialized = initialize_firebase()

# Initialize Firestore and pass to routes
db = None
if firebase_initialized:
    db = firestore.client()
    try:
        from backend.routes.login_route import init_db
        init_db(db)
        logger.info("Database initialized for login routes")
    except ImportError as e:
        logger.error(f"Error importing login_route: {e}")
else:
    logger.error("Firebase not initialized - database operations will fail")

if firebase_initialized:
    try:
        init_admin_routes(app, db)
        logger.info("Admin routes registered successfully")
    except Exception as e:
        logger.error(f"Error registering admin routes: {e}")


# --- Route Registration ---
# Register API blueprints FIRST to give them priority
def register_blueprints():
    try:
        from backend.routes.login_route import login_bp
        app.register_blueprint(login_bp, url_prefix='/api')
        logger.info("Login routes registered successfully")
    except ImportError as e:
        logger.error(f"Error registering blueprints: {e}")

register_blueprints()

# --- Static File and Frontend Routes (Registered AFTER API) ---
@app.route('/')
def serve_index():
    """Serves the main index.html file."""
    logger.info(f"Serving index.html from: {FRONTEND_DIR}")
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serves other static files like CSS, JS, or other HTML pages."""
    logger.info(f"Serving static file: {filename}")
    return send_from_directory(FRONTEND_DIR, filename)

@app.route('/api/health')
def health_check():
    """Provides a health check endpoint for debugging."""
    return jsonify({
        "status": "healthy",
        "firebase_initialized": firebase_initialized,
        "frontend_dir": FRONTEND_DIR,
        "frontend_exists": os.path.exists(FRONTEND_DIR)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)