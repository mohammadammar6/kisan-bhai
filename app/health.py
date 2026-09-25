from flask import Blueprint, jsonify
from sqlalchemy import text
from .extensions import db, get_redis

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health():
    result = {'app': 'ok', 'mysql': 'unknown', 'redis': 'unknown'}
    try:
        db.session.execute(text('SELECT 1'))
        result['mysql'] = 'ok'
    except Exception as exc:
        result['mysql'] = f'error: {exc}'
    r = get_redis()
    if r:
        try:
            r.ping()
            result['redis'] = 'ok'
        except Exception as exc:
            result['redis'] = f'error: {exc}'
    else:
        result['redis'] = 'unavailable'
    return jsonify(result), (200 if result['mysql'] == 'ok' else 503)
