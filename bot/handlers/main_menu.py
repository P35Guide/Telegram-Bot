import aiohttp
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from bot.states import BotState
from bot.keyboards import (
    actions_keyboard,
    choose_location_type_keyboard,
    settings_keyboard,
)
from bot.services.settings import (
    save_coordinates,
    get_user_settings,
    apply_user_data_from_api,
    get_settings_payload_for_api,
)
from bot.services.api_client import (
    get_user as api_get_user,
    save_user as api_save_user,
    save_user_settings as api_save_user_settings,
    get_city_coordinates,
)
from bot.utils.logger import logger

router = Router()


async def _save_coordinates_and_sync(user_id: int, latitude: float, longitude: float, session: aiohttp.ClientSession):
    """Зберігає координати локально та відправляє налаштування на сервер."""
    save_coordinates(user_id, latitude, longitude)
    await api_save_user_settings(user_id, get_settings_payload_for_api(user_id), session)


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

    open_now = s.get("openNow", False)
    open_status = "🟢 Так" if open_now else "🔴 Ні"

    return (
        f"⚙️ <b>Налаштування:</b>\n"
        f"├ 🌐 Мова: <code>{s.get('language', 'uk')}</code>\n"
        f"├ 📏 Радіус: <code>{s.get('radius', 1000)} м</code>\n"
        f"├ ✅ Включити: <code>{included}</code>\n"
        f"├ ❌ Виключити: <code>{excluded}</code>\n"
        f"├ 🔢 Максимальна кількість: <code>{s.get('maxResultCount', 20)}</code>\n"
        f"├ ⭐ Сортування: <code>{s.get('rankPreference', 'POPULARITY')}</code>\n"
        f"└ ⏰ Відкрите зараз: <code>{open_status}</code>"
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
        reply_markup=reply_kb,
    )


async def send_settings_menu(message: Message, user_id: int | None = None):
    """Показує екран налаштувань і клавіатуру (включно з кнопкою «Зберегти на сервер»)."""
    target_user_id = user_id or message.from_user.id
    await message.answer(
        settings_text(target_user_id),
        parse_mode="HTML",
        reply_markup=settings_keyboard(),
    )


@router.message(F.text == "⚙️ Налаштування")
async def show_settings_menu(message: Message):
    await send_settings_menu(message)


@router.message(F.text == "💾 Зберегти на сервер")
async def settings_save_handler(message: Message, session: aiohttp.ClientSession):
    """Обробник кнопки «Зберегти на сервер» — відправляє поточні налаштування на API."""
    user_id = message.from_user.id
    payload = get_settings_payload_for_api(user_id)
    result = await api_save_user_settings(user_id, payload, session)
    if result is not None:
        await message.answer("✅ Налаштування збережено на сервер")
    else:
        await message.answer("⚠️ Не вдалося зберегти налаштування на сервер")


@router.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: Message):
    await send_main_menu(message)


@router.message(CommandStart())
async def cmd_start(message: Message, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    logger.info(f"/start: user_id={user_id}")

    data, status = await api_get_user(user_id, session)
    if status == 200 and data:
        apply_user_data_from_api(user_id, data)
    elif status == 404:
        created = await api_save_user(user_id, session)
        if created is not None:
            apply_user_data_from_api(user_id, created)

    await send_main_menu(message)


@router.message(F.location)
async def handle_location_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    lat, lon = message.location.latitude, message.location.longitude
    logger.info(f"Користувач {message.from_user.username}({user_id}) надіслав локацію: {lat}, {lon}")
    await _save_coordinates_and_sync(user_id, lat, lon, session)
    await state.clear()
    await message.answer(
        "✅ Геолокацію отримано! Ви повернулися до головного меню.",
        reply_markup=actions_keyboard(),
    )


@router.message(F.text == "🏙️ Знайти потрібне місто")
async def ask_for_city_name_main_menu(message: Message, state: FSMContext):
    await state.set_state(BotState.entering_coordinates)
    await message.answer(
        "Введіть назву міста (наприклад: Львів, Київ, Одеса)"
    )


@router.message(StateFilter(BotState.entering_coordinates))
async def handle_city_input_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    text = message.text.strip()
    user_id = message.from_user.id
    await message.answer(f"Шукаю координати для міста: {text} ...")
    coords = await get_city_coordinates(text, session)
    if coords and coords.get("latitude") is not None and coords.get("longitude") is not None:
        await _save_coordinates_and_sync(
            user_id, coords["latitude"], coords["longitude"], session
        )
        await state.clear()
        await message.answer(
            f"✅ Місто '{text}' знайдено!\nТепер ви можете шукати місця поруч!"
        )
        await send_main_menu(message)
    else:
        await message.answer(
            f"❗️ Не вдалося знайти координати для міста '{text}'. Спробуйте ще раз."
        )
