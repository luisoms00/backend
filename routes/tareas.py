from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from config.db import get_db_connection

# create blueprint
tareas_bp = Blueprint('tareas', __name__)

# Helpers

def _clean_text(s: str) -> str:
    return s.strip() if isinstance(s, str) else s


def _get_pagination():
    try:
        page = int(request.args.get('page', '1'))
        page_size = int(request.args.get('page_size', '20'))
    except ValueError:
        page, page_size = 1, 20
    page = max(1, page)
    page_size = max(1, min(page_size, 100))
    offset = (page - 1) * page_size
    return page, page_size, offset


#Create a Endpoint, get tareas
@tareas_bp.route('/obtener', methods=['GET'])
@jwt_required()
def get():
    current_user_id = int(get_jwt_identity())
    page, page_size, offset = _get_pagination()

    cursor = get_db_connection()
    try:
        query = (
            """
            SELECT id, descripcion, usuario_id, creada_en
            FROM tareas
            WHERE usuario_id = %s
            ORDER BY creada_en DESC, id DESC
            LIMIT %s OFFSET %s
            """
        )
        cursor.execute(query, (current_user_id, page_size, offset))
        rows = cursor.fetchall()

        if not rows:
            return jsonify({"tareas": [], "page": page, "page_size": page_size}), 200

        tareas = [
            {
                "id": r[0],
                "descripcion": r[1],
                "usuario_id": r[2],
                "creada_en": r[3].isoformat() if hasattr(r[3], 'isoformat') else str(r[3])
            }
            for r in rows
        ]
        return jsonify({"tareas": tareas, "page": page, "page_size": page_size}), 200
    finally:
        cursor.close()


#Create endpoint with post getting data from the body
@tareas_bp.route('/crear', methods=['POST'])
@jwt_required()
def crear():
    current_user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    descripcion = _clean_text(data.get('descripcion'))

    if not descripcion:
        return jsonify({"error": "'descripcion' es requerida"}), 400

    cursor = get_db_connection()
    try:
        cursor.execute(
            'INSERT INTO tareas (descripcion, usuario_id) VALUES (%s, %s)',
            (descripcion, current_user_id)
        )
        cursor.connection.commit()
        new_id = cursor.lastrowid
        return jsonify({
            "mensaje": "Tarea creada exitosamente",
            "tarea": {
                "id": new_id,
                "descripcion": descripcion,
                "usuario_id": current_user_id
            }
        }), 201
    except Exception as e:
        return jsonify({"error": f"No se pudo crear la tarea: {str(e)}"}), 500
    finally:
        if cursor:
            cursor.close()

# Update task (only owner)
@tareas_bp.route('/modificar/<int:tarea_id>', methods=['PUT'])
@jwt_required()
def modificar(tarea_id):
    current_user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    descripcion = _clean_text(data.get('descripcion'))

    if not descripcion:
        return jsonify({"error": "'descripcion' es requerida"}), 400

    cursor = get_db_connection()
    try:
        # Update only if the task belongs to the current user
        cursor.execute(
            'UPDATE tareas SET descripcion = %s WHERE id = %s AND usuario_id = %s',
            (descripcion, tarea_id, current_user_id)
        )
        cursor.connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Tarea no encontrada o sin permisos"}), 404
        return jsonify({"mensaje": "Tarea actualizada"}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo actualizar la tarea: {str(e)}"}), 500
    finally:
        cursor.close()

# Get single task (only owner)
@tareas_bp.route('/tarea/<int:tarea_id>', methods=['GET'])
@jwt_required()
def obtener_tarea(tarea_id):
    current_user_id = int(get_jwt_identity())
    cursor = get_db_connection()
    try:
        cursor.execute(
            'SELECT id, descripcion, usuario_id, creada_en FROM tareas WHERE id = %s AND usuario_id = %s',
            (tarea_id, current_user_id)
        )
        r = cursor.fetchone()
        if not r:
            return jsonify({"error": "Tarea no encontrada"}), 404
        tarea = {
            "id": r[0],
            "descripcion": r[1],
            "usuario_id": r[2],
            "creada_en": r[3].isoformat() if hasattr(r[3], 'isoformat') else str(r[3])
        }
        return jsonify(tarea), 200
    finally:
        cursor.close()


# Delete task (only owner)
@tareas_bp.route('/tarea/<int:tarea_id>', methods=['DELETE'])
@jwt_required()
def eliminar_tarea(tarea_id):
    current_user_id = int(get_jwt_identity())
    cursor = get_db_connection()
    try:
        cursor.execute('DELETE FROM tareas WHERE id = %s AND usuario_id = %s', (tarea_id, current_user_id))
        cursor.connection.commit()
        if cursor.rowcount == 0:
            return jsonify({"error": "Tarea no encontrada o sin permisos"}), 404
        return jsonify({"mensaje": "Tarea eliminada"}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo eliminar la tarea: {str(e)}"}), 500
    finally:
        cursor.close()