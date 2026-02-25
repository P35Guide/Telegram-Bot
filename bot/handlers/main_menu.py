from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
import aiohttp

from bot.keyboards import actions_keyboard, location_choice_keyboard
from bot.services.settings import save_coordinates, get_user_settings
from bot.utils.logger import logger
from bot.states import BotState

router = Router()


@router.message(F.text == "📍 Передати координати")
async def show_location_choice_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Оберіть спосіб передачі координат:",
        reply_markup=location_choice_keyboard()
    )


def settings_text(user_id: int) -> str:
    s = get_user_settings(user_id)

    included = ", ".join(s.get("includedTypes", [])) if s.get(
        "includedTypes") else "Всі"
    excluded = ", ".join(s.get("excludedTypes", [])) if s.get(
        "excludedTypes") else "Немає"
    open_now = "Так" if s.get("openNow") else "Ні"

    return (
        f"⚙️ <b>Налаштування:</b>\n"
        f"├ 🌐 Мова: <code>{s.get('language', 'uk')}</code>\n"
        f"├ 📏 Радіус: <code>{s.get('radius', 1000)} м</code>\n"
        f"├ 🍴 Вибрати категорії: <code>{included}</code>\n"
        f"├ ⏰ Відкрите зараз: <code>{open_now}</code>\n"
        f"├ 🔢 Максимальна кількість: <code>{s.get('maxResultCount', 20)}</code>\n"
        f"└ ⭐ Сортування: <code>{s.get('rankPreference', 'POPULARITY')}</code>"
    )


async def send_main_menu(message: Message, user_id: int | None = None):
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    coords = s.get("coordinates")

    if coords:
        location_line = (
            f"📍 <b>Координати:</b>\n"
            f"├ Широта: <tg-spoiler>{coords['latitude']}</tg-spoiler>\n"
            f"└ Довгота: <tg-spoiler>{coords['longitude']}</tg-spoiler>"
        )
        await message.answer(
            f"👋 <b>P35Guide</b>\n\n"
            f"{settings_text(target_user_id)}\n\n"
            f"{location_line}",
            parse_mode="HTML",
            reply_markup=actions_keyboard()
        )
    else:
        await message.answer(
            f"👋 <b>P35Guide</b>\n\n"
            f"{settings_text(target_user_id)}\n\n"
            "Оберіть спосіб передачі координат:",
            parse_mode="HTML",
            reply_markup=location_choice_keyboard()
        )


@router.message(CommandStart())
async def cmd_start(message: Message):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) запустив бота")
    await send_main_menu(message)


@router.message(F.location)
async def handle_location_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    latitude = message.location.latitude
    longitude = message.location.longitude
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) надіслав локацію: {latitude}, {longitude}")
    save_coordinates(message.from_user.id, latitude, longitude)
    await state.clear()
    await message.answer(
        "✅ Геолокацію отримано! Ви повернулися до головного меню.",
        reply_markup=actions_keyboard()
    )


@router.message(F.text == "🌐 Ввести координати вручну")
async def ask_for_coordinates_main_menu(message: Message, state: FSMContext):
    await state.set_state(BotState.entering_coordinates)
    await message.answer(
        "Введіть координати у форматі: 49.2328, 28.4810\nНаприклад: 49.2328, 28.4810"
    )


@router.message(StateFilter(BotState.entering_coordinates))
async def handle_coordinates_input_main_menu(message: Message, state: FSMContext):
    import re
    text = message.text.strip().replace("|", ",")
    pattern = r"^\s*(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)\s*$"
    match = re.match(pattern, text)
    if not match:
        await message.answer(
            "❗️ Невірний формат координат. Спробуйте ще раз.\nНаприклад: 49.2328, 28.4810"
        )
        return
    lat, lon = float(match.group(1)), float(match.group(2))
    save_coordinates(message.from_user.id, lat, lon)
    await state.clear()
    await message.answer(
        f"✅ Координати збережено: {lat}, {lon}\nТепер ви можете шукати місця поруч!"
    )
    await send_main_menu(message)