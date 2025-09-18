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

# Nota importante sobre JWT:
# Algunos backends (p. ej., PyJWT>=2) esperan que el claim "sub" sea string.
# Por eso, al crear el token convertimos el id a string, y al leerlo lo
# convertimos de vuelta a int antes de usarlo en la base de datos.

# Helpers

def normalize_email(e):
    return e.strip().lower() if isinstance(e, str) else e

@usuarios_bp.route('/registrar', methods=['POST'])
def registrar():
    
    # Obtener del body los datos
    data = request.get_json()
    
    nombre = data.get('nombre')
    email = normalize_email(data.get('email'))
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
        
        return jsonify({
            "mensaje": "El usuario se creó correctamente",
            "usuario": {
                "id": cursor.lastrowid,
                "nombre": nombre,
                "email": email
            }
        }), 201
        
    except Exception as e:
        return jsonify({"error": f"Error al registrar al usuario {str(e)}"}), 500
        
    finally:
        cursor.close()
        
@usuarios_bp.route('/login', methods=['POST'])
def login():
    
    data = request.get_json()
    
    email = normalize_email(data.get('email'))
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'ERROR':'Faltan datos'}), 400
    
    cursor = get_db_connection()
    
    query = "SELECT password, id FROM usuarios WHERE email = %s"
    
    cursor.execute(query, (email,))
    
    usuario = cursor.fetchone()
    try:
        if usuario and bcrypt.check_password_hash(usuario[0], password):
            # generamos el JWT
            expires = datetime.timedelta(minutes=60)
            user_id = str(usuario[1])  # identity must be a string for some JWT backends
            access_token = create_access_token(identity=user_id, expires_delta=expires)
            return jsonify({
                'access_token': access_token,
                'token_type': 'Bearer',
                'expires_in_minutes': 60
            }), 200
        else:
            return jsonify({'error': 'Credenciales incorrectas'}), 401
    except Exception as e:
        return jsonify({'error': f'Error en login: {str(e)}'}), 500
    finally:
        cursor.close()
        
@usuarios_bp.route('/datos', methods=['GET'])
@jwt_required()
def datos():
    current_user_id = int(get_jwt_identity())
    cursor = get_db_connection()
    cursor.execute("SELECT id, nombre, email FROM usuarios WHERE id = %s", (current_user_id,))
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

@usuarios_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user_id = int(get_jwt_identity())
    cursor = get_db_connection()
    try:
        cursor.execute("SELECT id, nombre, email, created_at FROM usuarios WHERE id = %s", (current_user_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "Usuario no encontrado"}), 404
        user_info = {
            'id': row[0],
            'nombre': row[1],
            'email': row[2],
            'created_at': row[3].isoformat() if hasattr(row[3], 'isoformat') else str(row[3])
        }
        return jsonify(user_info), 200
    finally:
        cursor.close()


@usuarios_bp.route('/me', methods=['PUT'])
@jwt_required()
def actualizar_me():
    data = request.get_json() or {}
    nombre = data.get('nombre')
    email = normalize_email(data.get('email')) if data.get('email') is not None else None

    if nombre is None and email is None:
        return jsonify({"error": "Nada que actualizar"}), 400

    current_user_id = int(get_jwt_identity())
    cursor = get_db_connection()
    try:
        # Si cambia email, verificar que no exista
        if email is not None:
            cursor.execute("SELECT 1 FROM usuarios WHERE email = %s AND id <> %s", (email, current_user_id))
            if cursor.fetchone():
                return jsonify({"error": "El email ya está en uso"}), 409
        
        # Construir update dinámico con parámetros
        fields = []
        params = []
        if nombre is not None:
            fields.append("nombre = %s")
            params.append(nombre)
        if email is not None:
            fields.append("email = %s")
            params.append(email)
        params.append(current_user_id)
        
        sql = f"UPDATE usuarios SET {', '.join(fields)} WHERE id = %s"
        cursor.execute(sql, tuple(params))
        cursor.connection.commit()
        return jsonify({"mensaje": "Perfil actualizado"}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo actualizar: {str(e)}"}), 500
    finally:
        cursor.close()


@usuarios_bp.route('/me/password', methods=['PUT'])
@jwt_required()
def cambiar_password():
    data = request.get_json() or {}
    actual = data.get('password_actual')
    nueva = data.get('password_nueva')

    if not actual or not nueva:
        return jsonify({"error": "Se requieren 'password_actual' y 'password_nueva'"}), 400

    current_user_id = int(get_jwt_identity())
    cursor = get_db_connection()
    try:
        cursor.execute("SELECT password FROM usuarios WHERE id = %s", (current_user_id,))
        row = cursor.fetchone()
        if not row or not bcrypt.check_password_hash(row[0], actual):
            return jsonify({"error": "Password actual incorrecto"}), 401
        
        hashed = bcrypt.generate_password_hash(nueva).decode('utf-8')
        cursor.execute("UPDATE usuarios SET password = %s WHERE id = %s", (hashed, current_user_id))
        cursor.connection.commit()
        return jsonify({"mensaje": "Password actualizado"}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo cambiar el password: {str(e)}"}), 500
    finally:
        cursor.close()

# Nota: asegúrate de inicializar Bcrypt y JWTManager en tu app principal (app.py) con bcrypt.init_app(app) y JWTManager(app).