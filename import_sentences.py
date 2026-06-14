import urllib.request
import sqlite3
import os
import re

DATABASE = 'trainer.db'
# Raw URL of the TSV file containing ID, Simplified, Traditional, Pinyin, English
TSV_URL = 'https://raw.githubusercontent.com/krmanik/chinese-example-sentences/main/Chinese%20Example%20Sentences/cmn_sen_db_2.tsv'

def download_tsv():
    print(f"Downloading parallel corpus from: {TSV_URL} ...")
    try:
        req = urllib.request.Request(TSV_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = response.read().decode('utf-8')
            return data
    except Exception as e:
        print(f"Failed to download corpus: {e}")
        return None

def import_sentences(tsv_data):
    if not tsv_data:
        print("No TSV data to import.")
        return

    print("Parsing sentences...")
    lines = tsv_data.strip().split('\n')
    
    valid_sentences = []
    
    for line in lines:
        parts = line.split('\t')
        if len(parts) >= 5:
            traditional = parts[2].strip()
            english = parts[4].strip()
            
            # Simple sanitization
            if not traditional or not english:
                continue
                
            # Filter sentences for spelling training:
            # - English should be between 4 and 10 words
            # - No weird characters or extremely long symbols
            words = english.split()
            if 4 <= len(words) <= 10:
                # Avoid sentence if it contains bracketed info or weird markers
                if '[' in english or ']' in english or '(' in english or ')' in english:
                    continue
                valid_sentences.append({
                    'english': english,
                    'chinese': traditional
                })
    
    total_found = len(valid_sentences)
    print(f"Found {total_found} sentences matching spelling training criteria (4-10 words).")
    
    # We want to select 3,000 sentences
    target_count = min(3000, total_found)
    selected_sentences = valid_sentences[:target_count]
    
    # Group into Units of 50 sentences each
    sentences_per_unit = 50
    unit_count = (target_count + sentences_per_unit - 1) // sentences_per_unit
    
    print(f"Connecting to database to import {target_count} sentences in {unit_count} units...")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    inserted_sentences = 0
    
    # We will create new units starting from "Tatoeba 特訓 Unit 1"
    for u_idx in range(unit_count):
        unit_name = f"Tatoeba 特訓 Unit {u_idx + 1}"
        
        # Check if unit already exists
        cursor.execute("SELECT id FROM units WHERE name = ?", (unit_name,))
        row = cursor.fetchone()
        if row:
            unit_id = row[0]
            # Clear existing sentences in this unit to avoid duplicates
            cursor.execute("DELETE FROM sentences WHERE unit_id = ?", (unit_id,))
        else:
            cursor.execute("INSERT INTO units (name) VALUES (?)", (unit_name,))
            unit_id = cursor.lastrowid
            
        start_idx = u_idx * sentences_per_unit
        end_idx = min(start_idx + sentences_per_unit, target_count)
        
        for s_idx in range(start_idx, end_idx):
            item = selected_sentences[s_idx]
            cursor.execute(
                "INSERT INTO sentences (unit_id, english, chinese) VALUES (?, ?, ?)",
                (unit_id, item['english'], item['chinese'])
            )
            inserted_sentences += 1
            
    conn.commit()
    conn.close()
    print(f"Successfully imported {inserted_sentences} sentences across {unit_count} units into 'trainer.db'!")

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        print("Database 'trainer.db' not found. Please run Flask app first to initialize database.")
        exit(1)
        
    tsv_content = download_tsv()
    import_sentences(tsv_content)
