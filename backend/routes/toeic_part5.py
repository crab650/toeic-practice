from flask import Blueprint, jsonify, request

from ..config import DEFAULT_GEMINI_MODEL, get_config
from ..db import get_db
from ..services.gemini import explain_part5_question


toeic_part5_bp = Blueprint('toeic_part5', __name__)


@toeic_part5_bp.route('/api/toeic/questions', methods=['GET'])
def get_toeic_questions():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')

    conn = get_db()
    cursor = conn.cursor()

    query_parts = []
    params = []

    if status != 'all':
        query_parts.append("status = ?")
        params.append(status)
    if category != 'all':
        query_parts.append("category = ?")
        params.append(category)

    where_clause = " WHERE " + " AND ".join(query_parts) if query_parts else ""

    cursor.execute(f"SELECT COUNT(*) FROM toeic_questions{where_clause}", params)
    total = cursor.fetchone()[0]

    params_query = list(params)
    params_query.extend([limit, offset])
    cursor.execute(
        f"SELECT * FROM toeic_questions{where_clause} ORDER BY id ASC LIMIT ? OFFSET ?",
        params_query,
    )

    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({
        "questions": questions,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@toeic_part5_bp.route('/api/toeic/questions/<int:question_id>/status', methods=['POST'])
def update_toeic_status(question_id):
    data = request.get_json() or {}
    status = data.get('status')

    if status not in ['new', 'mastered', 'review']:
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE toeic_questions SET status = ? WHERE id = ?", (status, question_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "question_id": question_id, "status": status})


@toeic_part5_bp.route('/api/toeic/questions/<int:question_id>/ai-explain', methods=['POST'])
def explain_toeic_question(question_id):
    config = get_config()
    api_key = config.get('gemini_api_key', '')
    gemini_model = config.get('gemini_model', DEFAULT_GEMINI_MODEL)

    if not api_key:
        return jsonify({"error": "請先在「語音與金鑰設定」中填入您的 Gemini API 金鑰！"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM toeic_questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "找不到該多益題目"}), 404

    question_data = dict(row)

    try:
        result = explain_part5_question(api_key, gemini_model, question_data)
        chinese = result.get('chinese', '').strip()
        explanation = result.get('explanation', '').strip()

        if not chinese or not explanation:
            raise Exception("AI 回傳的資料格式不正確")

        cursor.execute(
            "UPDATE toeic_questions SET chinese = ?, explanation = ? WHERE id = ?",
            (chinese, explanation, question_id),
        )
        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "question_id": question_id,
            "chinese": chinese,
            "explanation": explanation,
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500
