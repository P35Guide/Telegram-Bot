import aiohttp
import json
import asyncio
from bot.config import API_BASE_URL


async def get_places(settings):
    """
    імітування запиту в апі, поки апі ще не реалізовано
    """
    # Імітація затримки
    await asyncio.sleep(1)

    coordinates = settings.get("coordinates")
    radius = settings.get("radius", 1000)

    if not coordinates:
        return None

    # Тут був би реальний запит:
    # params = {
    #     "latitude": coordinates["latitude"],
    #     "longitude": coordinates["longitude"],
    #     "radius": radius,
    # }

    try:
        data = json.loads(example_json_response)
        return data
    except json.JSONDecodeError:
        return None


async def get_place_details(place_id):
    """
    імітування запиту в апі, поки апі ще не реалізовано
    """
    # Імітація затримки
    await asyncio.sleep(0.2)

    try:
        data = json.loads(example_json_response)
        return next((p for p in data.get("Places", []) if p.get("Id") == place_id), None)
    except json.JSONDecodeError:
        return None


example_json_response = '''
	{
  "Places": [
    {
      "Id": "001",
      "Name": "Кав'ярня Aroma",
      "DisplayName": "Aroma Espresso Bar",
      "PrimaryType": "cafe",
      "Latitude": 50.4501,
      "Longitude": 30.5234,
      "Rating": 4.5,
      "UserRatingCount": 120,
      "ShortFormattedAddress": "вул. Хрещатик, 22, Київ",
      "PhoneNumber": "+380441234567",
      "WebsiteUri": "https://aroma.ua",
      "GoogleMapsUri": "https://maps.google.com/?q=50.4501,30.5234",
      "PriceLevel": "PRICE_LEVEL_INEXPENSIVE",
      "OpenNow": true,
      "WeekdayDescriptions": [
        "Пн-Пт: 08:00–22:00",
        "Сб-Нд: 09:00–21:00"
      ],
      "EditorialSummary": "Популярна кав'ярня у центрі Києва.",
      "GenerativeSummary": "Aroma Espresso Bar — це затишне місце для зустрічей та смачної кави."
    },
    {
      "Id": "002",
      "Name": "Піцерія Napoli",
      "DisplayName": null,
      "PrimaryType": "restaurant",
      "Latitude": 50.4547,
      "Longitude": 30.5238,
      "Rating": 4.2,
      "UserRatingCount": 85,
      "ShortFormattedAddress": "вул. Саксаганського, 10, Київ",
      "PhoneNumber": null,
      "WebsiteUri": null,
      "GoogleMapsUri": "https://maps.google.com/?q=50.4547,30.5238",
      "PriceLevel": "PRICE_LEVEL_INEXPENSIVE",
      "OpenNow": false,
      "WeekdayDescriptions": [
					"понеділок: 11:30–14:30, 17:00–22:00",
					"вівторок: 11:30–14:30, 17:00–22:00",
					"середа: 11:30–14:30, 17:00–22:00",
					"четвер: 11:30–14:30, 17:00–22:00",
					"пʼятниця: 11:30–14:30, 17:00–22:00",
					"субота: 17:00–22:00",
					"неділя: 17:00–22:00"
				],
      "EditorialSummary": null,
      "GenerativeSummary": null
    }
  ]
}
'''
