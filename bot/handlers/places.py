from aiogram.types import CallbackQuery
import aiohttp
import random
import base64
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter

from bot.handlers.main_menu import send_main_menu
from bot.keyboards import (
    place_navigation_keyboard,
    search_keyboard,
    random_choice_keyboard,
    places_keyboard,
    place_details_keyboard,
    choose_location_type_keyboard,
    favorites_action_keyboard,
    select_favorites_for_comparison_keyboard,
    error_action_keyboard,
    error_action_inline_keyboard,
)
from bot.services.api_client import (
    get_photos,
    get_places,
    get_place_details,
    api_add_favorite,
    api_remove_favorite,
    search_places_by_text,
    search_places_by_text,
)
from bot.services.settings import (
    add_favorite_place,
    get_favorite_places,
    get_user_settings,
    is_favorite_place,
    remove_favorite_place,
)
from bot.states import BotState, AddPlace
import asyncio
from bot.utils.formatter import format_place_text, format_comparison_text
from bot.utils.logger import logger
from bot.utils.localization import i18n


# Placeholder class for custom place


class Place:
    def __init__(self):
        self.NameOfPlace = ""
        self.Description = ""
        self.Address = ""
        self.Photo1 = ""
        self.Photo2 = ""
        self.Photo3 = ""
        self.Photo4 = ""
        self.Photo5 = ""

# Placeholder function for adding custom place


async def add_custom_place(place, session):
    logger.warning("add_custom_place not fully implemented")
    return False

# Placeholder function for decoding included types


def decode_included_types(user_id):
    return []


router = Router()
_place_name_cache: dict[str, str] = {}


@router.callback_query(F.data == "error_back_to_menu")
async def error_back_to_menu_callback(callback: CallbackQuery):
    await callback.answer()
    from bot.handlers.main_menu import send_main_menu
    await send_main_menu(callback.message, force_main_menu_keyboard=True)


@router.callback_query(F.data == "error_retry")
async def error_retry_callback(callback: CallbackQuery, state: FSMContext, session: aiohttp.ClientSession = None):
    await callback.answer()
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    data = await state.get_data()
    last_error_type = data.get("last_error_type")
    user_settings = get_user_settings(user_id)
    has_coordinates = user_settings and user_settings.get("coordinates")
    # Only retry place search if last error was server_unavailable and coordinates exist
    if last_error_type == "server_unavailable" and has_coordinates:
        from bot.handlers.places import perform_search, show_place_card
        loading_msg, places = await perform_search(callback.message, session, show_list=False, state=state)
        if not places:
            return
        await state.set_state(BotState.browsing_places)
        await state.update_data(places=places, current_index=0)
        try:
            await loading_msg.delete()
        except Exception as e:
            logger.warning(f"Could not delete loading message: {e}")
        await show_place_card(callback.message, state, session)
    else:
        # Fallback: ask for location type
        from bot.keyboards import choose_location_type_keyboard
        await callback.message.answer(
            i18n.get(user_id, 'choose_location_type', lang_code),
            reply_markup=choose_location_type_keyboard(user_id, lang_code)
        )
        await state.set_state(BotState.choosing_location_type)

# @router.message(F.text == "📌 Додати своє місце")
# async def add_place_handler(message: Message, state: FSMContext):
#     logger.info(
#         f"Користувач {message.from_user.username} ({message.from_user.id}) додає своє місце"
#     )
#     await message.answer('Введи назву місця')
#     await state.set_state(AddPlace.wait_for_title)


@router.message(AddPlace.wait_for_title)
async def add_title(message: Message, state: FSMContext):
    info = message.text
    await state.update_data(title=info)
    data = await state.get_data()
    saved = data.get("title")

    if (saved == info):
        logger.info("title local saved")
        await message.answer("[Назва збережена]\nВведи опис місця")
        await state.set_state(AddPlace.wait_for_discription)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()


@router.message(AddPlace.wait_for_discription)
async def add_discription(message: Message, state: FSMContext):
    info = message.text
    await state.update_data(discription=info)
    data = await state.get_data()
    saved = data.get("discription")

    if (saved == info):
        logger.info("discription local saved")
        await message.answer("[Опис збережений]\nВведи адресу місця")
        await state.set_state(AddPlace.wait_for_shor_adress)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()


@router.message(AddPlace.wait_for_shor_adress)
async def add_adress(message: Message, state: FSMContext):
    info = message.text
    await state.update_data(adress=info)
    data = await state.get_data()
    saved = data.get("adress")

    if (saved == info):
        logger.info("adress local saved")
        await message.answer("[Адреса збережена]\nНадай 5 фото місцевості")
        await state.set_state(AddPlace.wait_for_foto)
    else:
        await message.answer("[помилка в збережені]")
        send_main_menu()


@router.message(AddPlace.wait_for_foto, F.photo)
async def add_photo(message: Message, state: FSMContext, bot: Bot, session: aiohttp.ClientSession):
    data = await state.get_data()
    photos_ids = data.get("photos", [])

    photos_ids.append(message.photo[-1].file_id)

    await state.update_data(photos=photos_ids)

    number_photo = len(photos_ids)

    if (number_photo < 5):
        return

    encoded_phtos = []

    for photo_id in photos_ids:
        file = await bot.get_file(photo_id)

        photo_buffer = await bot.download_file(file.file_path)

        photo_byts = photo_buffer.read()
        base64photo = base64.b64encode(photo_byts).decode("utf-8")
        encoded_phtos.append(base64photo)

    place = Place()

    place.NameOfPlace = data.get("title")
    place.Description = data.get("discription")
    place.Address = data.get("adress")

    place.Photo1 = encoded_phtos[0]
    place.Photo2 = encoded_phtos[1]
    place.Photo3 = encoded_phtos[2]
    place.Photo4 = encoded_phtos[3]
    place.Photo5 = encoded_phtos[4]

    result = await add_custom_place(place, session)

    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    if (result == True):
        await message.answer(i18n.get(user_id, 'place_added_success', lang_code))
        await send_main_menu(message)
    else:
        await message.answer(i18n.get(user_id, 'place_added_error', lang_code))
        await send_main_menu(message)


# Обробник кнопки "📍 Надіслати геолокацію" (показує вибір способу)
@router.message(F.text == "📍 Надіслати геолокацію")
async def choose_location_method(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    await state.clear()
    await state.set_state(BotState.choosing_location_type)
    msg_text = i18n.get(user_id, 'choose_location_method', lang_code)
    await message.answer(
        msg_text,
        reply_markup=choose_location_type_keyboard()
    )


# Обробка вибору типу локації
@router.message(BotState.choosing_location_type, F.text.in_([
    # send_location — all locales
    "📍 Передати мою локацію", "📍 Send my location", "📍 Meinen Standort senden",
    "📍 Envoyer ma position", "📍 Enviar mi ubicación", "📍 Invia la mia posizione",
    "📍 Wyślij moją lokalizację", "📍 Enviar minha localização", "📍 現在地を送信", "📍 发送我的位置",
    # find_city — all locales
    "🏙️ Знайти потрібне місто", "🏙️ Find a city", "🏙️ Stadt finden",
    "🏙️ Trouver une ville", "🏙️ Encontrar ciudad", "🏙️ Trova città",
    "🏙️ Znajdź miasto", "🏙️ Encontrar cidade", "🏙️ 都市を検索", "🏙️ 查找城市",
]))
async def handle_location_type_choice(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    if message.text == "📍 Передати мою локацію":
        msg_text = i18n.get(user_id, 'send_location_request', lang_code)
        await message.answer(msg_text)
    elif message.text == "🏙️ Знайти потрібне місто":
        await state.set_state(BotState.entering_coordinates)
        msg_text = i18n.get(user_id, 'enter_city_name_prompt', lang_code)
        await message.answer(msg_text)
    else:
        msg_text = i18n.get(user_id, 'choose_variant', lang_code)
        await message.answer(msg_text, reply_markup=choose_location_type_keyboard())


# Команда /coordinates для отримання координат користувача
@router.message(Command("coordinates"))
async def show_user_coordinates(message: Message):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    coords = settings.get("coordinates")
    if coords:
        title = i18n.get(user_id, 'your_coordinates', lang_code)
        await message.answer(
            f"<b>{title}</b>\nLatitude: {coords['latitude']}\nLongitude: {coords['longitude']}",
            parse_mode="HTML"
        )
    else:
        msg_text = i18n.get(user_id, 'coordinates_not_set', lang_code)
        await message.answer(msg_text)


def filter_open_now(places, open_now):
    if not open_now:
        return places
    return [p for p in places if (p.get("openNow") is True or p.get("OpenNow") is True)]


async def get_places_with_mood(settings, user_id: int, session: aiohttp.ClientSession, message=None, loading_msg=None):
    """Універсальний запит місць з урахуванням обраного настрою."""
    mood_mode = decode_included_types(user_id)
    lang_code = settings.get("language", "uk")
    try:
        data = await get_places(settings, session)
        if not data or "places" not in data:
            return data

        places = data["places"]

        # Застосовуємо фільтр "відкрите зараз", якщо увімкнено
        if settings.get("openNow", False):
            places = filter_open_now(places, True)

        if not places:
            if loading_msg:
                await loading_msg.edit_text(
                    "📭 <b>На жаль, місць поруч не знайдено.</b>\n"
                    "Спробуйте збільшити радіус пошуку.",
                    parse_mode="HTML",
                    reply_markup=error_action_inline_keyboard(
                        user_id, lang_code)
                )
            if message:
                await message.answer("🔙 Повернулись у меню пошуку.", reply_markup=search_keyboard(user_id, lang_code))
            return None

        # Повертаємо всі місця
        return {"places": places}

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        edit_failed = False
        if loading_msg:
            try:
                kb = error_action_inline_keyboard(user_id, lang_code)
                logger.info(
                    f"[edit_text DIAG] server_unavailable: reply_markup type: {type(kb)}")
                await loading_msg.edit_text(
                    i18n.get(user_id, 'server_unavailable', lang_code),
                    parse_mode="HTML",
                    reply_markup=kb
                )
            except Exception as edit_error:
                logger.warning(f"Could not edit loading message: {edit_error}")
                edit_failed = True
                # Спробуємо видалити зависле повідомлення
                try:
                    await loading_msg.delete()
                except Exception as del_error:
                    logger.warning(
                        f"Could not delete loading message: {del_error}")
        if message:
            # Якщо не вдалося відредагувати loading_msg, надсилаємо окреме повідомлення про помилку
            if edit_failed or not loading_msg:
                try:
                    await message.answer(
                        i18n.get(user_id, 'server_unavailable', lang_code),
                        reply_markup=search_keyboard(user_id, lang_code)
                    )
                except Exception as answer_error:
                    logger.warning(
                        f"Could not send server unavailable message: {answer_error}")
            # Очищаємо стан і повертаємо у головне меню
            from aiogram.fsm.context import FSMContext
            if hasattr(message, 'bot') and hasattr(message, 'chat'):
                # Отримуємо FSMContext для цього користувача
                state = FSMContext(
                    message.bot, message.chat.id, message.from_user.id)
                await state.clear()
            try:
                from .main_menu import send_main_menu
                await send_main_menu(message)
            except Exception as e:
                logger.warning(
                    f"Could not send main menu after server error: {e}")


# Universal cancel handler for any state
@router.message(F.text.in_(["🔙 Скасувати", "🔙 Cancel", "🔙 Abbrechen", "🔙 Annuler", "🔙 Cancelar", "🔙 Annulla", "🔙 Anuluj", "🔙 Cancelar", "🔙 キャンセル", "🔙 取消"]))
async def cancel_any_state_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    await state.clear()
    await message.answer(i18n.get(user_id, 'search_cancelled', lang_code))
    await send_main_menu(message)


# ----- Text Search Handlers (Пошук за назвою) -----

@router.message(F.text.in_(["🔎 Пошук за назвою", "🔎 Search by name", "🔎 Nach Name suchen", "🔎 Rechercher par nom", "🔎 Buscar por nombre", "🔎 Cerca per nome", "🔎 Szukaj po nazwie", "🔎 Pesquisar por nome", "🔎 名前で検索", "🔎 按名称搜索"]))
async def start_text_search(message: Message, state: FSMContext):
    """Обробник кнопки 'Пошук за назвою' — запускає стан очікування тексту."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    logger.info(
        f"[TextSearch] User {message.from_user.username} ({user_id}) started text search")

    # Перевіряємо, чи є координати
    if not settings.get("coordinates"):
        logger.warning(f"[TextSearch] User {user_id} has no coordinates set")
        await message.answer(
            i18n.get(user_id, 'no_location_set', lang_code),
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard(user_id, lang_code)
        )
        return

    await state.set_state(BotState.waiting_for_text_search)
    await message.answer(
        i18n.get(user_id, 'enter_search_query', lang_code),
        parse_mode="HTML",
        reply_markup=search_keyboard(user_id, lang_code)
    )


@router.message(BotState.waiting_for_text_search, F.text.in_(["🔙 Скасувати", "🔙 Cancel", "🔙 Abbrechen", "🔙 Annuler", "🔙 Cancelar", "🔙 Annulla", "🔙 Anuluj", "🔙 Cancelar", "🔙 キャンセル", "🔙 取消"]))
async def cancel_text_search(message: Message, state: FSMContext):
    """Скасовує пошук за назвою та повертає до головного меню."""
    user_id = message.from_user.id
    logger.info(f"[TextSearch] User {user_id} cancelled text search")
    await state.clear()
    await send_main_menu(message)


@router.message(BotState.waiting_for_text_search)
async def process_text_search(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    """Обробляє текстовий запит пошуку місць."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    query = message.text.strip()
    # Не обробляти службові команди як запит
    cancel_texts = [
        i18n.get(user_id, 'menu_cancel', lang_code),
        '/coordinates',
        '/menu',
        '/start'
    ]
    if query in cancel_texts:
        await send_main_menu(message)
        return
    # Валідація запиту
    if not query or len(query) < 2:
        logger.warning(
            f"[TextSearch] User {user_id} entered too short query: '{query}'")
        await message.answer(
            i18n.get(user_id, 'category_too_short', lang_code),
            parse_mode="HTML"
        )
        return

    logger.info(
        f"[TextSearch] User {message.from_user.username} ({user_id}) searching for: '{query}'")

    # Відправляємо повідомлення про завантаження
    loading_msg = await message.answer(
        i18n.get(user_id, 'searching_places', lang_code, query=query),
        parse_mode="HTML"
    )

    try:
        # Виконуємо пошук через API
        data = await search_places_by_text(query, settings, session)

        if not data or "places" not in data or not data["places"]:
            logger.info(f"[TextSearch] No results found for query: '{query}'")
            try:
                await loading_msg.edit_text(
                    i18n.get(user_id, 'text_search_no_results',
                             lang_code, query=query),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(
                    f"[TextSearch] Could not edit loading message: {e}")
            await state.clear()
            await send_main_menu(message)
            return

        places = data["places"]
        places_count = len(places)
        logger.info(
            f"[TextSearch] Found {places_count} places for query: '{query}'")

        # Показуємо повідомлення про кількість знайдених
        title = i18n.get(user_id, 'text_search_results',
                         lang_code, query=query) + f" ({places_count})"
        try:
            await loading_msg.edit_text(f"✅ <b>{title}</b>", parse_mode="HTML")
        except Exception:
            pass

        # Зберігаємо місця в стан і запускаємо навігацію по 1 закладу
        await state.set_state(BotState.browsing_places)
        await state.update_data(places=places, current_index=0)
        await show_place_card(message, state, session)

    except Exception as e:
        logger.error(f"[TextSearch] Error during search for '{query}': {e}")
        edit_failed = False
        try:
            kb = error_action_inline_keyboard(user_id, lang_code)
            logger.info(
                f"[edit_text DIAG] text_search_error: reply_markup type: {type(kb)}")
            await loading_msg.edit_text(
                i18n.get(user_id, 'text_search_error', lang_code),
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception as edit_error:
            logger.warning(
                f"[TextSearch] Could not edit loading message: {edit_error}")
            edit_failed = True
            # Спробуємо видалити зависле повідомлення
            try:
                await loading_msg.delete()
            except Exception as del_error:
                logger.warning(
                    f"Could not delete loading message: {del_error}")
        if edit_failed:
            try:
                await message.answer(
                    i18n.get(user_id, 'text_search_error', lang_code),
                    reply_markup=search_keyboard(user_id, lang_code)
                )
            except Exception as answer_error:
                logger.warning(
                    f"[TextSearch] Could not send error message: {answer_error}")
        await state.clear()
        await send_main_menu(message)


async def show_places_list(loading_msg, places, title: str = None, user_id: int | None = None, lang_code: str = "uk"):
    """
    Оновлює повідомлення списком місць: клавіатура з назвами або текстовий fallback.
    title — рядок з плейсхолдером {count}. Якщо None, використовуємо localized 'places_found'.
    """
    count = len(places)
    if title is None:
        title = i18n.get(user_id, 'places_found', lang_code, count=count)
    else:
        title = title.format(count=count)
    heading = title
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
        try:
            await loading_msg.edit_text(
                f"✅ <b>{heading}:</b>\n\n{text}",
                parse_mode="HTML",
                reply_markup=error_action_inline_keyboard(user_id, lang_code)
            )
        except Exception as e:
            logger.warning(f"Could not edit loading message: {e}")
    else:
        select_text = i18n.get(user_id, 'select_place', lang_code)
        try:
            await loading_msg.edit_text(
                f"✅ <b>{heading}:</b>\n{select_text}",
                parse_mode="HTML",
                reply_markup=kb
            )
        except Exception as e:
            logger.warning(f"Could not edit loading message: {e}")
            try:
                await loading_msg.edit_text(
                    f"✅ <b>{heading}:</b>\n{select_text}",
                    parse_mode="HTML",
                    reply_markup=error_action_inline_keyboard(
                        user_id, lang_code)
                )
            except Exception as e2:
                logger.warning(
                    f"Could not edit loading message with error menu: {e2}")


async def perform_search(message: Message, session: aiohttp.ClientSession, show_list: bool = True, user_id: int | None = None, state: FSMContext = None):
    """
    Логіка пошуку місць поруч.
    Повертає (loading_msg, places) кортеж.
    У разі помилки обробляє UI оновлення та повертає (loading_msg, None).
    """
    start_user_id = user_id if user_id is not None else message.from_user.id
    logger.info(
        f"Користувач {message.from_user.username}({start_user_id}) шукає місця поруч")

    settings = get_user_settings(start_user_id)
    # Мова з налаштувань користувача
    lang_code = settings.get("language", "uk")

    loading_msg = await message.answer(
        i18n.get(start_user_id, 'search_loading', lang_code),
        parse_mode="HTML"
    )

    at_night = decode_included_types(start_user_id)
    settings = get_user_settings(start_user_id)

    if not settings or not settings.get("coordinates"):
        try:
            await loading_msg.delete()
        except Exception as e:
            logger.warning(f"Could not delete loading message: {e}")
        await message.answer(
            i18n.get(start_user_id, 'no_location_set', lang_code),
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard(
                start_user_id, lang_code)
        )
        if state:
            await state.update_data(last_error_type="no_coordinates")
        return loading_msg, None

    try:
        data = await get_places_with_mood(settings, start_user_id, session, message, loading_msg)

        if not data or "places" not in data:
            try:
                await loading_msg.delete()
            except Exception as e:
                logger.warning(f"Could not delete loading message: {e}")
            await message.answer(
                i18n.get(start_user_id, 'server_unavailable', lang_code),
                parse_mode="HTML",
                reply_markup=error_action_inline_keyboard(
                    start_user_id, lang_code)
            )
            if state:
                await state.update_data(last_error_type="server_unavailable")
            return None, None

        places = data["places"]

        if not places:
            try:
                await loading_msg.edit_text(
                    i18n.get(start_user_id, 'no_random_places', lang_code),
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.warning(f"Could not edit loading message: {e}")
            return loading_msg, None

        if show_list:
            user_id = start_user_id
            settings = get_user_settings(user_id)
            lang_code = settings.get("language", "uk")
            await show_places_list(loading_msg, places, user_id=user_id, lang_code=lang_code)

        return loading_msg, places

    except Exception as e:
        logger.error(f"Error in find_places_handler: {e}")
        try:
            await loading_msg.delete()
        except Exception as del_error:
            logger.warning(f"Could not delete loading message: {del_error}")
        await message.answer(
            i18n.get(start_user_id, 'server_unavailable', lang_code),
            parse_mode="HTML",
            reply_markup=error_action_inline_keyboard(start_user_id, lang_code)
        )
        if state:
            await state.update_data(last_error_type="server_unavailable")
        return None, None


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
    sent_message_ids = []
    try:
        place = await get_place_details(place_id, session, language)
        if not place:
            return False, []

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
                        if photo_url:
                            media_group.append(
                                InputMediaPhoto(media=photo_url))

                if media_group:
                    media_messages = await message.answer_media_group(media_group)
                    sent_message_ids.extend(
                        m.message_id for m in media_messages)
                    logger.info(
                        f"Надіслано {len(media_group)} фото для місця {place_id}")

            except Exception as e:
                logger.error(
                    f"Failed to send photos for place {place_id}: {e}")

        _place_name_cache[place_id] = place.get(
            "displayName") or place.get("name") or "Без назви"

        # Отримуємо координати користувача для розрахунку відстані та мову з налаштувань
        user_settings = get_user_settings(uid) if uid else {}
        user_coords = user_settings.get("coordinates")
        # Використовуємо мову з налаштувань
        lang_code = user_settings.get("language", language)

        favorite_callback = f"fav_toggle:{place_id}" if place_id else None
        text = format_place_text(place, user_coords, uid, lang_code)
        is_fav = is_favorite_place(uid, place_id) if uid else False
        kb = place_details_keyboard(
            place.get("websiteUri"),
            place.get("googleMapsUri"),
            favorite_callback,
            is_fav,
            uid,
            lang_code
        )

        text_msg = await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=kb,
            disable_web_page_preview=True
        )
        sent_message_ids.append(text_msg.message_id)

        if place.get("latitude") and place.get("longitude"):
            loc_msg = await message.answer_location(
                latitude=place["latitude"],
                longitude=place["longitude"]
            )
            sent_message_ids.append(loc_msg.message_id)

        return True, sent_message_ids

    except Exception as e:
        logger.error(f"Error sending place info: {e}")
        return False, []


@router.message(Command("place_list"))
async def list_places_handler(message: Message, session: aiohttp.ClientSession):
    """Показує список усіх знайдених місць."""
    result = await perform_search(message, session)

    if result is None or result[1] is None:
        return

    loading_msg, places = result


@router.message(F.text.in_(["🚀 Місця поблизу", "🚀 Nearby places", "🚀 Orte in der Nähe", "🚀 Lieux à proximité", "🚀 Lugares cercanos", "🚀 Luoghi vicini", "🚀 Miejsca w pobliżu", "🚀 Locais próximos", "🚀 近くの場所", "🚀 附近地点"]))
async def search_menu_handler(message: Message, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    logger.info(
        f"Користувач {message.from_user.username}({user_id}) запускає пошук місць поблизу")

    # Telegram rejects empty/invisible-only text, so use a minimal visible marker.
    msg_text = "🔎"
    await message.answer(
        msg_text,
        parse_mode="HTML",
        reply_markup=search_keyboard(user_id, lang_code)
    )


@router.message(Command("rand_place"))
async def random_choice_menu_handler(message: Message, state: FSMContext):
    """Показує вибір: випадкове з пошуку чи з улюблених."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    await state.clear()
    await state.set_state(BotState.choosing_random_type)
    msg_text = i18n.get(user_id, 'choose_random_source', lang_code)
    await message.answer(
        msg_text,
        parse_mode="HTML",
        reply_markup=random_choice_keyboard(user_id, lang_code),
    )


@router.message(StateFilter(BotState.choosing_random_type), F.text.in_(["🔙 Скасувати", "🔙 Cancel", "🔙 Abbrechen", "🔙 Annuler", "🔙 Cancelar", "🔙 Annulla", "🔙 Anuluj", "🔙 Cancelar", "🔙 キャンセル", "🔙 取消"]))
async def random_choice_back_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    await state.clear()
    msg_text = i18n.get(user_id, 'back_to_search_menu', lang_code)
    await message.answer(msg_text, reply_markup=search_keyboard(user_id, lang_code))


@router.message(F.text.in_(["🌟 Улюблені", "🌟 Favorites", "🌟 Favoriten", "🌟 Favoris", "🌟 Favoritos", "🌟 Preferiti", "🌟 Ulubione", "🌟 Favoritos", "🌟 お気に入り", "🌟 收藏"]))
async def favorite_menu_handler(message: Message, state: FSMContext):
    """Показує меню дій для улюблених місць."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    logger.info(
        f"Користувач {message.from_user.username}({user_id}) переглядає меню улюблених")

    favorites = get_favorite_places(user_id)
    if not favorites:
        msg_text = i18n.get(user_id, 'no_favorites_yet', lang_code)
        await message.answer(
            msg_text,
            parse_mode="HTML",
            reply_markup=search_keyboard(user_id, lang_code)
        )
        return

    await state.clear()
    msg_text = i18n.get(user_id, 'favorites_count',
                        lang_code, count=len(favorites))
    await message.answer(
        msg_text,
        parse_mode="HTML",
        reply_markup=favorites_action_keyboard(user_id, lang_code)
    )


@router.message(F.text.in_(["🌟 Переглянути", "🌟 View", "🌟 Anzeigen", "🌟 Afficher", "🌟 Ver", "🌟 Visualizza", "🌟 Wyświetl", "🌟 Visualizar", "🌟 表示", "🌟 查看"]))
async def view_favorite_places_handler(message: Message, session: aiohttp.ClientSession):
    """Показує список улюблених місць для перегляду."""
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) переглядає улюблені місця")

    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    favorites = get_favorite_places(user_id)
    if not favorites:
        await message.answer(i18n.get(user_id, 'comparison_no_favorites', lang_code))
        return

    places = [{"id": p["id"], "displayName": p["name"]} for p in favorites]
    loading_msg = await message.answer(i18n.get(user_id, 'loading_favorites', lang_code), parse_mode="HTML")
    title = i18n.get(user_id, 'favorites_list_title',
                     lang_code, count=len(favorites))
    await show_places_list(loading_msg, places, title, user_id=user_id, lang_code=lang_code)


@router.message(F.text.in_(["❤️ Випадкове з улюблених", "❤️ Random from favorites", "❤️ Zufällig aus Favoriten", "❤️ Aléatoire des favoris", "❤️ Aleatorio de favoritos", "❤️ Casuale dai preferiti", "❤️ Losowe z ulubionych", "❤️ Aleatório dos favoritos", "❤️ お気に入りからランダム", "❤️ 从收藏中随机"]))
async def random_from_favorites_handler(message: Message, state: FSMContext):
    """Випадково обирає місце з улюблених."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    logger.info(
        f"Користувач {message.from_user.username}({user_id}) обирає випадкове місце з улюблених")

    await state.clear()

    favorites = get_favorite_places(user_id)

    if not favorites:
        await message.answer(
            i18n.get(user_id, 'comparison_no_favorites', lang_code),
            reply_markup=search_keyboard(user_id, lang_code),
        )
        return

    await message.answer_dice(emoji="🎲")

    loading_msg = await message.answer(
        i18n.get(user_id, 'spinning_wheel', lang_code),
        parse_mode="HTML",
    )

    chosen = random.choice(favorites)
    chosen_id = chosen["id"]
    chosen_name = chosen["name"]
    place_for_kb = [{"id": chosen_id, "displayName": chosen_name}]

    title = i18n.get(user_id, 'random_from_favorites_title', lang_code)
    select_text = i18n.get(user_id, 'select_place', lang_code)
    await loading_msg.edit_text(
        f"{title}\n{select_text}",
        parse_mode="HTML",
        reply_markup=places_keyboard(
            [{"id": chosen_id, "displayName": chosen_name}]),
    )


@router.message(F.text.in_(["🔍 З результатів пошуку", "🔍 From search results", "🔍 Aus Suchergebnissen", "🔍 Des résultats de recherche", "🔍 De resultados de búsqueda", "🔍 Dai risultati di ricerca", "🔍 Z wyników wyszukiwania", "🔍 Dos resultados da pesquisa", "🔍 検索結果から", "🔍 从搜索结果"]))
async def random_place_handler(message: Message, session: aiohttp.ClientSession, state: FSMContext):
    """Випадково обирає місце з результатів пошуку за поточними налаштуваннями."""
    await state.clear()
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    if not settings.get("coordinates"):
        await message.answer(
            i18n.get(user_id, 'no_location_set', lang_code),
            parse_mode="HTML",
            reply_markup=search_keyboard(user_id, lang_code),
        )
        await state.clear()
        return

    await message.answer_dice(emoji="🎲")
    loading_msg = await message.answer(
        i18n.get(user_id, 'spinning_search', lang_code),
        parse_mode="HTML",
    )

    data = await get_places_with_mood(settings, user_id, session)
    places = (data or {}).get("places", [])
    places = filter_open_now(places, settings.get("openNow", False))

    if not places:
        await loading_msg.edit_text(
            i18n.get(user_id, 'no_places_with_filters', lang_code),
            parse_mode="HTML",
        )
        await message.answer(
            i18n.get(user_id, 'back_to_search_menu', lang_code),
            reply_markup=search_keyboard(user_id, lang_code),
        )
        await state.clear()
        return

    chosen = random.choice(places)
    chosen_id = chosen.get("id") or chosen.get("Id")
    chosen_name = chosen.get("displayName") or chosen.get(
        "DisplayName") or chosen.get("name") or "Місце"

    select_text = i18n.get(user_id, 'select_place', lang_code)
    random_title = i18n.get(user_id, 'random_place_from_search', lang_code)
    await loading_msg.edit_text(
        f"🎲 <b>{random_title}</b>\n{select_text}",
        parse_mode="HTML",
        reply_markup=places_keyboard(
            [{"id": chosen_id, "displayName": chosen_name}]),
    )
    await message.answer(
        i18n.get(user_id, 'back_to_search_menu', lang_code),
        reply_markup=search_keyboard(user_id, lang_code),
    )
    await state.clear()


@router.message(F.text.in_(["⚖️ Порівняти", "⚖️ Compare", "⚖️ Vergleichen", "⚖️ Comparer", "⚖️ Comparar", "⚖️ Confronta", "⚖️ Porównaj", "⚖️ Comparar", "⚖️ 比較", "⚖️ 比较"]))
async def start_comparison_handler(message: Message, state: FSMContext):
    """Розпочинає процес порівняння улюблених місць."""
    logger.info(
        f"Користувач {message.from_user.username}({message.from_user.id}) розпочинає порівняння")

    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    favorites = get_favorite_places(user_id)
    if not favorites or len(favorites) < 2:
        await message.answer(i18n.get(user_id, 'comparison_min_2', lang_code))
        return

    await state.set_state(BotState.comparing_favorites)
    await state.update_data(selected_for_comparison=[])

    kb = select_favorites_for_comparison_keyboard(
        favorites, [], user_id, lang_code)
    msg_text = i18n.get(user_id, 'comparison_select_places', lang_code)
    await message.answer(
        msg_text,
        parse_mode="HTML",
        reply_markup=kb
    )


async def show_place_card(message: Message, state: FSMContext, session: aiohttp.ClientSession, user_id: int | None = None):
    start_user_id = user_id if user_id is not None else message.from_user.id
    settings = get_user_settings(start_user_id)
    lang_code = settings.get("language", "uk")
    data = await state.get_data()
    places = data.get("places", [])
    index = data.get("current_index", 0)

    if not places:
        msg_text = i18n.get(start_user_id, 'places_list_empty', lang_code)
        await message.answer(msg_text)
        await state.clear()
        return

    if index < 0:
        index = 0
    if index >= len(places):
        msg_text = i18n.get(start_user_id, 'last_place_reached', lang_code)
        await message.answer(msg_text)
        index = len(places) - 1
        await state.update_data(current_index=index)

    place_summary = places[index]
    place_id = place_summary.get("id") or place_summary.get("Id")

    language = lang_code

    loading_msg = await message.answer(i18n.get(start_user_id, 'loading_info', lang_code))

    success, place_msg_ids = await send_place_info(message, session, place_id, language, user_id=start_user_id)

    if not success:
        msg_text = i18n.get(start_user_id, 'place_details_error', lang_code)
        await loading_msg.edit_text(msg_text)
        return

    await loading_msg.delete()
    msg_text = i18n.get(start_user_id, 'place_index', lang_code,
                        current=index + 1, total=len(places))
    index_msg = await message.answer(
        msg_text,
        parse_mode="HTML",
        reply_markup=place_navigation_keyboard(start_user_id, lang_code)
    )
    all_place_msg_ids = place_msg_ids + [index_msg.message_id]
    await state.update_data(last_place_message_ids=all_place_msg_ids)


@router.message(F.text.in_(["🚀 Місця", "🚀 Places", "🚀 Orte", "🚀 Lieux", "🚀 Lugares", "🚀 Luoghi", "🚀 Miejsca", "🚀 Locais", "🚀 場所", "🚀 地点"]))
async def search_places_handler(message: Message, session: aiohttp.ClientSession, state: FSMContext):
    loading_msg, places = await perform_search(message, session, show_list=False)

    if not places:
        return

    await state.set_state(BotState.browsing_places)
    await state.update_data(places=places, current_index=0)

    try:
        await loading_msg.delete()
    except Exception as e:
        logger.warning(f"Could not delete loading message: {e}")

    await show_place_card(message, state, session)


@router.message(BotState.browsing_places, F.text.in_(["➡️ Далі", "➡️ Next", "➡️ Weiter", "➡️ Suivant", "➡️ Siguiente", "➡️ Avanti", "➡️ Dalej", "➡️ Próximo", "➡️ 次へ", "➡️ 下一个"]))
async def next_place_handler(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    places = data.get("places", [])

    if current_index < len(places) - 1:
        await state.update_data(current_index=current_index + 1)
        await show_place_card(message, state, session)
    else:
        msg_text = i18n.get(user_id, 'last_place', lang_code)
        await message.answer(msg_text)


@router.message(BotState.browsing_places, F.text.in_(["👎 Дизлайк", "👎 Dislike", "👎 Nicht gefallen", "👎 Je n'aime pas", "👎 No me gusta", "👎 Non mi piace", "👎 Nie lubię", "👎 Não gostar", "👎 嫌い", "👎 不喜欢"]))
async def dislike_place_handler(message: Message, state: FSMContext, session: aiohttp.ClientSession, bot: Bot):
    """Дизлайк: видалити повідомлення поточного місця та перейти до наступного."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    data = await state.get_data()
    current_index = data.get("current_index", 0)
    places = data.get("places", [])
    chat_id = message.chat.id

    # Видаляємо повідомлення
    msg_ids = data.get("last_place_message_ids", [])
    for mid in msg_ids:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=mid)
        except Exception as e:
            logger.warning(f"Could not delete place message {mid}: {e}")
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Could not delete user message: {e}")

    if current_index < len(places) - 1:
        await state.update_data(current_index=current_index + 1, last_place_message_ids=[])
        await show_place_card(message, state, session)
    else:
        msg_text = i18n.get(user_id, 'last_place', lang_code)
        await bot.send_message(chat_id=chat_id, text=msg_text, reply_markup=place_navigation_keyboard(user_id, lang_code))


@router.message(BotState.browsing_places, F.text.in_(["🛑 Стоп", "🛑 Stop", "🛑 Stopp", "🛑 Arrêt", "🛑 Parar", "🛑 Fermare", "🛑 Zatrzymaj", "🛑 Parar", "🛑  停止", "🛑 停止"]))
async def stop_browsing_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    fsm_data = await state.get_data()
    first_start = fsm_data.get("first_start", False)
    await state.clear()

    if first_start:
        await send_main_menu(message)
    else:
        msg_text = i18n.get(user_id, 'browsing_finished', lang_code)
        await message.answer(msg_text, reply_markup=search_keyboard(user_id, lang_code))


@router.message(BotState.browsing_places)
async def unhandled_browsing_message(message: Message, state: FSMContext):
    """Обробляє невідповідні повідомлення під час переглядання місць."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    logger.warning(
        f"Невідповідне повідомлення для BotState.browsing_places: {message.text}")
    msg_text = i18n.get(user_id, 'unknown_command', lang_code)
    await message.answer(
        msg_text,
        reply_markup=place_navigation_keyboard(user_id, lang_code)
    )


@router.message(F.text.in_([
    "🛑 Стоп", "🛑️ Стоп", "🔴 Стоп",
    "🛑 Stop", "🛑️ Stop", "🔴 Stop",
    "🛑 Stopp", "🛑️ Stopp", "🔴 Stopp",
    "🛑 Arrêt", "🛑️ Arrêt", "🔴 Arrêt",
    "🛑 Parar", "🛑️ Parar", "🔴 Parar",
    "🛑 Fermare", "🛑️ Fermare", "🔴 Fermare",
    "🛑 Zatrzymaj", "🛑️ Zatrzymaj", "🔴 Zatrzymaj",
    "🛑 停止", "🛑️ 停止", "🔴 停止",
]))
async def global_stop_fallback(message: Message, state: FSMContext):
    """Fallback: stop should always return user to a stable menu even if FSM state was lost."""
    await state.clear()
    await send_main_menu(message)


@router.callback_query(F.data.startswith("place_view:"))
async def place_details_handler(callback: CallbackQuery, session: aiohttp.ClientSession, state: FSMContext):
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

    success, _ = await send_place_info(
        callback.message, session, place_id, language, user_id=callback.from_user.id
    )

    if not success:
        user_id = callback.from_user.id
        settings = get_user_settings(user_id)
        lang_code = settings.get("language", "uk")
        msg_text = i18n.get(user_id, 'place_not_found_message', lang_code)
        await callback.message.answer(msg_text, parse_mode="HTML")
        return


@router.callback_query(F.data.startswith("fav_toggle:"))
async def fav_toggle_handler(callback: CallbackQuery, session: aiohttp.ClientSession):
    """Додає або вилучає місце з улюблених (локально та на сервері)."""
    place_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    was_favorite = is_favorite_place(user_id, place_id)
    if was_favorite:
        remove_favorite_place(user_id, place_id)
        await api_remove_favorite(user_id, place_id, session)
        await callback.answer(i18n.get(user_id, 'removed_from_favorites', lang_code))
    else:
        name = _place_name_cache.get(
            place_id, i18n.get(user_id, 'unnamed', lang_code))
        add_favorite_place(user_id, place_id, name)
        await api_add_favorite(user_id, place_id, name, session)
        await callback.answer(i18n.get(user_id, 'added_to_favorites', lang_code))

    # Оновлюємо клавіатуру - змінюємо кнопку улюблених
    try:
        old_markup = callback.message.reply_markup
        if old_markup:
            new_keyboard = []
            for row in old_markup.inline_keyboard:
                new_row = []
                for button in row:
                    if button.callback_data and button.callback_data.startswith("fav_toggle:"):
                        # Змінюємо текст кнопки на протилежний
                        new_text = i18n.get(user_id, 'add_to_favorites', lang_code) if was_favorite else i18n.get(
                            user_id, 'remove_from_favorites', lang_code)
                        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
                        new_row.append(InlineKeyboardButton(
                            text=new_text, callback_data=button.callback_data))
                    else:
                        new_row.append(button)
                new_keyboard.append(new_row)
            await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=new_keyboard))
    except Exception as e:
        logger.warning(f"Could not update favorite button: {e}")


@router.message(StateFilter(BotState.comparing_favorites), F.text.in_(["🔙 Скасувати", "🔙 Cancel", "🔙 Abbrechen", "🔙 Annuler", "🔙 Cancelar", "🔙 Annulla", "🔙 Anuluj", "🔙 Cancelar", "🔙 キャンセル", "🔙 取消"]))
async def comparison_cancel_handler(message: Message, state: FSMContext):
    """Скасовує порівняння через кнопку."""
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    await state.clear()
    msg_text = i18n.get(user_id, 'comparison_cancelled', lang_code)
    await message.answer(msg_text)
    back_text = i18n.get(user_id, 'back_to_main_menu', lang_code)
    await message.answer(back_text, reply_markup=search_keyboard(user_id, lang_code))


@router.callback_query(F.data.startswith("compare_toggle:"))
async def compare_toggle_handler(callback: CallbackQuery, state: FSMContext):
    """Додає або видаляє місце із виділення для порівняння."""
    place_id = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    data = await state.get_data()
    selected_ids = data.get("selected_for_comparison", [])

    if place_id in selected_ids:
        selected_ids.remove(place_id)
    else:
        selected_ids.append(place_id)

    await state.update_data(selected_for_comparison=selected_ids)

    # Оновлюємо клавіатуру
    favorites = get_favorite_places(user_id)
    kb = select_favorites_for_comparison_keyboard(
        favorites, selected_ids, user_id, lang_code)

    await callback.message.edit_reply_markup(reply_markup=kb)

    count = len(selected_ids)
    if count >= 2:
        await callback.answer(f"✅ {i18n.get(callback.from_user.id, 'comparison_selected', callback.from_user.language_code)}: {count}")
    else:
        await callback.answer(f"⚖️ {count} / 2")


@router.callback_query(F.data == "perform_comparison")
async def perform_comparison_handler(callback: CallbackQuery, state: FSMContext, session: aiohttp.ClientSession):
    """Виконує порівняння обраних місць."""
    user_id = callback.from_user.id
    data = await state.get_data()
    selected_ids = data.get("selected_for_comparison", [])

    if len(selected_ids) < 2:
        await callback.answer(i18n.get(user_id, 'comparison_min_2', callback.from_user.language_code), show_alert=True)
        return

    await callback.answer()

    # Показуємо повідомлення про завантаження
    lang_code = callback.from_user.language_code
    loading_msg = await callback.message.answer(
        i18n.get(user_id, 'loading_comparison', lang_code),
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
            favorite = next(
                (p for p in favorites if p["id"] == place_id), None)
            if not favorite:
                continue

            # Отримуємо деталі місця
            place_details = await get_place_details(place_id, session, language)
            if place_details:
                places_details.append(place_details)

        if not places_details:
            lang_code = callback.from_user.language_code
            await loading_msg.edit_text(
                i18n.get(user_id, 'places_details_error', lang_code),
                parse_mode="HTML"
            )
            return

        # Форматуємо й надсилаємо порівняння
        lang_code = callback.from_user.language_code
        comparison_text = format_comparison_text(
            places_details,
            user_coords=user_coords,
            user_id=user_id,
            lang_code=lang_code
        )
        await loading_msg.edit_text(comparison_text, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Error in perform_comparison_handler: {e}")
        lang_code = callback.from_user.language_code
        await loading_msg.edit_text(
            i18n.get(user_id, 'comparison_error', lang_code),
            parse_mode="HTML"
        )
    finally:
        await state.clear()


@router.callback_query(F.data == "cancel_comparison")
async def cancel_comparison_handler(callback: CallbackQuery, state: FSMContext):
    """Скасовує порівняння й повертається до меню."""
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    await state.clear()
    await callback.answer()
    msg_text = i18n.get(user_id, 'comparison_cancelled', lang_code)
    await callback.message.edit_text(
        msg_text,
        parse_mode="HTML"
    )
    back_text = i18n.get(user_id, 'back_to_main_menu', lang_code)
    await callback.message.answer(back_text, reply_markup=search_keyboard(user_id, lang_code))


@router.callback_query(F.data == "comparison_help")
async def comparison_help_handler(callback: CallbackQuery):
    """Показує довідку про мінімальну кількість місць для порівняння."""
    user_id = callback.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    help_text = i18n.get(user_id, 'comparison_help_text', lang_code)
    await callback.answer(
        help_text,
        show_alert=False
    )
