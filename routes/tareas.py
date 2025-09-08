from flask import Blueprint, request, jsonify
from config.db import get_db_connection

# create blueprint
tareas_bp = Blueprint('tareas', __name__)

#Create a Endpoint, get tareas
@tareas_bp.route('/obtener', methods=['GET'])
def get():
    return jsonify({"Mensaje": "Estas son tus tareas"})

#Create endpoint with post getting data from the body
@tareas_bp.route('/crear', methods=['POST'])
def crear():
    
    # Obtain data from body
    data = request.get_json()
    
    descripcion = data.get('descripcion')
    
    if not descripcion:
        return jsonify({"Error": "Debes crear una descripcion de la tarea"}), 400
    
    # Get Cursor
    cursor = get_db_connection()
    
    # Do an insert
    try:
        cursor.execute('INSERT INTO tareas (descripcion) VALUES (%s)', (descripcion,))
        cursor.connection.commit()
        return jsonify({"message":"Tarea creada exitosamente"}), 201
    except Exception as e:
        return jsonify({"error":f"No se pudo crear la tarea: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()

# Create endpoint using PUT passing data through the body and url
@tareas_bp.route('/modificar/<int:user_id>', methods=['PUT'])
def modificar(user_id):
    
    #Get data from the bidy
    data = request.get_json()
    nombre = data.get('nombre')
    apellido = data.get('apellido')
    
    mensaje = f"Usuario con id: {user_id} y nombre: {nombre} y apellido: {apellido}"
    
    return jsonify({"saludo": mensaje})