from flask import Flask
import os
from dotenv import load_dotenv
from routes.tareas import tareas_bp
from config.db import init_db, mysql
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

#Import the user route
from routes.usuarios import usuarios_bp

#Load all the .env credentials
load_dotenv()

def create_app(): # Function to create the app
    # App instance
    app=Flask(__name__)
    
    # JWT Configuration
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False  # Set to True in production with proper expiration time
    
    # Initialize extensions
    jwt = JWTManager(app)
    bcrypt = Bcrypt(app)
    
    init_db(app)
    
    #Register blueprint
    app.register_blueprint(tareas_bp, url_prefix="/tareas")
    app.register_blueprint(usuarios_bp, url_prefix="/usuarios")
    
    return app
    
app = create_app()

if __name__ == "__main__":
    # Get the Port
    port = int(os.getenv("PORT",8000))

    # Run the application 
    app.run(host="0.0.0.0", port=port, debug=True)