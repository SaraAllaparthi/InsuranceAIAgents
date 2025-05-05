import os, requests

def check_weather(location, date, damage_type):
    key = os.getenv('OWM_API_KEY')
    geo = requests.get(
       f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={key}"
    ).json()[0]
    lat, lon = geo['lat'], geo['lon']
    dt = int(date.strftime('%s'))
    res = requests.get(
      f"https://api.openweathermap.org/data/2.5/onecall/timemachine?lat={lat}&lon={lon}&dt={dt}&appid={key}"
    ).json()
    for h in res.get('hourly', []):
        if damage_type == 'rain_damage' and h.get('rain', {}).get('1h', 0) > 0:
            return True
    return False
