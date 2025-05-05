def evaluate_claim(damage_info, weather_ok):
    if damage_info['type'] == 'rain_damage' and weather_ok:
        return True, ""
    return False, "No matching weather event found"
