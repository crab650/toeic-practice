"""One-time, idempotent conversion of legacy sentence practice rows."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import uuid
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.db import get_db, init_db  # noqa: E402


def backfill(date_value=None, timezone_name='Asia/Bangkok'):
    init_db()
    local_zone = ZoneInfo(timezone_name)
    conn = get_db()
    try:
        sql = '''
            SELECT ph.*, s.english, s.chinese, u.language
            FROM practice_history ph
            JOIN sentences s ON s.id = ph.sentence_id
            JOIN units u ON u.id = s.unit_id
            LEFT JOIN practice_events pe ON pe.legacy_history_id = ph.id
            WHERE pe.id IS NULL
        '''
        params = []
        if date_value:
            sql += ' AND ph.practice_date = ?'
            params.append(date_value)
        sql += ' ORDER BY ph.id'
        rows = conn.execute(sql, params).fetchall()
        converted = 0
        for row in rows:
            # SQLite CURRENT_TIMESTAMP is UTC and legacy rows contain no offset.
            occurred_utc = datetime.strptime(row['created_at'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            occurred_local = occurred_utc.astimezone(local_zone)
            language = (row['language'] or 'en').lower()
            conn.execute('''
                INSERT INTO practice_events (
                    event_id, legacy_history_id, device_id, sentence_id, language,
                    exercise_type, sentence_text, translation_text, user_answer,
                    is_correct, audio_play_count, revealed_answer, occurred_at,
                    timezone, sync_status, created_at
                )
                SELECT ?, ?, device_id, ?, ?, 'spelling', ?, ?, NULL, ?, ?, ?, ?, ?,
                       'pending', ?
                FROM app_installation WHERE id = 1
            ''', (
                str(uuid.uuid4()), row['id'], f'{language}-sentence-{row["sentence_id"]}',
                language, row['english'], row['chinese'], int(row['is_correct']),
                int(row['audio_play_count'] or 0), int(row['revealed_answer'] or 0),
                occurred_local.isoformat(), timezone_name, occurred_local.isoformat(),
            ))
            converted += 1
        conn.commit()
        return converted
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--date', help='Legacy practice_date in YYYY-MM-DD format')
    parser.add_argument('--timezone', default='Asia/Bangkok')
    args = parser.parse_args()
    print(f'Converted {backfill(args.date, args.timezone)} legacy practice record(s).')
