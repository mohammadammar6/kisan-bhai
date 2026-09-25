from flask import Blueprint, request, jsonify
from flask_login import login_required
from ..services.weather_service import get_weather

weather_bp = Blueprint("weather", __name__)

@weather_bp.route("/weather")
@login_required
def weather():
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)
    if lat is None or lon is None:
        return jsonify({"error": "lat and lon are required"}), 400
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return jsonify({"error": "Invalid coordinates"}), 400
    return jsonify(get_weather(lat, lon))
