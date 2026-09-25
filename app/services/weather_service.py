import hashlib
import json
import requests
from flask import current_app
from ..extensions import get_redis

def _cache_key(lat, lon, language):
    raw = f'{round(lat,4)}:{round(lon,4)}:{language}'
    return 'kisan:weather:' + hashlib.sha256(raw.encode()).hexdigest()

def get_weather(lat, lon, language="en"):
    redis_client = get_redis()
    language = "hi" if language == "hi" else "en"
    key = _cache_key(lat, lon, language)
    if redis_client:
        try:
            cached = redis_client.get(key)
            if cached:
                data = json.loads(cached)
                data['cached'] = True
                return data
        except Exception as exc:
            current_app.logger.warning('Redis read failed: %s', exc)

    api_key = current_app.config.get('OPENWEATHER_API_KEY', '').strip()
    if not api_key:
        message = 'OPENWEATHER_API_KEY is not configured in .env.'
        if language == 'hi':
            message = '.env में OPENWEATHER_API_KEY सेट नहीं है।'
        return {'available': False, 'cached': False,
                'message': message}

    params = {'lat': lat, 'lon': lon, 'appid': api_key, 'units': 'metric', 'lang': language}
    base = 'https://api.openweathermap.org/data/2.5'
    try:
        c_resp = requests.get(f'{base}/weather', params=params, timeout=10)
        c_resp.raise_for_status()
        f_resp = requests.get(f'{base}/forecast', params=params, timeout=10)
        f_resp.raise_for_status()
        c, f = c_resp.json(), f_resp.json()

        days = {}
        for item in f.get('list', []):
            day = item['dt_txt'].split(' ')[0]
            e = days.setdefault(day, {'temps': [], 'rain': 0.0, 'description': item['weather'][0]['description']})
            e['temps'].append(item['main']['temp'])
            e['rain'] += item.get('rain', {}).get('3h', 0) or 0
        forecast = []
        for day, e in list(days.items())[:5]:
            forecast.append({'date': day, 'min': round(min(e['temps']),1),
                             'max': round(max(e['temps']),1), 'rain_mm': round(e['rain'],1),
                             'description': e['description'].title()})
        data = {'available': True, 'cached': False, 'city': c.get('name'),
                'country': c.get('sys',{}).get('country'),
                'temperature': round(c['main']['temp'],1),
                'feels_like': round(c['main']['feels_like'],1),
                'humidity': c['main']['humidity'], 'wind_speed': c.get('wind',{}).get('speed',0),
                'description': c['weather'][0]['description'].title(),
                'icon': c['weather'][0]['icon'], 'rain_1h': c.get('rain',{}).get('1h',0),
                'forecast': forecast}
        if redis_client:
            try:
                redis_client.setex(key, current_app.config.get('WEATHER_CACHE_SECONDS',900), json.dumps(data))
            except Exception as exc:
                current_app.logger.warning('Redis write failed: %s', exc)
        return data
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 'unknown'
        message = (f'Weather API returned HTTP {status}. Check your API key.' if language == 'en'
                   else f'मौसम सेवा ने HTTP {status} त्रुटि दी। API कुंजी जाँचें।')
        return {'available': False, 'cached': False,
                'message': message}
    except requests.RequestException:
        message = ('Weather service connection error.' if language == 'en'
                   else 'मौसम सेवा से संपर्क नहीं हो सका।')
        return {'available': False, 'cached': False,
                'message': message}
