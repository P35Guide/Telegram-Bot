from math import log

from bot.config import PHOTO_MAX_HEIGHT
from bot.config import PHOTO_MAX_WIDTH
import aiohttp
from bot.config import API_BASE_URL
from bot.utils.logger import logger
import json

# Отримати координати міста через API
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
        logger.warning(f"Спроба пошуку місць без координат користувача! settings: {settings}")
        return None

    data_to_post = generate_request_object(settings)
    logger.info(f"[DEBUG] data_to_post: {data_to_post}")
    url = f"{API_BASE_URL}/api/place/google-maps-search-nearby"
    logger.info(f"[API] POST {url}\nPayload: {json.dumps(data_to_post, ensure_ascii=False)}")

    try:
        async with session.post(url, json=data_to_post, ssl=False) as response:
            logger.info(f"[API] Status: {response.status}")
            text = await response.text()
            logger.info(f"[API] Response: {text}")
            if response.status == 200:
                try:
                    data = json.loads(text)
                except Exception as e:
                    logger.error(f"[API] JSON decode error: {e}")
                    return None
                return data
            else:
                logger.warning(f"[API] Non-200 response: {response.status}, text: {text}")
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

    req = {
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
    logger.info(f"[DEBUG] generate_request_object: {req}")
    return req
