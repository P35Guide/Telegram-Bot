# Обробник кнопки "📍 Надіслати геолокацію" (показує вибір способу)

from bot.services.settings import add_favorite_place, is_favorite_place, remove_favorite_place, toggle_favorite_place
from bot.utils.logger import logger
from bot.utils.formatter import format_place_text
from bot.services.settings import get_user_settings
from bot.services.api_client import get_photos, get_places, get_place_details
from bot.keyboards import places_keyboard, place_details_keyboard
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
import random
import aiohttp
from bot.keyboards import search_keyboard
from bot.handlers.main_menu import send_main_menu
from ssl import SSLContext
from bot.keyboards import place_navigation_keyboard
from bot.states import BotState
from bot.keyboards import location_choice_keyboard
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
router = Router()


@router.message(F.text == "📍 Надіслати геолокацію")
async def choose_location_method(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Оберіть спосіб передачі координат:",
        reply_markup=location_choice_keyboard()
    )

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

router = Router()


def filter_open_now(places, open_now):
    if not open_now:
        return places
    return [p for p in places if (p.get("openNow") is True or p.get("OpenNow") is True)]


@router.message(F.text == "🎲 Випадкове місце")
async def random_place_handler(message: Message, session: aiohttp.ClientSession):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає випадкове місце")

    await message.answer_dice(emoji="🎲")

    loading_msg = await message.answer(
        "⏳ <b>Крутимо рулетку...</b>\n"
        "Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    settings = get_user_settings(message.from_user.id)

    if not settings.get("coordinates"):
        await loading_msg.delete()
        await message.answer(
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Будь ласка, надішліть геолокацію або введіть координати:",
            parse_mode="HTML",
            reply_markup=location_choice_keyboard()
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
        places = filter_open_now(places, settings.get("openNow"))
        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку або вимкніть фільтр 'Відкрито зараз'.",
                parse_mode="HTML"
            )
            return
        random_place = random.choice(places)
        await loading_msg.edit_text(
            f"🎲 <b>Випадкове місце:</b>\n"
            "Оберіть місце, щоб відкрити його на карті:",
            parse_mode="HTML",
            reply_markup=places_keyboard([random_place])
        )
    except Exception as e:
        logger.error(f"Error in random_place_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )


@router.message(F.text == "🔙 Скасувати")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await send_main_menu(message)


async def perform_search(message: Message, session: aiohttp.ClientSession, show_list: bool = True):
    """
    Логіка пошуку місць поруч.
    Повертає (loading_msg, places) кортеж.
    У разі помилки обробляє UI оновлення та повертає (loading_msg, None).
    """
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає місця поруч")

    loading_msg = await message.answer(
        "🔎 <b>Пошук місць поруч...</b>\n\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    settings = get_user_settings(message.from_user.id)

    if not settings.get("coordinates"):
        await loading_msg.delete()
        await message.answer(
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Будь ласка, надішліть геолокацію або введіть координати:",
            parse_mode="HTML",
            reply_markup=location_choice_keyboard()
        )
        return None, None

    try:
        data = await get_places(settings, session)

        if not data or "places" not in data:
            await loading_msg.edit_text(
                "⚠️ <b>Нічого не знайдено</b> або сервер не відповідає.",
                parse_mode="HTML"
            )
            return loading_msg, None

        places = data["places"]
        places = filter_open_now(places, settings.get("openNow"))
        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку або вимкніть фільтр 'Відкрито зараз'.",
                parse_mode="HTML"
            )
            return loading_msg, None

        if show_list:
            kb = places_keyboard(places)
            # Якщо клавіатура порожня (немає жодної кнопки) — fallback: просто текстовий список
            if not kb.inline_keyboard or len(kb.inline_keyboard) == 0:
                preview = []
                for idx, place in enumerate(places[:10], 1):
                    name = place.get('displayName') or place.get(
                        'name') or 'Без назви'
                    address = place.get('shortFormattedAddress') or ''
                    rating = place.get('rating')
                    rating_str = f" | ⭐ {rating}" if rating else ""
                    preview.append(
                        f"<b>{idx}.</b> {name}{rating_str}\n<code>{address}</code>")
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

        return loading_msg, places

    except Exception as e:
        logger.error(f"Error in perform_search: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )
        return loading_msg, None


async def send_place_info(message: Message, session: aiohttp.ClientSession, place_id: str, language: str):
    """
    Отримує деталі місця за його ID та відправляє їх користувачу.
    Повертає True, якщо успішно, False у разі помилки.
    """
    try:
        place = await get_place_details(place_id, session, language)
        if not place:
            return False

        photos = await get_photos(place_id, session)

        # Send photos
        if photos:
            try:
                media_group = [InputMediaPhoto(media=photo)
                               for photo in photos[:10]]
                if media_group:
                    await message.answer_media_group(media_group)
            except Exception as e:
                logger.error(
                    f"Failed to send photos for place {place_id}: {e}")

        # Send text info
        favorite_callback = f"fav_toggle:{place_id}" if place_id else None

        text = format_place_text(place)
        kb = place_details_keyboard(
            place.get("websiteUri"),
            place.get("googleMapsUri"),
            favorite_callback,
            is_favorite_place(message.from_user.id, place_id)
        )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True
        )

        # Send location
        if place.get("latitude") and place.get("longitude"):
            await message.answer_location(
                latitude=place["latitude"],
                longitude=place["longitude"]
            )

        return True

    except Exception as e:
        logger.error(f"Error sending place info: {e}")
        return False


@router.message(F.text == "🔍 Список")
async def find_places_handler(message: Message, session: aiohttp.ClientSession):
    loading_msg, places = await perform_search(message, session)

    if not places:
        return


@router.message(F.text == "🚀 Пошук маршрутів")
async def search_menu_handler(message: Message, session: aiohttp.ClientSession):
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) запускає пошук маршрутів")

    await message.answer(
        "<b>Оберіть варіант пошуку:</b>\n"
        "🚀 <b>Місця</b> - зручно оцінити місця\n"
        "🔍 <b>Список</b> - переглянути список знайдених місць.\n"
        "🎲 <b>Випадкове місце</b> - випадково вибрати місце",
        parse_mode="HTML",
        reply_markup=search_keyboard()
    )


async def show_place_card(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    data = await state.get_data()
    places = data.get("places", [])
    index = data.get("current_index", 0)

    if not places:
        await message.answer("⚠️ Список місць порожній.")
        await state.clear()
        return

    if index < 0:
        index = 0
    if index >= len(places):
        await message.answer("✅ Це було останнє місце.")
        index = len(places) - 1
        await state.update_data(current_index=index)

    place_summary = places[index]
    place_id = place_summary.get("id") or place_summary.get("Id")

    settings = get_user_settings(message.from_user.id)
    language = settings.get("language", "uk")

    loading_msg = await message.answer("⏳ Завантаження інформації...")

    success = await send_place_info(message, session, place_id, language)

    if not success:
        await loading_msg.edit_text("⚠️ Не вдалося отримати деталі місця.")
        return

    await loading_msg.delete()
    await message.answer(
        f"📍 <b>Місце {index + 1} з {len(places)}</b>",
        parse_mode="HTML",
        reply_markup=place_navigation_keyboard()
    )


@router.message(F.text == "🚀 Місця")
async def search_places_handler(message: Message, session: aiohttp.ClientSession, state: FSMContext):
    loading_msg, places = await perform_search(message, session, show_list=False)

    if not places:
        return

    await state.set_state(BotState.browsing_places)
    await state.update_data(places=places, current_index=0)

    await loading_msg.delete()

    await show_place_card(message, state, session)


@router.message(BotState.browsing_places, F.text == "➡️ Далі")
async def next_place_handler(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    places = data.get("places", [])

    if current_index < len(places) - 1:
        await state.update_data(current_index=current_index + 1)
        await show_place_card(message, state, session)
    else:
        await message.answer("✅ Це останнє місце у списку.")


@router.message(BotState.browsing_places, F.text == "⬅️ Назад")
async def prev_place_handler(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    data = await state.get_data()
    current_index = data.get("current_index", 0)

    if current_index > 0:
        await state.update_data(current_index=current_index - 1)
        await show_place_card(message, state, session)
    else:
        await message.answer("ℹ️ Це перше місце.")


@router.message(BotState.browsing_places, F.text == "🛑 Стоп")
async def stop_browsing_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("⏹ Перегляд завершено.", reply_markup=search_keyboard())


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

    success = await send_place_info(callback.message, session, place_id, language)

    if not success:
        await callback.message.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return


@router.callback_query(F.data.startswith("fav_toggle:"))
async def add_to_favorites_handler(callback: CallbackQuery):
    """Обробляє натискання «Додати/Вилучити з улюблених»."""
    place_id = callback.data.split(":", 1)[1]
    was_favorite = is_favorite_place(callback.from_user.id, place_id)
    toggle_favorite_place(callback.from_user.id, place_id)
    await callback.answer(
        "❌ Вилучено з улюблених" if was_favorite else "✅ Додано до улюблених"
    )
