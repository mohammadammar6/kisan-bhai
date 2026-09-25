import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')
    MYSQL_USER = os.getenv('MYSQL_USER', 'kisan')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'Kisan@12345')
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'kisan_bhai')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f'mysql+pymysql://{quote_plus(MYSQL_USER)}:{quote_plus(MYSQL_PASSWORD)}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
    WEATHER_CACHE_SECONDS = int(os.getenv('WEATHER_CACHE_SECONDS', '900'))
