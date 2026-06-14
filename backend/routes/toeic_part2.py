from flask import Blueprint, jsonify, request, send_from_directory

from ..config import CACHE_DIR, DEFAULT_GEMINI_MODEL, get_config
from ..db import get_db
from ..services.gemini import explain_part2_question
from ..services.tts import ensure_part2_audio


toeic_part2_bp = Blueprint('toeic_part2', __name__)


@toeic_part2_bp.route('/api/toeic/part2/questions/<int:question_id>/ai-explain', methods=['POST'])
def explain_toeic_part2_question(question_id):
    config = get_config()
    api_key = config.get('gemini_api_key', '')
    gemini_model = config.get('gemini_model', DEFAULT_GEMINI_MODEL)

    if not api_key:
        return jsonify({"error": "請先在「語音與金鑰設定」中填入您的 Gemini API 金鑰！"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM toeic_part2_questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "找不到該多益聽力題目"}), 404

    question_data = dict(row)

    try:
        result = explain_part2_question(api_key, gemini_model, question_data)
        chinese = result.get('chinese', '').strip()
        explanation = result.get('explanation', '').strip()

        if not chinese or not explanation:
            raise Exception("AI 回傳的資料格式不正確")

        cursor.execute(
            "UPDATE toeic_part2_questions SET chinese = ?, explanation = ? WHERE id = ?",
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


@toeic_part2_bp.route('/api/toeic/part2/questions', methods=['GET'])
def get_toeic_part2_questions():
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    status = request.args.get('status', 'all')

    conn = get_db()
    cursor = conn.cursor()

    if status == 'all':
        cursor.execute("SELECT COUNT(*) FROM toeic_part2_questions")
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT * FROM toeic_part2_questions ORDER BY id ASC LIMIT ? OFFSET ?",
            (limit, offset),
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM toeic_part2_questions WHERE status = ?", (status,))
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT * FROM toeic_part2_questions WHERE status = ? ORDER BY id ASC LIMIT ? OFFSET ?",
            (status, limit, offset),
        )

    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({
        "questions": questions,
        "total": total,
        "limit": limit,
        "offset": offset,
    })


@toeic_part2_bp.route('/api/toeic/part2/questions/<int:question_id>/status', methods=['POST'])
def update_toeic_part2_status(question_id):
    data = request.get_json() or {}
    status = data.get('status')

    if status not in ['new', 'mastered', 'review']:
        return jsonify({"error": "Invalid status value"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE toeic_part2_questions SET status = ? WHERE id = ?", (status, question_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "question_id": question_id, "status": status})


@toeic_part2_bp.route('/api/toeic/part2/questions/<int:question_id>/audio', methods=['GET'])
def get_toeic_part2_audio(question_id):
    filename = f"part2_{question_id}.mp3"
    filepath = CACHE_DIR / filename

    if not filepath.exists():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM toeic_part2_questions WHERE id = ?", (question_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return jsonify({"error": "Question not found"}), 404

        try:
            ensure_part2_audio(question_id, dict(row), filepath)
        except Exception as e:
            return jsonify({"error": f"Audio synthesis failed: {str(e)}"}), 500

    return send_from_directory(CACHE_DIR, filename)
