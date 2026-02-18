from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import CommandStart

from bot.keyboards.location import location_keyboard


router = Router()


@router.message(CommandStart())
async def request_location(message: Message):
    await message.answer(
        "Вітаю у 📍P35Guide!\nНатисни кнопку, щоб поділитися координатами:",
        reply_markup=location_keyboard()
    )


@router.message(F.location)
async def handle_location(message: Message):
    latitude = message.location.latitude
    longitude = message.location.longitude

    await message.answer(
        f"Отримано координати:\n"
        f"Широта: <tg-spoiler>{latitude}</tg-spoiler>\n"
        f"Довгота: <tg-spoiler>{longitude}</tg-spoiler>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove()
    )
