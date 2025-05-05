import os
import requests

def check_weather(location, date, damage_type):
    """
    Return True if historical weather at `location` on `date` matches the damage_type.
    Handles postcodes by appending ',CH' and safely returns False on any lookup failure.
    """
    key = os.getenv('OWM_API_KEY')
    if not key:
        return False

    # Geocode: allow postcode by adding Swiss country code
    try:
        resp = requests.get(
            f"http://api.openweathermap.org/geo/1.0/direct?q={location},CH&limit=1&appid={key}"
        )
        resp.raise_for_status()
        geo_data = resp.json()
        if not geo_data:
            return False
        lat, lon = geo_data[0]['lat'], geo_data[0]['lon']
    except Exception:
        return False

    # Fetch historical weather
    try:
        dt = int(date.strftime('%s'))
        weather_resp = requests.get(
            f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&dt={dt}&appid={key}"
        )
        weather_resp.raise_for_status()
        data = weather_resp.json()
    except Exception:
        return False

    # Evaluate hourly data
    for hour in data.get('hourly', []):
        # rain check
        if damage_type == 'rain_damage' and hour.get('rain', {}).get('1h', 0) > 0:
            return True
        # hail check
        if damage_type == 'hail_damage':
            for w in hour.get('weather', []):
                if w.get('main', '').lower() == 'hail':
                    return True
    return False
