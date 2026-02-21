import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from bot.keyboards import places_keyboard, place_details_keyboard
from bot.services.api_client import get_photos, get_places, get_place_details
from bot.services.settings import get_user_settings
from bot.utils.formatter import format_place_text
from bot.utils.logger import logger

router = Router()


@router.message(F.text == "🔍 Знайти місця поруч")
async def find_places_handler(message: Message, session: aiohttp.ClientSession):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає місця поруч")

    loading_msg = await message.answer(
        "🔍 <b>Пошук місць поруч...</b>\n\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    settings = get_user_settings(message.from_user.id)

    if not settings.get("coordinates"):
        await loading_msg.edit_text(
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Будь ласка, натисніть кнопку '📍 Надіслати геолокацію', щоб ми знали де шукати.",
            parse_mode="HTML"
        )
        return

    try:
        data = await get_places(settings, session)

        if not data or "places" not in data:
            await loading_msg.edit_text(
                "⚠️ <b>Нічого не знайдено</b> або сервер не відповідає.",
                parse_mode="HTML"
            )
            return

        places = data["places"]
        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку.",
                parse_mode="HTML"
            )
            return

        kb = places_keyboard(places)
        # Якщо клавіатура порожня (немає жодної кнопки) — fallback: просто текстовий список
        if not kb.inline_keyboard or len(kb.inline_keyboard) == 0:
            preview = []
            for idx, place in enumerate(places[:10], 1):
                name = place.get('displayName') or place.get('name') or 'Без назви'
                address = place.get('shortFormattedAddress') or ''
                rating = place.get('rating')
                rating_str = f" | ⭐ {rating}" if rating else ""
                preview.append(f"<b>{idx}.</b> {name}{rating_str}\n<code>{address}</code>")
            text = "\n\n".join(preview)
            await loading_msg.edit_text(
                f"✅ <b>Знайдено {len(places)} місць:</b>\n\n{text}",
                parse_mode="HTML"
            )
        else:
            await loading_msg.edit_text(
                f"✅ <b>Знайдено {len(places)} місць:</b>\n"
                "Оберіть місце, щоб відкрити його на карті:",
                parse_mode="HTML",
                reply_markup=kb
            )

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("place_view:"))
async def place_details_handler(callback: CallbackQuery, session: aiohttp.ClientSession):
    """
    Обробляє натискання на кнопку місця зі списку.
    Отримує деталі місця та надсилає їх окремим повідомленням.
    """
    place_id = callback.data.split(":")[1]
    logger.info(
        f"Користувач {callback.from_user.username}({callback.from_user.id}) переглядає місце {place_id}")

    await callback.answer()

    settings = get_user_settings(callback.from_user.id)
    language = settings.get("language", "uk")

    place = await get_place_details(place_id, session, language)
    photos = await get_photos(place_id, session)

    if not place:
        await callback.message.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return

    kb = place_details_keyboard(
        place.get("websiteUri"),
        place.get("googleMapsUri")
    )

    # надсилаємо фото
    if photos:
        try:
            media_group = [InputMediaPhoto(media=photo)
                           for photo in photos[:10]]
            if media_group:
                await callback.message.answer_media_group(media_group)
        except Exception as e:
            logger.error(f"Failed to send photos for place {place_id}: {e}")

    await callback.message.answer(
        format_place_text(place),
        parse_mode="HTML",
        reply_markup=kb,
        disable_web_page_preview=True
    )

    # надсилаємо мапу
    if place.get("latitude") and place.get("longitude"):
        await callback.message.answer_location(
            latitude=place["latitude"],
            longitude=place["longitude"]
        )

import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from bot.keyboards import places_keyboard, place_details_keyboard, location_choice_keyboard
from bot.services.api_client import get_photos, get_places, get_place_details
from bot.services.settings import get_user_settings
from bot.utils.formatter import format_place_text
from bot.utils.logger import logger
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from bot.states import BotState
from bot.handlers.main_menu import send_main_menu

router = Router()


# Обробник надсилання геолокації користувачем
@router.message(F.location)
async def handle_user_location(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    lat = message.location.latitude
    lon = message.location.longitude
    from bot.services.settings import update_coordinates
    update_coordinates(message.from_user.id, lat, lon)
    await state.clear()
    # Одразу запускаємо пошук місць поруч
    await find_places_handler(message, session)
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from bot.states import BotState
from bot.handlers.main_menu import send_main_menu

router = Router()

# Обробник кнопки 'Скасувати' при виборі локації або введенні координат
@router.message(F.text == "🔙 Скасувати")
async def cancel_location_input(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


@router.message(F.text == "🔍 Знайти місця поруч")
async def find_places_handler(message: Message, session: aiohttp.ClientSession):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає місця поруч")

    loading_msg = await message.answer(
        "🔍 <b>Пошук місць поруч...</b>\n\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    settings = get_user_settings(message.from_user.id)
    logger.info(f"[DEBUG] settings: {settings}")
    logger.info(f"[DEBUG] coordinates: {settings.get('coordinates')}")

    if not settings.get("coordinates"):
        await loading_msg.edit_text(
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Оберіть спосіб передачі локації:",
            parse_mode="HTML"
        )
        await message.answer(
            "Будь ласка, оберіть спосіб передачі локації:",
            reply_markup=location_choice_keyboard()
        )
        return

    # Додаємо логування після виклику get_places
    places = await get_places(settings, session)
    logger.info(f"[DEBUG] get_places result: {places}")
    if not places:
        await loading_msg.edit_text(
            "❌ <b>Не знайдено місць поруч.</b>\nСпробуйте змінити радіус або координати.",
            parse_mode="HTML"
        )
        return
    # ... тут має бути логіка відображення місць (залишаємо як є, якщо вона вже була нижче)
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from bot.states import BotState
# Обробник вибору способу передачі локації
@router.message(F.text == "🌐 Ввести координати вручну")
async def ask_for_coordinates(message: Message, state: FSMContext):
    await state.set_state(BotState.entering_coordinates)
    await message.answer(
        "Введіть координати у форматі:\n"
        "49.2328, 28.4810\n"
        "Ex.: Latitude: 40.829503 | Longitude: -74.118126\n"
        "Наприклад: 50.4501, 30.5234\n"
        "\nPlease enter coordinates in format:\n"
        "49.2328, 28.4810\n"
        "Example: 40.829503, -74.118126",
        reply_markup=location_choice_keyboard()
    )


# Обробник введення координат
@router.message(StateFilter(BotState.entering_coordinates))
async def handle_coordinates_input(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    import re
    text = message.text.strip().replace("|", ",")
    pattern = r"^\s*(-?\d{1,2}\.\d+)[,\s]+(-?\d{1,3}\.\d+)\s*$"
    match = re.match(pattern, text)
    if not match:
        await message.answer(
            "❗️ Невірний формат координат. Спробуйте ще раз.\n"
            "Наприклад: 49.2328, 28.4810\n"
            "Ex.: 40.829503, -74.118126\n"
            "\nPlease enter coordinates in format: 49.2328, 28.4810",
            reply_markup=location_choice_keyboard()
        )
        return
    lat, lon = float(match.group(1)), float(match.group(2))
    from bot.services.settings import update_coordinates
    update_coordinates(message.from_user.id, lat, lon)
    await state.clear()
    # Одразу запускаємо пошук місць поруч
    await find_places_handler(message, session)


@router.callback_query(F.data.startswith("place_view:"))
async def place_details_handler(callback: CallbackQuery, session: aiohttp.ClientSession):
    """
    Обробляє натискання на кнопку місця зі списку.
    Отримує деталі місця та надсилає їх окремим повідомленням.
    """
    place_id = callback.data.split(":")[1]
    logger.info(
        f"Користувач {callback.from_user.username}({callback.from_user.id}) переглядає місце {place_id}")

    await callback.answer()

    settings = get_user_settings(callback.from_user.id)
    language = settings.get("language", "uk")

    place = await get_place_details(place_id, session, language)
    photos = await get_photos(place_id, session)

    if not place:
        await callback.message.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return

    kb = place_details_keyboard(
        place.get("websiteUri"),
        place.get("googleMapsUri")
    )

    # надсилаємо фото
    if photos:
        try:
            media_group = [InputMediaPhoto(media=photo)
                           for photo in photos[:10]]
            if media_group:
                await callback.message.answer_media_group(media_group)
        except Exception as e:
            logger.error(f"Failed to send photos for place {place_id}: {e}")

    await callback.message.answer(
        format_place_text(place),
        parse_mode="HTML",
        reply_markup=kb,
        disable_web_page_preview=True
    )

    # надсилаємо мапу
    if place.get("latitude") and place.get("longitude"):
        await callback.message.answer_location(
            latitude=place["latitude"],
            longitude=place["longitude"]
        )
