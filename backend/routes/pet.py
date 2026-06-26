import json

from flask import Blueprint, jsonify, request

from ..db import get_db


pet_bp = Blueprint('pet', __name__)


@pet_bp.route('/api/pet/state', methods=['GET'])
def get_pet_state():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT state_json, updated_at FROM pet_state WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"state": None, "updated_at": None})

    try:
        state = json.loads(row['state_json'])
    except json.JSONDecodeError:
        state = None

    return jsonify({
        "state": state,
        "updated_at": row['updated_at'],
    })


@pet_bp.route('/api/pet/state', methods=['POST'])
def save_pet_state():
    data = request.get_json() or {}
    state = data.get('state')

    if not isinstance(state, dict):
        return jsonify({"error": "state must be an object"}), 400

    state_json = json.dumps(state, ensure_ascii=False)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        '''
        INSERT INTO pet_state (id, state_json, updated_at)
        VALUES (1, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            state_json = excluded.state_json,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (state_json,),
    )
    conn.commit()
    conn.close()

    return jsonify({"success": True, "state": state})
