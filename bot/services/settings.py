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
