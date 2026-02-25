from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
import aiohttp
import re

from bot.keyboards import actions_keyboard, choose_location_type_keyboard
from bot.services.settings import save_coordinates, get_user_settings
from bot.utils.logger import logger
from bot.states import BotState

router = Router()


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await send_main_menu(message)


@router.message(F.text.in_(["📍 Передати координати", "📍 Надіслати геолокацію"]))
async def show_location_choice_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Оберіть спосіб передачі координат:",
        reply_markup=choose_location_type_keyboard()
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
        f"├ 🧹 Скинути категорії: <code>{excluded}</code>\n"
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
        reply_kb = actions_keyboard()
    else:
        location_line = "Оберіть спосіб передачі координат:"
        reply_kb = choose_location_type_keyboard()

    await message.answer(
        f"👋 <b>P35Guide</b>\n\n"
        f"{settings_text(target_user_id)}\n\n"
        f"{location_line}",
        parse_mode="HTML",
        reply_markup=reply_kb
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


@router.message(F.text == "🏙️ Знайти потрібне місто")
async def ask_for_city_name_main_menu(message: Message, state: FSMContext):
    await state.set_state(BotState.entering_coordinates)
    await message.answer(
        "Введіть назву міста (наприклад: Львів, Київ, Одеса)"
    )


@router.message(F.text == "🌐 Ввести координати вручну")
async def ask_for_coordinates_main_menu(message: Message, state: FSMContext):
    await state.set_state(BotState.entering_coordinates)
    await message.answer(
        "Введіть координати у форматі:\n"
        "49.2328, 28.4810\n"
        "Наприклад: 50.4501, 30.5234"
    )


@router.message(StateFilter(BotState.entering_coordinates))
async def handle_city_input_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    text = message.text.strip()
    coord_match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", text)

    if coord_match:
        lat = float(coord_match.group(1))
        lon = float(coord_match.group(2))
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            await message.answer("❗️ Невірний діапазон координат. Спробуйте ще раз.")
            return

        save_coordinates(message.from_user.id, lat, lon)
        await state.clear()
        await message.answer(
            f"✅ Координати збережено: {lat}, {lon}\nТепер ви можете шукати місця поруч!"
        )
        await send_main_menu(message)
        return

    from bot.services.api_client import get_city_coordinates
    await message.answer(f"Шукаю координати для міста: {text} ...")
    coords = await get_city_coordinates(text, session)
    if coords and coords.get("latitude") and coords.get("longitude"):
        save_coordinates(message.from_user.id, coords["latitude"], coords["longitude"])
        await state.clear()
        await message.answer(
            f"✅ Місто '{text}' знайдено!\nТепер ви можете шукати місця поруч!"
        )
        await send_main_menu(message)
    else:
        await message.answer(
            f"❗️ Не вдалося знайти координати для міста '{text}'. Спробуйте ще раз."
        )
