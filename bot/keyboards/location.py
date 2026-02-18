from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def location_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📍 Надіслати геолокацію",
                    request_location=True
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    return keyboard
