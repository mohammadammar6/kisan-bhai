import redis
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'
csrf = CSRFProtect()
redis_client = None

def init_redis(app):
    global redis_client
    redis_client = redis.from_url(
        app.config['REDIS_URL'], decode_responses=True,
        socket_connect_timeout=3, socket_timeout=3
    )
    try:
        redis_client.ping()
        app.logger.info('Redis connection: OK')
    except redis.exceptions.RedisError as exc:
        app.logger.warning('Redis unavailable at %s: %s', app.config['REDIS_URL'], exc)
        redis_client = None

def get_redis():
    return redis_client

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return db.session.get(User, int(user_id))
