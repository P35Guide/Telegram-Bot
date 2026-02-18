from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def actions_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Надіслати геолокацію",
                            request_location=True)],
            [KeyboardButton(text="🔍 Знайти місця поруч")],
            [
                KeyboardButton(text="🌐 Мова"),
                KeyboardButton(text="📏 Радіус")
            ],
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
