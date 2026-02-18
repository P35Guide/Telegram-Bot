from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext

from bot.keyboards import actions_keyboard, cancel_keyboard
from bot.services.settings import save_coordinates, update_language, update_radius, get_user_settings
from bot.states import BotState
from bot.utils.logger import logger


router = Router()


def settings_text(user_id: int) -> str:
    s = get_user_settings(user_id)
    return (
        f"⚙️ <b>Налаштування:</b>\n"
        f"├ 🌐 Мова: <code>{s['language']}</code>\n"
        f"└ 📏 Радіус: <code>{s['radius']} м</code>"
    )


async def send_main_menu(message: Message):
    s = get_user_settings(message.from_user.id)
    coords = s.get("coordinates")

    if coords:
        location_line = (
            f"📍 <b>Координати:</b>\n"
            f"├ Широта: <tg-spoiler>{coords['latitude']}</tg-spoiler>\n"
            f"└ Довгота: <tg-spoiler>{coords['longitude']}</tg-spoiler>"
        )
    else:
        location_line = "📍 Натисни кнопку, щоб поділитися координатами:"

    await message.answer(
        f"👋 <b>P35Guide</b>\n\n"
        f"{settings_text(message.from_user.id)}\n\n"
        f"{location_line}",
        parse_mode="HTML",
        reply_markup=actions_keyboard()
    )


@router.message(F.text == "🔍 Знайти місця поруч")
async def find_places_handler(message: Message):
    logger.info(f"Користувач {message.from_user.id} шукає місця поруч")
    await message.answer(
        "🔍 <b>Пошук місць поруч...</b>\n\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )


@router.message(F.text == "🌐 Мова")
async def language_handler(message: Message, state: FSMContext):
    logger.info(f"Користувач {message.from_user.id} хоче змінити мову")
    await state.set_state(BotState.selecting_language)
    await message.answer(
        "✏️ Введіть мову пошуку:",
        reply_markup=cancel_keyboard()
    )


@router.message(F.text == "📏 Радіус")
async def radius_handler(message: Message, state: FSMContext):
    logger.info(f"Користувач {message.from_user.id} хоче змінити радіус")
    await state.set_state(BotState.selecting_radius)
    await message.answer(
        "✏️ Введіть радіус пошуку в метрах:",
        reply_markup=cancel_keyboard()
    )


@router.message(CommandStart())
async def cmd_start(message: Message):
    logger.info(f"Користувач {message.from_user.id} запустив бота")
    await send_main_menu(message)


@router.message(F.location)
async def handle_location(message: Message):
    latitude = message.location.latitude
    longitude = message.location.longitude
    logger.info(f"Користувач {message.from_user.id} надіслав локацію: {latitude}, {longitude}")
    save_coordinates(message.from_user.id, latitude, longitude)
    await send_main_menu(message)


@router.message(BotState.selecting_language, F.text == "🔙 Скасувати")
async def cancel_language(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_language)
async def set_language_handler(message: Message, state: FSMContext):
    lang = message.text.strip()
    logger.info(f"Користувач {message.from_user.id} змінив мову на {lang}")
    update_language(message.from_user.id, lang)
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_radius, F.text == "🔙 Скасувати")
async def cancel_radius(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.selecting_radius)
async def set_radius_handler(message: Message, state: FSMContext):
    radius = message.text.strip()
    logger.info(f"Користувач {message.from_user.id} змінив радіус на {radius}")
    update_radius(message.from_user.id, radius)
    await state.clear()
    await send_main_menu(message)
