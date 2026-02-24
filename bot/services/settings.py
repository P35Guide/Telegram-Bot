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


def add_favorite_place(user_id, place_id):
    settings = get_user_settings(user_id)
    if place_id not in settings["favoritePlaces"]:
        settings["favoritePlaces"].append(place_id)
    return settings


def remove_favorite_place(user_id, place_id):
    settings = get_user_settings(user_id)
    if place_id in settings["favoritePlaces"]:
        settings["favoritePlaces"].remove(place_id)
    return settings


def toggle_favorite_place(user_id, place_id):
    settings = get_user_settings(user_id)
    if place_id in settings["favoritePlaces"]:
        remove_favorite_place(user_id, place_id)
    else:
        add_favorite_place(user_id, place_id)
    return settings


def is_favorite_place(user_id, place_id):
    settings = get_user_settings(user_id)
    return place_id in settings["favoritePlaces"]


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
