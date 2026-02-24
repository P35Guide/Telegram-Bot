from math import log

from bot.config import PHOTO_MAX_HEIGHT
from bot.config import PHOTO_MAX_WIDTH
import aiohttp
from bot.config import API_BASE_URL
from bot.utils.logger import logger
from bot.model.place import Place
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


async def add_custom_place(place:Place,session: aiohttp.ClientSession):
    data_to_post = {
        "id": 0,
        "nameOfPlace": f"{place.NameOfPlace}",
        "address": f"{place.Address}",
        "description": f"{place.Description}",
        "photoUrl": f"{place.PhotoUrl}"
    }
    try:
        async with session.post(f"https://localhost:7124/api/custom/addPlace",json=data_to_post,ssl=False)as response:
            if response.status == 200:
                logger.info("custom place added")
                return True
            else:
                return False
    except Exception as e:
        logger.error(f"API Request Error: {e}")

async def get_all_custom_places(session:aiohttp.ClientSession):
    try:
        async with session.get(f"https://localhost:7124/api/custom/getAllPlaces",ssl=False) as resposns:
            if resposns.status == 200:
                logger.info("custom places gotten")
                return resposns.json()
            else:
                return None
    except Exception as e:
        logger.error(f"API Request Error: {e}")

async def get_custom_place_by_id(id:int,session:aiohttp.ClientSession):
    try:
        async with session.get(f"https://localhost:7124/api/custom/getPlaceById?Id={id}",ssl=False) as resposns:
            if resposns.status == 200:
                logger.info("custom places gotten")
                return resposns.json()
            else:
                return None
    except Exception as e:
        logger.error(f"API Request Error: {e}")

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
