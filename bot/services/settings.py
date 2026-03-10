import aiohttp
from bot.services.api_client import get_places
from bot.utils.logger import logger
from bot.model.types_dict import SearchTypes
import re
import json
import aiohttp
from bot.services.api_client import get_places
from bot.utils.logger import logger
import re
import json
DEFAULTS = {
    "language": "uk",
    "radius": 1000,
    "coordinates": None,
    "includedTypes": [],
    "excludedTypes": [],
    "maxResultCount": 20,
    "rankPreference": "POPULARITY",
    "openNow": False,
    "favoritePlaces": [],
}

user_settings = {
}


def _parse_coordinates(coord):
    """Повертає None якщо coordinates порожні або нульові."""
    if not coord or not isinstance(coord, dict):
        return None
    lat = coord.get("latitude")
    lon = coord.get("longitude")
    if lat is None or lon is None:
        return None
    try:
        if float(lat) == 0 and float(lon) == 0:
            return None
    except (TypeError, ValueError):
        return None
    return {"latitude": float(lat), "longitude": float(lon)}


def apply_user_data_from_api(user_id: int, api_user: dict):
    """
    Заповнює user_settings з відповіді API (get_user).
    api_user: { "settings": {...}, "favoritePlaces": [...] }
    """
    server_settings = api_user.get("settings") or {}
    server_favorites = api_user.get("favoritePlaces") or []

    # Отримуємо мову з сервера, якщо вона є
    server_language = server_settings.get("language")
    if server_language:
        language = server_language
    else:
        language = DEFAULTS["language"]

    merged = {
        "language": language,
        "radius": server_settings.get("radius") or DEFAULTS["radius"],
        "coordinates": _parse_coordinates(server_settings.get("coordinates")),
        "includedTypes": list(server_settings.get("includedTypes") or []),
        "excludedTypes": list(server_settings.get("excludedTypes") or []),
        "maxResultCount": server_settings.get("maxResultCount") or DEFAULTS["maxResultCount"],
        "rankPreference": server_settings.get("rankPreference") or DEFAULTS["rankPreference"],
        "openNow": server_settings.get("openNow") if server_settings.get("openNow") is not None else DEFAULTS["openNow"],
        "favoritePlaces": [],
    }
    for p in server_favorites:
        n = _normalize_favorite(p)
        if n and n.get("id"):
            merged["favoritePlaces"].append(n)

    user_settings[user_id] = merged
    
    # Також встановлюємо мову в i18n.user_languages
    from bot.utils.localization import i18n
    i18n.set_user_language(user_id, language)
    
    return merged


def get_user_settings(user_id):
    settings = user_settings.get(user_id)
    if settings is None:
        settings = {
            k: list(v) if isinstance(v, list) else v for k, v in DEFAULTS.items()
        }
        user_settings[user_id] = settings
    else:
        for key, value in DEFAULTS.items():
            if key not in settings:
                settings[key] = list(value) if isinstance(value, list) else value
    return settings


# Поля налаштувань для POST /api/telegram-user/{id}/settings (контракт API)
SETTINGS_API_KEYS = (
    "language", "radius", "coordinates", "includedTypes", "excludedTypes",
    "maxResultCount", "rankPreference", "openNow",
)


def _coordinates_for_api(coord):
    """Повертає coordinates для API: None або { latitude, longitude }."""
    if not coord or not isinstance(coord, dict):
        return None
    try:
        lat = float(coord.get("latitude", 0))
        lon = float(coord.get("longitude", 0))
        return {"latitude": lat, "longitude": lon}
    except (TypeError, ValueError):
        return None


def get_settings_payload_for_api(user_id):
    """Словник для POST /api/telegram-user/{id}/settings: id, language, radius, coordinates, ..."""
    s = get_user_settings(user_id)
    payload = {"id": user_id}
    for key in SETTINGS_API_KEYS:
        val = s.get(key)
        if key == "coordinates":
            payload[key] = _coordinates_for_api(val)
        elif isinstance(val, list):
            payload[key] = list(val)
        else:
            payload[key] = val
    return payload


# --- Основні функції для категорій (Чекбокси та Текст) ---

def update_included_types(user_id, types):
    settings = get_user_settings(user_id)
    settings["includedTypes"] = types
    user_settings[user_id] = settings
    return settings


def toggle_included_type(user_id, type_code):
    """Додає категорію, якщо її немає, або видаляє, якщо є (для кнопок-чекбоксів)"""
    settings = get_user_settings(user_id)
    included = settings.get("includedTypes", [])

    if type_code in included:
        included.remove(type_code)
    else:
        included.append(type_code)

    settings["includedTypes"] = included
    user_settings[user_id] = settings
    return settings


def add_included_type(user_id, type_code):
    """Тільки додає категорію (для ручного введення тексту)"""
    settings = get_user_settings(user_id)
    included = settings.get("includedTypes", [])

    if type_code not in included:
        included.append(type_code)
        settings["includedTypes"] = included
        user_settings[user_id] = settings
    return settings

def decode_included_types(user_id):
    mood_types = SearchTypes.mood_types 
    settings = get_user_settings(user_id)
    types = settings.get("includedTypes", [])
    new_types = []
    at_night = False
    for type in types:
        if(type =="Loud Company 🍻"):
            for intype in mood_types.get("Loud Company 🍻"):
                if intype not in new_types:
                    new_types.append(intype)
        elif(type == "Date Night 🌙"):
            at_night = True
            for intype in mood_types.get("Date Night 🌙"):
                if intype not in new_types:
                    new_types.append(intype)
        elif(type == "Need to Work 💻"):
            for intype in mood_types.get("Need to Work 💻"):
                if intype not in new_types:
                    new_types.append(intype)
        else:
            if type not in new_types:
                    new_types.append(type)
    
    settings["includedTypes"] = new_types
    user_settings[user_id] = settings
    return at_night

def incode_included_types(user_id, at_night):
    mood_types = SearchTypes.mood_types 
    settings = get_user_settings(user_id)
    types = settings.get("includedTypes", [])
    new_types = []

    loud_company = all(type in types for type in mood_types.get("Loud Company 🍻"))
    work = all(type in types for type in mood_types.get("Need to Work 💻"))
    night = all(type in types for type in mood_types.get("Date Night 🌙"))

    if(loud_company == True):
        new_types.append('Loud Company 🍻')
    if(night == True):
        if(at_night == True):
            new_types.append("Date Night 🌙")
    if(work == True):
        if(at_night != True):
            new_types.append("Need to Work 💻")

    included_types = []

    if(len(new_types)>0):
        temp_list = []
        for type in new_types:
            temp_list.extend(mood_types.get(type))
        included_types = dict.fromkeys(temp_list)

    for type in types:
        if type in included_types:
            continue
        if type not in new_types:
            new_types.append(type)
    
    settings["includedTypes"] = new_types
    user_settings[user_id] = settings
        


def sort_by_night_places(places):
    new_places = []
    template = r"(\d{1,2}):(\d{2})(?:\s*(AM|PM))?"
    logger.info("started sorting")
    if(places == None):
        logger.info("we have places as None")
        return []
    logger.info(f"got weekdayDescriptions")
    for place in places:
        texts = place.get("weekdayDescriptions", [])
        logger.info(f"place name: {place.get('displayName')}")
        if(texts == None or len(texts)==0):
            logger.info("bad info")
            continue
        for text in texts:

            if re.search(template,text)  is None:
                logger.info("time is out of us controll")
                continue

            times_start_end =  re.findall(template,text)

            time_end = times_start_end[-1]

            hours = float(time_end[0])
            minutes = float(time_end[1])/100

            close_in = hours+minutes
            logger.info(f"close in {close_in}")

            time_type = time_end[2]

            if(time_type == "PM"):
                close_in = close_in+12
            
            if(close_in >= 22 or close_in<8):
                new_places.append(place)
                logger.info(f"added place")
                break
            
    return new_places

def add_included_list_type(user_id, type_label):
    mood_types = SearchTypes.mood_types
    settings = get_user_settings(user_id)
    place_list = mood_types.get(type_label, [])
    included = settings.get("includedTypes", [])
    included.clear()
    
    for place_type in place_list:
        if place_type not in included:
            included.append(place_type)
    
    settings["includedTypes"] = included
    user_settings[user_id] = settings
            



def clear_included_types(user_id):
    """Очищає список категорій"""
    return update_included_types(user_id, [])


def remove_included_type(user_id, type_code):
    """Видаляє конкретну категорію"""
    settings = get_user_settings(user_id)
    included = settings.get("includedTypes", [])

    if type_code in included:
        included.remove(type_code)
        settings["includedTypes"] = included
        user_settings[user_id] = settings
    return settings


def update_excluded_types(user_id, types):
    settings = get_user_settings(user_id)
    settings["excludedTypes"] = types
    user_settings[user_id] = settings
    return settings


def update_max_result_count(user_id, count):
    settings = get_user_settings(user_id)
    settings["maxResultCount"] = count
    user_settings[user_id] = settings
    return settings


def update_rank_preference(user_id, preference):
    settings = get_user_settings(user_id)
    settings["rankPreference"] = preference
    user_settings[user_id] = settings
    return settings


def update_open_now(user_id, open_now):
    settings = get_user_settings(user_id)
    settings["openNow"] = open_now
    user_settings[user_id] = settings
    return settings


def _normalize_favorite(item):
    if isinstance(item, dict) and "id" in item:
        return {"id": item["id"], "name": item.get("name") or "Без назви"}
    if isinstance(item, str):
        return {"id": item, "name": "Без назви"}
    return None


def _ensure_favorites_format(settings):
    raw = settings.get("favoritePlaces") or []
    normalized = []
    for place in raw:
        normalized_item = _normalize_favorite(place)
        if normalized_item and normalized_item["id"]:
            normalized.append(normalized_item)
    settings["favoritePlaces"] = normalized


def get_favorite_places(user_id):
    settings = get_user_settings(user_id)
    _ensure_favorites_format(settings)
    return settings["favoritePlaces"]


def add_favorite_place(user_id, place_id: str, name: str):
    favs = get_favorite_places(user_id)
    if any(place["id"] == place_id for place in favs):
        return
    favs.append({"id": place_id, "name": name})
    get_user_settings(user_id)["favoritePlaces"] = favs


def remove_favorite_place(user_id, place_id: str):
    settings = get_user_settings(user_id)
    _ensure_favorites_format(settings)
    settings["favoritePlaces"] = [
        place for place in settings["favoritePlaces"] if place["id"] != place_id
    ]


def is_favorite_place(user_id, place_id: str) -> bool:
    favs = get_favorite_places(user_id)
    return any(place["id"] == place_id for place in favs)


def save_coordinates(user_id, latitude, longitude):
    settings = get_user_settings(user_id)
    settings["coordinates"] = {
        "latitude": latitude,
        "longitude": longitude,
    }
    user_settings[user_id] = settings
    return settings


def update_coordinates(user_id, latitude, longitude):
    return save_coordinates(user_id, latitude, longitude)


def get_coordinates(user_id):
    settings = get_user_settings(user_id)
    return settings.get("coordinates")


def update_language(user_id, language):
    settings = get_user_settings(user_id)
    settings["language"] = language
    user_settings[user_id] = settings
    return settings


def update_radius(user_id, radius):
    settings = get_user_settings(user_id)
    settings["radius"] = radius
    user_settings[user_id] = settings
    return settings


def update_mood(user_id: int, mood: str):
    """Update user's mood setting and populate includedTypes accordingly."""
    settings = get_user_settings(user_id)
    settings["mood"] = mood
    # Clear manual includedTypes so mood types take effect
    settings["includedTypes"] = []
    if mood:
        mood_label = SearchTypes.mood_code_map.get(mood)
        if mood_label:
            settings["includedTypes"] = list(SearchTypes.mood_types.get(mood_label, []))
    user_settings[user_id] = settings
