
import aiohttp
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.states import BotState
from bot.keyboards import (
    actions_keyboard,
    choose_location_type_keyboard,
    settings_keyboard,
    test_keyboard,
    error_action_inline_keyboard,
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
from bot.utils.localization import i18n
from bot.model.types_dict import SearchTypes

router = Router()

@router.message(F.text.in_(["🔍 Пошук маршрутів", "🔍 Search routes", "🔍 Suche nach Routen", "🔍 Recherche d'itinéraires", "🔍 Buscar rutas", "🔍 Cerca percorsi", "🔍 Szukaj tras", "🔍 Pesquisar rotas", "🔍 検索ルート", "🔍 搜索路线"]))
async def search_routes_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    if not settings.get("coordinates"):
        await message.answer(
            i18n.get(user_id, 'how_to_use_bot', lang_code),
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard(user_id, lang_code)
        )
        return

def _format_language_display(lang_code: str) -> str:
    """Повертає назву мови з прапорцем у форматі: Українська 🇺🇦."""
    value = i18n.get_available_languages().get(lang_code, lang_code)
    parts = value.split(" ", 1)
    if len(parts) == 2:
        flag, name = parts[0], parts[1]
        return f"{name} {flag}"
    return value


async def _save_coordinates_and_sync(
    user_id: int,
    latitude: float,
    longitude: float,
    session: aiohttp.ClientSession,
    city_name: str | None = None,
):
    """Зберігає координати, локальний підпис локації та відправляє налаштування на сервер."""
    save_coordinates(user_id, latitude, longitude)
    settings = get_user_settings(user_id)
    settings["location_city"] = city_name.strip() if city_name else None
    await api_save_user_settings(user_id, get_settings_payload_for_api(user_id), session)


@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await send_main_menu(message)


@router.message(F.text.in_(["📍 Передати координати", "📍 Надіслати геолокацію", "📍 Send coordinates", "📍 Envoyer les coordonnées", "📍 Koordinaten senden", "📍 Enviar coordenadas", "📍 Invia coordinate", "📍 Wyślij współrzędne", "📍 Enviar coordenadas", "📍 座標を送信", "📍 发送坐标"]))
async def show_location_choice_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    # Keep FSM data (e.g., first_start flag) and only switch state.
    await state.set_state(BotState.choosing_location_type)
    await message.answer(
        i18n.get(user_id, 'choose_location_type', lang_code),
        reply_markup=choose_location_type_keyboard(user_id, lang_code)
    )


def settings_text(user_id: int, telegram_lang_code: str = None) -> str:
    s = get_user_settings(user_id)
    # Використовуємо мову з налаштувань користувача
    lang_code = s.get('language', 'uk')
    language_display = _format_language_display(lang_code)
    rank_code = (s.get("rankPreference") or "POPULARITY").upper()
    rank_display = i18n.get(user_id, 'rank_distance', lang_code) if rank_code == "DISTANCE" else i18n.get(
        user_id, 'rank_popularity', lang_code)

    mood_code = (s.get("mood") or "").strip().lower()
    mood_key_map = {
        "work": "mood_work",
        "date": "mood_date",
        "company": "mood_company",
        "breakfast": "mood_breakfast",
    }
    included_types = s.get("includedTypes", [])
    mood_key = mood_key_map.get(mood_code)
    if not mood_key and included_types:
        included_set = set(included_types)
        reverse_mood_code_map = {v: k for k,
                                 v in SearchTypes.mood_code_map.items()}
        for mood_label, mood_types in SearchTypes.mood_types.items():
            if included_set == set(mood_types):
                inferred_mood_code = reverse_mood_code_map.get(mood_label)
                mood_key = mood_key_map.get(inferred_mood_code)
                if mood_key:
                    break
    if mood_key:
        # Якщо обраний настрій — показуємо його назву
        categories = i18n.get(user_id, mood_key, lang_code)
    elif included_types:
        # Якщо вручну обрані категорії — показуємо їх
        categories = ", ".join(included_types)
    else:
        categories = i18n.get(user_id, 'all', lang_code)

    open_now = s.get("openNow", False)
    open_status = i18n.get(user_id, 'open_yes', lang_code) if open_now else i18n.get(
        user_id, 'open_no', lang_code)
    location_city = (s.get("location_city") or "").strip()
    if location_city:
        location_value = location_city
    elif s.get("coordinates"):
        location_value = "GPS"
    else:
        location_value = i18n.get(user_id, 'none', lang_code)

    return (
        f"{i18n.get(user_id, 'settings_title', lang_code)}\n"
        f"├ {i18n.get(user_id, 'settings_lang_label', lang_code, language=language_display)}\n"
        f"├ {i18n.get(user_id, 'settings_radius_label', lang_code, radius=s.get('radius', 1000))}\n"
        f"├ {i18n.get(user_id, 'settings_categories_compact', lang_code, categories=categories)}\n"
        f"├ {i18n.get(user_id, 'settings_rank_label', lang_code, rank=rank_display)}\n"
        f"├ {i18n.get(user_id, 'settings_location_label', lang_code, location=location_value)}\n"
        f"└ {i18n.get(user_id, 'settings_open_label', lang_code, status=open_status)}"
    )


async def send_main_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None, force_main_menu_keyboard: bool = False):
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    lang_code = s.get('language', 'uk')
    coords = s.get("coordinates")

    if force_main_menu_keyboard:
        reply_kb = actions_keyboard(target_user_id, lang_code)
    else:
        if coords:
            reply_kb = actions_keyboard(target_user_id, lang_code)
        else:
            reply_kb = choose_location_type_keyboard(target_user_id, lang_code)

    text = (
        f"{i18n.get(target_user_id, 'welcome', lang_code)}\n\n"
        f"{settings_text(target_user_id, lang_code)}"
    )
    lat = coords.get("latitude") if coords else None
    lon = coords.get("longitude") if coords else None
    if lat is not None and lon is not None:
        text += "\n\n" + i18n.get(
            target_user_id, "coordinates_label", lang_code,
            latitude=lat, longitude=lon,
        )

    await message.answer(text, parse_mode="HTML", reply_markup=reply_kb)


async def send_settings_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None):
    """Показує екран налаштувань і клавіатуру (включно з кнопкою «Зберегти на сервер»)."""
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    # Використовуємо мову з налаштувань користувача
    lang_code = s.get('language', 'uk')
    await message.answer(
        settings_text(target_user_id, lang_code),
        parse_mode="HTML",
        reply_markup=settings_keyboard(target_user_id, lang_code),
    )


@router.message(F.text.in_(["⚙️ Налаштування", "⚙️ Settings", "⚙️ Einstellungen", "⚙️ Paramètres", "⚙️ Ajustes", "⚙️ Impostazioni", "⚙️ Ustawienia", "⚙️ Configurações", "⚙️ 設定", "⚙️ 设置"]))
async def show_settings_menu(message: Message):
    await send_settings_menu(message)


@router.message(F.text.in_(["💾 Зберегти налаштування", "💾 Save settings", "💾 Einstellungen speichern", "💾 Enregistrer les paramètres", "💾 Guardar configuración", "💾 Salva impostazioni", "💾 Zapisz ustawienia", "💾 Salvar configurações", "💾 設定を保存", "💾 保存设置"]))
async def settings_save_handler(message: Message, session: aiohttp.ClientSession):
    """Обробник кнопки «Зберегти на сервер» — відправляє поточні налаштування на API."""
    user_id = message.from_user.id
    s = get_user_settings(user_id)
    lang_code = s.get('language', 'uk')
    payload = get_settings_payload_for_api(user_id)
    result = await api_save_user_settings(user_id, payload, session)
    if result is not None:
        await message.answer(i18n.get(user_id, 'settings_saved', lang_code))
    else:
        await message.answer(i18n.get(user_id, 'settings_save_failed', lang_code))


@router.message(F.text.in_(["🔙 Назад", "🔙 Back", "🔙 Zurück", "🔙 Retour", "🔙 Atrás", "🔙 Indietro", "🔙 Wstecz", "🔙 Voltar", "🔙 戻る", "🔙 返回"]))
async def back_to_main_menu(message: Message):
    await send_main_menu(message)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    telegram_lang_code = (message.from_user.language_code or "").lower()
    mapped_lang = i18n.LANGUAGE_MAPPING.get(
        telegram_lang_code, telegram_lang_code)
    detected_lang = i18n.LANGUAGE_CODES.get(mapped_lang, mapped_lang)
    if detected_lang not in i18n.get_available_languages():
        detected_lang = 'en'

    logger.info(f"/start: user_id={user_id}, detected_lang={detected_lang}")

    # Отримуємо дані користувача з API
    data, status = await api_get_user(user_id, session)
    if status == 200 and data:
        apply_user_data_from_api(user_id, data)
    elif status == 404:
        created = await api_save_user(user_id, session)
        if created is not None:
            apply_user_data_from_api(user_id, created)

    settings = get_user_settings(user_id)
    current_language = settings.get("language")
    settings["language"] = detected_lang
    i18n.set_user_language(user_id, detected_lang)

    if current_language != detected_lang:
        payload = get_settings_payload_for_api(user_id)
        await api_save_user_settings(user_id, payload, session)
        logger.info(
            f"Set user language from Telegram and saved to server: {detected_lang}")

    await state.update_data(first_start=True)
    await message.answer(i18n.get(user_id, 'start_intro', detected_lang))
    await message.answer(
        i18n.get(user_id, 'choose_action', detected_lang),
        reply_markup=test_keyboard(user_id, detected_lang),
    )


@router.callback_query(F.data == "start_continue")
async def start_continue_callback(callback: CallbackQuery):
    """Продовжити з автоматично визначеною мовою"""
    user_id = callback.from_user.id
    await callback.answer()
    await callback.message.delete()
    await send_main_menu(callback.message, user_id=user_id)

    # Одразу показуємо головне меню (вибір мови лише в налаштуваннях)
    # Якщо координат немає - спочатку просимо їх надати
    settings = get_user_settings(user_id)
    detected_lang = settings.get("language", "uk")
    if not settings.get("coordinates"):
        await callback.message.answer(
            i18n.get(user_id, 'how_to_use_bot', detected_lang),
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard(user_id, detected_lang),
        )
    else:
        await send_main_menu(callback.message, user_id=user_id, telegram_lang_code=detected_lang)


@router.message(F.location)
async def handle_location_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    lat, lon = message.location.latitude, message.location.longitude
    logger.info(
        f"Користувач {message.from_user.username}({user_id}) надіслав локацію: {lat}, {lon}")
    await _save_coordinates_and_sync(user_id, lat, lon, session)

    # Перевірка доступності сервера (get_places)
    from bot.services.api_client import get_places
    try:
        settings_check = get_user_settings(user_id)
        data = await get_places(settings_check, session)
        if data is None:
            raise Exception("Server unavailable")
    except Exception:
        from aiogram.types import ReplyKeyboardRemove
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=i18n.get(user_id, 'menu_back', lang_code))],
                [KeyboardButton(text="🔄 " + i18n.get(user_id, 'retry', lang_code))]
            ],
            resize_keyboard=True,
        )
        await message.answer(
            i18n.get(user_id, 'server_unavailable', lang_code),
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        return

    fsm_data = await state.get_data()
    first_start = fsm_data.get("first_start", False)
    await state.clear()

    if first_start:
        # First start flow: coordinates -> mood -> search.
        await state.update_data(first_start=True)
        builder = InlineKeyboardBuilder()
        moods = [
            ("mood_work", "work"),
            ("mood_date", "date"),
            ("mood_company", "company"),
            ("mood_breakfast", "breakfast"),
        ]
        for mood_key, mood_code in moods:
            builder.button(
                text=i18n.get(user_id, mood_key, lang_code),
                callback_data=f"set_mood:{mood_code}"
            )
        builder.adjust(1)
        await message.answer(
            i18n.get(user_id, 'choose_mood', lang_code, current=""),
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
        return

    await message.answer(
        i18n.get(user_id, 'location_received', lang_code),
        reply_markup=actions_keyboard(user_id, lang_code),
    )

    # Показуємо координати у форматі поточної мови інтерфейсу
    title = i18n.get(user_id, 'your_coordinates', lang_code)
    lat_label = i18n.get(user_id, 'latitude_label', lang_code)
    lon_label = i18n.get(user_id, 'longitude_label', lang_code)
    await message.answer(
        f"{title}\n{lat_label} {lat}\n{lon_label} {lon}",
        parse_mode="HTML",
    )


@router.message(F.text.in_(["🏙️ Знайти потрібне місто", "🏙️ Find a city", "🏙️ Stadt finden", "🏙️ Trouver une ville", "🏙️ Encontrar ciudad", "🏙️ Trova città", "🏙️ Znajdź miasto", "🏙️ Encontrar cidade", "🏙️ 都市を検索", "🏙️ 查找城市"]))
async def ask_for_city_name_main_menu(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    await state.set_state(BotState.entering_coordinates)
    await message.answer(
        i18n.get(user_id, 'enter_city_name', lang_code)
    )


@router.message(StateFilter(BotState.entering_coordinates))
async def handle_city_input_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    text = message.text.strip()
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")

    await message.answer(i18n.get(user_id, 'searching_city', lang_code, city=text))
    coords = await get_city_coordinates(text, session, lang_code)
    if coords and coords.get("latitude") is not None and coords.get("longitude") is not None:
        await _save_coordinates_and_sync(
            user_id, coords["latitude"], coords["longitude"], session, city_name=text
        )

        fsm_data = await state.get_data()
        first_start = fsm_data.get("first_start", False)
        await state.clear()

        await message.answer(
            i18n.get(user_id, 'city_found', lang_code, city=text)
        )

        if first_start:
            # First start flow: coordinates -> mood -> search.
            await state.update_data(first_start=True)
            builder = InlineKeyboardBuilder()
            moods = [
                ("mood_work", "work"),
                ("mood_date", "date"),
                ("mood_company", "company"),
                ("mood_breakfast", "breakfast"),
            ]
            for mood_key, mood_code in moods:
                builder.button(
                    text=i18n.get(user_id, mood_key, lang_code),
                    callback_data=f"set_mood:{mood_code}"
                )
            builder.adjust(1)
            await message.answer(
                i18n.get(user_id, 'choose_mood', lang_code, current=""),
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
            return

        await send_main_menu(message, telegram_lang_code=lang_code)
    else:
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        reply_markup = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text=i18n.get(user_id, 'menu_back', lang_code))],
                [KeyboardButton(text="🔄 " + i18n.get(user_id, 'retry', lang_code))]
            ],
            resize_keyboard=True,
        )
        await message.answer(
            i18n.get(user_id, 'city_not_found', lang_code, city=text),
            reply_markup=reply_markup
        )

@router.message(F.text == i18n.get(0, 'menu_back', 'uk'))
async def back_to_main_menu_action(message: Message):
    await send_main_menu(message)

@router.message(F.text == "🔄 " + i18n.get(0, 'retry', 'uk'))
async def retry_city_search(message: Message, state: FSMContext):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    await state.set_state(BotState.choosing_location_type)
    await message.answer(
        i18n.get(user_id, 'choose_location_type', lang_code),
        reply_markup=choose_location_type_keyboard(user_id, lang_code)
    )
