import json
import sqlite3
import urllib.request
import urllib.error
import time
import os

DATABASE = 'trainer.db'
CONFIG_FILE = 'config.json'

def init_db_table():
    print("Connecting to database...")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create toeic_part2_questions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toeic_part2_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            option_a TEXT NOT NULL,
            option_b TEXT NOT NULL,
            option_c TEXT NOT NULL,
            answer TEXT NOT NULL,
            status TEXT DEFAULT 'new'
        )
    ''')
    conn.commit()
    conn.close()
    print("Table 'toeic_part2_questions' is ready.")

def get_api_key():
    if not os.path.exists(CONFIG_FILE):
        return None
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config.get('gemini_api_key', '')
    except Exception:
        return None

def generate_questions_batch(api_key, batch_num):
    print(f"Generating batch {batch_num}/15 via Gemini API...")
    
    prompt = """
You are a senior TOEIC test designer. Generate 10 highly realistic TOEIC Listening Part 2 (Question-Response) questions.
Each question must consist of:
1. A question or statement (e.g. "Where is the marketing department?")
2. Three response options (A, B, C). Exactly one option must be the logically correct response. The other two options must be realistic distractors (e.g., repeating words with similar sounds, or answering the wrong question word).
3. The correct answer letter ('A', 'B', or 'C').

Please output the result as a raw JSON array of objects with exactly these keys:
"question", "option_a", "option_b", "option_c", "answer"

Do not include any markdown fences (like ```json) or explanation text outside the JSON object.
Make sure to cover various question types:
- Wh-questions (Who, What, Where, When, Why, How)
- Yes/No questions (Can you..., Did you..., Is there...)
- Statements/Comments (The printer is out of paper.)
- Tag questions/Choice questions (Would you prefer coffee or tea?)
"""

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "responseMimeType": "application/json"
        }
    }
    
    max_retries = 2
    backoff = 1
    
    for attempt in range(max_retries):
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
            if e.code in [429, 503]:
                print(f"  Attempt {attempt+1}/{max_retries} rate limited or unavailable ({e.code}). Retrying in {backoff} seconds...")
                time.sleep(backoff)
                backoff *= 2
            else:
                print(f"HTTP Error calling API for batch {batch_num}: {e}")
                break
        except Exception as e:
            print(f"Error calling API for batch {batch_num}: {e}")
            break
            
    return []

import random

def generate_local_fallback_questions(count_needed):
    departments = ["marketing", "sales", "human resources", "accounting", "design", "IT support", "public relations", "legal", "purchasing", "logistics"]
    tasks = ["preparing the presentation", "organizing the files", "booking the flight", "writing the report", "fixing the copier", "sending the invitations", "updating the database", "renewing the contract", "checking the inventory"]
    events = ["annual seminar", "staff meeting", "board conference", "orientation session", "training workshop", "client luncheon", "product launch", "retirement party", "awards ceremony"]
    places = ["airport", "headquarters", "downtown office", "conference hall", "auditorium", "warehouse", "exhibition center", "hotel lobby", "cafeteria"]
    items = ["printer", "projector", "air conditioner", "elevator", "scanner", "router", "laptop", "photocopier", "vending machine"]
    
    wh_questions = [
        # Where
        {
            "q": "Where is the {dept} department?",
            "options": ["On the third floor.", "Yes, I agree.", "At 2:30 PM."],
            "answer": "A"
        },
        {
            "q": "Where should I submit the {task_noun}?",
            "options": ["To Ms. Thompson in room 405.", "Yes, it is very helpful.", "By Friday morning."],
            "answer": "A"
        },
        {
            "q": "Where did you park your car?",
            "options": ["In the underground parking lot.", "At 9 o'clock.", "No, it's mine."],
            "answer": "A"
        },
        # Who
        {
            "q": "Who is in charge of {task_gerund}?",
            "options": ["No, I am not.", "Mr. Green from the IT department.", "At the main entrance."],
            "answer": "B"
        },
        {
            "q": "Who scheduled the {event}?",
            "options": ["Yes, it was scheduled.", "The branch manager did.", "To discuss the budget."],
            "answer": "B"
        },
        {
            "q": "Who is the new supervisor for the {dept} team?",
            "options": ["She used to work in London.", "Mr. Miller was appointed yesterday.", "Yes, I know him."],
            "answer": "B"
        },
        # When
        {
            "q": "When is the {event} supposed to start?",
            "options": ["In the main conference room.", "No, it hasn't started yet.", "Right after the lunch break."],
            "answer": "C"
        },
        {
            "q": "When did they install the new {item}?",
            "options": ["Late last night.", "Yes, it's brand new.", "On the desk."],
            "answer": "A"
        },
        {
            "q": "When are the quarterly sales reports due?",
            "options": ["By the end of this week.", "No, I didn't see them.", "In the filing cabinet."],
            "answer": "A"
        },
        # How
        {
            "q": "How can I get to the {place}?",
            "options": ["Take the subway line 3.", "Sure, I can help you.", "Yes, it's very far."],
            "answer": "A"
        },
        {
            "q": "How did you like the {event}?",
            "options": ["It was very informative.", "Yes, I did.", "By plane."],
            "answer": "A"
        },
        {
            "q": "How often do you check the inventory in the {place}?",
            "options": ["Twice a week.", "No, I haven't checked it.", "At the front desk."],
            "answer": "A"
        },
        # Why
        {
            "q": "Why is the {item} out of service?",
            "options": ["Because they are repairing it.", "Yes, it is.", "Tomorrow afternoon."],
            "answer": "A"
        },
        {
            "q": "Why did we change the venue for the {event}?",
            "options": ["The original room was too small.", "Yes, we did.", "To meet the client."],
            "answer": "A"
        },
        {
            "q": "Why are you leaving the office so early today?",
            "options": ["I have a dentist appointment at 4 PM.", "No, I'm staying late.", "To finish the project."],
            "answer": "A"
        },
        # Yes/No
        {
            "q": "Did you finish {task_gerund}?",
            "options": ["No, I still need another hour.", "In the filing cabinet.", "Yes, she is."],
            "answer": "A"
        },
        {
            "q": "Have you seen the review for the {event}?",
            "options": ["Not yet, is it online?", "On the second floor.", "Yes, I went there."],
            "answer": "A"
        },
        {
            "q": "Is the new {item} working well?",
            "options": ["Yes, it's much faster than the old one.", "No, thank you.", "At the department store."],
            "answer": "A"
        },
        # Choice
        {
            "q": "Should we take a taxi or catch the bus to the {place}?",
            "options": ["Yes, let's go.", "A taxi would be much faster.", "No, it's not here."],
            "answer": "B"
        },
        {
            "q": "Would you prefer coffee or tea?",
            "options": ["Yes, please.", "Either one is fine with me.", "No, thank you."],
            "answer": "B"
        }
    ]
    
    task_nouns = {
        "preparing the presentation": "presentation slides",
        "organizing the files": "annual reports",
        "booking the flight": "travel itinerary",
        "writing the report": "financial summary",
        "fixing the copier": "maintenance request",
        "sending the invitations": "guest list",
        "updating the database": "client information",
        "renewing the contract": "agreement draft",
        "checking the inventory": "stock list"
    }

    generated = []
    seen_questions = set()
    
    while len(generated) < count_needed:
        template = random.choice(wh_questions)
        dept = random.choice(departments)
        task_g = random.choice(tasks)
        task_n = task_nouns[task_g]
        event = random.choice(events)
        place = random.choice(places)
        item = random.choice(items)
        
        q_text = template["q"].format(
            dept=dept,
            task_gerund=task_g,
            task_noun=task_n,
            event=event,
            place=place,
            item=item
        )
        
        if q_text not in seen_questions:
            seen_questions.add(q_text)
            options = template["options"]
            generated.append({
                "question": q_text,
                "option_a": options[0],
                "option_b": options[1],
                "option_c": options[2],
                "answer": template["answer"]
            })
            
    return generated

def main():
    init_db_table()
    
    api_key = get_api_key()
    if not api_key:
        print("Gemini API Key not found in config.json. Will use local fallback generator for all questions.")
        api_key = None

    # Check if table already has questions
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM toeic_part2_questions")
    count = cursor.fetchone()[0]
    
    if count >= 300:
        print(f"Table already has {count} questions. Skipping automatic generation.")
        conn.close()
        return

    needed = 300 - count
    batches_needed = (needed + 9) // 10
    print(f"Current database has {count} questions. Generating {batches_needed * 10} more to reach 300...")
    
    all_questions = []
    
    if api_key:
        # Generate batches (Gemini API free tier allows 15 RPM, so we sleep 4 seconds between requests)
        for i in range(1, batches_needed + 1):
            batch = generate_questions_batch(api_key, i)
            if batch:
                all_questions.extend(batch)
            else:
                print(f"Batch {i} failed or rate limited. Will supplement with local fallback questions.")
            time.sleep(4)  # Avoid rate limits

    # Check if we need to supplement with local fallback questions
    if len(all_questions) < needed:
        still_needed = needed - len(all_questions)
        print(f"Seeding remaining {still_needed} questions using high-quality local templates...")
        fallback_questions = generate_local_fallback_questions(still_needed)
        all_questions.extend(fallback_questions)
        
    print(f"Generated {len(all_questions)} questions. Importing to SQLite...")
    
    inserted = 0
    for q in all_questions:
        try:
            question = q.get('question', '').strip()
            opt_a = q.get('option_a', '').strip()
            opt_b = q.get('option_b', '').strip()
            opt_c = q.get('option_c', '').strip()
            answer = q.get('answer', '').strip().upper()
            
            if question and opt_a and opt_b and opt_c and answer in ['A', 'B', 'C']:
                cursor.execute('''
                    INSERT INTO toeic_part2_questions (question, option_a, option_b, option_c, answer)
                    VALUES (?, ?, ?, ?, ?)
                ''', (question, opt_a, opt_b, opt_c, answer))
                inserted += 1
        except Exception as e:
            print(f"Error inserting question: {e}")
            
    conn.commit()
    conn.close()
    print(f"Successfully imported {inserted} TOEIC Part 2 questions into SQLite!")

if __name__ == '__main__':
    main()
