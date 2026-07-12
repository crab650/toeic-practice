import json
from datetime import datetime, timezone
from urllib import error, request

from ..config import get_config, get_platform_token
from ..db import get_db


RETRYABLE_HTTP_CODES = {408, 425, 429, 500, 502, 503, 504}


def _request_json(method, url, token, payload=None, timeout=20):
    body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = request.Request(url, data=body, method=method)
    req.add_header('Accept', 'application/json')
    req.add_header('Authorization', f'Bearer {token}')
    if body is not None:
        req.add_header('Content-Type', 'application/json; charset=utf-8')
    try:
        with request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode('utf-8')
            return response.status, json.loads(raw or '{}')
    except error.HTTPError as exc:
        raw = exc.read().decode('utf-8', errors='replace')
        try:
            data = json.loads(raw or '{}')
        except json.JSONDecodeError:
            data = {'error': f'Platform returned HTTP {exc.code}'}
        return exc.code, data


def get_remote_identity(base_url, token):
    status, data = _request_json('GET', f'{base_url}/api/v1/auth/me', token)
    identity = data.get('data', data) if isinstance(data, dict) else {}
    if status != 200 or not identity.get('user_id'):
        raise ValueError(data.get('error') or f'Unable to verify platform account (HTTP {status})')
    return identity


def _event_payload(row):
    return {
        'event_id': row['event_id'],
        'sentence_id': row['sentence_id'],
        'language': row['language'],
        'exercise_type': row['exercise_type'],
        'sentence_text': row['sentence_text'],
        'translation_text': row['translation_text'],
        'user_answer': row['user_answer'],
        'is_correct': bool(row['is_correct']),
        'audio_play_count': row['audio_play_count'],
        'revealed_answer': bool(row['revealed_answer']),
        'occurred_at': row['occurred_at'],
        'timezone': row['timezone'],
    }


def sync_pending_events():
    config = get_config()
    base_url = config.get('platform_base_url', '').rstrip('/')
    token, _ = get_platform_token()
    if not base_url:
        raise ValueError('Learning platform Base URL is not configured.')
    if not token:
        raise ValueError('Learning platform Token is not configured.')

    identity = get_remote_identity(base_url, token)
    user_id = str(identity['user_id'])
    conn = get_db()
    try:
        foreign_pending = conn.execute(
            "SELECT COUNT(*) FROM practice_events WHERE sync_status = 'pending' AND platform_user_id IS NOT NULL AND platform_user_id <> ?",
            (user_id,),
        ).fetchone()[0]
        if foreign_pending:
            raise ValueError('Pending records belong to another platform account; sync or discard them before switching accounts.')

        conn.execute(
            "UPDATE practice_events SET platform_user_id = ? WHERE sync_status = 'pending' AND platform_user_id IS NULL",
            (user_id,),
        )
        conn.commit()

        totals = {'created': 0, 'duplicate': 0, 'conflict': 0, 'rejected': 0}
        while True:
            rows = conn.execute(
                "SELECT * FROM practice_events WHERE sync_status = 'pending' AND platform_user_id = ? ORDER BY created_at, id LIMIT 100",
                (user_id,),
            ).fetchall()
            if not rows:
                break
            device_id = rows[0]['device_id']
            event_ids = [row['event_id'] for row in rows]
            placeholders = ','.join('?' for _ in event_ids)
            conn.execute(
                f"UPDATE practice_events SET sync_attempts=sync_attempts+1 WHERE event_id IN ({placeholders})",
                event_ids,
            )
            conn.commit()
            try:
                status, response = _request_json(
                    'POST', f'{base_url}/api/v1/study/practice-logs', token,
                    {'device_id': device_id, 'events': [_event_payload(row) for row in rows]},
                )
            except Exception as exc:
                conn.execute(
                    f"UPDATE practice_events SET last_sync_error=? WHERE event_id IN ({placeholders})",
                    (str(exc), *event_ids),
                )
                conn.commit()
                raise
            if status != 200:
                message = response.get('error') or f'Platform returned HTTP {status}'
                conn.execute(
                    f"UPDATE practice_events SET last_sync_error=? WHERE event_id IN ({placeholders})",
                    (message, *event_ids),
                )
                conn.commit()
                if status not in RETRYABLE_HTTP_CODES:
                    raise ValueError(message)
                raise RuntimeError(message)

            by_id = {row['event_id']: row for row in rows}
            returned_ids = set()
            now = datetime.now(timezone.utc).isoformat()
            for result in response.get('data', {}).get('results', []):
                event_id = result.get('event_id')
                if event_id not in by_id:
                    continue
                returned_ids.add(event_id)
                item_status = result.get('status')
                if item_status in ('created', 'duplicate'):
                    conn.execute(
                        "UPDATE practice_events SET sync_status='synced', last_sync_error=NULL, platform_log_id=?, synced_at=? WHERE event_id=?",
                        (str(result.get('log_id', '')), now, event_id),
                    )
                    totals[item_status] += 1
                elif item_status in ('rejected', 'conflict'):
                    message = json.dumps(result.get('errors') or result.get('error') or item_status, ensure_ascii=False)
                    conn.execute(
                        "UPDATE practice_events SET sync_status='failed', last_sync_error=? WHERE event_id=?",
                        (message, event_id),
                    )
                    totals[item_status] += 1
                else:
                    conn.rollback()
                    raise RuntimeError(f'Platform returned unknown event status: {item_status!r}')
            missing = set(by_id) - returned_ids
            if missing:
                conn.rollback()
                raise RuntimeError('Platform response omitted one or more event results; batch left pending for safe retry.')
            conn.commit()
        return {'account': identity, **totals}
    finally:
        conn.close()
