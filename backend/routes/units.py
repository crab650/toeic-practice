from flask import Blueprint, jsonify, request

from ..config import DEFAULT_GEMINI_MODEL, get_config
from ..db import get_db
from ..services.gemini import explain_sentence, lookup_word_pronunciation


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
    cursor.execute(
        '''
        SELECT
            s.*,
            n.chinese AS ai_chinese,
            n.grammar_note,
            n.vocabulary_note,
            n.common_mistakes,
            n.example AS ai_example,
            n.updated_at AS ai_note_updated_at
        FROM sentences s
        LEFT JOIN sentence_ai_notes n ON n.sentence_id = s.id
        WHERE s.unit_id = ?
        ORDER BY s.id ASC
        ''',
        (unit_id,),
    )
    sentences = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(sentences)


@units_bp.route('/api/sentences/<int:sentence_id>/ai-explain', methods=['GET', 'POST'])
def handle_sentence_ai_explain(sentence_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sentences WHERE id = ?", (sentence_id,))
    sentence_row = cursor.fetchone()

    if not sentence_row:
        conn.close()
        return jsonify({"error": "Sentence not found"}), 404

    if request.method == 'GET':
        cursor.execute("SELECT * FROM sentence_ai_notes WHERE sentence_id = ?", (sentence_id,))
        note = cursor.fetchone()
        conn.close()
        return jsonify({"note": dict(note) if note else None})

    cursor.execute("SELECT * FROM sentence_ai_notes WHERE sentence_id = ?", (sentence_id,))
    existing = cursor.fetchone()
    force = bool((request.get_json() or {}).get('force'))
    if existing and not force:
        conn.close()
        return jsonify({"success": True, "sentence_id": sentence_id, "note": dict(existing), "cached": True})

    config = get_config()
    api_key = config.get('gemini_api_key', '')
    gemini_model = config.get('gemini_model', DEFAULT_GEMINI_MODEL)

    if not api_key:
        conn.close()
        return jsonify({"error": "請先在設定中填入 Gemini API 金鑰。"}), 400

    try:
        result = explain_sentence(api_key, gemini_model, dict(sentence_row))
        note = {
            "chinese": result.get("chinese", "").strip(),
            "grammar_note": result.get("grammar_note", "").strip(),
            "vocabulary_note": result.get("vocabulary_note", "").strip(),
            "common_mistakes": result.get("common_mistakes", "").strip(),
            "example": result.get("example", "").strip(),
        }

        if not note["grammar_note"]:
            raise Exception("AI 回傳的句子解析格式不完整")

        cursor.execute(
            '''
            INSERT INTO sentence_ai_notes
                (sentence_id, chinese, grammar_note, vocabulary_note, common_mistakes, example, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(sentence_id) DO UPDATE SET
                chinese = excluded.chinese,
                grammar_note = excluded.grammar_note,
                vocabulary_note = excluded.vocabulary_note,
                common_mistakes = excluded.common_mistakes,
                example = excluded.example,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (
                sentence_id,
                note["chinese"],
                note["grammar_note"],
                note["vocabulary_note"],
                note["common_mistakes"],
                note["example"],
            ),
        )
        conn.commit()
        cursor.execute("SELECT * FROM sentence_ai_notes WHERE sentence_id = ?", (sentence_id,))
        saved = dict(cursor.fetchone())
        conn.close()
        return jsonify({"success": True, "sentence_id": sentence_id, "note": saved, "cached": False})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


@units_bp.route('/api/words/lookup', methods=['GET', 'POST'])
def handle_word_lookup():
    if request.method == 'GET':
        word = request.args.get('word', '').strip().lower()
        if not word:
            return jsonify({"error": "Missing word"}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM word_notes WHERE word = ?", (word,))
        note = cursor.fetchone()
        conn.close()
        return jsonify({"note": dict(note) if note else None})

    data = request.get_json() or {}
    word = data.get('word', '').strip().lower()
    sentence = data.get('sentence', '').strip()
    force = bool(data.get('force'))

    if not word:
        return jsonify({"error": "Missing word"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM word_notes WHERE word = ?", (word,))
    existing = cursor.fetchone()
    if existing and not force:
        conn.close()
        return jsonify({"success": True, "note": dict(existing), "cached": True})

    config = get_config()
    api_key = config.get('gemini_api_key', '')
    gemini_model = config.get('gemini_model', DEFAULT_GEMINI_MODEL)

    if not api_key:
        conn.close()
        return jsonify({"error": "請先在設定中填入 Gemini API 金鑰。"}), 400

    try:
        result = lookup_word_pronunciation(api_key, gemini_model, word, sentence)
        note = {
            "word": result.get("word", word).strip().lower() or word,
            "ipa": result.get("ipa", "").strip(),
            "syllables": result.get("syllables", "").strip(),
            "stress": result.get("stress", "").strip(),
            "meaning_zh": result.get("meaning_zh", "").strip(),
            "pronunciation_note": result.get("pronunciation_note", "").strip(),
            "example": result.get("example", "").strip(),
        }

        if not note["ipa"]:
            raise Exception("AI 回傳的音標資料格式不完整")

        cursor.execute(
            '''
            INSERT INTO word_notes
                (word, ipa, syllables, stress, meaning_zh, pronunciation_note, example, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(word) DO UPDATE SET
                ipa = excluded.ipa,
                syllables = excluded.syllables,
                stress = excluded.stress,
                meaning_zh = excluded.meaning_zh,
                pronunciation_note = excluded.pronunciation_note,
                example = excluded.example,
                updated_at = CURRENT_TIMESTAMP
            ''',
            (
                note["word"],
                note["ipa"],
                note["syllables"],
                note["stress"],
                note["meaning_zh"],
                note["pronunciation_note"],
                note["example"],
            ),
        )
        conn.commit()
        cursor.execute("SELECT * FROM word_notes WHERE word = ?", (note["word"],))
        saved = dict(cursor.fetchone())
        conn.close()
        return jsonify({"success": True, "note": saved, "cached": False})
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


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
