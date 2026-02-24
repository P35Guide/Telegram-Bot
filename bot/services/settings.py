def update_coordinates(user_id, latitude, longitude):
    return save_coordinates(user_id, latitude, longitude)


user_settings = {}

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


def get_user_settings(user_id):
    if user_id not in user_settings:
        user_settings[user_id] = {
            k: list(v) if isinstance(v, list) else v for k, v in DEFAULTS.items()
        }
    return user_settings[user_id]


def update_included_types(user_id, types):
    settings = get_user_settings(user_id)
    settings["includedTypes"] = types
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
    """Повертає завжди dict {id, name}. Для зворотної сумісності зі старими даними (str)."""
    if isinstance(item, dict) and "id" in item:
        return {"id": item["id"], "name": item.get("name") or "Без назви"}
    if isinstance(item, str):
        return {"id": item, "name": "Без назви"}
    return None


def _ensure_favorites_format(settings):
    """Приводить favoritePlaces до списку dict {id, name}. Викликати при читанні."""
    raw = settings.get("favoritePlaces") or []
    normalized = []
    for p in raw:
        n = _normalize_favorite(p)
        if n and n["id"]:
            normalized.append(n)
    settings["favoritePlaces"] = normalized


def get_favorite_places(user_id):
    """Повертає список улюблених: [{"id": str, "name": str}, ...]."""
    settings = get_user_settings(user_id)
    _ensure_favorites_format(settings)
    return settings["favoritePlaces"]


def add_favorite_place(user_id, place_id: str, name: str):
    """Додає місце в улюблені. name зберігається для показу без API."""
    favs = get_favorite_places(user_id)
    if any(p["id"] == place_id for p in favs):
        return
    favs.append({"id": place_id, "name": name})
    get_user_settings(user_id)["favoritePlaces"] = favs


def remove_favorite_place(user_id, place_id: str):
    settings = get_user_settings(user_id)
    _ensure_favorites_format(settings)
    settings["favoritePlaces"] = [p for p in settings["favoritePlaces"] if p["id"] != place_id]


def is_favorite_place(user_id, place_id: str) -> bool:
    favs = get_favorite_places(user_id)
    return any(p["id"] == place_id for p in favs)


def save_coordinates(user_id, latitude, longitude):
    settings = get_user_settings(user_id)
    settings["coordinates"] = {
        "latitude": latitude,
        "longitude": longitude,
    }
    user_settings[user_id] = settings
    return settings


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
