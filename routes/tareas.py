from flask import Blueprint, request, jsonify, jwrequired, get_jwt_identity
from flask_jwt_extended import jwt_required
from config.db import get_db_connection

# create blueprint
tareas_bp = Blueprint('tareas', __name__)

#Create a Endpoint, get tareas
@tareas_bp.route('/obtener', methods=['GET'])
@jwt_required()
def get():
    current = get_jwt_identity()
    
    cursor=get_db_connection()
    query = '''SELECT a.id_tarea, a.descripcion, b.name 
                FROM tareas as a 
                INNER JOIN usuarios as b ON a.id_usuario = b.id_usuario
                WHERE a.id_usuario = %s'''
                
    cursor.execute(query, (current,))
    tareas = cursor.fetchall()
    cursor.close()
    
    if not tareas:
        return jsonify({"error": "No se encontraron tareas"}), 404
    
    tareas = [{"id": tarea[0], "descripcion": tarea[1], "name":tarea[2]} for tarea in tareas]
    
    if not tareas:
        return jsonify({"error": "No se encontraron tareas"}), 404
    
    return jsonify({"tareas": tareas}), 200



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