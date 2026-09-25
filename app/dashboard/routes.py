from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from flask_login import login_required, current_user
from ..extensions import db
from ..models import Crop
from ..services.weather_service import get_weather
from ..services.advice_service import generate_advice
from ..services.farmer_updates import get_state_news, state_scheme_links
from ..state_data import STATES, STATE_NAMES_HI

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    crops = db.session.scalars(db.select(Crop).order_by(Crop.id)).all()
    return render_template('index.html', crops=crops, states=STATES,
                           state_names_hi=STATE_NAMES_HI,
                           farmer_state=session.get('farmer_state'))

@dashboard_bp.route('/dashboard')
@login_required
def index():
    return render_template('dashboard.html', states=STATES, state_names_hi=STATE_NAMES_HI,
                           farmer_state=current_user.state)

@dashboard_bp.route('/dashboard/state', methods=['POST'])
def set_state():
    selected_state = request.form.get('state', '').strip()
    selected_state = selected_state if selected_state in STATES else None
    if current_user.is_authenticated:
        current_user.state = selected_state
        db.session.commit()
        return redirect(url_for('dashboard.index'))
    if selected_state:
        session['farmer_state'] = selected_state
    else:
        session.pop('farmer_state', None)
    return redirect(url_for('dashboard.home'))

@dashboard_bp.route('/api/farmer-updates')
def farmer_updates():
    state = current_user.state if current_user.is_authenticated else session.get('farmer_state')
    if state not in STATES:
        state = None
    if not state:
        return jsonify({'state': None, 'news': [], 'schemes': []})
    language = (current_user.preferred_language if current_user.is_authenticated
                else session.get('language', 'en'))
    return jsonify({
        'state': state,
        'state_display': STATE_NAMES_HI.get(state, state) if language == 'hi' else state,
        'news': get_state_news(state, language),
        'schemes': state_scheme_links(state, language),
    })

@dashboard_bp.route('/api/dashboard-data')
@login_required
def dashboard_data():
    lat = request.args.get('lat', type=float) or current_user.latitude
    lon = request.args.get('lon', type=float) or current_user.longitude
    weather = get_weather(lat, lon, current_user.preferred_language) if lat is not None and lon is not None else None
    saved = [{'id': uc.id, 'crop_id': uc.crop_id, 'crop': uc.crop.name,
              'emoji': uc.crop.emoji, 'stage': uc.current_stage,
              'start_date': uc.start_date.isoformat() if uc.start_date else None}
             for uc in current_user.crops]
    if current_user.preferred_language == "hi":
        from ..translations import translate
        for item in saved:
            item["crop"] = translate(item["crop"])
            item["stage"] = translate(item["stage"])
    advice = generate_advice(weather, [uc.crop for uc in current_user.crops])
    if current_user.preferred_language == "hi":
        from ..translations import translate
        for item in advice:
            for key in ("crop", "title", "text"):
                item[key] = translate(item[key])
            item["crop"] = {"Paddy": "धान", "Rice": "चावल", "Corn / Maize": "मक्का",
                            "Potato": "आलू", "Onion": "प्याज", "Garlic": "लहसुन", "Ginger": "अदरक"}.get(item["crop"], item["crop"])
    return jsonify({'location': {'name': current_user.location_name, 'latitude': lat, 'longitude': lon},
                    'weather': weather, 'saved_crops': saved, 'advice': advice})
