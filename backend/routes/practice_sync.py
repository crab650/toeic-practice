from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
import re
import uuid

from flask import Blueprint, jsonify, request

from ..config import get_config, get_platform_token
from ..db import get_db
from ..services.practice_sync import sync_pending_events


practice_sync_bp = Blueprint('practice_sync', __name__)
EXERCISE_TYPES = {'spelling', 'scramble', 'toeic_part5', 'toeic_part2'}
ID_PATTERN = re.compile(r'^[A-Za-z0-9_.:-]{1,120}$')


@practice_sync_bp.route('/api/practice/events', methods=['POST'])
def create_practice_event():
    data = request.get_json(silent=True) or {}
    required = ('sentence_id', 'language', 'exercise_type', 'sentence_text', 'is_correct', 'occurred_at', 'timezone')
    missing = [key for key in required if key not in data]
    if missing:
        return jsonify({'error': f'Missing fields: {", ".join(missing)}'}), 400
    sentence_id = str(data['sentence_id'])
    if not ID_PATTERN.fullmatch(sentence_id):
        return jsonify({'error': 'Invalid sentence_id'}), 400
    if data['exercise_type'] not in EXERCISE_TYPES:
        return jsonify({'error': 'Invalid exercise_type'}), 400
    if data['language'] not in {'en', 'vi'}:
        return jsonify({'error': 'Invalid language'}), 400
    if type(data['is_correct']) is not bool or type(data.get('revealed_answer', False)) is not bool:
        return jsonify({'error': 'Boolean fields must be JSON booleans'}), 400
    audio_count = data.get('audio_play_count', 0)
    if type(audio_count) is not int or not 0 <= audio_count <= 10000:
        return jsonify({'error': 'audio_play_count must be an integer from 0 to 10000'}), 400
    try:
        occurred = datetime.fromisoformat(data['occurred_at'])
        if occurred.utcoffset() is None:
            raise ValueError
        ZoneInfo(data['timezone'])
    except (ValueError, TypeError, ZoneInfoNotFoundError):
        return jsonify({'error': 'occurred_at and timezone are invalid'}), 400
    for key in ('sentence_text', 'translation_text', 'user_answer'):
        value = data.get(key)
        if value is not None and (not isinstance(value, str) or len(value) > 10000):
            return jsonify({'error': f'{key} must be a string of at most 10000 characters'}), 400
    if not data['sentence_text']:
        return jsonify({'error': 'sentence_text cannot be empty'}), 400

    conn = get_db()
    try:
        device_id = conn.execute('SELECT device_id FROM app_installation WHERE id=1').fetchone()[0]
        event_id = str(uuid.uuid4())
        created_at = datetime.now().astimezone().isoformat()
        conn.execute('''
            INSERT INTO practice_events (
                event_id, device_id, sentence_id, language, exercise_type,
                sentence_text, translation_text, user_answer, is_correct,
                audio_play_count, revealed_answer, occurred_at, timezone, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event_id, device_id, sentence_id, data['language'], data['exercise_type'],
            data['sentence_text'], data.get('translation_text'), data.get('user_answer'),
            int(data['is_correct']), audio_count, int(data.get('revealed_answer', False)),
            data['occurred_at'], data['timezone'], created_at,
        ))
        conn.commit()
        return jsonify({'success': True, 'event_id': event_id}), 201
    finally:
        conn.close()


@practice_sync_bp.route('/api/practice/sync/status', methods=['GET'])
def sync_status():
    conn = get_db()
    try:
        counts = dict(conn.execute('SELECT sync_status, COUNT(*) FROM practice_events GROUP BY sync_status').fetchall())
        last = conn.execute("SELECT MAX(synced_at) FROM practice_events WHERE sync_status='synced'").fetchone()[0]
        device_id = conn.execute('SELECT device_id FROM app_installation WHERE id=1').fetchone()[0]
    finally:
        conn.close()
    config = get_config()
    token, source = get_platform_token()
    return jsonify({
        'pending': counts.get('pending', 0), 'synced': counts.get('synced', 0),
        'failed': counts.get('failed', 0), 'last_synced_at': last,
        'device_id': device_id, 'base_url': config.get('platform_base_url', ''),
        'token_set': bool(token), 'token_source': source,
    })


@practice_sync_bp.route('/api/practice/sync', methods=['POST'])
def run_sync():
    try:
        return jsonify({'success': True, 'data': sync_pending_events()})
    except ValueError as exc:
        return jsonify({'success': False, 'error': str(exc)}), 400
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 503
