from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def location_choice_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Передати мою геолокацію", request_location=True)],
            [KeyboardButton(text="🌐 Ввести координати вручну")]
        ],
        resize_keyboard=True
    )

def actions_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
                [KeyboardButton(text="📍 Передати координати")],
            [KeyboardButton(text="🚀 Пошук маршрутів")],
            [
                KeyboardButton(text="🌐 Мова"),
                KeyboardButton(text="📏 Радіус"),
            ],
            [
                KeyboardButton(text="🍴 Вибрати категорії"),
                 
            ],
            [
                KeyboardButton(text="🔢 Кількість"),
                KeyboardButton(text="⭐ Сортування"),
               
            ],
            [
                KeyboardButton(text="⏰ Відкрите зараз")
            ]
        ],
        resize_keyboard=True
    )
    return keyboard


def search_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Місця"), KeyboardButton(text="🔍 Список")],
            [KeyboardButton(text="🎲 Випадкове місце")],
            [KeyboardButton(text="🔙 Скасувати")],
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
                "DisplayName") or place.get("name") or place.get("Name")

            builder.button(
                text=name,
                callback_data=f"place_view:{place_id}"
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


def place_navigation_keyboard():
    Keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад"), KeyboardButton(text="➡️ Далі")],
            [KeyboardButton(text="🛑 Стоп")],
        ],
        resize_keyboard=True
    )

    return Keyboard
