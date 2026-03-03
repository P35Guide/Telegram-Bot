import json
import aiohttp

from bot.config import API_BASE_URL, PHOTO_MAX_HEIGHT, PHOTO_MAX_WIDTH
from bot.utils.logger import logger

# --- Допоміжні функції для API ---


async def _parse_json_response(response) -> dict:
    """Читає тіло відповіді при status 200; порожнє або не-JSON повертає {}."""
    text = await response.text()
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


# --- API telegram-user (користувач, налаштування, улюблені) ---


async def get_user(user_id: int, session: aiohttp.ClientSession) -> tuple[dict | None, int]:
    """
    GET користувача за telegram user_id.
    Повертає (data, status): при 200 — (data, 200), інакше (None, status).
    """
    url = f"{API_BASE_URL}/api/telegram-user/{user_id}"
    try:
        async with session.get(url, ssl=False) as response:
            logger.info(f"[API] GET {url} -> {response.status}")
            if response.status == 200:
                data = await response.json()
                return data, 200
            return None, response.status
    except Exception as e:
        logger.error(f"API Request Error (get_user): {e}")
        return None, 0


async def save_user(user_id: int, session: aiohttp.ClientSession) -> dict | None:
    """POST /api/telegram-user/{id} — створити користувача (при 404 на get_user)."""
    url = f"{API_BASE_URL}/api/telegram-user/{user_id}"
    try:
        async with session.post(url, ssl=False) as response:
            logger.info(f"[API] POST {url} -> {response.status}")
            if response.status != 200:
                return None
            return await _parse_json_response(response)
    except Exception as e:
        logger.error(f"API Request Error (save_user): {e}")
        return None


async def save_user_settings(
    user_id: int, settings: dict, session: aiohttp.ClientSession
) -> dict | None:
    """POST /api/telegram-user/{id}/settings — зберегти налаштування."""
    url = f"{API_BASE_URL}/api/telegram-user/{user_id}/settings"
    try:
        async with session.post(url, json=settings, ssl=False) as response:
            logger.info(f"[API] POST {url} -> {response.status}")
            if response.status != 200:
                return None
            return await _parse_json_response(response)
    except Exception as e:
        logger.error(f"API Request Error (save_user_settings): {e}")
        return None


async def api_add_favorite(
    user_id: int, place_id: str, name: str, session: aiohttp.ClientSession
) -> dict | None:
    """POST /api/telegram-user/{id}/favorites — додати місце в улюблені. Body: { id, name }."""
    url = f"{API_BASE_URL}/api/telegram-user/{user_id}/favorites"
    try:
        async with session.post(
            url, json={"id": place_id, "name": name}, ssl=False
        ) as response:
            logger.info(f"[API] POST {url} -> {response.status}")
            if response.status != 200:
                return None
            return await _parse_json_response(response)
    except Exception as e:
        logger.error(f"API Request Error (api_add_favorite): {e}")
        return None


async def api_remove_favorite(
    user_id: int, place_id: str, session: aiohttp.ClientSession
) -> dict | None:
    """POST /api/telegram-user/{id}/favorites/remove — видалити місце з улюблених. Body: { placeId }."""
    url = f"{API_BASE_URL}/api/telegram-user/{user_id}/favorites/remove"
    try:
        async with session.post(
            url, json={"placeId": place_id}, ssl=False
        ) as response:
            logger.info(f"[API] POST {url} -> {response.status}")
            if response.status != 200:
                return None
            return await _parse_json_response(response)
    except Exception as e:
        logger.error(f"API Request Error (api_remove_favorite): {e}")
        return None


# --- API place (місця, координати міст) ---


async def get_city_coordinates(city_name: str, session: aiohttp.ClientSession, language_code: str = "uk"):
    """
    Отримує координати міста за назвою через бекенд.
    """
    url = f"{API_BASE_URL}/api/place/city-coordinates?query={city_name}&languageCode={language_code}"
    try:
        async with session.get(url, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                return data  # {"latitude": ..., "longitude": ...}
            else:
                return None
    except Exception as e:
        logger.error(f"API Request Error (city-coordinates): {e}")
        return None


async def get_places(settings, session: aiohttp.ClientSession):
    """
    Отримує список місць у заданому радіусі від користувача.
    """
    if not settings.get("coordinates"):
        return None

    data_to_post = generate_request_object(settings)

    try:
        async with session.post(f"{API_BASE_URL}/api/place/google-maps-search-nearby", json=data_to_post, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                return None
    except Exception as e:
        logger.error(f"API Request Error: {e}")
        return None


async def get_place_details(place_id, session: aiohttp.ClientSession, language_code: str = "uk"):
    """
    Отримує деталі місця за його ID.
    """
    try:
        url = f"{API_BASE_URL}/api/place/google-maps-details/{place_id}?lang={language_code}"
        async with session.get(url, ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                return None
    except Exception as e:
        logger.error(f"API Request Error: {e}")
        return None


async def get_photos(place_id, session: aiohttp.ClientSession):
    """
    Отримує фото місця за його ID.
    """
    data_to_post = {
        "placeId": place_id,
        "maxHeight": PHOTO_MAX_HEIGHT,
        "maxWidth": PHOTO_MAX_WIDTH
    }
    try:
        async with session.post(f"{API_BASE_URL}/api/place/google-maps-photo", json=data_to_post, ssl=False) as response:
            if response.status == 200:
                photos = await response.json()
                logger.info(
                    f"Отримано {len(photos)} фото для місця {place_id}")
                return photos
            else:
                return None
    except Exception as e:
        logger.error(f"API Request Error: {e}")
        return None


def generate_request_object(settings):
    """
    Генерує об'єкт запиту на основі налаштувань користувача.
    """
    coords = settings.get("coordinates", {})
    latitude = float(coords.get("latitude", 0))
    longitude = float(coords.get("longitude", 0))
    radius = int(settings.get("radius", 1000))
    included_types = settings.get("includedTypes", [])
    excluded_types = settings.get("excludedTypes", [])
    max_result_count = int(settings.get("maxResultCount", 20))
    rank_preference = settings.get("rankPreference", "POPULARITY")
    language = settings.get("language", "uk")

    return {
        "includedTypes": included_types,
        "excludedTypes": excluded_types,
        "maxResultCount": max_result_count,
        "rankPreference": rank_preference,
        "languageCode": language,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude
                },
                "radius": radius
            }
        }
    }
