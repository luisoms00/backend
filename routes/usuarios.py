from flask import Blueprint, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_bcrypt import Bcrypt

from config.db import get_db_connection

import os
from dotenv import load_dotenv

import datetime
load_dotenv()

# Crear el blueprint
usuarios_bp = Blueprint('usuarios', __name__)

# Inicializamos a Bcrypt
bcrypt = Bcrypt()

@usuarios_bp.route('/registrar', methods=['POST'])
def registrar():
    
    # Obtener del body los datos
    data = request.get_json()
    
    nombre = data.get('nombre')
    email = data.get('email')
    password = data.get('password')

    # Validacion
    if not nombre or not email or not password:
        return jsonify({"error": "Faltan datos de usuario"}), 400
    
    # Obtener el cursor de la bd
    cursor = get_db_connection()
    
    try:
        # Verificamos que el usuario no existe
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({"error": "Ese usuario ya existe"}), 400
        
        # Hacemos hash al password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Insertar el registro del nuevo usuario en la base de datos
        cursor.execute(
            "INSERT INTO usuarios (nombre, email, password) VALUES (%s,%s,%s)", 
            (nombre, email, hashed_password)
        )
        # Guardamos el nuevo registro
        cursor.connection.commit()
        
        return jsonify({"mensaje":"El usuario se creo correctamente"})
        
    except Exception as e:
        return jsonify({"error": f"Error al registrar al usuario {str(e)}"}), 500
        
    finally:
        cursor.close()
        
@usuarios_bp.route('/login', methods=['POST'])
def login():
    
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'ERROR':'Faltan datos'}), 400
    
    cursor = get_db_connection()
    
    query = "SELECT password, id_usuario FROM usuarios WHERE email = %s"
    
    cursor.execute(query, (email,))
    
    usuario = cursor.fetchone()
    if usuario and bcrypt.check_password_hash(usuario[0], password):
        #generamos el JWT
        expires = datetime.timedelta(minutes=60)
        access_token = create_access_token(identity=usuario[1], expires_delta=expires)
        
    else:
        return jsonify({'error': 'Credenciales incorrectas'}), 401
    
    
@usuarios_bp.route('/datos', methods=['GET'])
@jwt_required()
def datos():
    current_user_id = get_jwt_identity()
    cursor = get_db_connection()
    cursor.execute("SELECT * FROM usuarios WHERE id_usuario = %s", (current_user_id,))
    usuario = cursor.fetchone()
    cursor.close()
    
    if usuario:
        user_info={
            'id': usuario[0],
            'name': usuario[1],
            'email': usuario[2]
        }
        return jsonify({"datos":user_info}), 200
    else:
        return jsonify({"error": "Usuario no encontrado"}), 404