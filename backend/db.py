import sqlite3
import json

from .classifier import classify_question_locally
from .config import DATABASE
from .seed_data import DEFAULT_BANKS


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cursor = conn.cursor()

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pet_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            state_json TEXT NOT NULL,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sentence_ai_notes (
            sentence_id INTEGER PRIMARY KEY,
            chinese TEXT,
            grammar_note TEXT,
            vocabulary_note TEXT,
            common_mistakes TEXT,
            example TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sentence_id) REFERENCES sentences(id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS word_notes (
            word TEXT PRIMARY KEY,
            ipa TEXT,
            syllables TEXT,
            stress TEXT,
            meaning_zh TEXT,
            pronunciation_note TEXT,
            example TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute("SELECT id FROM pet_state WHERE id = 1")
    if not cursor.fetchone():
        default_pet_state = {
            "level": 1,
            "exp": 0,
            "streak": 0,
            "lastFedDate": "",
            "skin": "default",
            "inventory": {
                "snack": 0,
                "toy": 0,
                "charm": 0,
            },
            "daily": {
                "date": "",
                "correct": 0,
                "sentence": 0,
                "part2": 0,
                "claimed": [],
            },
        }
        cursor.execute(
            "INSERT INTO pet_state (id, state_json) VALUES (1, ?)",
            (json.dumps(default_pet_state),),
        )

    for column_sql in [
        "ALTER TABLE toeic_part2_questions ADD COLUMN chinese TEXT",
        "ALTER TABLE toeic_part2_questions ADD COLUMN explanation TEXT",
        "ALTER TABLE toeic_questions ADD COLUMN category TEXT",
    ]:
        try:
            cursor.execute(column_sql)
        except sqlite3.OperationalError:
            pass

    cursor.execute("SELECT id, option_a, option_b, option_c, option_d FROM toeic_questions WHERE category IS NULL")
    null_rows = cursor.fetchall()
    if null_rows:
        print(f"Categorizing {len(null_rows)} TOEIC questions...")
        for row in null_rows:
            cat = classify_question_locally(row['option_a'], row['option_b'], row['option_c'], row['option_d'])
            cursor.execute("UPDATE toeic_questions SET category = ? WHERE id = ?", (cat, row['id']))

    conn.commit()

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
                        (unit_id, sent["english"], sent["chinese"]),
                    )
            except Exception as e:
                print(f"Error seeding default data: {e}")
        conn.commit()

    conn.close()
