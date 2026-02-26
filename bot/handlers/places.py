import aiohttp
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from bot.handlers.main_menu import send_main_menu
from bot.keyboards import (
    place_navigation_keyboard,
    search_keyboard,
    places_keyboard,
    place_details_keyboard,
    choose_location_type_keyboard,
    favorites_action_keyboard,
    select_favorites_for_comparison_keyboard,
)
from bot.services.api_client import (
    get_photos,
    get_places,
    get_place_details,
    api_add_favorite,
    api_remove_favorite,
)
from bot.services.settings import (
    add_favorite_place,
    get_favorite_places,
    get_user_settings,
    is_favorite_place,
    remove_favorite_place,
)
from bot.states import BotState
from bot.utils.formatter import format_place_text, format_comparison_text
from bot.utils.logger import logger


router = Router()
_place_name_cache: dict[str, str] = {}

@router.message(F.text == "📌 Додати своє місце")
async def add_place_handler(message:Message,state:FSMContext):
    logger.info(
        f"Користувач {message.from_user.username} ({message.from_user.id}) додає своє місце"
    )
    await message.answer('Введи назву місця')
    await state.set_state(AddPlace.wait_for_title)
@router.message(AddPlace.wait_for_title)
async def add_title(message:Message,state:FSMContext):
    info = message.text
    await state.update_data(title=info)
    data = await state.get_data()
    saved = data.get("title")

    if(saved == info):
        logger.info("title local saved")
        await message.answer("[Назва збережена]\nВведи опис місця")
        await state.set_state(AddPlace.wait_for_discription)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()
@router.message(AddPlace.wait_for_discription)
async def add_discription(message:Message,state:FSMContext):
    info = message.text
    await state.update_data(discription=info)
    data = await state.get_data()
    saved = data.get("discription")

    if(saved == info):
        logger.info("discription local saved")
        await message.answer("[Опис збережений]\nВведи адресу місця")
        await state.set_state(AddPlace.wait_for_shor_adress)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()
@router.message(AddPlace.wait_for_shor_adress)
async def add_adress(message:Message,state:FSMContext):
    info = message.text
    await state.update_data(adress=info)
    data = await state.get_data()
    saved =  data.get("adress")

    if(saved == info):
        logger.info("adress local saved")
        await message.answer("[Адреса збережена]\nНадай 5 фото місцевості")
        await state.set_state(AddPlace.wait_for_foto)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()
@router.message(AddPlace.wait_for_foto,F.photo)
async def add_photo(message:Message,state:FSMContext,bot:Bot,session:aiohttp.ClientSession):
    data = await state.get_data()
    photos_ids = data.get("photos",[])

    photos_ids.append(message.photo[-1].file_id)

    await state.update_data(photos = photos_ids)

    number_photo = len(photos_ids)

    if(number_photo<5):
        return

    encoded_phtos = []

    for photo_id in photos_ids:
        file = await bot.get_file(photo_id)

        photo_buffer = await bot.download_file(file.file_path)

        photo_byts = photo_buffer.read()
        base64photo = base64.b64encode(photo_byts).decode("utf-8")
        encoded_phtos.append(base64photo)
    
    place = Place()

    place.NameOfPlace =  data.get("title")
    place.Description =  data.get("discription")
    place.Address =  data.get("adress")

    place.Photo1 = encoded_phtos[0]
    place.Photo2 = encoded_phtos[1]
    place.Photo3 = encoded_phtos[2]
    place.Photo4 = encoded_phtos[3]
    place.Photo5 = encoded_phtos[4]

    result = await add_custom_place(place,session)

    if(result == True):
        await message.answer("Place added")
        await send_main_menu(message)
    else:
        await message.answer("We got error")
        await send_main_menu(message)


# Обробник кнопки "📍 Надіслати геолокацію" (показує вибір способу)
@router.message(F.text == "📍 Надіслати геолокацію")
async def choose_location_method(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BotState.choosing_location_type)
    await message.answer(
        "Оберіть спосіб передачі координат:",
        reply_markup=choose_location_type_keyboard()
    )


# Обробка вибору типу локації
@router.message(BotState.choosing_location_type)
async def handle_location_type_choice(message: Message, state: FSMContext):
    if message.text == "📍 Передати мою локацію":
        await message.answer("Будь ласка, надішліть свою геолокацію через кнопку нижче.")
    elif message.text == "🏙️ Знайти потрібне місто":
        await state.set_state(BotState.entering_coordinates)
        await message.answer("Введіть назву міста, для якого потрібно знайти координати:")
    else:
        await message.answer("Будь ласка, оберіть один із варіантів.", reply_markup=choose_location_type_keyboard())


# Команда /coordinates для отримання координат користувача
@router.message(Command("coordinates"))
async def show_user_coordinates(message: Message):
    coords = get_user_settings(message.from_user.id).get("coordinates")
    if coords:
        await message.answer(
            f"Ваші координати:\nШирота: {coords['latitude']}\nДовгота: {coords['longitude']}"
        )
    else:
        await message.answer("Координати не встановлено. Спочатку оберіть місто або надішліть свою геолокацію.")


def filter_open_now(places, open_now):
    if not open_now:
        return places
    return [p for p in places if (p.get("openNow") is True or p.get("OpenNow") is True)]


async def get_places_with_mood(settings, user_id: int, session: aiohttp.ClientSession):
    """Універсальний запит місць з урахуванням обраного настрою."""
    mood_mode = decode_included_types(user_id)
    try:
        data = await get_places(settings, session)
        if not data or "places" not in data:
            return data

        places = data["places"]

        # Застосовуємо фільтр "відкрите зараз", якщо увімкнено
        if settings.get("openNow", False):
            places = filter_open_now(places, True)

        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку.",
                parse_mode="HTML"
            )
            await message.answer("Повернутися до пошуку.", reply_markup=search_keyboard())
            return

        # Вибираємо випадкове місце
        chosen = random.choice(places)
        place_id = chosen.get("id") or chosen.get("Id")


        if place_id:
            language = settings.get("language", "uk")
            await loading_msg.delete()


            # Показуємо вибране місце
            success = await send_place_info(message, session, place_id, language)


            if not success:
                await message.answer(
                    "⚠️ <b>Не вдалося отримати деталі місця.</b>",
                    parse_mode="HTML"
                )
        else:
            await loading_msg.edit_text(
                "⚠️ <b>Помилка при виборі випадкового місця.</b>",
                parse_mode="HTML"
            )

    except Exception as e:
        logger.error(f"Error in random_place_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )
        await message.answer("Повернутися до пошуку.", reply_markup=search_keyboard())


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
            await message.answer("Повернутися до пошуку.", reply_markup=search_keyboard())
            return

        places = data["places"]
        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку.",
                parse_mode="HTML"
            )
            await message.answer("Повернутися до пошуку.", reply_markup=search_keyboard())
            return

        await loading_msg.edit_text(
            f"✅ <b>Знайдено {len(places)} місць:</b>\n"
            "Оберіть місце, щоб відкрити його на карті:",
            parse_mode="HTML",
            reply_markup=places_keyboard(places)
        )

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )
        await message.answer("Повернутися до пошуку.", reply_markup=search_keyboard())


@router.message(F.text == "🔙 Скасувати")
async def cancel_handler(message: Message,state:FSMContext):
async def cancel_handler(message: Message,state:FSMContext):
    await state.clear()
    await send_main_menu(message)


async def show_places_list(loading_msg, places, title: str = "Знайдено {count} місць"):
    """
    Оновлює повідомлення списком місць: клавіатура з назвами або текстовий fallback.
    title — рядок з плейсхолдером {count}.
    """
    count = len(places)
    heading = title.format(count=count)
    kb = places_keyboard(places)
    if not kb.inline_keyboard or len(kb.inline_keyboard) == 0:
        preview = []
        for idx, place in enumerate(places[:10], 1):
            name = place.get("displayName") or place.get("name") or "Без назви"
            address = place.get("shortFormattedAddress") or ""
            rating = place.get("rating")
            rating_str = f" | ⭐ {rating}" if rating else ""
            preview.append(
                f"<b>{idx}.</b> {name}{rating_str}\n<code>{address}</code>")
        text = "\n\n".join(preview)
        await loading_msg.edit_text(
            f"✅ <b>{heading}:</b>\n\n{text}",
            parse_mode="HTML"
        )
    else:
        await loading_msg.edit_text(
            f"✅ <b>{heading}:</b>\nОберіть місце, щоб відкрити його на карті:",
            parse_mode="HTML",
            reply_markup=kb
        )


async def perform_search(message: Message, session: aiohttp.ClientSession, show_list: bool = True):
    """
    Логіка пошуку місць поруч.
    Повертає (loading_msg, places) кортеж.
    У разі помилки обробляє UI оновлення та повертає (loading_msg, None).
    """
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) шукає місця поруч")

    loading_msg = await message.answer(
        "🔍 <b>Пошук місць поруч...</b>\n\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    at_night = decode_included_types(message.from_user.id)

    settings = get_user_settings(message.from_user.id)

    if not settings or not settings.get("coordinates"):
        await loading_msg.delete() 
        await message.answer(     
            "❌ <b>Помилка:</b> Не встановлено геолокацію!\n"
            "Оберіть спосіб передачі координат:",
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard()
        )
        return loading_msg, None

    try:
        data = await get_places_with_mood(settings, message.from_user.id, session)

        if not data or "places" not in data:
            await loading_msg.edit_text(
                "⚠️ <b>Нічого не знайдено</b> або сервер не відповідає.",
                parse_mode="HTML"
            )
            return

        places = data["places"]

        # Застосовуємо фільтр "відкрите зараз", якщо увімкнено
        if settings.get("openNow", False):
            places = filter_open_now(places, True)

        if not places:
            await loading_msg.edit_text(
                "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                "Спробуйте збільшити радіус пошуку.",
                parse_mode="HTML"
            )
            return

        if show_list:
            await show_places_list(loading_msg, places)

        return loading_msg, places

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при обробці запиту.</b>",
            parse_mode="HTML"
        )


async def send_place_info(
    message: Message,
    session: aiohttp.ClientSession,
    place_id: str,
    language: str,
    user_id: int | None = None,
):
    """
    Отримує деталі місця за його ID та відправляє їх користувачу.
    """
    uid = user_id if user_id is not None else (
        message.from_user.id if message.from_user else None)
    try:
        place = await get_place_details(place_id, session, language)
        if not place:
            return False

        photos = await get_photos(place_id, session)

        if photos and len(photos) > 0:
            try:
                media_group = []
                for photo in photos[:10]:
                    # Якщо API повертає URL напряму
                    if isinstance(photo, str):
                        media_group.append(InputMediaPhoto(media=photo))
                    # Якщо API повертає словник з полем photoUri або url
                    elif isinstance(photo, dict):
                        photo_url = photo.get('photoUri') or photo.get(
                            'url') or photo.get('uri')
                        photo_url = photo.get('photoUri') or photo.get(
                            'url') or photo.get('uri')
                        if photo_url:
                            media_group.append(
                                InputMediaPhoto(media=photo_url))

                            media_group.append(
                                InputMediaPhoto(media=photo_url))

                if media_group:
                    await message.answer_media_group(media_group)
                    logger.info(
                        f"Надіслано {len(media_group)} фото для місця {place_id}")
                    logger.info(
                        f"Надіслано {len(media_group)} фото для місця {place_id}")
            except Exception as e:
                logger.error(
                    f"Failed to send photos for place {place_id}: {e}")

        _place_name_cache[place_id] = place.get(
            "displayName") or place.get("name") or "Без назви"

        # Отримуємо координати користувача для розрахунку відстані
        user_coords = get_user_settings(uid).get("coordinates") if uid else None
        
        favorite_callback = f"fav_toggle:{place_id}" if place_id else None
        text = format_place_text(place, user_coords)
        is_fav = is_favorite_place(uid, place_id) if uid else False
        kb = place_details_keyboard(
            place.get("websiteUri"),
            place.get("googleMapsUri"),
            favorite_callback,
            is_fav,
        )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True
        )

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
        
        parse_mode="HTML",
        reply_markup=search_keyboard()
    )



@router.message(F.text == "🌟 Улюблені")
async def favorite_menu_handler(message: Message, state: FSMContext):
    """Показує меню дій для улюблених місць."""
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) переглядає меню улюблених")

    favorites = get_favorite_places(message.from_user.id)
    if not favorites:
        await message.answer(
            "🌟 <b>Улюблених місць поки немає</b>\n\n"
            "Спочатку додайте улюблені місця через пошук! 🔍",
            parse_mode="HTML",
            reply_markup=search_keyboard()
        )
        return

    await state.clear()
    await message.answer(
        f"🌟 <b>У вас {len(favorites)} улюблених місць</b>\n\n"
        "Що ви хочете зробити?",
        parse_mode="HTML",
        reply_markup=favorites_action_keyboard()
    )


@router.message(F.text == "🌟 Переглянути")
async def view_favorite_places_handler(message: Message, session: aiohttp.ClientSession):
    """Показує список улюблених місць для перегляду."""
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) переглядає улюблені місця")

    favorites = get_favorite_places(message.from_user.id)
    if not favorites:
        await message.answer("🌟 Улюблених місць поки немає.")
        return

    places = [{"id": p["id"], "displayName": p["name"]} for p in favorites]
    loading_msg = await message.answer("🌟 Завантаження улюблених місць...", parse_mode="HTML")
    await show_places_list(loading_msg, places, "Улюблені місця ({count})")


@router.message(F.text == "❤️ Випадкове з улюблених")
async def random_from_favorites_handler(message: Message, session: aiohttp.ClientSession):
    """Випадково обирає місце з улюблених."""
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) обирає випадкове місце з улюблених")

    user_id = message.from_user.id
    favorites = get_favorite_places(user_id)

    if not favorites:
        await message.answer(
            "🌟 Улюблених місць поки немає.\nДодайте місця через пошук.",
            reply_markup=search_keyboard(),
        )
        return

    await message.answer_dice(emoji="🎲")

    loading_msg = await message.answer(
        "⏳ <b>Крутимо рулетку...</b>\n"
        "Зачекайте, виконується запит до API...",
        parse_mode="HTML",
    )

    chosen = random.choice(favorites)
    place_for_kb = [{"id": chosen["id"], "displayName": chosen["name"]}]

    await loading_msg.edit_text(
        "🎲 <b>Випадкове місце з улюблених:</b>\n"
        "Оберіть місце, щоб відкрити його на карті:",
        parse_mode="HTML",
        reply_markup=places_keyboard(place_for_kb),
    )


@router.message(F.text == "⚖️ Порівняти")
async def start_comparison_handler(message: Message, state: FSMContext):
    """Розпочинає процес порівняння улюблених місць."""
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) розпочинає порівняння")

    favorites = get_favorite_places(message.from_user.id)
    if not favorites or len(favorites) < 2:
        await message.answer("⚖️ Потрібно мінімум 2 улюблених місця для порівняння.")
        return

    await state.set_state(BotState.comparing_favorites)
    await state.update_data(selected_for_comparison=[])

    kb = select_favorites_for_comparison_keyboard(favorites, [])
    await message.answer(
        "⚖️ <b>Обрати місця для порівняння:</b>\n\n"
        "Натисніть на місце, щоб обрати його для порівняння (мінімум 2):",
        parse_mode="HTML",
        reply_markup=kb
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

    success = await send_place_info(
        callback.message, session, place_id, language, user_id=callback.from_user.id
    )

    if not success:
        await callback.message.answer("⚠️ <b>Інформацію про це місце не знайдено.</b>", parse_mode="HTML")
        return


@router.callback_query(F.data.startswith("fav_toggle:"))
async def fav_toggle_handler(callback: CallbackQuery, session: aiohttp.ClientSession):
    """Додає або вилучає місце з улюблених (локально та на сервері)."""
    place_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    if is_favorite_place(user_id, place_id):
        remove_favorite_place(user_id, place_id)
        await api_remove_favorite(user_id, place_id, session)
        await callback.answer("❌ Вилучено з улюблених")
        return

    name = _place_name_cache.get(place_id, "Без назви")
    add_favorite_place(user_id, place_id, name)
    await api_add_favorite(user_id, place_id, name, session)
    await callback.answer("✅ Додано до улюблених")


@router.callback_query(F.data.startswith("compare_toggle:"), BotState.comparing_favorites)
async def compare_toggle_handler(callback: CallbackQuery, state: FSMContext):
    """Додає або видаляє місце із виділення для порівняння."""
    place_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    data = await state.get_data()
    selected_ids = data.get("selected_for_comparison", [])

    if place_id in selected_ids:
        selected_ids.remove(place_id)
    else:
        selected_ids.append(place_id)

    await state.update_data(selected_for_comparison=selected_ids)

    # Оновлюємо клавіатуру
    favorites = get_favorite_places(user_id)
    kb = select_favorites_for_comparison_keyboard(favorites, selected_ids)

    await callback.message.edit_reply_markup(reply_markup=kb)

    count = len(selected_ids)
    if count >= 2:
        await callback.answer(f"✅ Обрано {count} місць")
    else:
        await callback.answer(f"️ Обрано {count} / мінімум 2")


@router.callback_query(F.data == "perform_comparison", BotState.comparing_favorites)
async def perform_comparison_handler(callback: CallbackQuery, state: FSMContext, session: aiohttp.ClientSession):
    """Виконує порівняння обраних місць."""
    user_id = callback.from_user.id
    data = await state.get_data()
    selected_ids = data.get("selected_for_comparison", [])

    if len(selected_ids) < 2:
        await callback.answer("⚠️ Потрібно обрати мінімум 2 місця", show_alert=True)
        return

    await callback.answer()

    # Показуємо повідомлення про завантаження
    loading_msg = await callback.message.answer(
        "⚖️ <b>Завантаження деталей для порівняння...</b>\n"
        "⏳ Зачекайте, виконується запит до API...",
        parse_mode="HTML"
    )

    try:
        # Отримуємо деталі всіх вибраних місць
        favorites = get_favorite_places(user_id)
        settings = get_user_settings(user_id)
        language = settings.get("language", "uk")
        user_coords = settings.get("coordinates")

        places_details = []
        for place_id in selected_ids:
            # Знаходимо улюблене місце у списку
            favorite = next((p for p in favorites if p["id"] == place_id), None)
            if not favorite:
                continue

            # Отримуємо деталі місця
            place_details = await get_place_details(place_id, session, language)
            if place_details:
                places_details.append(place_details)

        if not places_details:
            await loading_msg.edit_text(
                "⚠️ <b>Не вдалося отримати деталі місць.</b>",
                parse_mode="HTML"
            )
            return

        # Форматуємо й надсилаємо порівняння
        comparison_text = format_comparison_text(places_details, user_coords)
        await loading_msg.edit_text(comparison_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in perform_comparison_handler: {e}")
        await loading_msg.edit_text(
            "❌ <b>Сталася помилка при порівнянні місць.</b>",
            parse_mode="HTML"
        )
    finally:
        await state.clear()


@router.callback_query(F.data == "cancel_comparison", BotState.comparing_favorites)
async def cancel_comparison_handler(callback: CallbackQuery, state: FSMContext):
    """Скасовує порівняння й повертається до меню."""
    await state.clear()
    await callback.answer()
    await callback.message.edit_text(
        "❌ Порівняння скасовано.",
        parse_mode="HTML"
    )
    await callback.message.answer("Повернулися до головного меню.", reply_markup=search_keyboard())


@router.callback_query(F.data == "comparison_help", BotState.comparing_favorites)
async def comparison_help_handler(callback: CallbackQuery):
    """Показує довідку про мінімальну кількість місць для порівняння."""
    await callback.answer(
        "Обрати мінімум 2 місця для порівняння",
        show_alert=False
    )
