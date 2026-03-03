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

    merged = {
        "language": server_settings.get("language") or DEFAULTS["language"],
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
    payload = {"id": 0}
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
