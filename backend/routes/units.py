from flask import Blueprint, jsonify, request

from ..db import get_db


units_bp = Blueprint('units', __name__)


@units_bp.route('/api/units', methods=['GET'])
def get_units():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM units ORDER BY id ASC")
    units = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(units)


@units_bp.route('/api/units/<int:unit_id>/sentences', methods=['GET'])
def get_unit_sentences(unit_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sentences WHERE unit_id = ? ORDER BY id ASC", (unit_id,))
    sentences = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(sentences)


@units_bp.route('/api/sentences/<int:sentence_id>/status', methods=['POST'])
def update_sentence_status(sentence_id):
    data = request.get_json() or {}
    status = data.get('status')

    if status not in ['new', 'mastered', 'review']:
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE sentences SET status = ? WHERE id = ?", (status, sentence_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "sentence_id": sentence_id, "status": status})


@units_bp.route('/api/import', methods=['POST'])
def import_sentences():
    data = request.get_json() or {}
    unit_name = data.get('unit_name', '').strip()
    sentences = data.get('sentences', [])

    if not unit_name or not sentences:
        return jsonify({"error": "Missing unit_name or sentences data"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM units WHERE name = ?", (unit_name,))
        row = cursor.fetchone()
        if row:
            unit_id = row['id']
        else:
            cursor.execute("INSERT INTO units (name) VALUES (?)", (unit_name,))
            unit_id = cursor.lastrowid

        inserted_count = 0
        for item in sentences:
            eng = item.get('english', '').strip()
            chi = item.get('chinese', '').strip()
            if eng and chi:
                cursor.execute(
                    "SELECT id FROM sentences WHERE unit_id = ? AND english = ?",
                    (unit_id, eng),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO sentences (unit_id, english, chinese) VALUES (?, ?, ?)",
                        (unit_id, eng, chi),
                    )
                    inserted_count += 1

        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "unit_id": unit_id,
            "unit_name": unit_name,
            "inserted_count": inserted_count,
        })

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500
