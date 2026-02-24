from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def actions_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Надіслати геолокацію",
                            request_location=True)],
            [KeyboardButton(text = "🧾 Дістати місця користувачів")],
            [
                KeyboardButton(text="🔍 Знайти місця поруч"),
                KeyboardButton(text ="📌 Додати своє місце")
            ],
            [
                KeyboardButton(text="🌐 Мова"),
                KeyboardButton(text="📏 Радіус"),
            ],
            [
                KeyboardButton(text="✅ Включити типи"),
                KeyboardButton(text="❌ Виключити типи"),
            ],
            [
                KeyboardButton(text="🔢 Кількість"),
                KeyboardButton(text="⭐ Сортування"),
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def cancel_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Скасувати")]],
        resize_keyboard=True
    )
    return keyboard


def places_keyboard(places):
    """
    Генерує клавіатуру зі списком місць.
    Кожна кнопка має callback_data з ID місця.
    """
    builder = InlineKeyboardBuilder()

    for place in places:
        place_id = place.get("id") or place.get("Id")
        if place_id:
            name = place.get("displayName") or place.get(
                "DisplayName") or place.get("name") or place.get("Name") or place.get("NameOfPlace")

            builder.button(
                text=name,
                callback_data=f"place_view:{place_id}"
            )

    builder.adjust(2)
    return builder.as_markup()

def custom_places_keyboard(places):
    """
    Генерує клавіатуру зі списком місць.
    Кожна кнопка має callback_data з ID місця.
    """
    builder = InlineKeyboardBuilder()

    for place in places:
        place_id = place.get("id") or place.get("Id")
        if place_id:
            name = place.get("displayName") or place.get(
                "DisplayName") or place.get("name") or place.get("Name") or place.get("NameOfPlace")

            builder.button(
                text=name,
                callback_data=f"custom_place_view:{place_id}"
            )

    builder.adjust(2)
    return builder.as_markup()

def place_details_keyboard(place_url=None, google_maps_url=None):
    """
    Генерує клавіатуру для детального перегляду місця.
    """
    builder = InlineKeyboardBuilder()

    if place_url:
        builder.button(text="🌍 Сайт", url=place_url)

    if google_maps_url:
        builder.button(text="📍 Карта", url=google_maps_url)

    return builder.as_markup()
