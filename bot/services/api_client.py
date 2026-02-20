import aiohttp
from bot.config import API_BASE_URL
from bot.utils.logger import logger
import json


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


async def get_place_details(place_id, session: aiohttp.ClientSession):
    """
    Отримує деталі місця за його ID.
    """
    try:
        async with session.get(f"{API_BASE_URL}/api/place/google-maps-details/{place_id}", ssl=False) as response:
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
    try:
        async with session.get(f"{API_BASE_URL}/api/place/google-maps-photo/{place_id}", ssl=False) as response:
            if response.status == 200:
                data = await response.json()
                return data
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

    return {
        "includedTypes": included_types,
        "excludedTypes": excluded_types,
        "maxResultCount": max_result_count,
        "rankPreference": rank_preference,
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
