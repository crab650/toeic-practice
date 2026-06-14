import json
import sqlite3
import urllib.request
import os

DATABASE = 'trainer.db'
JSON_URL = 'https://raw.githubusercontent.com/tranvien98/fill_toeic/master/data.json'

def init_db_table():
    print("Connecting to database...")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create toeic_questions table
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
    conn.commit()
    conn.close()
    print("Table 'toeic_questions' is ready.")

def download_data():
    print(f"Downloading TOEIC question dataset from: {JSON_URL} ...")
    try:
        # Fetch json from github
        req = urllib.request.Request(JSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except Exception as e:
        print(f"Error downloading data: {e}")
        return None

def import_to_db(data):
    if not data:
        print("No data to import.")
        return
        
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check if table already has questions
    cursor.execute("SELECT COUNT(*) FROM toeic_questions")
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"Database already has {count} TOEIC questions. Clearing existing questions...")
        cursor.execute("DELETE FROM toeic_questions")
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='toeic_questions'")
        conn.commit()

    print("Importing questions to database...")
    inserted_count = 0
    
    # Loop and insert
    # data is a dict of dicts: {"1": {"1": "...", "2": "...", "3": "...", "4": "...", "anwser": "...", "question": "..."}}
    for key, item in data.items():
        try:
            raw_question = item.get('question', '')
            # Standardize the blank display: Replace "___" or similar with a clean blank "_______"
            # Some questions might use "___", "____" or even a single "_"
            question = raw_question
            
            opt_1 = item.get('1', '').strip()
            opt_2 = item.get('2', '').strip()
            opt_3 = item.get('3', '').strip()
            opt_4 = item.get('4', '').strip()
            raw_answer = item.get('anwser', '').strip()
            
            # Map raw answer text to A, B, C, or D letter
            answer_letter = ''
            if raw_answer == opt_1:
                answer_letter = 'A'
            elif raw_answer == opt_2:
                answer_letter = 'B'
            elif raw_answer == opt_3:
                answer_letter = 'C'
            elif raw_answer == opt_4:
                answer_letter = 'D'
            else:
                # If spelling differs slightly (e.g. trailing period), do a fuzzy matching
                if opt_1.lower() in raw_answer.lower():
                    answer_letter = 'A'
                elif opt_2.lower() in raw_answer.lower():
                    answer_letter = 'B'
                elif opt_3.lower() in raw_answer.lower():
                    answer_letter = 'C'
                elif opt_4.lower() in raw_answer.lower():
                    answer_letter = 'D'
                else:
                    # Fallback to option A if no match found
                    answer_letter = 'A'
            
            cursor.execute('''
                INSERT INTO toeic_questions (question, option_a, option_b, option_c, option_d, answer)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (question, opt_1, opt_2, opt_3, opt_4, answer_letter))
            
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting item {key}: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully imported {inserted_count} TOEIC questions into 'trainer.db'.")

if __name__ == '__main__':
    init_db_table()
    raw_data = download_data()
    import_to_db(raw_data)
