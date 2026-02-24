from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from bot.keyboards import actions_keyboard
from bot.services.settings import save_coordinates, get_user_settings
from bot.utils.logger import logger
from aiogram.fsm.state import default_state

router = Router()


def settings_text(user_id: int) -> str:
    s = get_user_settings(user_id)

    included = ", ".join(s.get("includedTypes", [])) if s.get(
        "includedTypes") else "Всі"
    excluded = ", ".join(s.get("excludedTypes", [])) if s.get(
        "excludedTypes") else "Немає"

    return (
        f"⚙️ <b>Налаштування:</b>\n"
        f"├ 🌐 Мова: <code>{s.get('language', 'uk')}</code>\n"
        f"├ 📏 Радіус: <code>{s.get('radius', 1000)} м</code>\n"
        f"├ ✅ Включити: <code>{included}</code>\n"
        f"├ ❌ Виключити: <code>{excluded}</code>\n"
        f"├ 🔢 Максимальна кількість: <code>{s.get('maxResultCount', 20)}</code>\n"
        f"└ ⭐ Сортування: <code>{s.get('rankPreference', 'POPULARITY')}</code>"
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


@router.message(CommandStart())
async def cmd_start(message: Message):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) запустив бота")
    await send_main_menu(message)


@router.message(F.location, default_state)
async def handle_location(message: Message):
    latitude = message.location.latitude
    longitude = message.location.longitude
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) надіслав локацію: {latitude}, {longitude}")
    save_coordinates(message.from_user.id, latitude, longitude)
    await send_main_menu(message)
