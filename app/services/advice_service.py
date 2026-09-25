def generate_advice(weather, crops):
    if not weather or not weather.get("available"):
        return []

    advice = []
    temp = weather["temperature"]
    humidity = weather["humidity"]
    rain = sum(d["rain_mm"] for d in weather.get("forecast", []))

    for crop in crops:
        crop_name = crop.name.lower()
        crop_advice = []

        if rain >= 25:
            crop_advice.append({
                "crop": crop.name,
                "severity": "warning",
                "title": "Heavy rain expected",
                "text": "Avoid unnecessary irrigation and check field drainage before the rainfall."
            })
        elif rain < 3 and temp >= 30:
            crop_advice.append({
                "crop": crop.name,
                "severity": "info",
                "title": "Hot and relatively dry period",
                "text": "Check soil moisture regularly and irrigate according to crop stage and local soil conditions."
            })

        if humidity >= 80:
            crop_advice.append({
                "crop": crop.name,
                "severity": "warning",
                "title": "High humidity",
                "text": "Inspect leaves and stems regularly for fungal disease symptoms and improve airflow/drainage where possible."
            })

        if crop_name in {"paddy", "rice"} and temp >= 32:
            crop_advice.append({
                "crop": crop.name,
                "severity": "info",
                "title": "High temperature",
                "text": "Monitor soil moisture closely and avoid prolonged moisture stress, especially during sensitive growth stages."
            })

        if crop_name in {"potato"} and rain >= 20:
            crop_advice.append({
                "crop": crop.name,
                "severity": "warning",
                "title": "Potato rain-risk reminder",
                "text": "Check drainage and inspect foliage for disease symptoms after wet conditions."
            })

        advice.extend(crop_advice)

    if not advice:
        advice.append({
            "crop": "General",
            "severity": "success",
            "title": "Routine field monitoring",
            "text": "Weather conditions do not trigger a major rule in KISAN BHAI. Continue normal crop-stage monitoring."
        })
    return advice
