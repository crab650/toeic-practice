import os
import json
import sqlite3
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')
DATABASE = 'trainer.db'
DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 8000
DEFAULT_GEMINI_MODEL = 'gemini-3.1-flash-lite'

# Default Sentence Bank to initialize empty database
DEFAULT_BANKS = [
  {
    "name": "Unit 11 健康與醫療",
    "sentences": [
      { "english": "I need a prescription.", "chinese": "我需要一張處方。" },
      { "english": "The doctor is writing a prescription.", "chinese": "醫生正在開處方箋。" },
      { "english": "Does this medicine have side effects?", "chinese": "這種藥物有副作用嗎？" },
      { "english": "Take this medicine after meals.", "chinese": "飯後服用這種藥。" },
      { "english": "I have a terrible headache.", "chinese": "我頭痛得很厲害。" },
      { "english": "You should get some rest.", "chinese": "你應該多休息。" },
      { "english": "The nurse is taking his temperature.", "chinese": "護理師正在量他的體溫。" },
      { "english": "I want to make an appointment with Dr. Smith.", "chinese": "我想預約史密斯醫生的門診。" }
    ]
  },
  {
    "name": "Unit 1 日常生活英語",
    "sentences": [
      { "english": "What time do you usually wake up?", "chinese": "你通常幾點起床？" },
      { "english": "I need to wash my car this weekend.", "chinese": "我這週末需要洗車。" },
      { "english": "Could you pass me the salt, please?", "chinese": "請把鹽遞給我好嗎？" },
      { "english": "I am looking forward to our trip.", "chinese": "我非常期待我們的旅行。" },
      { "english": "Don't forget to lock the door.", "chinese": "別忘了鎖門。" },
      { "english": "It is going to rain this afternoon.", "chinese": "今天下午要下雨了。" }
    ]
  }
]

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def common_prefix_len(str1, str2):
    i = 0
    while i < min(len(str1), len(str2)) and str1[i] == str2[i]:
        i += 1
    return i

def classify_question_locally(opt_a, opt_b, opt_c, opt_d):
    opts = [o.lower().strip() for o in [opt_a, opt_b, opt_c, opt_d] if o]
    if len(opts) < 4:
        return 'grammar'
    s1, s2, s3, s4 = opts[0], opts[1], opts[2], opts[3]
    pairs_sharing = 0
    for i in range(4):
        for j in range(i + 1, 4):
            if common_prefix_len(opts[i], opts[j]) >= 3:
                pairs_sharing += 1
    if pairs_sharing >= 3:
        return 'grammar'
    grammar_words = {
        'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 
        'they', 'them', 'their', 'theirs', 'themselves', 'i', 'me', 'my', 'mine', 'myself',
        'we', 'us', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourselves',
        'who', 'whom', 'whose', 'which', 'that',
        'in', 'on', 'at', 'by', 'for', 'with', 'about', 'between', 'through', 'during',
        'because', 'although', 'though', 'even', 'if', 'unless', 'since', 'until', 'while',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'do', 'does', 'did', 'done', 'doing',
        'have', 'has', 'had', 'having', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must'
    }
    if all(o in grammar_words for o in opts):
        return 'grammar'
    return 'vocabulary'

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id INTEGER,
            english TEXT NOT NULL,
            chinese TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            FOREIGN KEY (unit_id) REFERENCES units(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toeic_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            option_d TEXT NOT NULL,
            answer TEXT NOT NULL,
            chinese TEXT,
            explanation TEXT,
            status TEXT DEFAULT 'new'
        )
    ''')
    
    # Create toeic_part2_questions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toeic_part2_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            answer TEXT NOT NULL,
            status TEXT DEFAULT 'new',
            chinese TEXT,
            explanation TEXT
        )
    ''')
    
    # Ensure toeic_part2_questions has chinese and explanation columns if it was created earlier without them
    try:
        cursor.execute("ALTER TABLE toeic_part2_questions ADD COLUMN chinese TEXT")
    except sqlite3.OperationalError:
        pass
        
    try:
        cursor.execute("ALTER TABLE toeic_part2_questions ADD COLUMN explanation TEXT")
    except sqlite3.OperationalError:
        pass

    # Ensure toeic_questions has category column
    try:
        cursor.execute("ALTER TABLE toeic_questions ADD COLUMN category TEXT")
    except sqlite3.OperationalError:
        pass
        
    # Auto-classify questions if category is NULL
    cursor.execute("SELECT id, option_a, option_b, option_c, option_d FROM toeic_questions WHERE category IS NULL")
    null_rows = cursor.fetchall()
    if null_rows:
        print(f"Categorizing {len(null_rows)} TOEIC questions...")
        for r in null_rows:
            qid, opt_a, opt_b, opt_c, opt_d = r
            cat = classify_question_locally(opt_a, opt_b, opt_c, opt_d)
            cursor.execute("UPDATE toeic_questions SET category = ? WHERE id = ?", (cat, qid))

    conn.commit()

    # Prepopulate if database is brand new
    cursor.execute("SELECT COUNT(*) FROM units")
    if cursor.fetchone()[0] == 0:
        print("Initializing database with default units and sentences...")
        for bank in DEFAULT_BANKS:
            try:
                cursor.execute("INSERT INTO units (name) VALUES (?)", (bank["name"],))
                unit_id = cursor.lastrowid
                for sent in bank["sentences"]:
                    cursor.execute(
                        "INSERT INTO sentences (unit_id, english, chinese) VALUES (?, ?, ?)",
                        (unit_id, sent["english"], sent["chinese"])
                    )
            except Exception as e:
                print(f"Error seeding default data: {e}")
        conn.commit()
    
    conn.close()

# Initialize DB when module is imported/started
init_db()

# ----------------- Web UI Routes -----------------

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# ----------------- API Endpoints -----------------

# Get all units
@app.route('/api/units', methods=['GET'])
def get_units():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM units ORDER BY id ASC")
    units = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(units)

# Get sentences for a unit
@app.route('/api/units/<int:unit_id>/sentences', methods=['GET'])
def get_unit_sentences(unit_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sentences WHERE unit_id = ? ORDER BY id ASC", (unit_id,))
    sentences = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(sentences)

# Update status of a sentence (mastered, review, new)
@app.route('/api/sentences/<int:sentence_id>/status', methods=['POST'])
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

# Import new unit or add sentences to existing unit
@app.route('/api/import', methods=['POST'])
def import_sentences():
    data = request.get_json() or {}
    unit_name = data.get('unit_name', '').strip()
    sentences = data.get('sentences', [])

    if not unit_name or not sentences:
        return jsonify({"error": "Missing unit_name or sentences data"}), 400

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if unit already exists
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
                # Avoid exact duplicate sentences in same unit
                cursor.execute(
                    "SELECT id FROM sentences WHERE unit_id = ? AND english = ?",
                    (unit_id, eng)
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO sentences (unit_id, english, chinese) VALUES (?, ?, ?)",
                        (unit_id, eng, chi)
                    )
                    inserted_count += 1
        
        conn.commit()
        conn.close()
        return jsonify({
            "success": True,
            "unit_id": unit_id,
            "unit_name": unit_name,
            "inserted_count": inserted_count
        })

    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

CONFIG_FILE = 'config.json'

def get_config_file_data():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            pass
    return config

def get_config():
    config = get_config_file_data()
    env_api_key = os.environ.get('GEMINI_API_KEY', '').strip()
    if env_api_key:
        config['gemini_api_key'] = env_api_key

    env_model = os.environ.get('GEMINI_MODEL', '').strip()
    if env_model:
        config['gemini_model'] = env_model
    elif not config.get('gemini_model'):
        config['gemini_model'] = DEFAULT_GEMINI_MODEL

    return config

def save_config(config_data):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=2)
    except Exception as e:
        print(f"Error saving config: {e}")

import urllib.request
import urllib.error

def build_gemini_url(api_key, model_name):
    model = (model_name or DEFAULT_GEMINI_MODEL).strip()
    return f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

def call_gemini_api(api_key, model_name, question_data):
    # Prepare prompt for Gemini
    prompt = f"""
You are an expert English teacher preparing students for the TOEIC exam. 
Provide a high-quality translation and educational analysis for the following TOEIC Part 5 question.

Question: {question_data['question']}
Options:
(A) {question_data['option_a']}
(B) {question_data['option_b']}
(C) {question_data['option_c']}
(D) {question_data['option_d']}
Correct Answer: ({question_data['answer']})

Please output your response in JSON format with exactly two keys: "chinese" and "explanation".
The "chinese" key must contain the Traditional Chinese translation of the correct completed sentence.
The "explanation" key must contain a structured, educational breakdown in Traditional Chinese. It should be formatted exactly like this:
【核心解析】
[Explain why the correct answer is correct, focusing on the grammar rule or word choice tested]

【選項剖析】
- (A) [Briefly explain why this option is wrong]
- (B) [Briefly explain why this option is wrong]
- (C) [Briefly explain why this option is wrong]
- (D) [Briefly explain why this option is wrong]

【關鍵字彙與片語】
- [Word/Phrase] ([Part of speech]): [Traditional Chinese meaning]
- [Word/Phrase] ([Part of speech]): [Traditional Chinese meaning]
...

Do not include any markdown fences (like ```json) or explanation text outside the JSON object.
"""

    url = build_gemini_url(api_key, model_name)
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            return json.loads(text_response)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_msg)
            message = err_json.get('error', {}).get('message', str(e))
        except Exception:
            message = err_msg
        if "quota" in message.lower() or "limit" in message.lower() or e.code == 429:
            raise Exception("您的 Gemini API 金鑰已達免費額度限制 (429 / 請求過於頻繁)。請稍候 1 分鐘後再重試，或是至 Google AI Studio 升級成計費方案。")
        raise Exception(f"Google API Error: {message}")
    except Exception as e:
        raise Exception(f"Gemini Translation failed: {str(e)}")


# ----------------- Settings Endpoints -----------------

@app.route('/api/settings/config', methods=['GET', 'POST'])
def handle_config():
    if request.method == 'POST':
        data = request.get_json() or {}
        api_key = data.get('gemini_api_key', '').strip()
        gemini_model = data.get('gemini_model', '').strip() or DEFAULT_GEMINI_MODEL
        
        config = get_config_file_data()
        if api_key:
            config['gemini_api_key'] = api_key
        config['gemini_model'] = gemini_model
        save_config(config)
        return jsonify({"success": True, "gemini_model": gemini_model})
    else:
        config = get_config()
        api_key = config.get('gemini_api_key', '')
        gemini_model = config.get('gemini_model', DEFAULT_GEMINI_MODEL)
        return jsonify({
            "gemini_api_key_set": bool(api_key),
            "gemini_api_key_masked": (api_key[:4] + "..." + api_key[-4:]) if len(api_key) > 8 else "",
            "gemini_model": gemini_model,
            "default_gemini_model": DEFAULT_GEMINI_MODEL
        })


# ----------------- TOEIC Endpoints -----------------

# Get TOEIC questions with pagination and filtering
@app.route('/api/toeic/questions', methods=['GET'])
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

    # Get total
    cursor.execute(f"SELECT COUNT(*) FROM toeic_questions{where_clause}", params)
    total = cursor.fetchone()[0]

    # Get questions
    params_query = list(params)
    params_query.extend([limit, offset])
    cursor.execute(
        f"SELECT * FROM toeic_questions{where_clause} ORDER BY id ASC LIMIT ? OFFSET ?",
        params_query
    )

    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({
        "questions": questions,
        "total": total,
        "limit": limit,
        "offset": offset
    })

# Update status of a TOEIC question
@app.route('/api/toeic/questions/<int:question_id>/status', methods=['POST'])
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

# Call Gemini AI to translate and explain a TOEIC question
@app.route('/api/toeic/questions/<int:question_id>/ai-explain', methods=['POST'])
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
        # Generate translation and explanation via Gemini API
        result = call_gemini_api(api_key, gemini_model, question_data)
        chinese = result.get('chinese', '').strip()
        explanation = result.get('explanation', '').strip()
        
        if not chinese or not explanation:
            raise Exception("AI 回傳的資料格式不正確")
            
        # Update SQLite row
        cursor.execute(
            "UPDATE toeic_questions SET chinese = ?, explanation = ? WHERE id = ?",
            (chinese, explanation, question_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "question_id": question_id,
            "chinese": chinese,
            "explanation": explanation
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


def call_gemini_part2_api(api_key, model_name, question_data):
    # Prepare prompt for Gemini
    prompt = f"""
You are an expert English teacher preparing students for the TOEIC exam. 
Translate the following TOEIC Listening Part 2 (Question-Response) question and its three response options into Traditional Chinese.
Also, explain why the correct response is correct, and why other options are incorrect or inappropriate as responses.

Question/Statement: {question_data['question']}
Options:
(A) {question_data['option_a']}
(B) {question_data['option_b']}
(C) {question_data['option_c']}
Correct Response: ({question_data['answer']})

Please output your response in JSON format with exactly two keys: "chinese" and "explanation".
The "chinese" key must contain the Traditional Chinese translation of the Question/Statement, followed by the translations of options (A), (B), and (C).
The "explanation" key must contain a concise explanation of the response logic and why the correct answer fits, in Traditional Chinese.
Do not include any markdown fences (like ```json) or explanation text outside the JSON object.
"""

    url = build_gemini_url(api_key, model_name)
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    try:
        req = urllib.request.Request(
            url, 
            data=json.dumps(payload).encode('utf-8'), 
            headers=headers,
            method='POST'
        )
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text_response = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
            return json.loads(text_response)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_msg)
            message = err_json.get('error', {}).get('message', str(e))
        except Exception:
            message = err_msg
        if "quota" in message.lower() or "limit" in message.lower() or e.code == 429:
            raise Exception("您的 Gemini API 金鑰已達免費額度限制 (429 / 請求過於頻繁)。請稍候 1 分鐘後再重試，或是至 Google AI Studio 升級成計費方案。")
        raise Exception(f"Google API Error: {message}")
    except Exception as e:
        raise Exception(f"Gemini Translation failed: {str(e)}")


# Call Gemini AI to translate and explain a TOEIC Part 2 question
@app.route('/api/toeic/part2/questions/<int:question_id>/ai-explain', methods=['POST'])
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
        # Generate translation and explanation via Gemini API
        result = call_gemini_part2_api(api_key, gemini_model, question_data)
        chinese = result.get('chinese', '').strip()
        explanation = result.get('explanation', '').strip()
        
        if not chinese or not explanation:
            raise Exception("AI 回傳的資料格式不正確")
            
        # Update SQLite row
        cursor.execute(
            "UPDATE toeic_part2_questions SET chinese = ?, explanation = ? WHERE id = ?",
            (chinese, explanation, question_id)
        )
        conn.commit()
        conn.close()
        
        return jsonify({
            "success": True,
            "question_id": question_id,
            "chinese": chinese,
            "explanation": explanation
        })
    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500


# ----------------- TOEIC Part 2 Endpoints -----------------

# Get TOEIC Part 2 questions with pagination and filtering
@app.route('/api/toeic/part2/questions', methods=['GET'])
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
            (limit, offset)
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM toeic_part2_questions WHERE status = ?", (status,))
        total = cursor.fetchone()[0]
        cursor.execute(
            "SELECT * FROM toeic_part2_questions WHERE status = ? ORDER BY id ASC LIMIT ? OFFSET ?",
            (status, limit, offset)
        )

    questions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify({
        "questions": questions,
        "total": total,
        "limit": limit,
        "offset": offset
    })

# Update status of a TOEIC Part 2 question
@app.route('/api/toeic/part2/questions/<int:question_id>/status', methods=['POST'])
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

import asyncio
import edge_tts

# Audio Cache directory
CACHE_DIR = 'audio_cache'
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

VOICES = [
    'en-US-GuyNeural',
    'en-US-AriaNeural',
    'en-GB-RyanNeural',
    'en-GB-SoniaNeural',
    'en-AU-NatashaNeural',
    'en-AU-WilliamNeural'
]

async def generate_part2_audio(question_id, question, opt_a, opt_b, opt_c, filepath):
    # Deterministic voice selection
    voice = VOICES[question_id % len(VOICES)]
    
    # We use punctuation (ellipses and periods) to create natural pauses.
    # This prevents edge-tts from escaping and literally reading XML tags like <break>.
    text_content = (
        f"Number {question_id}. ... "
        f"{question} ... ... "
        f"(A) {opt_a} ... "
        f"(B) {opt_b} ... "
        f"(C) {opt_c}"
    )
    
    communicate = edge_tts.Communicate(text=text_content, voice=voice)
    await communicate.save(filepath)

# Stream MP3 audio for a Part 2 question. Generates if not cached.
@app.route('/api/toeic/part2/questions/<int:question_id>/audio', methods=['GET'])
def get_toeic_part2_audio(question_id):
    filename = f"part2_{question_id}.mp3"
    filepath = os.path.join(CACHE_DIR, filename)

    # If file not in cache, generate it using edge-tts
    if not os.path.exists(filepath):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM toeic_part2_questions WHERE id = ?", (question_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({"error": "Question not found"}), 404
            
        q_data = dict(row)
        
        # Run asynchronous edge-tts task in sync Flask context
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(
                    generate_part2_audio(
                        question_id, 
                        q_data['question'], 
                        q_data['option_a'], 
                        q_data['option_b'], 
                        q_data['option_c'], 
                        filepath
                    )
                )
            finally:
                loop.close()
        except Exception as e:
            return jsonify({"error": f"Audio synthesis failed: {str(e)}"}), 500

    return send_from_directory(CACHE_DIR, filename)


if __name__ == '__main__':
    # Local-only by default. Override with APP_HOST, APP_PORT, and FLASK_DEBUG if needed.
    host = os.environ.get('APP_HOST', DEFAULT_HOST)
    port = int(os.environ.get('APP_PORT', DEFAULT_PORT))
    debug = os.environ.get('FLASK_DEBUG', '').lower() in {'1', 'true', 'yes', 'on'}
    app.run(host=host, port=port, debug=debug)
