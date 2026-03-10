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
from bot.utils.localization import i18n

router = Router()


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
    await state.clear()
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
    rank_display = i18n.get(user_id, 'rank_distance', lang_code) if rank_code == "DISTANCE" else i18n.get(user_id, 'rank_popularity', lang_code)

    categories = ", ".join(s.get("includedTypes", [])) if s.get(
        "includedTypes") else i18n.get(user_id, 'all', lang_code)

    open_now = s.get("openNow", False)
    open_status = i18n.get(user_id, 'open_yes', lang_code) if open_now else i18n.get(user_id, 'open_no', lang_code)

    return (
        f"{i18n.get(user_id, 'settings_title', lang_code)}\n"
        f"├ {i18n.get(user_id, 'settings_lang_label', lang_code, language=language_display)}\n"
        f"├ {i18n.get(user_id, 'settings_radius_label', lang_code, radius=s.get('radius', 1000))}\n"
        f"├ {i18n.get(user_id, 'settings_categories_compact', lang_code, categories=categories)}\n"
        f"├ {i18n.get(user_id, 'settings_rank_label', lang_code, rank=rank_display)}\n"
        f"└ {i18n.get(user_id, 'settings_open_label', lang_code, status=open_status)}"
    )


async def send_main_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None):
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    # Використовуємо мову з налаштувань користувача
    lang_code = s.get('language', 'uk')
    coords = s.get("coordinates")

    if coords:
        location_city = (s.get("location_city") or "").strip()
        if location_city:
            location_line = f"📍 Локація: {location_city}"
        else:
            location_line = "📍 Локація: Визначено за GPS"
        reply_kb = actions_keyboard(target_user_id, lang_code)
    else:
        reply_kb = choose_location_type_keyboard(target_user_id, lang_code)

    await message.answer(
        f"{i18n.get(target_user_id, 'welcome', lang_code)}\n\n"
        f"{settings_text(target_user_id, lang_code)}",
        reply_markup=reply_kb,
    )


async def send_settings_menu(message: Message, user_id: int | None = None, telegram_lang_code: str = None):
    """Показує екран налаштувань і клавіатуру (включно з кнопкою «Зберегти на сервер»)."""
    target_user_id = user_id or message.from_user.id
    s = get_user_settings(target_user_id)
    # Використовуємо мову з налаштувань користувача
    lang_code = s.get('language', 'uk')
    await message.answer(
        settings_text(target_user_id, lang_code),
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
async def cmd_start(message: Message, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    lang_code = message.from_user.language_code
    
    # Автоматично визначаємо мову користувача
    detected_lang = i18n.get_user_language(user_id, lang_code)
    logger.info(f"/start: user_id={user_id}, detected_lang={detected_lang}")

    # Отримуємо дані користувача з API
    data, status = await api_get_user(user_id, session)
    if status == 200 and data:
        apply_user_data_from_api(user_id, data)
    elif status == 404:
        created = await api_save_user(user_id, session)
        if created is not None:
            apply_user_data_from_api(user_id, created)
    
    # Встановлюємо визначену мову з Telegram, якщо у налаштуваннях ще не встановлена
    settings = get_user_settings(user_id)
    current_language = settings.get("language")
    
    # Якщо мова не була збережена на сервері (None, порожній рядок), встановлюємо detected_lang
    if not current_language:
        settings["language"] = detected_lang
        i18n.set_user_language(user_id, detected_lang)
        
        # Зберігаємо налаштування на сервер
        payload = get_settings_payload_for_api(user_id)
        await api_save_user_settings(user_id, payload, session)
        logger.info(f"Set user language to detected and saved to server: {detected_lang}")
    else:
        # Використовуємо мову з сервера
        detected_lang = current_language
        i18n.set_user_language(user_id, detected_lang)
        logger.info(f"Using language from server: {current_language}")

    # Одразу показуємо головне меню (вибір мови лише в налаштуваннях)
    # Якщо координат немає - спочатку просимо їх надати
    settings = get_user_settings(user_id)
    if not settings.get("coordinates"):
        await message.answer(
            i18n.get(user_id, 'how_to_use_bot', detected_lang),
            parse_mode="HTML",
            reply_markup=choose_location_type_keyboard(user_id, detected_lang),
        )
    else:
        await send_main_menu(message, user_id=user_id, telegram_lang_code=detected_lang)


@router.message(F.location)
async def handle_location_main_menu(message: Message, state: FSMContext, session: aiohttp.ClientSession):
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    lang_code = settings.get("language", "uk")
    lat, lon = message.location.latitude, message.location.longitude
    logger.info(f"Користувач {message.from_user.username}({user_id}) надіслав локацію: {lat}, {lon}")
    await _save_coordinates_and_sync(user_id, lat, lon, session)
    await state.clear()
    
    # Показуємо повідомлення про отримання локації
    await message.answer(
        i18n.get(user_id, 'location_received', lang_code),
        reply_markup=actions_keyboard(user_id, lang_code),
    )
    
    # Показуємо координати українською
    title = i18n.get(user_id, 'your_coordinates', lang_code)
    lat_label = i18n.get(user_id, 'latitude_label', lang_code)
    lon_label = i18n.get(user_id, 'longitude_label', lang_code)
    await message.answer(
        f"{title}\n{lat_label} {lat}\n{lon_label} {lon}",
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
        await state.clear()
        await message.answer(
            i18n.get(user_id, 'city_found', lang_code, city=text)
        )
        
        # Показуємо координати
        title = i18n.get(user_id, 'your_coordinates', lang_code)
        lat_label = i18n.get(user_id, 'latitude_label', lang_code)
        lon_label = i18n.get(user_id, 'longitude_label', lang_code)
        await message.answer(
            f"{title}\n{lat_label} {coords['latitude']}\n{lon_label} {coords['longitude']}",
        )
        
        await send_main_menu(message, telegram_lang_code=lang_code)
    else:
        await message.answer(
            i18n.get(user_id, 'city_not_found', lang_code, city=text)
        )
