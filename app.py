from flask import Flask, jsonify, request
import os
from dotenv import load_dotenv
from routes.tareas import tareas_bp
from config.db import init_db, mysql
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from flask_bcrypt import Bcrypt

# Extra imports for CORS and datetime
from flask_cors import CORS
import datetime

#Import the user route
from routes.usuarios import usuarios_bp

#Load all the .env credentials
load_dotenv()

# Config from environment
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'http://localhost:4200,http://127.0.0.1:4200,http://localhost:5173').split(',')
JWT_EXPIRES_MIN = int(os.getenv('JWT_EXPIRES_MIN', '60'))  # 60 minutes by default

def create_app(): # Function to create the app
    # App instance
    app = Flask(__name__)

    # Basic app config
    app.config['JSON_SORT_KEYS'] = False
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH_MB', '10')) * 1024 * 1024  # default 10MB

    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(minutes=JWT_EXPIRES_MIN)

    # Initialize extensions
    jwt = JWTManager(app)
    bcrypt = Bcrypt(app)

    # Enable CORS for frontend apps
    CORS(app, resources={r"/*": {"origins": ALLOWED_ORIGINS}}, supports_credentials=True)

    @app.after_request
    def add_security_headers(resp):
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['X-Frame-Options'] = 'DENY'
        resp.headers['X-XSS-Protection'] = '1; mode=block'
        # Allow common headers for APIs
        resp.headers.setdefault('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        resp.headers.setdefault('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        return resp

    init_db(app)
    
    @app.get("/debug/whoami")
    @jwt_required()
    def whoami():
        return {
            "identity": get_jwt_identity(),   # debería ser "2" (string) si usaste identity=str(user_id)
            "claims": get_jwt()               # aquí puedes ver el payload completo
        }, 200

    @app.get("/_debug/routes")
    def _list_routes():
        output = []
        for rule in app.url_map.iter_rules():
            methods = ",".join(sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS")))
            output.append({
                "rule": str(rule),
                "endpoint": rule.endpoint,
                "methods": methods
            })
        return jsonify(output), 200

    # Health checks
    @app.get('/health/app')
    def health_app():
        return jsonify({"status": "ok", "time": datetime.datetime.utcnow().isoformat() + 'Z'}), 200

    @app.get('/health/db')
    def health_db():
        try:
            cur = mysql.connection.cursor()
            cur.execute('SELECT 1')
            cur.fetchone()
            cur.close()
            return jsonify({"status": "ok"}), 200
        except Exception as e:
            return jsonify({"status": "error", "detail": str(e)}), 500

    #Register blueprint
    app.register_blueprint(tareas_bp, url_prefix="/tareas")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")

    # JSON error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad Request", "detail": getattr(e, 'description', str(e))}), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({"error": "Unauthorized"}), 401

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not Found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"error": "Method Not Allowed"}), 405

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify({"error": "Unprocessable Entity"}), 422

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Internal Server Error"}), 500

    return app
    
app = create_app()


if __name__ == "__main__":
    # Get the Port
    port = int(os.getenv("PORT",8000))

    # Run the application
    app.run(host=os.getenv('HOST', '0.0.0.0'), port=port, debug=os.getenv('FLASK_DEBUG', 'true').lower() == 'true')