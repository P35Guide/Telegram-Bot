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

user_settings = {}


def save_user_settings(user_id, settings):
    user_settings[user_id] = settings
    return settings


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
    mood_types:dict = {
        "Loud Company 🍻":list(("stadium","dance_hall","karaoke","bar","night_club","comedy_club","live_music_venue","event_venue")),
        "Breakfast at 2 PM 🥞": list(("restaurant","cafe","fast_food_restaurant","bakery","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant","steak_house")),
        "Date Night 🌙": list(("restaurant","cafe","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant")),
        "Need to Work 💻":list(("restaurant","cafe","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant"))
    } 
    settings = get_user_settings(user_id)
    types = settings.get("includedTypes", [])
    new_types = []
    at_night = False
    for type in types:
        if(type =="Loud Company 🍻"):
            for intype in mood_types.get("Loud Company 🍻"):
                if intype not in new_types:
                    new_types.append(intype)
        elif (type == "Breakfast at 2 PM 🥞"):
            for intype in mood_types.get("Breakfast at 2 PM 🥞"):
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

def incode_included_types(user_id,at_night):
    mood_types:dict = {
        "Loud Company 🍻":list(("stadium","dance_hall","karaoke","bar","night_club","comedy_club","live_music_venue","event_venue")),
        "Breakfast at 2 PM 🥞": list(("restaurant","cafe","fast_food_restaurant","bakery","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant","steak_house")),
        "Date Night 🌙": list(("restaurant","cafe","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant")),
        "Need to Work 💻":list(("restaurant","cafe","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant"))
    } 
    settings = get_user_settings(user_id)
    types = settings.get("includedTypes", [])
    new_types = []

    loud_company = all(type in types for type in mood_types.get("Loud Company 🍻"))
    breakfest = all(type in types for type in mood_types.get("Breakfast at 2 PM 🥞"))
    work = all(type in types for type in mood_types.get("Need to Work 💻"))
    night = all(type in types for type in mood_types.get("Date Night 🌙"))

    if(loud_company == True):
        new_types.append('Loud Company 🍻')
    if(breakfest == True):
        new_types.append('Breakfast at 2 PM 🥞')
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

def  add_included_list_type(user_id,type_labal):
    mood_types:dict = {
        "Loud Company 🍻":list(("stadium","dance_hall","karaoke","bar","night_club","comedy_club","live_music_venue","event_venue")),
        "Breakfast at 2 PM 🥞": list(("restaurant","cafe","food","fast_food_restaurant","bakery","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant","steak_house")),
        "Date Night 🌙": False,
        "Need to Work 💻":True
    } 
    settings = get_user_settings(user_id)
    code = mood_types.get(type_labal)
    included = settings.get("includedTypes", [])
    included.clear()
    if(code == True):
        place_list = {"restaurant","cafe","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant"}
        for type in place_list:
            if type not in included:
                included.append(type)
                settings["includedTypes"] = included
                user_settings[user_id] = settings
        
        return
    elif(code == False):
        place_list = {"restaurant","cafe","pizza_restaurant","japanese_restaurant","chinese_restaurant","mexican_restaurant"}

        for type in place_list:
            if type not in included:
                included.append(type)
                settings["includedTypes"] = included
                user_settings[user_id] = settings

    else:
        for type in code:
            if type not in included:
                included.append(type)
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
